#!/bin/bash
set -e

# Docker Compose utilities script for TG Community Manager
# This script contains common setup and startup functions used by docker-compose services

setup_system_deps() {
    echo "Installing system dependencies..."
    apt-get update
    apt-get install -y --no-install-recommends libgomp1 curl
    rm -rf /var/lib/apt/lists/*
}

setup_uv() {
    echo "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="/root/.cargo/bin:$PATH"
}

install_python_requirements() {
    echo "Installing Python requirements..."
    if command -v uv >/dev/null 2>&1; then
        uv pip install -r requirements.txt
    else
        python -m pip install --upgrade pip
        pip install --no-cache-dir -r requirements.txt
    fi
}

run_migrations() {
    echo "Running database migrations..."
    alembic upgrade head || true
}

start_bot() {
    echo "Starting Telegram bot..."
    setup_system_deps
    setup_uv
    install_python_requirements
    run_migrations
    echo "Launching dispatcher..."
    exec python3 src/dispatcher.py
}

start_cas_listener() {
    echo "Starting CAS feed listener..."
    setup_system_deps
    setup_uv
    install_python_requirements
    echo "Launching CAS listener..."
    exec python3 src/cas_feed_listener.py
}

# Main entry point
main() {
    local service_name="${1:-}"

    case "$service_name" in
        bot)
            start_bot
            ;;
        cas_listener)
            start_cas_listener
            ;;
        *)
            echo "Usage: $0 {bot|cas_listener}"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"