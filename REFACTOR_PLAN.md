# Refactoring Plan for Trading Service

**Goal:** Decompose the monolithic `trading_service.py`.

**Principles:**
- Create a dedicated directory for the service.
- The new service entrypoint should be `core.py`.
