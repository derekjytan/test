# University Recruiting - Practical Interview Project

Notion (internal only): https://app.notion.com/p/decagon/UR-Build-an-AI-Chatbot-3a71ef4377338049b27dd1bbe24308e1?source=copy_link

A small AI chatbot: a React frontend, a FastAPI backend, and a Postgres
database. Everything runs in Docker, so the only thing you need to install is
Docker — no Node, Python, or Postgres required.

| Service  | What it is                | URL on your machine                                 |
| -------- | ------------------------- | --------------------------------------------------- |
| `web`    | React + Vite frontend     | http://localhost:5273                               |
| `api`    | FastAPI backend           | http://localhost:8787                               |
| `db`     | Postgres 17 database      | `postgresql://app:app@localhost:5433/chatbot`       |
| `worker` | Background worker scaffold | No HTTP port; idle until implemented              |
| `migrate` | Applies pending SQL migrations, then exits | No HTTP port                         |

## 1. Install Docker

Pick the section for your operating system. When you're done, confirm Docker
works by running these in a terminal (both should print a version number):

    docker --version
    docker compose version

> Use `docker compose` (with a space). The older `docker-compose` command is
> not supported.

### macOS

1. Download **Docker Desktop** from
   https://www.docker.com/products/docker-desktop/ — choose **Apple Silicon**
   for M-series Macs or **Intel** for older Macs ( → About This Mac shows
   which you have).
   - Homebrew alternative: `brew install --cask docker`
2. Open **Docker** from Applications and accept the prompts. Wait until the
   whale icon in the menu bar says Docker is running.
3. Open **Terminal** for the remaining steps.

### Windows

1. Install **WSL 2** (Docker needs it). Open **PowerShell as Administrator**
   and run the command below, then restart your computer:

       wsl --install

2. Download and install **Docker Desktop** from
   https://www.docker.com/products/docker-desktop/. Keep the
   **"Use WSL 2 instead of Hyper-V"** option checked.
3. Open **Docker Desktop** and wait until it says Docker is running.
4. **Recommended:** run the project from inside WSL (the **Ubuntu** app
   installed by `wsl --install`) and keep the project folder in your Linux home
   directory (e.g. `~/interview-project`), not under `C:\` or `/mnt/c/`.
   Live reload does not detect file changes on the Windows filesystem, and it
   is noticeably faster inside WSL. Then follow the **macOS / Linux** commands
   below.
   - To edit the files with VS Code, run `code .` from the project folder in
     Ubuntu.
   - If you use PowerShell instead, everything works except live reload: you
     will need to restart the app to see code changes.

### Linux

1. Install **Docker Engine** and the **Compose plugin** for your distribution
   by following https://docs.docker.com/engine/install/ (on Ubuntu/Debian this
   includes the `docker-compose-plugin` package). Docker Desktop for Linux also
   works if you prefer a GUI.
2. Allow your user to run Docker without `sudo`, then **log out and back in**:

       sudo usermod -aG docker $USER

3. Make sure the Docker service is running:

       sudo systemctl enable --now docker

## 2. Initialize the project

Do this once, from a terminal in the project folder (the one containing
`docker-compose.yml`).

**Step 1 — Get the code.** Clone the repository (or unzip the folder you were
given) and `cd` into it.

**Step 2 — Create your environment file.** This is where your OpenAI API key
lives. The file goes in the project folder, next to `docker-compose.yml` —
Docker Compose reads it automatically.

macOS / Linux / WSL:

    cp .env.example .env

Windows PowerShell:

    Copy-Item .env.example .env

**Step 3 — Add your OpenAI API key.** Open `.env` in your editor
and replace the placeholder:

    OPENAI_API_KEY=sk-...your key...

The app still starts without a key; everything except sending chat messages
works, and the chat shows "The AI service is not configured" until you add one.

**Step 4 — Start everything.**

    docker compose up --build

If you have Node.js/npm installed, the equivalent one-command startup from
the **repository root** is:

    npm run dev

No `npm install`, Python setup, or manual SQLAlchemy installation is needed
on your machine. The command builds and starts Postgres, the API, and the
frontend using Docker, installs their dependencies, and initializes a fresh
database automatically. Docker must be installed and running; configure the
API key in `.env` as above to send chat messages. Running `npm run dev` from
inside `web/` starts only the frontend.

The first run downloads images and installs dependencies, which takes a few
minutes. You'll know it's ready when the logs show the frontend (`web-1`)
printing a `Local: http://localhost:5273/` line and the backend (`api-1`)
printing `Application startup complete`.

**Step 5 — Check it works.**

- Open http://localhost:5273 and send a message to the chatbot.
- Open http://localhost:5273/api/health — it should show `{"ok":true}`, which
  means the frontend, backend, and database are all connected.

## 3. Day-to-day usage

- **Code changes reload automatically.** Edit files in `web/` or `server/` and
  the frontend / backend restart on their own.
- **Stop the app:** press `Ctrl+C` in the terminal running it, or run
  `docker compose down` from another terminal.
- **Start again later:** `docker compose up` (use
  `docker compose up --build -V` if you changed dependencies in
  `web/package.json` or `server/pyproject.toml` — `-V` re-creates the web
  container's anonymous `node_modules` volume; database data is unaffected).
  Alternatively, run `npm run dev` from the repository root; it always builds
  the images and refreshes the frontend dependency volume while keeping the
  database data.
- **Run in the background:** `docker compose up -d`, then
  `docker compose logs -f` to watch the logs.

### Useful commands

| Command                                         | What it does                          |
| ----------------------------------------------- | ------------------------------------- |
| `docker compose up --build`                     | Build and start everything            |
| `npm run dev` (repository root)                 | Build and start everything with npm   |
| `docker compose up --build -V`                  | Rebuild with fresh `node_modules`     |
| `docker compose down`                           | Stop everything (database data kept)  |
| `docker compose down -v`                        | Stop and **wipe** the database data   |
| `docker compose logs -f api`                    | Follow the backend logs (`web`, `db`) |
| `docker compose exec db psql -U app chatbot`    | Open a SQL shell in the database      |
| `docker compose ps`                             | Show which services are running       |

## Database

- Postgres runs in the `db` container. From your machine (e.g. with TablePlus,
  DBeaver, or `psql`) connect to
  `postgresql://app:app@localhost:5433/chatbot`.
- The backend reads the `DATABASE_URL` environment variable (set in
  `docker-compose.yml`). SQLAlchemy uses the existing Psycopg 3 driver;
  `server/db.py` selects `postgresql+psycopg` automatically, so the standard
  Postgres URL works unchanged.
- Routes receive a request-scoped SQLAlchemy `Session` through `DbSession`
  in `server/api/dependencies.py`. `server/db.py` owns the shared connection
  pool, which is disposed when the API shuts down.
- `server/entities.py` contains ORM mappings for all four tables. Files in
  `server/models/` remain Pydantic request/response schemas. Services convert
  ORM objects to these schemas before returning them.
- Write services explicitly commit before returning. Request cleanup rolls
  back unfinished transactions and releases connections. Chat completion
  releases its read transaction before calling the model, then saves both
  messages and the conversation update in one transaction.
- `.sql` files in `db/init/` run automatically, in filename order (e.g.
  `01_schema.sql`, `02_seed.sql`) — but **only on the first startup with an
  empty database**. Use numbered migrations for subsequent schema changes so
  existing data is preserved.

### Running migrations

Compose starts `db`, runs the `migrate` service, then starts the API and worker
only after migrations succeed. An exited `migrate` container with exit code 0
is expected. The starter has no migration files and makes no application-schema
changes; the runner only creates its empty `schema_migrations` tracking table.

To change the schema:

1. Add a file to `server/migrations/`, such as `001_add_conversation_notes.sql`.
   Use increasing, zero-padded numbers (`001_`, `002_`, etc.). For example:

   ```sql
   ALTER TABLE conversations ADD COLUMN notes text;
   ```

2. Update the matching ORM mapping in `server/entities.py`. Updating a Python
   model alone does not change Postgres. Update public Pydantic schemas if the
   field should also appear in API responses.
3. Apply pending files from the repository root:

   ```sh
   docker compose run --rm migrate
   ```

   Full startup (`npm run dev` or `docker compose up --build`) also applies them.
   If the API and worker are already running, stop them before a schema change,
   then run the migration and start them again:

   ```sh
   docker compose stop api worker
   docker compose run --rm migrate
   docker compose up -d api worker
   ```

The runner applies files in filename order and records them in
`schema_migrations`. Re-running skips applied files. All pending files run in
one transaction: a failure rolls back the batch and prevents dependent services
from starting on full startup. Fix a failed, unapplied file and rerun. Do not edit
or rename an applied file; add a new migration instead. Do not put `BEGIN`,
`COMMIT`, or commands that cannot run inside a transaction (such as
`CREATE INDEX CONCURRENTLY`) in these files. There is no automatic down migration;
undo a deployed change with a new migration. This project does not use Alembic.

Inspect migration history with:

```sh
docker compose exec db psql -U app -d chatbot -c "SELECT * FROM schema_migrations ORDER BY name;"
```

Do not use `docker compose down -v` to apply a migration: it deletes database data.

### Using SQLAlchemy

The existing auth and conversation services provide examples of reads,
inserts, updates, and deletes. For example, inside a service:

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from entities import Conversation


def conversation_titles(session: Session, user_id):
    return session.scalars(
        select(Conversation.title)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
    ).all()
```

Pass the route's `DbSession` to the service. Keep database work synchronous,
and commit successful writes explicitly. A flush sends pending changes to
Postgres but does not commit them. Keep ORM mappings and numbered SQL migrations
in sync when changing tables; SQLAlchemy does not automatically migrate the
database, and this project does not use Alembic.

### Database tests

The integration tests use real Postgres and stub the model service, so they
do not need an OpenAI API key. Each test creates and removes a unique schema;
use a disposable database whose user can create schemas.

With the Compose database running, create a test database once:

```sh
docker compose exec db createdb -U app chatbot_test
```

After rebuilding the API image for the new dependencies, run:

```sh
docker compose run --rm --no-deps -v ./db:/db:ro -e TEST_DATABASE_URL=postgresql://app:app@db:5432/chatbot_test api uv run --frozen pytest
```

Or, with Python 3.12 and `uv` installed locally (macOS / Linux / WSL):

```sh
cd server
TEST_DATABASE_URL=postgresql://app:app@localhost:5433/chatbot_test uv run --frozen pytest
```

Tests cover authentication, ownership, archival, message ordering, model
failures, transaction rollback when saving a chat exchange fails, and migration
ordering, repeatability, and rollback after a failed batch.

## Background worker scaffold

The `worker` container starts automatically with `npm run dev` or
`docker compose up --build`. It uses the API's Python image, dependencies,
environment, and mounted `server/` source directory, and needs no host port.
`server/worker.py` calls `run_once()` every five seconds. **That function is
intentionally empty:** it does not access the database, call the model, or modify
conversations. No scheduled-task tables, APIs, UI, or job behavior are supplied.

Implement one iteration in `run_once()`, calling your own service functions.
The existing `db.SessionLocal` is available when you need database access:

```python
from db import SessionLocal


def run_once() -> None:
    with SessionLocal() as session:
        # Query your tables and call your service functions here.
        # Commit successful writes explicitly with session.commit(),
        # unless the service already commits them.
        pass
```

Use a fresh session for each iteration (and each thread, if adding concurrency).
Closing a session rolls back unfinished work. Avoid holding a transaction open
while waiting on a model or another external service. Shared Python services can
be imported directly; a worker does not need to call the API over HTTP.

The loop logs startup and exceptions, continues after a failed iteration, and
stops gracefully on Ctrl-C or `docker compose stop worker`. It finishes the
current iteration before stopping; long-running work needs its own shutdown
handling. The scaffold does not define job retries or execution guarantees.

```sh
docker compose logs -f worker
docker compose restart worker        # Reload worker code after editing it
docker compose stop worker           # API and chat continue running
docker compose up -d worker          # Start it again
```

Unlike the API, the worker does not auto-reload Python changes. To change polling,
set `WORKER_POLL_SECONDS` to a positive number in `.env`, then run
`docker compose up -d --force-recreate worker` to load the new environment.

For a second checkout, set a distinct `COMPOSE_PROJECT_NAME` and unused
`WEB_PORT`, `API_PORT`, and `DB_PORT` in its `.env` (see `.env.example`). Defaults
remain 5273, 8787, and 5433.

## Auth

The app requires sign-in. The database is seeded with three users, and the
sign-in page has a quick-login button for each:

| Name    | Password         |
| ------- | ---------------- |
| `alice` | `alice-password` |
| `bob`   | `bob-password`   |
| `carol` | `carol-password` |

- Each user sees only their own conversations.
- Signing in returns a session token, which the frontend keeps in
  `sessionStorage` and sends as `Authorization: Bearer <token>`. Storage is
  per tab, so two tabs can be signed in as different users.
- Sessions don't expire; they end when you log out from the sidebar.
- To create a user, enter a name and password on the sign-in page and click
  "Create account". Names must be unique; an already-taken name shows an
  error.
- Passwords are stored in plaintext for demonstration only — see the warning
  in `server/service/auth.py`.

## Troubleshooting

- **`Cannot connect to the Docker daemon` / `docker: command not found`** —
  Docker isn't running or installed. Start Docker Desktop (macOS/Windows) or
  run `sudo systemctl start docker` (Linux). On Windows + WSL, check Docker
  Desktop → Settings → Resources → WSL integration is enabled for Ubuntu.
- **`port is already allocated` / `address already in use`** — something else
  is using port 5273, 8787, or 5433. Stop that program, or change the
  left-hand number of the matching `ports:` entry in `docker-compose.yml`.
- **`permission denied ... docker.sock` (Linux)** — you haven't logged out and
  back in after adding yourself to the `docker` group.
- **The first chat message fails** — the backend takes a few seconds longer to
  start than the frontend. Wait a moment and try again.
- **Chat returns "The AI service is not configured"** — check the key in
  `.env`, then restart with `docker compose up`.
- **Something is stuck or weird** — `docker compose down -v` and then
  `docker compose up --build` gives you a completely fresh start.

## Notes

- The app is a small chatbot backed by OpenAI's Responses API. Choose a model,
  send a message, and the API returns the model's answer.
- The API key is read from `.env` at the project root. Do not expose it to the
  frontend or commit that file.
- The app has two pages: `/login` and the chat page — `/` starts a new chat
  and `/chat/<id>` opens a conversation.
- `GET /api/models` returns the supported text models. The same backend model
  enum validates every chat request before an OpenAI API call is made.
- The UI is React + TypeScript in `web/src/App.tsx`. The API is FastAPI in
  `server/app.py`.
