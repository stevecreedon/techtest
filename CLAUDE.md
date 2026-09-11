````
# FastAPI Project

## Commands
`uvicorn app.main:app --reload` — Start development server on port 8000
`pytest` — Run test suite
`pytest --cov=app` — Run tests with coverage report
`alembic upgrade head` — Apply database migrations
`alembic revision --autogenerate -m "description"` — Create new migration
`ruff check .` — Run linter
`ruff format .` — Format code
`mypy app/` — Type check

## Architecture
- **Framework**: FastAPI with async/await throughout
- **Database**: SQLAlchemy 2.0 async with PostgreSQL
- **Migrations**: Alembic for schema migrations
- **Validation**: Pydantic v2 models for request/response schemas
- **Auth**: JWT tokens via python-jose, password hashing with passlib
- **Testing**: pytest with httpx AsyncClient for API tests

## Project Structure
```
app/
├── main.py              # FastAPI app factory, middleware, startup/shutdown
├── config.py            # Settings via pydantic-settings (reads .env)
├── dependencies.py      # Shared FastAPI dependencies (get_db, get_current_user)
├── models/              # SQLAlchemy ORM models
├── schemas/             # Pydantic request/response models
├── routers/             # API route modules (one per domain)
├── services/            # Business logic layer (called by routers)
├── repositories/        # Database query layer (called by services)
└── tests/
    ├── conftest.py      # Fixtures: async client, test DB, auth headers
    ├── test_routers/    # API integration tests
    └── test_services/   # Unit tests for business logic
```

## SDLC
- when planning from requirements always use beads
- when an issue is started from beads then create a git worktree
- when the issue is completed then push to git and create a PR to main

## Code Conventions
- Router functions are thin — delegate business logic to services/
- Use dependency injection for DB sessions: `db: AsyncSession = Depends(get_db)`
- Pydantic schemas separate Create, Update, and Response models (e.g., UserCreate, UserUpdate, UserResponse)
- All routes return typed Pydantic response models — never return raw dicts or ORM objects
- Use HTTPException for client errors (4xx), let unhandled exceptions become 500s
- Background tasks via FastAPI's BackgroundTasks, not Celery (unless explicitly needed)

## Error Handling
- Validation errors return 422 with Pydantic's default error format
- Business logic errors raise HTTPException with appropriate status codes
- Use custom exception handlers in main.py for domain-specific error types
- Never catch broad Exception — catch specific exception types

## Testing
- Tests use a separate test database (configured in conftest.py)
- Each test runs in a transaction that rolls back — tests don't affect each other
- Use `httpx.AsyncClient` with `app=app` for integration tests
- Factory functions in conftest.py for creating test data (e.g., `create_test_user`)
- Mock external services (email, payment) but hit the real test database

## Things to Avoid
- Do NOT put business logic in router functions — use the service layer
- Do NOT use `*` imports
- Do NOT hardcode configuration — use pydantic-settings and environment variables
- Do NOT use global mutable state — use FastAPI's dependency injection system

````

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:7510c1e2 -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
<!-- END BEADS INTEGRATION -->
