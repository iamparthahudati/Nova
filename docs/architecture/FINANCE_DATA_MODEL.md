# Nova Finance — Final Data Model (Design Artifact)

**Status:** Final design. Approved input for FIN-1. No code in this document is implemented.
**Supersedes:** the schema sections (§2) of [`FINANCE_DOMAIN.md`](FINANCE_DOMAIN.md). The domain decomposition, API surface, screen hierarchy, and gate ladder in that document stand; where this document and that one disagree on schema, **this document wins**.
**Hard constraints (unchanged, restated):** Nova Architecture v2 governing rules; Memory is the only persistence owner; services are orchestration only; routers are thin; desktop talks only to FastAPI; `MutationEvent` is the canonical mutation object; `finalize_mutations()` is the single post-mutation pipeline; no duplicate write paths.

**Approved decisions baked into this model (not re-litigated here):**
integer paise (`amount_minor`) everywhere · `occurred_on` is a local DATE · `created_at`/`updated_at` are UTC timestamps · balances, reward balances, statement status, and benefit usage are **derived, never stored** · `transfer_group_id` replaces `transfer_peer_id` · `adjustment` transaction kind exists · SQLite `foreign_keys` enabled before Finance · `wallet` account type exists · categories and merchants stay TEXT · `money` migrates into `transactions` additively.

---

## 1. Bounded Contexts

Finance is one domain, five bounded contexts, plus one shared reference context. Contexts communicate only through aggregate IDs and MutationEvents — never through joins that reach across a context to *mutate* (read-side projections may join anything).

| Context | Aggregate root(s) | Child entities | Owns |
|---|---|---|---|
| **Ledger** (core) | `Account`, `Transaction` | `CreditCardProfile`, `LoanProfile` (satellites of Account) | Where money lives and every movement of it. The only context that changes balances — and balances themselves are *derived* from it. |
| **Recurring** | `RecurringRule` | — | Bills, EMIs, subscriptions: expectations of future transactions. Never writes transactions itself; "mark paid" is a service orchestration that creates a Ledger transaction referencing the rule. |
| **Statements** | `Statement` | — | Credit-card billing cycles: user-entered cycle totals over a card's transactions. Status and paid-amount are projections, not columns. |
| **Rewards** | `RewardProgram` | `RewardEvent` | Points/cashback programs attached to a card. Balance = fold over events. |
| **Benefits** | `Benefit` | `BenefitUsage` | Card perks (lounge, vouchers, milestones) with quota tracking. Usage count = fold over usage rows. |
| **Reference** (shared) | `Institution` | — | Banks/issuers/lenders, deduplicated. Read-only from every other context. |

**Aggregate root definition used here:** the unit of consistency for a single write. A REST call or chat command mutates exactly one aggregate — with two sanctioned exceptions, both orchestrated inside `services/finance` in one DB transaction: (a) a transfer/card-payment writes **two** Transaction rows sharing a `transfer_group_id`; (b) creating an account may write its profile satellite in the same call.

**Institution — recommended: yes, implement now.** Three tables would otherwise carry free-text issuer/lender/bank names (`accounts`, `card_profiles`, `loan_profiles`), fragmenting instantly ("HDFC" / "HDFC Bank" / "hdfc"). A two-column reference table costs one CREATE now; retrofitting dedup after data exists costs a data-cleaning migration. This is deliberately *unlike* categories/merchants, which are single-column, per-transaction, and cheap to normalize later.

Projections (Dashboard, Net Worth, Upcoming Payments, Credit Utilization, Statement Summary, Cash Flow, Rewards Summary) are **not** contexts. They own no tables and emit no events (§6, §7 of this doc; pattern: `services/api/projections/home.py`).

---

## 2. Entity Relationship Diagram

```
                        ┌──────────────┐
                        │ Institution   │ (reference; no deletes)
                        └──────┬───────┘
                               │ 0..1 ◄── N (nullable FK)
                               │
   ┌───────────────────────────▼──────────────────────────┐
   │                       Account                         │
   │  type: cash | bank | wallet | credit_card | loan      │
   │  classification: asset | liability                    │
   └──┬──────────┬──────────┬───────────┬─────────┬───────┘
      │ 1        │ 1        │ 1         │ 1       │ 1
      │          │          │           │         │
      │ 0..1     │ 0..1     │ N         │ N       │ N
┌─────▼─────┐ ┌──▼────────┐ ┌▼─────────┐ ┌▼──────┐ ┌▼─────────┐
│CreditCard  │ │LoanProfile│ │Transaction│ │State- │ │Benefit    │
│Profile     │ │(1:1 with  │ │ (ledger)  │ │ment   │ │(cards     │
│(1:1 with   │ │ loan acct)│ └┬───┬───┬─┘ │(cards │ │ only)     │
│ card acct) │ └───────────┘  │   │   │   │ only) │ └────┬──────┘
└─────┬──────┘                │   │   │   └───▲───┘      │ 1
      │ 1                     │   │   │       │          │
      │                       │   │   └───────┘          │ N
      │ N                     │   │  N : 0..1        ┌───▼────────┐
┌─────▼────────┐              │   │  (statement_id)  │BenefitUsage │
│RewardProgram │              │   │                  └────────────┘
│(via account) │              │   │ N : 0..1 (recurring_rule_id)
└─────┬────────┘              │   │
      │ 1                     │  ┌▼─────────────┐
      │ N                     │  │RecurringRule  │
┌─────▼────────┐              │  │bill|sub|emi   │──── 0..1 ──► Account
│ RewardEvent  │◄─── 0..1 ────┘  └───────┬──────┘     (loan_account_id,
└──────────────┘  (transaction_id)       │             emi only)
                                         └──── 1 ──► Account (account_id,
                                                      payment source)
Transaction ◄──── transfer_group_id ────► Transaction
        (exactly 2 rows share one group id; not a FK)
```

Relationship inventory (every edge, explicit):

| From | To | Cardinality | Via | Notes |
|---|---|---|---|---|
| Account | Institution | N : 0..1 | `accounts.institution_id` (nullable FK) | Cash/wallet accounts typically NULL. |
| CreditCardProfile | Account | 1 : 1 | `card_profiles.account_id` (PK = FK) | Exists iff `accounts.type='credit_card'`. |
| LoanProfile | Account | 1 : 1 | `loan_profiles.account_id` (PK = FK) | Exists iff `accounts.type='loan'`. |
| Transaction | Account | N : 1 | `transactions.account_id` (FK, NOT NULL) | Every movement belongs to exactly one account. |
| Transaction | Transaction | 2-row group | `transfer_group_id` (TEXT UUID, nullable, **not a FK**) | Exactly two live rows per non-null group id; enforced by the service invariant (§4), backed by index. |
| Transaction | RecurringRule | N : 0..1 | `transactions.recurring_rule_id` (nullable FK) | "This payment satisfied that rule for its period." |
| Transaction | Statement | N : 0..1 | `transactions.statement_id` (nullable FK) | Spend assignment to a cycle, and payment-leg allocation to the cycle it pays. |
| RecurringRule | Account | N : 1 | `recurring_rules.account_id` (FK, NOT NULL) | Payment source (which bank/card pays it). |
| RecurringRule | Account (loan) | N : 0..1 | `recurring_rules.loan_account_id` (nullable FK) | Set iff `kind='emi'`. |
| Statement | Account | N : 1 | `statements.account_id` (FK, NOT NULL) | Target must be a `credit_card` account. |
| RewardProgram | Account | N : 1 | `reward_programs.account_id` (FK, NOT NULL) | Usually 1:1 per card; N allowed (co-branded cards can carry two programs). |
| RewardEvent | RewardProgram | N : 1 | `reward_events.program_id` (FK, NOT NULL) | The rewards ledger. |
| RewardEvent | Transaction | N : 0..1 | `reward_events.transaction_id` (nullable FK) | Provenance: "this cashback came from that spend." |
| Benefit | Account | N : 1 | `benefits.account_id` (FK, NOT NULL) | Target must be a `credit_card` account. |
| BenefitUsage | Benefit | N : 1 | `benefit_usages.benefit_id` (FK, NOT NULL) | The usage ledger; `used_count` is COUNT over this. |
| BenefitUsage | Transaction | N : 0..1 | `benefit_usages.transaction_id` (nullable FK) | Optional: a lounge-visit fee, a voucher redemption spend. |

---

## 3. Database Tables

Conventions applying to **every** table below (stated once):

- **PKs:** `id INTEGER PRIMARY KEY AUTOINCREMENT`, consistent with `tasks`/`reminders` (profiles use `account_id` as PK — 1:1 satellites). `transfer_group_id` is a TEXT UUID *value*, not a key.
- **Audit fields:** `created_at TEXT NOT NULL` and `updated_at TEXT NOT NULL` — UTC ISO-8601 via `_connection.now()`. `updated_at` set equal to `created_at` on insert; bumped on every UPDATE (including soft delete).
- **Domain dates:** `occurred_on`, `period_start`, `due_date`, etc. are **local calendar dates**, `TEXT 'YYYY-MM-DD'`. The producer (desktop client / chat translator) supplies them; the backend never derives a local date from a UTC timestamp except in the one migration backfill (§9).
- **Soft delete:** `deleted_at TEXT NULL` on user-editable rows. Soft-deleted rows are invisible to every list, projection, SUM, and invariant check. Accounts and institutions are never deleted — accounts **archive** (`archived_at`), institutions persist. Hard deletes never happen (same philosophy as `memories`).
- **Money:** `*_minor INTEGER` paise, always `> 0` where it denotes a magnitude (direction carries sign). No REAL anywhere.
- **FK enforcement:** requires `PRAGMA foreign_keys = ON` per connection — a **precondition change to `memory/_connection.py`** (see §12). All FKs are `ON DELETE RESTRICT` semantics (the default with the pragma on); soft delete makes cascade unnecessary.
- **CHECK constraints:** used for closed enums and positivity. They are the storage-layer backstop; business validation (§8) remains in the service/memory layer.

### 3.1 `institutions`

*Purpose:* deduplicated bank/issuer/lender reference.

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER PK | no | |
| `name` | TEXT | no | "HDFC Bank" |
| `kind` | TEXT | no | CHECK in `('bank','card_issuer','lender','wallet_provider','other')` — descriptive, not restrictive; one institution can back many account types |
| `notes` | TEXT | yes | |
| `created_at`, `updated_at` | TEXT | no | |

Constraints/indexes: `UNIQUE (name COLLATE NOCASE)`. No soft delete (reference data; unreferenced rows are harmless).

### 3.2 `accounts`

*Purpose:* the core aggregate — anything money lives in or is owed to. **No balance column.** Balance is derived (§6).

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER PK | no | |
| `name` | TEXT | no | "HDFC Millennia", "Cash", "Home Loan" |
| `type` | TEXT | no | CHECK in `('cash','bank','wallet','credit_card','loan')` — `investment` reserved (§10), added by CHECK-widening migration when built |
| `classification` | TEXT | no | CHECK in `('asset','liability')`; derived-by-convention from type at create (cash/bank/wallet → asset; credit_card/loan → liability) but stored, so Net Worth is a two-line GROUP BY |
| `currency` | TEXT | no | DEFAULT `'INR'`; reserved for multi-currency (§10) |
| `opening_balance_minor` | INTEGER | no | DEFAULT 0. **Signed**: liabilities opened with existing debt use a negative value. The only stored quantity in the balance formula. |
| `opening_balance_on` | TEXT date | no | The local date the opening balance is true *as of*; transactions before it are invalid (§8) |
| `institution_id` | INTEGER FK → institutions | yes | |
| `archived_at` | TEXT | yes | Archive-not-delete. Archived accounts are hidden from pickers and dashboards, kept in history and Net Worth-as-of-past. |
| `created_at`, `updated_at` | TEXT | no | |

Constraints/indexes: `UNIQUE (name COLLATE NOCASE) WHERE archived_at IS NULL` (live names unique; archived names reusable). Index `(type)` — small table, mostly for intent.

### 3.3 `card_profiles` — CreditCardProfile

*Purpose:* credit-card-specific attributes; 1:1 satellite of a `credit_card` account.

| Column | Type | Null | Notes |
|---|---|---|---|
| `account_id` | INTEGER PK, FK → accounts | no | PK = FK enforces 1:1 |
| `network` | TEXT | yes | "Visa", "RuPay" — display only |
| `last4` | TEXT | yes | display only |
| `credit_limit_minor` | INTEGER | no | CHECK `> 0`; utilization denominator |
| `statement_day` | INTEGER | no | CHECK 1–31; day-of-month the cycle closes; clamped to month length by the cycle sweep (Feb → 28/29) |
| `due_day_offset` | INTEGER | no | CHECK `> 0`; days from statement date to payment due date |
| `autopay` | INTEGER (0/1) | no | DEFAULT 0 |
| `created_at`, `updated_at` | TEXT | no | |

No soft delete (lives and dies with its account's archive state). No extra indexes (PK lookup only).

### 3.4 `loan_profiles` — LoanProfile

*Purpose:* loan-specific attributes; 1:1 satellite of a `loan` account.

| Column | Type | Null | Notes |
|---|---|---|---|
| `account_id` | INTEGER PK, FK → accounts | no | PK = FK enforces 1:1 |
| `principal_minor` | INTEGER | no | CHECK `> 0`; original principal |
| `interest_rate_bps` | INTEGER | no | basis points, integer — no float rates |
| `tenure_months` | INTEGER | no | CHECK `> 0` |
| `start_date` | TEXT date | no | local date |
| `emi_amount_minor` | INTEGER | yes | user-entered; NULL until known. No amortization engine (non-goal). |
| `created_at`, `updated_at` | TEXT | no | |

No soft delete, no extra indexes. Lender = the account's `institution_id`.

### 3.5 `transactions` — the ledger (replaces `money`)

*Purpose:* every money movement. The single source from which all balances derive.

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER PK | no | |
| `account_id` | INTEGER FK → accounts | no | |
| `direction` | TEXT | no | CHECK in `('debit','credit')` — effect on *this* account, uniform sign convention (§6.0) |
| `kind` | TEXT | no | CHECK in `('expense','income','transfer','card_payment','refund','fee','interest','cashback','adjustment')` |
| `amount_minor` | INTEGER | no | CHECK `> 0` — magnitude only; direction carries sign |
| `category` | TEXT | yes | canonical list lives in config; free TEXT by decision |
| `merchant` | TEXT | yes | free TEXT by decision |
| `note` | TEXT | yes | |
| `occurred_on` | TEXT date | no | **local DATE** — the fix for "created_at doubles as transaction date" |
| `transfer_group_id` | TEXT (UUID) | yes | non-NULL iff `kind IN ('transfer','card_payment')`; exactly two live rows share a value (§4) |
| `recurring_rule_id` | INTEGER FK → recurring_rules | yes | payment satisfies a rule occurrence |
| `statement_id` | INTEGER FK → statements | yes | spend → the cycle it falls in; card-payment credit leg → the cycle it pays |
| `source` | TEXT | no | CHECK in `('manual','chat','voice','migrated_money')` — provenance, not producer metadata (fixed vocabulary, set at create, never used for behavior) |
| `legacy_money_id` | INTEGER | yes | backfill idempotency key (§9); NULL for all post-migration rows |
| `created_at`, `updated_at` | TEXT | no | |
| `deleted_at` | TEXT | yes | soft delete |

Constraints/indexes:
- `UNIQUE (legacy_money_id) WHERE legacy_money_id IS NOT NULL`
- `(account_id, occurred_on DESC, id DESC) WHERE deleted_at IS NULL` — account ledger views, running balance
- `(occurred_on) WHERE deleted_at IS NULL` — period aggregates (dashboard, cash flow)
- `(transfer_group_id) WHERE transfer_group_id IS NOT NULL` — pair lookup + invariant check
- `(recurring_rule_id, occurred_on) WHERE recurring_rule_id IS NOT NULL` — "is this period paid"
- `(statement_id) WHERE statement_id IS NOT NULL` — statement totals & paid amount

### 3.6 `recurring_rules`

*Purpose:* bills + subscriptions + EMIs, unified by `kind`. Occurrences are **computed, never materialized** — "paid" = a live transaction with this `recurring_rule_id` in the period.

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER PK | no | |
| `kind` | TEXT | no | CHECK in `('bill','subscription','emi')` |
| `name` | TEXT | no | "Electricity", "Netflix", "Car EMI" |
| `amount_minor` | INTEGER | no | CHECK `> 0`; expected amount |
| `is_variable` | INTEGER (0/1) | no | DEFAULT 0; fluctuating bills — expected amount is a hint, not a validation bound |
| `cadence` | TEXT | no | CHECK in `('weekly','monthly','quarterly','yearly')` |
| `due_day` | INTEGER | no | day-of-month (1–31, clamped) or weekday (1–7) for weekly |
| `account_id` | INTEGER FK → accounts | no | payment source |
| `loan_account_id` | INTEGER FK → accounts | yes | non-NULL iff `kind='emi'` |
| `autopay` | INTEGER (0/1) | no | DEFAULT 0; drives reminder copy ("verify" vs "pay") |
| `starts_on` | TEXT date | no | local date |
| `ends_on` | TEXT date | yes | NULL = open-ended; for EMIs derivable from tenure but stored explicitly (user may prepay) |
| `is_active` | INTEGER (0/1) | no | DEFAULT 1; pause without delete |
| `created_at`, `updated_at` | TEXT | no | |
| `deleted_at` | TEXT | yes | soft delete |

Constraints/indexes: partial index `(kind, is_active) WHERE deleted_at IS NULL AND is_active = 1` — the upcoming-payments scan.

### 3.7 `statements`

*Purpose:* one credit-card billing cycle with user-entered totals. **No `status`, no `paid_amount_minor` column** — both derived (§6.5).

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER PK | no | |
| `account_id` | INTEGER FK → accounts | no | must be a `credit_card` account (§8) |
| `period_start`, `period_end` | TEXT date | no | local dates; half-open convention `[start, end]` inclusive, generated from `statement_day` |
| `statement_date` | TEXT date | no | = period_end (kept explicit for issuer quirks) |
| `due_date` | TEXT date | no | statement_date + `due_day_offset` |
| `total_due_minor` | INTEGER | yes | NULL until the user enters the arrived statement; entered value wins over the computed spend sum (issuer is truth) |
| `min_due_minor` | INTEGER | yes | user-entered |
| `created_at`, `updated_at` | TEXT | no | |
| `deleted_at` | TEXT | yes | soft delete (typo'd cycle rows) |

Constraints/indexes: `UNIQUE (account_id, period_start) WHERE deleted_at IS NULL`; index `(account_id, due_date) WHERE deleted_at IS NULL` — upcoming dues.

### 3.8 `reward_programs`

*Purpose:* a points or cashback program attached to a card. **No balance column** — derived from events (§6.7).

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER PK | no | |
| `account_id` | INTEGER FK → accounts | no | must be `credit_card` (§8) |
| `name` | TEXT | no | "Reward Points", "CashPoints" |
| `unit` | TEXT | no | CHECK in `('points','cashback_minor')` — one unit per program; events are integers in that unit |
| `earn_rate_note` | TEXT | yes | free text; Nova is not a rewards calculator (non-goal) |
| `expiry_note` | TEXT | yes | free text policy |
| `created_at`, `updated_at` | TEXT | no | |
| `deleted_at` | TEXT | yes | soft delete |

Constraints/indexes: `UNIQUE (account_id, name COLLATE NOCASE) WHERE deleted_at IS NULL`.

### 3.9 `reward_events`

*Purpose:* the rewards ledger — every earn/redeem/expire/adjust.

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER PK | no | |
| `program_id` | INTEGER FK → reward_programs | no | |
| `kind` | TEXT | no | CHECK in `('earned','redeemed','expired','adjusted')` |
| `direction` | TEXT | no | CHECK in `('credit','debit')` — earned → credit; redeemed/expired → debit; adjusted → either (mirrors the transaction convention) |
| `amount` | INTEGER | no | CHECK `> 0`; in the program's `unit` |
| `transaction_id` | INTEGER FK → transactions | yes | provenance link |
| `note` | TEXT | yes | |
| `occurred_on` | TEXT date | no | local date |
| `created_at`, `updated_at` | TEXT | no | |
| `deleted_at` | TEXT | yes | soft delete |

Constraints/indexes: `(program_id, occurred_on) WHERE deleted_at IS NULL` — balance fold + history list.

### 3.10 `benefits`

*Purpose:* a card perk with an optional quota per period. **No `used_count` column** — derived (§6.7).

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER PK | no | |
| `account_id` | INTEGER FK → accounts | no | must be `credit_card` (§8) |
| `title` | TEXT | no | "Airport lounge access" |
| `description` | TEXT | yes | |
| `kind` | TEXT | no | CHECK in `('lounge','voucher','milestone','insurance','other')` |
| `quota` | INTEGER | yes | NULL = unlimited/untracked; CHECK `> 0` when set |
| `quota_period` | TEXT | yes | CHECK in `('month','quarter','year','lifetime')`; NULL iff `quota` NULL |
| `expires_on` | TEXT date | yes | vouchers |
| `created_at`, `updated_at` | TEXT | no | |
| `deleted_at` | TEXT | yes | soft delete |

Constraints/indexes: `(account_id) WHERE deleted_at IS NULL`.

### 3.11 `benefit_usages`

*Purpose:* the usage ledger a benefit's `used_count` derives from (required by "benefit usage is derived").

| Column | Type | Null | Notes |
|---|---|---|---|
| `id` | INTEGER PK | no | |
| `benefit_id` | INTEGER FK → benefits | no | |
| `used_on` | TEXT date | no | local date — the period bucket key |
| `note` | TEXT | yes | "T2 lounge, DEL" |
| `transaction_id` | INTEGER FK → transactions | yes | optional linked spend |
| `created_at`, `updated_at` | TEXT | no | |
| `deleted_at` | TEXT | yes | soft delete (undo a mis-logged visit) |

Constraints/indexes: `(benefit_id, used_on) WHERE deleted_at IS NULL` — per-period counting.

---

## 4. Aggregate Rules (Invariants)

Enforced in `services/finance` / `memory/finance` before any write; CHECK constraints are the storage backstop, never the primary enforcement. All invariants read only **live** rows (`deleted_at IS NULL`).

**Account**
- A1. An account is never hard-deleted. Archiving requires no *open* obligations: no active recurring rules sourced from it, no unpaid statements on it (derived status ∉ {paid}). History (transactions, past statements) never blocks archiving.
- A2. `card_profiles` row exists **iff** `type='credit_card'`; `loan_profiles` row exists **iff** `type='loan'`. Created in the same DB transaction as the account; a typed account without its profile is invalid.
- A3. `type` is immutable after creation (a card is not editable into a bank account). `classification` follows `type` and is likewise immutable.
- A4. `opening_balance_minor` / `opening_balance_on` are editable only while the account has zero live transactions; afterwards, corrections go through an `adjustment` transaction (that is what the kind exists for).

**Transaction**
- T1. Cannot exist without an account (`account_id` NOT NULL + enforced FK).
- T2. `occurred_on ≥` the account's `opening_balance_on`.
- T3. **Transfer pair invariant:** a non-NULL `transfer_group_id` is shared by *exactly two* live rows, with: opposite `direction`s, equal `amount_minor`, equal `occurred_on`, distinct `account_id`s, identical `kind` ∈ {`transfer`,`card_payment`}. Both legs are written, soft-deleted, and amount/date-edited **atomically as a pair** — there is no API to touch one leg. `card_payment` additionally requires the credit leg on a `credit_card` account and the debit leg on an asset account (cash/bank/wallet).
- T4. Kind→direction matrix (validated, not inferred): `expense`,`fee`,`interest` → debit; `income`,`refund`,`cashback` → credit; `adjustment` → either; `transfer`,`card_payment` → the pair (T3).
- T5. `statement_id`, when set: the statement must belong to the same account (for spend on the card) or — for a `card_payment` credit leg — to the card account of that leg; and `occurred_on` must fall within `[period_start, period_end]` for spend assignment (payment legs may fall after `period_end`, before/around `due_date`).
- T6. `recurring_rule_id`, when set, must reference a live rule; at most one live transaction per (rule, occurrence period) — the "paid" marker is unambiguous.
- T7. Soft delete of a transfer/card-payment leg soft-deletes the whole group (both rows, one transaction).

**RecurringRule**
- R1. `loan_account_id` is non-NULL **iff** `kind='emi'`, and must reference a live `loan` account.
- R2. `account_id` (payment source) must be a live, unarchived account.
- R3. `starts_on ≤ ends_on` when both set. Deactivation (`is_active=0`) never touches linked transactions.
- R4. Deleting a rule (soft) leaves past linked transactions intact — `recurring_rule_id` keeps pointing at the soft-deleted rule for history; the rule simply stops generating occurrences.

**Statement**
- S1. Belongs to exactly one `credit_card` account, immutable after creation.
- S2. Periods for one card never overlap; `UNIQUE(account_id, period_start)` plus service check on range overlap.
- S3. `due_date > period_end ≥ period_start`.
- S4. Status is never written — it is a total function of (`total_due_minor`, `due_date`, derived paid amount, today) — see §6.5.
- S5. A statement with linked live transactions cannot be soft-deleted until they are unlinked (their `statement_id` set NULL) — same orchestration, one DB transaction.

**RewardProgram / RewardEvent**
- W1. Every event belongs to exactly one program; programs belong to exactly one card account.
- W2. Balance = Σ(credit) − Σ(debit) over live events; a `redeemed`/`expired` event may not push the derived balance below zero (validated at write against the current fold).
- W3. Soft-deleting a program requires no live events (delete/adjust events first) — prevents orphaned ledgers behind a hidden program.

**Benefit / BenefitUsage**
- B1. Every usage belongs to exactly one benefit; benefits belong to exactly one card account.
- B2. When `quota` is set: COUNT(live usages in the `used_on` period bucket) `< quota` at write time. (Strict — no over-quota logging; an issuer goodwill visit is an untracked note, not a ledger lie.)
- B3. A usage `used_on` after `expires_on` is invalid.

**Institution**
- I1. Never deleted; rename-only edits. Uniqueness is case-insensitive by name.

---

## 5. Domain Events

All events are `MutationEvent`s — pure domain objects per DESKTOP_WRITE_OPERATIONS §0 — flowing through the one `finalize_mutations()` pipeline. Producers: REST routers via new pure builders in `runtime/mutation_builders.py`; chat via `runtime/mutation_chat.py` for the verbs that exist by voice. Consumers are identical for every event and are listed once: **(1)** `domain_events.publish_mutation_events` → WebSocket → desktop `invalidation-map.ts` (query-key invalidation); **(2)** `memory_producers.memories_from_mutations` (policy column below); **(3)** `schedule_entity_extraction()` (unconditional, batched).

`entity_type` vocabulary added to the canon: `account`, `transaction`, `recurring_rule`, `statement`, `reward_program`, `reward_event`, `benefit`, `benefit_usage`.

| `event_type` | entity_type / operation | Producer(s) | Emitted when | Memory policy |
|---|---|---|---|---|
| `finance.account.created` | `account` / `create` | REST, chat | Account (+ profile satellite) committed | **Yes** — "opened/added <name>" is durable personal fact |
| `finance.account.updated` | `account` / `update` | REST | Rename, institution, profile field edits | No |
| `finance.account.archived` | `account` / `archive` | REST | Archive committed | **Yes** for `loan` type (loan closed — milestone); No otherwise |
| `finance.transaction.created` | `transaction` / `create` | REST, chat | Single-leg transaction committed | Only above configurable notable-amount threshold |
| `finance.transaction.updated` | `transaction` / `update` | REST | Edit committed (both legs if paired) | No |
| `finance.transaction.deleted` | `transaction` / `delete` | REST | Soft delete committed (both legs if paired) | No |
| `finance.transfer.created` | `transaction` / `transfer` | REST, chat | Both legs committed atomically — **one event for the pair**, `entity` = both legs, `metadata.transfer_group_id` set | No |
| `finance.recurring.created` | `recurring_rule` / `create` | REST, chat | Rule committed | **Yes** — a new obligation is a durable fact |
| `finance.recurring.updated` | `recurring_rule` / `update` | REST | Edit / activate / deactivate | No |
| `finance.recurring.deleted` | `recurring_rule` / `delete` | REST | Soft delete | No |
| `finance.recurring.paid` | `transaction` / `pay_recurring` | REST, chat | Mark-paid orchestration commits the linked transaction — emitted **instead of** `finance.transaction.created`, `metadata.recurring_rule_id` set | Yes for `emi` kind; No otherwise |
| `finance.statement.created` | `statement` / `create` | REST, service sweep | Cycle row created (user entry or lazy sweep) | No |
| `finance.statement.updated` | `statement` / `update` | REST | Totals/min-due entered or corrected | No |
| `finance.statement.paid` | `transaction` / `pay_statement` | REST, chat | Pay orchestration commits the card-payment pair with `statement_id` — emitted instead of `finance.transfer.created` | No |
| `finance.reward_program.created` | `reward_program` / `create` | REST | Program committed | No |
| `finance.reward.logged` | `reward_event` / `log` | REST, chat | Reward event committed | No |
| `finance.benefit.created` | `benefit` / `create` | REST | Benefit committed | No |
| `finance.benefit.updated` / `.deleted` | `benefit` / `update` / `delete` | REST | Edit / soft delete | No |
| `finance.benefit.used` | `benefit_usage` / `use` | REST, chat | Usage row committed | No |

Rules: one mutation → one event (orchestrations that write a transaction *as their purpose* emit their specific event, not a generic transaction event — no double emission). During migration only, the transaction write path additionally emits legacy `spending.logged` until FIN-2 desktop cutover (§9 step 5), then that emission is deleted.

---

## 6. Projections (Read Models)

All projections are pure reads in `services/finance` (aggregation logic) surfaced through `services/api` routers — no storage, no events, no CRUD, pattern of `projections/home.py`. Every SUM/COUNT filters `deleted_at IS NULL`. Definitions below are the canonical formulas.

**6.0 Sign convention (used by everything).** For any account:

```
balance(account, as_of) =
    opening_balance_minor
  + Σ amount_minor over live credit legs  (occurred_on ≤ as_of)
  − Σ amount_minor over live debit legs   (occurred_on ≤ as_of)
```

One formula for all types. Asset accounts trend positive; liability accounts trend negative (a card you owe ₹12,000 on has balance −1200000). Presentation ("you owe ₹12,000") is a mapper concern.

**6.1 Dashboard** (`GET /finance/dashboard`, one aggregate payload)
Builds from: accounts (+profiles), transactions, recurring_rules, statements, reward_programs/events, benefits/usages.
Contents: per-account balances (6.0) · current-month income/expense totals and category breakdown (transactions grouped by `kind`, `category` over the month's `occurred_on`) · per-card utilization (6.4) · upcoming payments, next 14 days (6.2) · statements with derived status ∈ {due, overdue, partial} (6.5) · rewards summary (6.7) · benefits expiring or near-quota (6.7).

**6.2 Upcoming Payments** (`GET /finance/upcoming`)
Builds from: recurring_rules (live, active) + statements (live, unpaid) + transactions (paid-detection).
For each active rule, compute the next occurrence date(s) in the window from `cadence` + `due_day` + `starts_on/ends_on`; an occurrence is **paid** iff a live transaction links `recurring_rule_id` within that occurrence's period (T6). Merge with statement `due_date`s where derived status ∉ {paid}. Output: date-sorted calendar entries `{source: rule|statement, name, amount_minor (expected or total_due), due_on, state: paid|pending|overdue, autopay}`.

**6.3 Net Worth** (`GET /finance/net-worth`)
Builds from: accounts + transactions only.
`net_worth = Σ balance(a) for classification='asset' + Σ balance(a) for classification='liability'` (liability balances are already negative — it is a plain sum). Include archived accounts only for as-of-past queries. Trend history (`net_worth_snapshots`) is **reserved** (§10), not built.

**6.4 Credit Utilization** (per card; consumed by Dashboard and Card detail)
Builds from: accounts, card_profiles, transactions, statements.
Live: `utilization = max(0, −balance(card)) / credit_limit_minor`. Historical per cycle: `statement.total_due_minor / credit_limit_minor` (entered total wins; computed spend sum as fallback when total not yet entered).

**6.5 Statement Summary** (per card; Cards screens + Dashboard alerts)
Builds from: statements + transactions.
`spend_in_cycle = Σ debit − Σ credit` over live card transactions with this `statement_id` (excluding payment legs) — display alongside the user-entered `total_due_minor`, never overriding it. `paid_minor = Σ amount_minor` over live `card_payment` credit legs with this `statement_id`. **Derived status** (S4):

```
no total_due entered               → open        (cycle known, statement not arrived)
paid_minor ≥ total_due             → paid
0 < paid_minor < total_due         → partial     (overdue-partial if today > due_date)
paid_minor = 0 and today ≤ due_date → due
paid_minor = 0 and today > due_date → overdue
```

**6.6 Cash Flow** (`GET /finance/cashflow`, month/period grouping)
Builds from: transactions only.
Per period bucket over `occurred_on`: `inflow = Σ income + refund` (asset accounts), `outflow = Σ expense + fee + interest`, `net = inflow − outflow`. `transfer`/`card_payment` pairs net to zero across accounts and are **excluded** from in/out (they move money, they don't earn or spend it); `cashback` reported as its own line, not inflow; `adjustment` excluded from flow (it corrects stock, not flow).

**6.7 Rewards Summary** (Dashboard tile + Card detail tab)
Builds from: reward_programs + reward_events; benefits + benefit_usages.
Per program: `balance = Σ credit − Σ debit` over live events (in program `unit`); recent events list. Per benefit: `used = COUNT(live usages in current quota_period bucket)`, `remaining = quota − used` (NULL quota → untracked); flag `expires_on` within 30 days.

---

## 7. Query Patterns and Index Design

High-frequency queries (dashboard poll + screen loads dominate; writes are rare — this is a personal ledger, tens of writes/day, thousands of rows/year). Every index below already appears in §3; this table is the justification.

| # | Query (hot path) | Shape | Served by |
|---|---|---|---|
| Q1 | Account ledger page: latest N transactions for one account | `WHERE account_id=? AND deleted_at IS NULL ORDER BY occurred_on DESC, id DESC LIMIT ?` | `transactions(account_id, occurred_on DESC, id DESC) WHERE deleted_at IS NULL` |
| Q2 | Balance fold per account (6.0) — dashboard, net worth | `SELECT direction, SUM(amount_minor) ... WHERE account_id=? AND deleted_at IS NULL GROUP BY direction` | same index as Q1 (prefix `account_id`) |
| Q3 | Month totals / category breakdown / cash flow | `WHERE occurred_on BETWEEN ? AND ? AND deleted_at IS NULL GROUP BY kind[,category]` | `transactions(occurred_on) WHERE deleted_at IS NULL` |
| Q4 | Transfer pair fetch + T3 invariant check | `WHERE transfer_group_id=?` | partial index on `transfer_group_id` |
| Q5 | "Is this rule paid for this period" (6.2, per rule per window) | `WHERE recurring_rule_id=? AND occurred_on BETWEEN ? AND ? AND deleted_at IS NULL` | `transactions(recurring_rule_id, occurred_on)` partial |
| Q6 | Statement paid amount + cycle spend (6.5) | `WHERE statement_id=? AND deleted_at IS NULL` | partial index on `statement_id` |
| Q7 | Upcoming-payment rule scan (6.2) | `WHERE is_active=1 AND deleted_at IS NULL` | `recurring_rules(kind, is_active)` partial |
| Q8 | Unpaid/upcoming statements per card or globally | `WHERE deleted_at IS NULL AND due_date >= ? [AND account_id=?]` | `statements(account_id, due_date)` partial |
| Q9 | Reward balance fold + event history | `WHERE program_id=? AND deleted_at IS NULL [ORDER BY occurred_on DESC]` | `reward_events(program_id, occurred_on)` partial |
| Q10 | Benefit usage count in period bucket (B2, 6.7) | `WHERE benefit_id=? AND used_on BETWEEN ? AND ? AND deleted_at IS NULL` | `benefit_usages(benefit_id, used_on)` partial |
| Q11 | Backfill idempotency probe (§9, migration only) | `WHERE legacy_money_id=?` | unique partial index on `legacy_money_id` |

Deliberate non-indexes: `category`, `merchant`, `kind` alone (low cardinality, always filtered inside an `occurred_on` range that Q3's index already bounds); `source` (never queried on a hot path). Text search (`q` filter) is a scan — acceptable at personal scale, revisit only on observed slowness (same trigger discipline as the graph-DB deferral in ARCHITECTURE_v2 §4).

Derived-balance cost check: Q2 is an indexed single-account fold over at most a few thousand rows — sub-millisecond in SQLite. Dashboard folds all accounts in one grouped query (`GROUP BY account_id, direction` over the Q1 index). No materialized balance is warranted at this scale; the extension point if that ever changes is a *cached projection*, never a written-back column (§10).

---

## 8. Validation Rules (Business Layer)

Beyond the invariants of §4 (which are hard rules), the write paths validate — in `services/finance` orchestration and `memory/finance` writers, never in routers, never duplicated in UI-only form:

**Transactions**
1. `amount_minor` integer `> 0`; reject zero, negative, and any non-integer input (the API contract carries paise as integers end-to-end; rupee→paise conversion is a client/mapper concern).
2. `occurred_on` a valid calendar date; not before the account's `opening_balance_on`; not more than 1 day in the future (allow "tonight" across timezones, block accidental year typos).
3. `kind`/`direction` per matrix T4; `transfer_group_id` presence per T3.
4. `category`, when present, warned-if-not-in canonical config list but **accepted** (TEXT-by-decision means the list is guidance, not a constraint).
5. Account must be live (unarchived) for new transactions; edits to transactions on archived accounts allowed (history correction).
6. Statement/recurring links per T5/T6.

**Accounts** — profile completeness per A2 (a `credit_card` create without `credit_limit_minor`/`statement_day`/`due_day_offset` is rejected whole); archive preconditions per A1; opening-balance edit lock per A4.

**Recurring rules** — `due_day` within 1–31 (or 1–7 weekly); `ends_on ≥ starts_on`; EMI linkage per R1; expected-amount mismatch on mark-paid: if entered amount ≠ `amount_minor` and `is_variable=0`, require explicit confirmation flag in the request (chat asks; desktop shows inline confirm) — never silently accept, never hard-reject.

**Statements** — dates per S3; overlap per S2; `min_due_minor ≤ total_due_minor`; entered totals `≥ 0` (a credit balance statement is total 0 with a note).

**Payments (orchestrations)** — statement pay amount `> 0` and warn-with-confirm when exceeding derived remaining due (overpayment is legal — it becomes card credit — but never silent); mark-paid rejects a second payment for an already-paid occurrence (T6).

**Rewards** — redemption/expiry not exceeding derived balance (W2); event `occurred_on` not in the future.

**Benefits** — quota ceiling per B2; expiry per B3.

**Cross-cutting** — every UPDATE/soft-DELETE targets a live row (editing a deleted row is a 409/conflict, not a resurrect); all writes bump `updated_at`; soft delete is the only delete verb exposed anywhere.

---

## 9. Migration Strategy: `money` → `transactions`

Principles (all four required properties, mapped to mechanism): **additive** — only CREATEs and INSERTs, `money` never altered; **idempotent** — `legacy_money_id` unique index makes the backfill re-runnable; **reversible** — `money` is frozen, never mutated, so reverting is repointing reads; **no dual-write** — the write path flips atomically in one deploy; at no moment do two tables accept writes.

```
        money (frozen after step 3, kept forever)
          │  backfill, one-time, idempotent
          ▼
     transactions  ◄── the only write path from step 3 onward
```

**Step 0 — Precondition (FIN-0, before any Finance DDL).** Enable `PRAGMA foreign_keys = ON` in `memory/_connection.connect()`. Verify the existing suite passes: current tables declare only two `REFERENCES` (graph tables, already self-enforced in `memory/graph/service.py`), so enabling the pragma must be a no-op for existing data — proven by a one-time integrity scan (`PRAGMA foreign_key_check`) in the same change.

**Step 1 — Additive schema (FIN-1).** All §3 tables created idempotently in `init_db()` (CREATE IF NOT EXISTS, same pattern as every existing table). Seed exactly one default **Cash** account (`type='cash'`, opening balance 0, `opening_balance_on` = earliest `money.created_at` date or today if `money` is empty) — seeded only if no accounts exist (idempotent). `money` untouched.

**Step 2 — Backfill (FIN-1, script under `scripts/database/`).** For each `money` row, INSERT one transaction:
- `earned` → `direction='credit'`, `kind='income'`; `spent` → `direction='debit'`, `kind='expense'`.
- `amount` REAL rupees → integer paise, round-half-up; the script prints per-type totals old vs new for eyeball verification and **aborts without writing** on any negative/NaN amount (manual triage — expected count: zero).
- `occurred_on` = the **local** calendar date of `created_at` (UTC→local via the machine's zone at migration time — the one sanctioned UTC→local derivation in the domain, documented in the script header).
- `note` carried; `category`/`merchant` NULL; `account_id` = Cash; `source='migrated_money'`; `legacy_money_id` = old id; `created_at`/`updated_at` = original `created_at`.
- Idempotency: `INSERT ... ON CONFLICT(legacy_money_id) DO NOTHING`-equivalent guarded by the unique partial index — re-running skips existing rows; interrupted runs resume safely.
- No MutationEvents are emitted for backfilled rows (they are history, not new mutations — no memory writes, no WS storm).

**Step 3 — Atomic write cutover (FIN-1, same release).** `POST /spending` and the chat `log_spending` verb translate to a Cash-account transaction write. `memory/money.py` write helpers are deleted in this change (read helpers survive until step 6). From this commit, `money` receives zero writes — **frozen**. There is no window where both tables accept writes, hence nothing to reconcile.

**Step 4 — Read cutover + event compatibility (FIN-1).** `planner.get_spending_summary` and the home projection switch to transaction-backed totals (numbers proven equal in step 2). The transaction write path emits `finance.transaction.created` **plus** legacy `spending.logged` so the existing desktop spending screen keeps invalidating correctly.

**Step 5 — Frontend cutover (FIN-2).** Finance screens land; `/spending` routes redirect; the dual `spending.logged` emission, the `/spending` adapter endpoints, and the spending screen/hooks/mappers/mocks are deleted together.

**Step 6 — Disposition.** `money` remains in the schema permanently as inert legacy data (never-drop rule; costs nothing). `memory/money.py` read helpers are deleted once step 4's consumers are verified; `schema.py` keeps the CREATE until a natural future tidy.

**Rollback at any step:** step ≤ 2 — drop nothing, just don't proceed (new tables are inert); step 3/4 — repoint endpoints and summary reads back at `money` (it is exactly as it was, frozen); step 5 — restore the redirect. No reverse data migration exists or is needed, because `money` is never mutated after step 0.

---

## 10. Future Reserved Extensions

**Implemented now (FIN-1…FIN-5 scope):** everything in §3 — institutions, accounts (+ both profiles), transactions with `transfer_group_id` and `adjustment`, recurring rules, statements, reward programs/events, benefits/usages; all §6 projections; the §9 migration.

**Reserved for future** (the schema deliberately leaves a socket; building them is additive):

| Extension | Reserved socket in this model | When built, adds |
|---|---|---|
| Investments | `accounts.type` CHECK widened to include `'investment'`; `classification` already covers it | `holdings` + `valuation_snapshots` tables; Net Worth reads latest valuations |
| Goals | none needed — new aggregate | `goals` table; optionally links accounts/rules by id |
| Budgets | `transactions.category` is the join key | `budgets` table (category, period, limit_minor) + a projection; zero ledger changes |
| Attachments | integer PKs are the anchor | polymorphic `attachments` (entity_type, entity_id, path) — the `entity_type` vocabulary of §5 is the enum |
| Merchant entity | `transactions.merchant` TEXT | `merchants` table + additive nullable `merchant_id`; backfill by name match; TEXT column retained |
| Categories entity | `transactions.category` TEXT + config canonical list | `categories` table + additive nullable `category_id`; same recipe as merchants |
| Multi-currency | `accounts.currency` column exists | per-transaction currency + an fx-rate source; until then single-currency INR is asserted at account create |
| Offline sync / Mobile | UTC audit stamps, soft deletes everywhere, append-only ledgers, MutationEvent stream | a sync log keyed by (`entity_type`, id, `updated_at`); mobile is just another producer through the same FastAPI + `finalize_mutations()` — architecture already guarantees this |
| Cached balance projection | balances derived by formula 6.0 | if scale ever demands: a rebuildable cache table maintained by the event stream — LanceDB precedent: *derived, rebuildable, never source of truth* |

**Out of scope permanently (re-affirmed non-goals):** bank/UPI sync, statement PDF/OCR import, amortization engine, rewards earn-rate calculation engine, any second credential, hard deletes.

---

## 11. Risk Analysis — decisions that get expensive after production data exists

Ordered by cost-to-reverse once real rows exist:

1. **Paise conversion at backfill (highest, one-shot).** A wrong rounding rule corrupts every historical amount silently. Mitigations are in §9 step 2 (printed totals, abort on anomalies) — but the *rule itself* (round-half-up) must be right before the script runs; it cannot be re-derived later because the REAL originals stay frozen in `money` (which is also the safety net: re-backfill is possible as long as `legacy_money_id` rows are deleted first — the one sanctioned correction path, documented here so it isn't invented under pressure).
2. **`occurred_on` timezone semantics.** "Local DATE supplied by the producer" must be enforced from the first write. If any code path ever derives it server-side from UTC, dates near midnight shift and period aggregates (months, statement cycles) silently misbucket — and it is unfixable retroactively because the true local date was never captured. The migration backfill (§9) is the single documented exception.
3. **Sign convention (6.0).** Every projection, validation, and future consumer assumes *direction = effect on the account, liabilities trend negative*. Flipping it later means rewriting stored `direction` values. It is stated once in §6.0; FIN-1 tests must pin it (a card spend decreases card balance; a card payment increases it).
4. **Transfer-pair integrity lives in the service, not the DB.** SQLite cannot declare "exactly two rows share this UUID." A future writer bypassing `services/finance` orchestration could create one-legged transfers that corrupt two balances at once. Guard: the architecture already bans second write paths; add a cheap integrity assertion (grouped count check) to the test suite and the backup script.
5. **Enum CHECKs vs. evolution.** SQLite CHECK constraints can't be altered in place — widening `kind` or `type` requires the documented CHECK-widening recipe (new table + copy or pragma-guarded rebuild). Acceptable because enums here are closed by design; the recipe just needs to exist in the migration script library before it's needed in anger.
6. **Statement period edge cases.** `statement_day` 29–31 clamping, and users whose issuer shifts cycle dates: `period_start` uniqueness makes a wrong generated cycle a *conflict* rather than a duplicate, and rows are user-editable pre-linking — but linked transactions (T5) make later period corrections a re-linking exercise. Keep cycle generation lazy and user-confirmable (the sweep proposes; the user's statement entry confirms).
7. **Soft-delete leakage.** One aggregate that forgets `deleted_at IS NULL` shows resurrected money — the classic derived-model bug. Mitigation is structural: `memory/finance` exposes only live-row query helpers; raw table access stays private to the package (same discipline as `_connection`).
8. **Institution as required-later.** Kept nullable now; if it were ever made mandatory, backfilling "which bank is 'Cash'" is unanswerable. It stays optional forever — flagged so nobody "tidies" it into NOT NULL.
9. **Derived balances at scale** — lowest risk: personal-scale math (§7), and the escape hatch is a rebuildable cache (§10), an additive change.

---

## 12. Final Recommendation — changes required BEFORE the first line of FIN-1

1. **FIN-0 (blocking): enable `PRAGMA foreign_keys = ON` in `memory/_connection.connect()`** + run `PRAGMA foreign_key_check` once against existing data + full suite green. This is a behavior change to *every* existing connection and must land, isolated, before any Finance DDL exists — approved in the review conclusions, restated here as the entry gate.
2. **Amend `DESKTOP_WRITE_OPERATIONS.md` §4** with the §5 event table and the eight new `entity_type` values *in the FIN-1 PR itself* — that document is canon for event names; Finance must not fork the vocabulary informally.
3. **Pin the sign convention and the kind→direction matrix in tests first** (T4, §6.0) — write these parity/unit tests before the first write path, since risk #3 is unfixable after data exists.
4. **Fix the canonical category list location** (config file path + initial values) before the first transaction write, so `source='manual'` data never starts with ad-hoc category spellings the warn-only validation (§8.4) can't help with.
5. **Decide the notable-amount memory threshold** (single config value, e.g. `NOVA_FINANCE_MEMORY_THRESHOLD_MINOR`) before FIN-1, because `memory_producers` policy ships with the gate and silent policy defaults become de-facto contracts.
6. **Write the CHECK-widening migration recipe** into `scripts/database/` documentation alongside the backfill script (risk #5) — cheap now, painful the day `investment` lands.
7. **No other changes.** Specifically re-affirmed as *correct and final* after this pass: derived balances/status/usage (no stored aggregates anywhere), `transfer_group_id` over peer-id, integer paise, local-DATE `occurred_on`, statements as projected cycles, institutions implemented now as nullable reference, categories/merchants as TEXT, and `MutationEvent` + `finalize_mutations()` untouched — the Finance domain adds builders and policy rows, never pipeline changes.

With FIN-0 and items 2–6 folded into the FIN-1 plan, this model is ready for implementation.
