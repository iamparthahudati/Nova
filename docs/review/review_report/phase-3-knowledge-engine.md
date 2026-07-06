# Phase 3 — Knowledge Engine

> Deliverables per roadmap: PDF indexing, Markdown, Notes, GitHub, OCR, Document search.
> Verification: RAI locates information across personal documents.

**Status: Not started (0%)**

**Gate:** Blocked behind Phase 1 (3/8 complete) and Phase 2 (0%) per roadmap ordering.

---

## 1. What changed
Nothing. No document-indexing, OCR, or file-search code exists anywhere in the repo.

## 2. Folder structure
No `services/knowledge_engine/` or document-index directory exists. Note: Roadmap v4's Phase 1 Milestone 7 is also called "Knowledge Service" but is a narrower, different thing — live external providers (weather/GitHub notifications/RSS), currently inline in `nova.py`. Phase 3's "Knowledge Engine" is about indexing the user's own documents (PDFs, notes, markdown) and is unrelated in scope; don't conflate the two when planning.

## 3. Files added
None.

## 4. Files modified
None.

## 5. Public APIs
None defined. Anticipated shape, not implemented:

```python
# hypothetical — not implemented
index_document(path: str) -> None
search_documents(query: str, k: int = 5) -> list[dict]
ocr_extract(path: str) -> str
```

## 6. Dependency graph
Not applicable — no code exists. Would likely depend on Phase 2's semantic-search primitives (embeddings/retrieval) once those exist, plus a new `services/knowledge_engine/` (or similarly named) module.

## 7. Remaining work
Everything: PDF text extraction, markdown/notes ingestion, GitHub content indexing (distinct from the existing GitHub *notifications* polling in `nova.py`'s `get_github_notifications`), OCR pipeline, and a document search API consumable by Brain.

## 8. Known issues
None to report — no code exists to have issues.

## 9. Architecture diagram
```mermaid
flowchart LR
    BRAIN[services.brain] -.->|not yet built| KE["services.knowledge_engine\n(PDF/MD/Notes/GitHub/OCR index)"]
    KE -.-> SEM["Phase 2 semantic search\n(not yet built)"]
    style KE fill:#5b2020,color:#fff
    style SEM fill:#5b2020,color:#fff
```

## 10. Current completion percentage
**0%.** Blocked on Phases 1–2.
