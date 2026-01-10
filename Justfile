# Justfile for tg_community_manager

set dotenv-load := false
set shell := ["bash", "-euco", "pipefail"]

# Helpers
default: help

help:
    @echo "Available recipes:"
    @just --list

# --- Environment ---

# Create/update config/.env interactively
env-setup:
    python3 config/setenv.py

# Load the .env into current shell (use: `just -s -- env-source && your_command`)
env-source:
    @echo "source config/setenv.sh"

# --- Local Dev (no Docker) ---

# Start local PostgreSQL (no Docker)
db-up:
    @just pg-start

# Stop local PostgreSQL (no Docker)
db-stop:
    @just pg-stop

# Check local PostgreSQL status
db-status:
    @just pg-status

# Start local PostgreSQL if available (no Docker)
pg-start:
    @echo "Checking for local PostgreSQL..."
    @if command -v pg_ctl >/dev/null 2>&1 || command -v postgres >/dev/null 2>&1; then \
        echo "Found local PostgreSQL installation"; \
        if pg_isready -h localhost >/dev/null 2>&1; then \
            echo "PostgreSQL is already running on localhost"; \
            psql --version 2>/dev/null || postgres --version 2>/dev/null || echo ""; \
        else \
            echo "PostgreSQL is not running, attempting to start..."; \
            if command -v brew >/dev/null 2>&1 && brew services list 2>/dev/null | grep -q postgresql; then \
                echo "Starting PostgreSQL via Homebrew..."; \
                brew services start postgresql@15 2>/dev/null || brew services start postgresql@14 2>/dev/null || brew services start postgresql 2>/dev/null || echo "Homebrew start failed"; \
            elif command -v pg_ctl >/dev/null 2>&1; then \
                echo "Starting PostgreSQL via pg_ctl..."; \
                pg_ctl -D /usr/local/var/postgres start 2>/dev/null || \
                pg_ctl -D /opt/homebrew/var/postgres start 2>/dev/null || \
                pg_ctl -D ~/Library/Application\ Support/Postgres/var-15 start 2>/dev/null || \
                pg_ctl -D ~/Library/Application\ Support/Postgres/var-14 start 2>/dev/null || \
                echo "Could not auto-start PostgreSQL with pg_ctl. Try manually."; \
            elif command -v systemctl >/dev/null 2>&1; then \
                echo "Starting PostgreSQL via systemctl..."; \
                sudo systemctl start postgresql || echo "systemctl start failed"; \
            else \
                echo "Could not determine how to start PostgreSQL. Please start it manually."; \
            fi; \
            sleep 2; \
            if pg_isready -h localhost >/dev/null 2>&1; then \
                echo "✓ PostgreSQL started successfully"; \
                psql --version 2>/dev/null || postgres --version 2>/dev/null || echo ""; \
            else \
                echo "⚠ Warning: PostgreSQL may not have started. Check manually with: pg_isready -h localhost"; \
            fi; \
        fi; \
    else \
        echo "No local PostgreSQL found (checked for: pg_ctl, postgres commands)"; \
        echo "Use 'just dc-up-db' to start via Docker instead."; \
        exit 1; \
    fi

# Stop local PostgreSQL if running
pg-stop:
    @echo "Stopping local PostgreSQL..."
    @if command -v brew >/dev/null 2>&1 && brew services list 2>/dev/null | grep postgresql | grep -q started; then \
        echo "Stopping PostgreSQL via Homebrew..."; \
        brew services stop postgresql@15 2>/dev/null || brew services stop postgresql@14 2>/dev/null || brew services stop postgresql 2>/dev/null; \
    elif command -v pg_ctl >/dev/null 2>&1; then \
        echo "Stopping PostgreSQL via pg_ctl..."; \
        pg_ctl -D /usr/local/var/postgres stop 2>/dev/null || \
        pg_ctl -D /opt/homebrew/var/postgres stop 2>/dev/null || \
        pg_ctl -D ~/Library/Application\ Support/Postgres/var-15 stop 2>/dev/null || \
        pg_ctl -D ~/Library/Application\ Support/Postgres/var-14 stop 2>/dev/null || \
        echo "Could not stop PostgreSQL with pg_ctl"; \
    elif command -v systemctl >/dev/null 2>&1; then \
        echo "Stopping PostgreSQL via systemctl..."; \
        sudo systemctl stop postgresql; \
    else \
        echo "Could not determine how to stop PostgreSQL"; \
        exit 1; \
    fi
    @sleep 1
    @if pg_isready -h localhost >/dev/null 2>&1; then \
        echo "⚠ Warning: PostgreSQL still appears to be running"; \
    else \
        echo "✓ PostgreSQL stopped"; \
    fi

# Check PostgreSQL status
pg-status:
    @echo "Checking PostgreSQL status..."
    @if pg_isready -h localhost >/dev/null 2>&1; then \
        echo "✓ PostgreSQL is running on localhost"; \
        psql --version 2>/dev/null || postgres --version 2>/dev/null || true; \
        if command -v brew >/dev/null 2>&1; then \
            echo ""; \
            brew services list 2>/dev/null | grep postgresql || true; \
        fi; \
    else \
        echo "✗ PostgreSQL is not running on localhost"; \
        if command -v pg_ctl >/dev/null 2>&1 || command -v postgres >/dev/null 2>&1; then \
            echo "  (Local installation found, use 'just pg-start' to start)"; \
        else \
            echo "  (No local installation found, use 'just dc-up-db' for Docker)"; \
        fi; \
    fi

# Setup environment and start local PostgreSQL if available
dev-setup:
    @echo "Running config/setenv.py..."
    python3 config/setenv.py
    @echo ""
    @echo "Checking for local PostgreSQL..."
    @if command -v pg_ctl >/dev/null 2>&1 || command -v postgres >/dev/null 2>&1; then \
        echo "Found local PostgreSQL installation"; \
        if pg_isready -h localhost >/dev/null 2>&1; then \
            echo "PostgreSQL is already running"; \
        else \
            echo "PostgreSQL is not running, attempting to start..."; \
            if command -v brew >/dev/null 2>&1 && brew services list 2>/dev/null | grep -q postgresql; then \
                echo "Starting PostgreSQL via Homebrew..."; \
                brew services start postgresql@15 || brew services start postgresql@14 || brew services start postgresql; \
            elif command -v pg_ctl >/dev/null 2>&1; then \
                echo "Starting PostgreSQL via pg_ctl..."; \
                pg_ctl -D /usr/local/var/postgres start || pg_ctl -D ~/Library/Application\ Support/Postgres/var-15 start || echo "Could not auto-start PostgreSQL. Please start it manually."; \
            else \
                echo "Could not determine how to start PostgreSQL. Please start it manually."; \
            fi; \
            sleep 2; \
            if pg_isready -h localhost >/dev/null 2>&1; then \
                echo "PostgreSQL started successfully"; \
            else \
                echo "Warning: PostgreSQL may not have started. Check manually."; \
            fi; \
        fi; \
    else \
        echo "No local PostgreSQL found. Use 'just dc-up-db' to start via Docker."; \
    fi

install:
    # Prefer uv if available, fallback to pip
    if command -v uv >/dev/null 2>&1; then \
        uv pip install -r requirements.txt; \
    else \
        python3 -m pip install --upgrade pip; \
        pip3 install -r requirements.txt; \
    fi

run:
    # Ensure .env is present
    test -f config/.env || (echo "Missing config/.env. Run: just env-setup" && exit 1)
    python3 src/dispatcher.py

cas-listener:
    test -f config/.env || (echo "Missing config/.env. Run: just env-setup" && exit 1)
    python3 src/cas_feed_listener.py

migrate:
    # Uses alembic.ini and ENV_DB_* from environment/.env
    test -f config/.env || (echo "Missing config/.env. Run: just env-setup" && exit 1)
    source config/setenv.sh && alembic upgrade head

revision msg="auto":
    source config/setenv.sh && alembic revision -m "{{msg}}" --autogenerate

# --- Docker Compose ---

dc-up:
    # Bring up DB + bot (and CAS listener). Ensure .env exists.
    test -f config/.env || (echo "Missing config/.env. Run: just env-setup" && exit 1)
    docker compose up -d --build

dc-up-bot:
    test -f config/.env || (echo "Missing config/.env. Run: just env-setup" && exit 1)
    docker compose up -d --build bot

dc-up-db:
    docker compose up -d db

dc-logs:
    docker compose logs -f --tail=200

dc-logs-bot:
    docker compose logs -f bot

dc-down:
    docker compose down

dc-restart:
    docker compose restart

dc-ps:
    docker compose ps

psql:
    # Open psql shell into the db service
    docker compose exec -e PGPASSWORD=${ENV_DB_PASSWORD:-postgres} db psql -U ${ENV_DB_USER:-postgres} -d ${ENV_DB_DATABASE:-tgcm}

alembic-in-docker:
    # Run alembic inside bot container
    docker compose exec bot bash -lc 'source config/setenv.sh && alembic upgrade head'
