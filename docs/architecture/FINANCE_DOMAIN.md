# Nova Finance Domain — Architecture (Design Only)

**Status:** Design only. Nothing in this document is implemented.
**Context:** Written after Gate C, before any Gate D work. Replaces the "Spending" feature with a full Finance domain.
**Scope:** Finance domain only. The overall Nova architecture (Electron → React → React Query → dataSource → nova-api → FastAPI → memory → MutationEvent → `finalize_mutations()`) is unchanged and is a hard constraint on every choice below.
**Out of scope (unchanged from ROADMAP.md):** bank/UPI sync, receipt OCR, automatic transaction import, any second credential. All data enters by hand, chat, or voice.

---

## 0. Review of the current implementation

### What exists today

| Layer | Artifact | Shape |
|---|---|---|
| DB | `money` table | `id, type ('earned'\|'spent'), amount REAL, note, created_at` |
| Memory | `memory/money.py` | add, get-by-id, get-latest (chat translator), recent, since, totals-between |
| Service | `planner/api_commands.log_spending()` | validates type, inserts, returns (row, message) |
| API | `/spending` GET/POST, `/spending/summary` GET | month totals + recent list; POST emits `spending.logged` via `build_spending_logged` → `finalize_mutations()` |
| Contracts | `SpendingResponse`, `LogSpendingRequest`, `SpendingMutationResponse` | in `packages/api-contracts` |
| Desktop | `spending-screen.tsx`, `use-spending*`, `mappers/spending.ts` | two total cards + flat transaction list + inline add form |
| Events | `spending.logged` → invalidates `spending`, `home` query keys | via `invalidation-map.ts` |

### Structural limitations

1. **No concept of *where* money lives.** A single flat ledger cannot express credit cards, loans, or balances — everything a dashboard needs starts with accounts.
2. **`created_at` doubles as the transaction date.** You cannot log yesterday's expense. Domain date (`occurred_at`) and row-audit date (`created_at`) are conflated.
3. **No category, merchant, or account dimension** — nothing to group or chart by.
4. **No update or delete.** A typo is permanent. (Nothing on desktop has update/delete yet; Finance will be the first domain to need it, so it sets the pattern.)
5. **Amounts are REAL floats.** Fine for logging, wrong for balances, utilization percentages, and EMI arithmetic that must sum exactly.
6. **`type` conflates direction with meaning.** "earned/spent" cannot express a credit-card payment (a transfer, neither income nor expense), a refund, or a cashback credit.
7. **`entity_type="money"` / `operation="log"`** is a dead-end vocabulary — there is no natural `money.updated` or second money entity.

None of this is wrong for what Phase 2 asked for; it simply cannot grow into a financial dashboard. The pipeline around it, however, is exactly right and is reused wholesale.

---

## 1. Domain architecture

Finance decomposes into **five primitive concepts**. Every requested feature is one of these or a projection over them.

```
                    ┌────────────────────────────────────────────┐
                    │              FINANCE DOMAIN                 │
                    │                                            │
   ┌──────────┐    │  ┌──────────┐        ┌───────────────────┐ │
   │ Accounts │◀───┼──│Transactions│──────▶│ Recurring rules   │ │
   │ cash/bank│    │  │  (ledger)  │       │ bills/EMIs/subs   │ │
   │ card/loan│    │  └──────────┘        └───────────────────┘ │
   │ invest*  │    │        │                      │             │
   └──────────┘    │        ▼                      ▼             │
        │          │  ┌──────────┐        ┌───────────────────┐ │
        │          │  │Statements│        │ Rewards & benefits│ │
        │          │  │ (cycles) │        │ (ledger + catalog)│ │
        │          │  └──────────┘        └───────────────────┘ │
        └──────────┴────────────────────────────────────────────┘
                                │
                     read-only projections
                                ▼
        Dashboard · Net worth* · Credit utilization · Upcoming payments
                                                        (* = future)
```

| Concept | Owns | Covers requested features |
|---|---|---|
| **Accounts** | anything with a balance or a debt: cash, bank, credit card, loan, investment (future). Card- and loan-specific attributes live in satellite profiles. | Credit Cards, Loan tracking, Net Worth (future), Investments (future) |
| **Transactions** | every money movement: expense, income, transfer, card payment, refund, cashback credit. Linked to an account; optionally to a recurring rule and a statement. | Transactions, cashback tracking (per-txn) |
| **Recurring rules** | one table for bills, subscriptions, and EMIs — same lifecycle (amount, cadence, due day, autopay), differentiated by `kind`. EMIs additionally link to a loan account. | Bills, EMIs, Subscriptions, Payment reminders |
| **Statements** | per-card billing cycles: period, statement total, min due, due date, paid state. | Statement cycle management, credit utilization history, due alerts |
| **Rewards & benefits** | per-card reward program (points or cashback, balance) + event ledger (earn/redeem/expire), and a benefits catalog (lounge visits, milestone vouchers) with usage/expiry. | Cashback tracking, Reward points, Card benefits |

**Projections, not entities:** Dashboard, Net Worth, Credit Utilization, and Upcoming Payments are *computed read models* over the five primitives — the same pattern as `services/api/projections/home.py`. They own no storage and require no CRUD. Payment reminders are derived from recurring rules + statement due dates; an optional sweep can materialize them into the existing `reminders` domain (reusing Gate C) rather than inventing a parallel reminder system.

### Backend module placement (obeys ARCHITECTURE_v2 governing rules)

- **`memory/finance/`** — new sub-package beside `memory/money.py`: one module per table family (`accounts.py`, `transactions.py`, `recurring.py`, `statements.py`, `rewards.py`). Memory remains the only persistence owner; tables are created idempotently from `memory/schema.py` exactly like every existing table.
- **`services/finance/`** — new leaf service (rule 3: new capability = new leaf). Owns domain logic that is more than a row insert: dashboard aggregation, utilization math, upcoming-payment projection, statement-cycle sweep, mark-paid orchestration (create txn + link instance + update statement). It does **not** call Claude and does **not** open the DB directly — it calls `memory.finance.*`.
- **`services/api/routers/finance/`** — thin routers per sub-resource, same shape as `routers/spending.py`: validate → call service/memory → build mutation events → `finalize_mutations()` → typed response.
- **`runtime/mutation_builders.py`** — new pure builders (`build_transaction_created`, `build_account_updated`, …). `MutationEvent` stays untouched; the existing dataclass already expresses everything Finance needs.
- **`memory_producers.py`** — policy additions only where a mutation is genuinely memorable (see §5 event table). Routine transaction logging should *not* produce semantic memories (noise); loan closure, card added, large one-off expenses (above a config threshold) are candidates.
- **Chat path:** planner commands gain finance verbs over time; `mutation_chat.py` translates them to the same events. Parity tests per gate, same as Gate A.

---

## 2. Database model suggestions

All tables created idempotently in `init_db()`; existing `_migrate_*` pattern reused. `TEXT` ISO timestamps, consistent with the rest of the schema.

**Money representation:** store amounts as **INTEGER minor units (paise)** in all new tables (`amount_minor`), with a `currency TEXT DEFAULT 'INR'` column on accounts. Balances, utilization %, and EMI schedules must sum exactly; REAL cannot guarantee that. The UI already formats via `formatINR` — only the mapper changes.

**Soft delete:** `deleted_at` on user-editable tables (transactions, recurring rules, benefits), consistent with the memories philosophy that migration/deletion never destroys data.

### `accounts`
| Column | Notes |
|---|---|
| `id` | PK |
| `name` | "HDFC Millennia", "Cash", "Home Loan" |
| `type` | `cash` \| `bank` \| `credit_card` \| `loan` \| `investment` (future) |
| `classification` | `asset` \| `liability` — makes Net Worth a two-line SUM later |
| `currency` | default `INR` |
| `opening_balance_minor`, `current_balance_minor` | current balance maintained by transaction writes |
| `is_archived` | closed accounts stay for history |
| `created_at`, `updated_at` | |

### `card_profiles` (1:1 with a `credit_card` account)
| Column | Notes |
|---|---|
| `account_id` | PK, FK → accounts |
| `network`, `last4`, `issuer` | display |
| `credit_limit_minor` | denominator for utilization |
| `statement_day` | day-of-month the cycle closes → drives statement generation |
| `due_day_offset` | days from statement date to payment due date |
| `autopay` | flag |

### `loan_profiles` (1:1 with a `loan` account)
| Column | Notes |
|---|---|
| `account_id` | PK, FK → accounts |
| `principal_minor`, `interest_rate_bps` | rate in basis points (integer) |
| `tenure_months`, `start_date` | |
| `emi_amount_minor` | user-entered (no amortization engine needed initially) |
| `lender` | display |

### `transactions` (replaces `money`)
| Column | Notes |
|---|---|
| `id` | PK |
| `account_id` | FK → accounts (which account the money moved on) |
| `direction` | `debit` \| `credit` (effect on the account) |
| `kind` | `expense` \| `income` \| `transfer` \| `card_payment` \| `refund` \| `fee` \| `interest` \| `cashback` |
| `amount_minor` | |
| `category` | TEXT from a canonical list in config (a categories table is deferred until proven needed) |
| `merchant` | optional TEXT |
| `note` | |
| `occurred_at` | domain date — separable from `created_at` (fixes limitation #2) |
| `recurring_rule_id` | nullable FK — "this payment satisfied that bill/EMI/subscription" |
| `statement_id` | nullable FK — assignment to a card cycle |
| `transfer_peer_id` | nullable self-FK — the other leg of a transfer/card payment |
| `source` | `manual` \| `chat` \| `voice` \| `migrated_money` |
| `legacy_money_id` | nullable — idempotent backfill key (see §7) |
| `created_at`, `updated_at`, `deleted_at` | |

### `recurring_rules` (bills + subscriptions + EMIs unified)
| Column | Notes |
|---|---|
| `id` | PK |
| `kind` | `bill` \| `subscription` \| `emi` |
| `name` | "Electricity", "Netflix", "Car loan EMI" |
| `amount_minor` | expected amount (`is_variable` flag for bills that fluctuate) |
| `cadence` | `monthly` \| `quarterly` \| `yearly` \| `weekly` |
| `due_day` | day-of-month (or weekday for weekly) |
| `account_id` | payment source (which card/bank pays it) |
| `loan_account_id` | nullable FK — set only for `kind='emi'` |
| `autopay` | drives reminder behavior (autopay → "verify", manual → "pay") |
| `starts_on`, `ends_on` | `ends_on` derivable from loan tenure for EMIs |
| `is_active`, `created_at`, `updated_at`, `deleted_at` | |

**Occurrences are computed, not materialized.** "Next due" is derived from `cadence + due_day + linked paid transactions`. A `paid` occurrence is simply a transaction with `recurring_rule_id` set in that period. This avoids a generator job, a backlog of phantom unpaid rows, and reconciliation bugs. If reminder *notifications* are wanted, a nightly sweep writes deduplicated rows into the existing `reminders` table (Gate C infrastructure) — Finance never grows its own notification channel.

### `statements` (per credit card)
| Column | Notes |
|---|---|
| `id` | PK |
| `account_id` | FK → accounts (credit_card) |
| `period_start`, `period_end`, `statement_date`, `due_date` | dates generated from `card_profiles.statement_day` |
| `total_due_minor`, `min_due_minor` | user-entered when the statement arrives (no bank sync) |
| `paid_amount_minor`, `status` | `open` \| `generated` \| `paid` \| `partial` \| `overdue` |
| `created_at`, `updated_at` | |

Cycle rows are created by a lightweight sweep in `services/finance` (invoked on API access, like entity extraction's lazy scheduling — no new daemon). Utilization = card balance ÷ credit limit (live) and statement total ÷ limit (historical).

### `reward_programs` (1:1 or 1:N with a card) and `reward_events`
| `reward_programs` | `reward_events` |
|---|---|
| `id`, `account_id`, `type` (`points` \| `cashback`), `balance` (points) or `balance_minor` (cashback), `notes` (earn-rate rules as text — Nova is not a rewards calculator), `expiry_policy` | `id`, `program_id`, `kind` (`earned` \| `redeemed` \| `expired` \| `adjusted`), `amount` / `amount_minor`, `transaction_id` nullable FK, `note`, `occurred_at`, `created_at` |

### `card_benefits`
| Column | Notes |
|---|---|
| `id`, `account_id` | FK → accounts (credit_card) |
| `title`, `description` | "8 lounge visits/year", "₹1000 voucher at 1L spend milestone" |
| `kind` | `lounge` \| `voucher` \| `milestone` \| `insurance` \| `other` |
| `quota`, `used_count`, `period` | e.g. 8 per `year` |
| `expires_at` | for vouchers |
| `created_at`, `updated_at`, `deleted_at` | |

### Future (designed-for, not built)
- **Investments:** `holdings` (account_id, instrument, units, cost_basis_minor) + `valuation_snapshots` (holding_id, value_minor, as_of). The `investment` account type and `classification` column already reserve their place.
- **Net worth:** first version is a pure projection — SUM(asset balances) − SUM(liability balances) + latest valuations. Add `net_worth_snapshots` only when trend history is wanted.

### Indexes
`transactions(occurred_at)`, `transactions(account_id, occurred_at)`, `transactions(recurring_rule_id)`, `transactions(legacy_money_id)` unique-where-not-null, `statements(account_id, period_start)` unique, partial index on active recurring rules — matching the existing "index the hot query shapes" discipline in `schema.py`.

---

## 3. API surface

All under a `/finance` prefix; one router module per sub-resource. Every mutation returns the Gate A envelope `{ item, meta: { message } }` and flows through `finalize_mutations()`.

### Projections (GET only)
| Route | Returns |
|---|---|
| `GET /finance/dashboard` | one aggregate payload (like `/home`): account balances, month income/spend, spend-by-category, per-card utilization, upcoming payments (next 14 days), open/overdue statements, rewards summary, expiring benefits |
| `GET /finance/upcoming` | payment calendar — computed occurrences from recurring rules + statement due dates, with `paid/pending/overdue` state |
| `GET /finance/net-worth` | (future) asset/liability totals + snapshots |

### Accounts
`POST /finance/accounts` · `GET /finance/accounts` · `GET /finance/accounts/{id}` · `PATCH /finance/accounts/{id}` · `POST /finance/accounts/{id}/archive`
Card/loan profile fields ride on the account payloads (create/patch accept an optional `card_profile` / `loan_profile` object) — one API concept, satellite storage.

### Transactions
| Route | Notes |
|---|---|
| `GET /finance/transactions` | filters: `account_id`, `category`, `kind`, `from`, `to`, `q`, `limit`/`offset` |
| `POST /finance/transactions` | first-class replacement for `POST /spending` |
| `PATCH /finance/transactions/{id}` | first update endpoint in Nova — sets the edit pattern |
| `DELETE /finance/transactions/{id}` | soft delete |

### Recurring (bills / subscriptions / EMIs)
`POST /finance/recurring` · `GET /finance/recurring?kind=` · `PATCH /finance/recurring/{id}` · `DELETE /finance/recurring/{id}` · `POST /finance/recurring/{id}/mark-paid` (orchestrated: creates the linked transaction, returns both)

### Statements
`GET /finance/cards/{account_id}/statements` · `POST /finance/cards/{account_id}/statements` (enter statement totals) · `PATCH /finance/statements/{id}` · `POST /finance/statements/{id}/pay` (orchestrated: card_payment transaction + paired transfer leg + status update)

### Rewards & benefits
`GET /finance/rewards` · `POST /finance/rewards/{program_id}/events` · `POST/GET/PATCH/DELETE /finance/benefits` · `POST /finance/benefits/{id}/use`

### Back-compat
`/spending` (GET/POST/summary) is kept as a deprecated adapter over `transactions` during migration (§7), then removed. `planner.get_spending_summary` moves its data source to the new totals helpers; the chat/voice "log spent 500" path keeps working throughout.

### Domain events (extends the §4 table in DESKTOP_WRITE_OPERATIONS.md)
`finance.account.created/updated` · `finance.transaction.created/updated/deleted` · `finance.recurring.created/updated/deleted` · `finance.recurring.paid` · `finance.statement.created/updated/paid` · `finance.reward.logged` · `finance.benefit.used`
During migration, `spending.logged` is emitted alongside `finance.transaction.created` until the desktop cutover, then retired.

---

## 4. Screen hierarchy

Finance becomes a **section** with its own layout (sub-navigation inside the existing `AppShell`), not a single screen.

```
FinanceLayout (sub-nav: Dashboard · Transactions · Cards · Bills & EMIs · Loans)
│
├── Dashboard            /finance
│     balance strip (per account) · month in/out + category chart
│     upcoming payments (14d) · utilization gauges per card
│     statement alerts · rewards summary · expiring benefits
│
├── Transactions         /finance/transactions
│     filterable list (account/category/date/search) · add/edit/delete
│     [transaction editor as inline panel or dialog]
│
├── Cards                /finance/cards
│   └── Card detail      /finance/cards/:id
│         utilization · current cycle · tabs:
│         Statements | Transactions (filtered) | Rewards | Benefits
│
├── Bills & EMIs         /finance/bills        (recurring_rules, kind filter tabs:
│                                               All · Bills · Subscriptions · EMIs)
│         upcoming/overdue grouping · mark-paid action
│
├── Loans                /finance/loans
│   └── Loan detail      /finance/loans/:id    (progress: paid/remaining, linked EMI rule)
│
├── Investments          /finance/investments  (future — stub route, hidden until built)
└── Net worth            /finance/net-worth    (future)
```

Frontend follows the existing per-domain conventions exactly: contract types in `packages/api-contracts`, `mappers/finance/*.ts`, view models in `view-models`, `use-finance-*.ts` hooks over `dataSource`, and mock-mode parity in `dev/mocks`. Query keys get a nested `finance` namespace (mirroring `system`): `queryKeys.finance.dashboard()`, `.transactions(params)`, `.accounts()`, `.recurring(params)`, `.statements(cardId)`, `.rewards()` — all sharing a `['nova','finance']` root so one invalidation can sweep the domain. `invalidation-map.ts` maps each `finance.*` event to its specific keys plus `finance.dashboard` and `home`.

---

## 5. Navigation

- Sidebar: replace **Spending** (`Wallet`, `/spending`) with **Finance** (`Wallet`, `/finance`) — same position, one top-level item. The section's breadth lives in the FinanceLayout sub-nav, keeping the sidebar flat like today.
- Router: `/finance` is a nested route group with `FinanceLayout` as the element and the screens above as children — the first nested route group in the app, structurally identical to how `AppShell` already wraps top-level routes.
- `/spending` becomes a redirect to `/finance/transactions` during migration, deleted afterwards.

---

## 6. CRUD roadmap (Finance gates)

Same rhythm as Gates A–C: backend + events + parity tests first, desktop second; stop and verify between gates. Deliberately ordered so each gate ships a usable increment.

| Gate | Scope | Contents |
|---|---|---|
| **FIN-1** | Ledger backend | New tables + `memory/finance/` + accounts & transactions endpoints + mutation builders/events + `money` backfill (§7) + `/spending` adapter + parity tests. `entity_type` vocabulary: `account`, `transaction`. |
| **FIN-2** | Desktop foundation | FinanceLayout + nav swap + Dashboard v1 (balances, month totals, category breakdown — all available from FIN-1 data) + Transactions screen with full create/edit/delete. Retire spending screen/hooks/mappers; retire dual `spending.logged` emission. |
| **FIN-3** | Credit cards | `card_profiles`, `statements`, cycle sweep, utilization; Cards list + detail screens; statement entry + pay flow; dashboard gains utilization gauges + statement alerts. |
| **FIN-4** | Recurring & loans | `recurring_rules`, `loan_profiles`, upcoming-payments projection, mark-paid orchestration, reminder-sweep into existing `reminders`; Bills & EMIs + Loans screens; dashboard gains upcoming payments. |
| **FIN-5** | Rewards & benefits | reward programs/events, `card_benefits`, use/expire flows; Rewards & Benefits tabs on card detail; dashboard tiles. |
| **FIN-6** *(future)* | Investments & net worth | holdings + valuations, net-worth projection + snapshots, remaining screens. Nothing earlier blocks on this. |

Chat parity per gate: each gate that adds mutations also adds the planner verbs + `mutation_chat` translation for the ones that make sense by voice ("log 500 on food with HDFC card", "mark electricity paid") with the Gate A-style parity tests. Memory-producer policy additions ride the gate that introduces the mutation (e.g. `transaction/create` above a notable-amount threshold → memory; routine transactions → no memory).

The original Gate D (Products) and E/F resume after FIN-2 or interleave — Finance gates are independent of them by construction.

---

## 7. Migration strategy from `money`

Principles: **additive, idempotent, no data ever dropped** (same rules `_migrate_memories` already follows), and chat/voice logging keeps working at every step.

1. **Additive schema (FIN-1).** New tables created in `init_db()`; `money` untouched. A default **"Cash"** account is seeded on first run of the new schema.
2. **Backfill (FIN-1).** A script under `scripts/database/` copies every `money` row → `transactions`: `earned` → `credit`/`income`, `spent` → `debit`/`expense`; `note` carried over; `created_at` becomes both `occurred_at` and `created_at`; `category` null; `account_id` = Cash; `source='migrated_money'`; `legacy_money_id` = old id. The unique index on `legacy_money_id` makes re-runs idempotent. Amounts convert REAL rupees → integer paise with round-half-up; the script prints old/new totals for eyeball verification.
3. **Single write path immediately.** After backfill, `POST /spending` and the chat `log_spending` command write **transactions** (Cash account) — `money` is frozen read-only from this moment; there is no dual-write window to reconcile. `memory/money.py` write helpers are retired; `planner.get_spending_summary` and the home projection switch to the new totals helpers (same numbers, verified in step 2).
4. **Event compatibility.** The transaction write path emits both `finance.transaction.created` and legacy `spending.logged` until FIN-2 ships the new frontend; then the legacy emission and the `/spending` adapter endpoints are deleted.
5. **Frontend cutover (FIN-2).** New Finance screens land; `/spending` route redirects; spending screen, hooks, mappers, mocks, and contracts are removed in the same gate (small surface: one screen, two hooks, one mapper).
6. **`money` table disposition.** Kept permanently as inert legacy data (it costs nothing and honors the never-drop rule). All code paths referencing it are gone after step 3; `schema.py` keeps creating it only until the next natural schema tidy.
7. **Rollback story.** Because writes cut over atomically and `money` is never mutated after step 2, rolling back any step is "point the endpoints back at money.py" — no reverse data migration required.

---

## 8. Explicit non-goals / deferred decisions

- No bank sync, statement PDF parsing, or OCR (roadmap-level exclusion stands).
- No amortization engine — EMI amounts are user-entered; loan progress = payments logged against principal.
- No rewards *rules* engine — earn rates are notes; balances move by explicit events.
- Categories stay TEXT with a canonical list in config; a categories table only if custom-category CRUD is ever wanted.
- Multi-currency: schema carries `currency` but the UI assumes INR until needed.
- Budgets/spending limits: natural later addition (a `budgets` table + dashboard tile); intentionally left out of the gate ladder to keep it honest.
