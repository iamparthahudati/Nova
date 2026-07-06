# @nova/api-contracts

TypeScript types mirroring `apps/backend/services/api/schemas/`. Source of truth for field shapes is the Python Pydantic models; update both in the same PR when the API changes.

Desktop and future clients should import from this package instead of duplicating DTOs.
