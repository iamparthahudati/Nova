# RAI Roadmap v4 --- Architecture First

> **Mission:** Build **RAI** as a long-term Personal AI Operating
> System.\
> RAI is not a chatbot. It is a modular, maintainable system that
> thinks, remembers, plans, automates, and evolves.

------------------------------------------------------------------------

# Core Engineering Principles

## Non-negotiable Rules

-   Architecture before intelligence.
-   Refactor before adding features.
-   One service per milestone.
-   Never grow `nova.py`.
-   Every service owns a single responsibility.
-   No circular dependencies.
-   No duplicated logic.
-   No feature work during refactoring milestones.
-   Production-quality code only.

------------------------------------------------------------------------

# Permanent Claude Instructions

Before every implementation:

1.  Review the current architecture.
2.  Explain whether the requested change improves or hurts the
    architecture.
3.  Recommend a better long-term approach if one exists.
4.  Never implement the first solution automatically.
5.  Think like a Staff Engineer building software that will live for 10+
    years.
6.  Protect the architecture from technical debt.
7.  If my request creates technical debt, explain why and push back.

------------------------------------------------------------------------

# Phase 1 --- Architecture Foundation

## Objective

Convert RAI from a large Python script into a modular operating system.

No new capabilities.

Only architecture.

------------------------------------------------------------------------

## Milestone 1 --- Memory Service ✅

### Goal

Extract all memory-related functionality into an independent service.

### Requirements

-   Own SQLite
-   CRUD APIs
-   Repository pattern
-   No direct database access outside the service
-   Documentation
-   Tests

### Verification

-   Memory can be replaced without changing other services.
-   No module accesses SQLite directly.

------------------------------------------------------------------------

## Milestone 2 --- Voice Service

### Scope

-   Wake word
-   Microphone
-   Whisper
-   Recording
-   Audio
-   Follow-up mode
-   TTS

### Expectations

-   Voice owns everything audio.
-   Other services communicate only through its public API.

### Verification

-   No audio logic remains in `nova.py`.
-   Voice can be disabled without breaking the system.

------------------------------------------------------------------------

## Milestone 3 --- Brain Service

### Scope

-   Claude API
-   Prompt generation
-   Conversation history
-   Tool routing
-   Tool execution

### Expectations

-   No business logic in `nova.py`.
-   Brain never directly manipulates storage.
-   Uses Memory APIs.

### Verification

-   Claude implementation can be swapped without changing Planner or
    Voice.

------------------------------------------------------------------------

## Milestone 4 --- Planner Service

### Scope

-   Morning briefing
-   Evening summary
-   Daily planner
-   Weekly planner
-   Priorities
-   Habit planning

### Expectations

Planner consumes:

-   Calendar
-   Memory
-   Goals
-   Tasks

Planner returns:

-   Daily schedule
-   Focus blocks
-   Priorities

### Verification

Planner never calls Claude directly except through Brain.

------------------------------------------------------------------------

## Milestone 5 --- Calendar Service

### Scope

-   Apple Calendar
-   Events
-   Reminders
-   Scheduling

### Verification

Calendar implementation can be replaced without touching Planner.

------------------------------------------------------------------------

## Milestone 6 --- Automation Service

### Scope

-   AppleScript
-   Finder
-   Browser
-   VS Code
-   Terminal
-   Mail
-   WhatsApp
-   Notifications

### Expectations

Plugin-based architecture.

Every automation isolated.

### Verification

New automation can be added without modifying existing plugins.

------------------------------------------------------------------------

## Milestone 7 --- Knowledge Service

### Scope

-   RSS
-   Weather
-   Reflection
-   External information providers

### Expectations

Knowledge gathers information.

Brain reasons over it.

### Verification

Knowledge contains no Claude logic.

------------------------------------------------------------------------

## Milestone 8 --- Bootstrap

### Goal

Shrink `nova.py`.

### Expected

``` python
from services import *

def main():
    app = RaiApplication()
    app.start()

if __name__ == "__main__":
    main()
```

### Verification Checklist

-   `nova.py` \< 100 lines
-   No business logic
-   No SQL
-   No Claude
-   No Whisper
-   No AppleScript
-   No planner logic
-   Only startup and shutdown

------------------------------------------------------------------------

# Phase 1 Completion Criteria

-   Memory Service
-   Voice Service
-   Brain Service
-   Planner Service
-   Calendar Service
-   Automation Service
-   Knowledge Service
-   Bootstrap complete

Only after ALL are complete may Phase 2 begin.

------------------------------------------------------------------------

# Phase 2 --- Semantic Memory

## Goal

Upgrade memory without changing architecture.

### Deliverables

-   LanceDB
-   Embeddings
-   Semantic Search
-   Long-term Memory
-   Importance Scoring
-   Retrieval Pipeline

### Verification

RAI answers questions about old conversations using semantic retrieval.

------------------------------------------------------------------------

# Phase 3 --- Knowledge Engine

### Deliverables

-   PDF indexing
-   Markdown
-   Notes
-   GitHub
-   OCR
-   Document search

### Verification

RAI locates information across personal documents.

------------------------------------------------------------------------

# Phase 4 --- Developer Service

### Deliverables

-   Git awareness
-   Project awareness
-   Branch tracking
-   TODO analysis
-   Code search
-   Architecture review

### Verification

"Continue yesterday's work" restores development context.

------------------------------------------------------------------------

# Phase 5 --- Vision

### Deliverables

-   Screenshot pipeline
-   OCR
-   Claude Vision
-   UI understanding
-   Error detection

### Verification

RAI recognizes build errors from screenshots and explains them.

------------------------------------------------------------------------

# Phase 6 --- Desktop

### Deliverables

-   Electron
-   React
-   WebSocket
-   Live dashboard
-   Memory search
-   Voice UI

### Verification

The desktop application becomes the primary interface.

------------------------------------------------------------------------

# Definition of Done (Every Milestone)

-   Architecture reviewed
-   Single Responsibility Principle
-   Public API documented
-   No circular dependencies
-   Unit-testable
-   Logging added
-   Configuration supported
-   Documentation updated
-   No regressions
-   Existing functionality preserved

------------------------------------------------------------------------

# Architecture Review Prompt

``` text
Act as a Principal Software Architect.

Review ONLY the module completed in this milestone.

Evaluate:

1. Architecture
2. Separation of concerns
3. SOLID principles
4. Dependency graph
5. Testability
6. Maintainability
7. Scalability
8. Technical debt
9. Code smells
10. Future risks

Score it out of 10.

If below 9.5/10, explain exactly what must change before the next milestone.
```
