#!/usr/bin/env python3
"""
Interactive .env creator for tg_community_manager.

Guides you through entering environment variables used by the project
and writes them to config/.env (backing up an existing file).

Usage:
  python3 config/setenv.py

After creating .env, load it into your shell when needed:
  source config/setenv.sh
"""

import os
import sys
import re
import time
from pathlib import Path
from typing import Optional, Dict
from getpass import getpass


SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR / ".env"


def read_env(path: Path) -> dict:
    """Basic .env reader supporting KEY=VALUE and quoted values."""
    env = {}
    if not path.exists():
        return env
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # Allow lines starting with export
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()
        if (val.startswith("\"") and val.endswith("\"")) or (
            val.startswith("'") and val.endswith("'")
        ):
            val = val[1:-1]
        # Unescape common sequences
        val = val.replace("\\n", "\n").replace("\\t", "\t").replace("\\\"", '"')
        env[key] = val
    return env


def should_quote(value: str) -> bool:
    if value == "":
        return False
    # Safe characters without quoting
    safe = re.compile(r"^[A-Za-z0-9._@/:#\-]+$")
    return not bool(safe.match(value))


def serialize_env(env: dict) -> str:
    lines = []
    for k, v in env.items():
        if v is None:
            v = ""
        if should_quote(v):
            # Escape embedded quotes
            vv = v.replace('"', '\\"')
            lines.append(f"{k}=\"{vv}\"")
        else:
            lines.append(f"{k}={v}")
    return "\n".join(lines) + "\n"


def yes_no(prompt: str, default: bool = True) -> bool:
    d = "Y/n" if default else "y/N"
    while True:
        ans = input(f"{prompt} [{d}]: ").strip().lower()
        if ans == "" or ans is None:
            return default
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        print("Please answer 'y' or 'n'.")


def prompt_value(name: str, prompt: str, default: Optional[str] = None, *, secret: bool = False,
                 validator=None) -> str:
    while True:
        shown_default = None
        if default is not None and default != "":
            shown_default = "***" if secret else default
        suffix = f" [default: {shown_default}]" if shown_default is not None else ""
        if secret:
            raw = getpass(f"{prompt}{suffix}: ")
        else:
            raw = input(f"{prompt}{suffix}: ")
        value = raw if raw != "" else (default or "")
        if validator:
            ok, msg = validator(value)
            if not ok:
                print(msg)
                continue
        return value


def validate_int(nonempty: bool = False):
    def _v(s: str):
        if s == "":
            return (not nonempty, "This value is required and should be an integer.") if nonempty else (True, "")
        if re.fullmatch(r"[-+]?\d+", s):
            return True, ""
        return False, "Please enter a valid integer."
    return _v


def validate_nonempty():
    def _v(s: str):
        return (s != "", "This value is required.") if s == "" else (True, "")
    return _v


def build_defaults(existing: dict) -> dict:
    # Sensible defaults
    defaults = {
        # Bot core
        "ENV_BOT_MODE": existing.get("ENV_BOT_MODE", "dev"),
        "ENV_BOT_CONCURRENCY": existing.get("ENV_BOT_CONCURRENCY", "1"),
        "PORT": existing.get("PORT", "8080"),

        # DB
        "ENV_DB_HOST": existing.get("ENV_DB_HOST", "localhost"),
        "ENV_DB_PORT": existing.get("ENV_DB_PORT", "5432"),
        "ENV_DB_USER": existing.get("ENV_DB_USER", "postgres"),
        "ENV_DB_PASSWORD": existing.get("ENV_DB_PASSWORD", ""),
        "ENV_DB_DATABASE": existing.get("ENV_DB_DATABASE", "tgcm"),
        "ENV_DB_NAME": existing.get("ENV_DB_NAME", existing.get("ENV_DB_DATABASE", "tgcm")),

        # OpenAI
        "ENV_OPENAI_KEY": existing.get("ENV_OPENAI_KEY", ""),
        "ENV_OPENAI_EMBEDDING_MODEL": existing.get("ENV_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        "OPENAI_API_KEY": existing.get("OPENAI_API_KEY", existing.get("ENV_OPENAI_KEY", "")),
        "EMBEDDING_MODEL": existing.get("EMBEDDING_MODEL", existing.get("ENV_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")),
        "ENV_OPENAI_MODEL": existing.get("ENV_OPENAI_MODEL", "gpt-4o-mini"),

        # Telethon (main account)
        "TELETHON1_API_ID": existing.get("TELETHON1_API_ID", ""),
        "TELETHON1_API_HASH": existing.get("TELETHON1_API_HASH", ""),
        "TELETHON1_PHONE_NUMBER": existing.get("TELETHON1_PHONE_NUMBER", ""),
        "TELETHON1_SESSION": existing.get("TELETHON1_SESSION", ""),
        "TELETHON1_SESSION_STRING": existing.get("TELETHON1_SESSION_STRING", ""),
        "TELETHON2_SESSION": existing.get("TELETHON2_SESSION", ""),

        # CAS listener
        "CAS_TELETHON_API_ID": existing.get("CAS_TELETHON_API_ID", ""),
        "CAS_TELETHON_API_HASH": existing.get("CAS_TELETHON_API_HASH", ""),
        "CAS_TELETHON_SESSION_STRING": existing.get("CAS_TELETHON_SESSION_STRING", ""),
        "CAS_FEED_CHANNEL": existing.get("CAS_FEED_CHANNEL", "cas_feed"),

        # Logging
        "LOGGING_FORMAT": existing.get("LOGGING_FORMAT", "%(asctime)s - %(levelname)s - %(message)s"),
        "LOGGING_CONSOLE_ENABLED": existing.get("LOGGING_CONSOLE_ENABLED", "true"),
        "LOGGING_TELEGRAM_1_ENABLED": existing.get("LOGGING_TELEGRAM_1_ENABLED", "false"),
        "LOGGING_TELEGRAM_1_CHAT_ID": existing.get("LOGGING_TELEGRAM_1_CHAT_ID", ""),
        "LOGGING_TELEGRAM_2_ENABLED": existing.get("LOGGING_TELEGRAM_2_ENABLED", "false"),
        "LOGGING_TELEGRAM_2_CHAT_ID": existing.get("LOGGING_TELEGRAM_2_CHAT_ID", ""),
        "LOGGING_SENTRY_ENABLED": existing.get("LOGGING_SENTRY_ENABLED", "false"),
        "LOGGING_SENTRY_DSN": existing.get("LOGGING_SENTRY_DSN", existing.get("SENTRY_DSN", "")),

        # Sentry
        "SENTRY_DSN": existing.get("SENTRY_DSN", existing.get("LOGGING_SENTRY_DSN", "")),

        # Misc
        "ENV_BOT_KEY": existing.get("ENV_BOT_KEY", ""),
        "ENV_BOT_ADMIN_ID": existing.get("ENV_BOT_ADMIN_ID", ""),
        "ENV_INFO_CHAT_ID": existing.get("ENV_INFO_CHAT_ID", ""),
        "ENV_ERROR_CHAT_ID": existing.get("ENV_ERROR_CHAT_ID", ""),
        "BRIGHTDATA_PROXY": existing.get("BRIGHTDATA_PROXY", ""),

        # Heroku
        "HEROKU_APP_NAME": existing.get("HEROKU_APP_NAME", ""),
        "HEROKU_API_KEY": existing.get("HEROKU_API_KEY", ""),
    }
    return defaults


def collect_values(existing: dict) -> dict:
    d = build_defaults(existing)

    print("\n=== tg_community_manager .env setup ===")
    print(f"Target file: {ENV_PATH}")

    values: Dict[str, str] = {}

    # Core bot
    print("\n--- Core Bot ---")
    values["ENV_BOT_MODE"] = prompt_value("ENV_BOT_MODE", "Bot mode (dev/prod)", d["ENV_BOT_MODE"], validator=validate_nonempty())
    values["ENV_BOT_KEY"] = prompt_value("ENV_BOT_KEY", "Telegram Bot token", d["ENV_BOT_KEY"], secret=True, validator=validate_nonempty())
    values["ENV_BOT_ADMIN_ID"] = prompt_value("ENV_BOT_ADMIN_ID", "Bot admin user id", d["ENV_BOT_ADMIN_ID"], validator=validate_int(nonempty=True))
    values["ENV_INFO_CHAT_ID"] = prompt_value("ENV_INFO_CHAT_ID", "Info chat id", d["ENV_INFO_CHAT_ID"], validator=validate_int(nonempty=True))
    values["ENV_ERROR_CHAT_ID"] = prompt_value("ENV_ERROR_CHAT_ID", "Error chat id (optional)", d["ENV_ERROR_CHAT_ID"], validator=validate_int(nonempty=False))
    values["ENV_BOT_CONCURRENCY"] = prompt_value("ENV_BOT_CONCURRENCY", "Bot concurrency (workers)", d["ENV_BOT_CONCURRENCY"], validator=validate_int(nonempty=True))
    values["PORT"] = prompt_value("PORT", "HTTP port", d["PORT"], validator=validate_int(nonempty=True))

    # Database
    print("\n--- Database ---")
    values["ENV_DB_HOST"] = prompt_value("ENV_DB_HOST", "DB host", d["ENV_DB_HOST"], validator=validate_nonempty())
    values["ENV_DB_PORT"] = prompt_value("ENV_DB_PORT", "DB port", d["ENV_DB_PORT"], validator=validate_int(nonempty=True))
    values["ENV_DB_USER"] = prompt_value("ENV_DB_USER", "DB user", d["ENV_DB_USER"], validator=validate_nonempty())
    values["ENV_DB_PASSWORD"] = prompt_value("ENV_DB_PASSWORD", "DB password", d["ENV_DB_PASSWORD"], secret=True, validator=validate_nonempty())
    values["ENV_DB_DATABASE"] = prompt_value("ENV_DB_DATABASE", "DB name (ENV_DB_DATABASE)", d["ENV_DB_DATABASE"], validator=validate_nonempty())
    # Maintain both ENV_DB_DATABASE and ENV_DB_NAME for components expecting either
    values["ENV_DB_NAME"] = prompt_value("ENV_DB_NAME", "DB name (ENV_DB_NAME)", d["ENV_DB_NAME"], validator=validate_nonempty())

    # OpenAI
    print("\n--- OpenAI ---")
    values["ENV_OPENAI_KEY"] = prompt_value("ENV_OPENAI_KEY", "OpenAI API key", d["ENV_OPENAI_KEY"], secret=True)
    values["ENV_OPENAI_EMBEDDING_MODEL"] = prompt_value(
        "ENV_OPENAI_EMBEDDING_MODEL", "OpenAI embedding model", d["ENV_OPENAI_EMBEDDING_MODEL"])
    values["ENV_OPENAI_MODEL"] = prompt_value("ENV_OPENAI_MODEL", "OpenAI chat model", d["ENV_OPENAI_MODEL"])
    # Keep OPENAI_API_KEY and EMBEDDING_MODEL in sync if unset
    values["OPENAI_API_KEY"] = prompt_value("OPENAI_API_KEY", "OPENAI_API_KEY (leave blank to mirror ENV_OPENAI_KEY)", d["OPENAI_API_KEY"], secret=True)
    if not values["OPENAI_API_KEY"]:
        values["OPENAI_API_KEY"] = values["ENV_OPENAI_KEY"]
    values["EMBEDDING_MODEL"] = prompt_value("EMBEDDING_MODEL", "EMBEDDING_MODEL (leave blank to mirror ENV_OPENAI_EMBEDDING_MODEL)", d["EMBEDDING_MODEL"]) or values["ENV_OPENAI_EMBEDDING_MODEL"]

    # Telethon (main)
    print("\n--- Telethon (main account) ---")
    values["TELETHON1_API_ID"] = prompt_value("TELETHON1_API_ID", "Telethon API ID", d["TELETHON1_API_ID"], validator=validate_int(nonempty=True))
    values["TELETHON1_API_HASH"] = prompt_value("TELETHON1_API_HASH", "Telethon API hash", d["TELETHON1_API_HASH"], secret=True, validator=validate_nonempty())
    values["TELETHON1_PHONE_NUMBER"] = prompt_value("TELETHON1_PHONE_NUMBER", "Phone number (with +)", d["TELETHON1_PHONE_NUMBER"], validator=validate_nonempty())
    values["TELETHON1_SESSION_STRING"] = prompt_value("TELETHON1_SESSION_STRING", "Telethon session string (optional)", d["TELETHON1_SESSION_STRING"], secret=True)
    values["TELETHON1_SESSION"] = prompt_value("TELETHON1_SESSION", "Telethon session (tests) (optional)", d["TELETHON1_SESSION"], secret=True)
    values["TELETHON2_SESSION"] = prompt_value("TELETHON2_SESSION", "Telethon second session (tests) (optional)", d["TELETHON2_SESSION"], secret=True)

    # CAS feed listener (optional)
    if yes_no("Configure CAS feed listener variables?", default=False):
        print("\n--- CAS Listener ---")
        values["CAS_TELETHON_API_ID"] = prompt_value("CAS_TELETHON_API_ID", "CAS Telethon API ID", d["CAS_TELETHON_API_ID"], validator=validate_int(nonempty=True))
        values["CAS_TELETHON_API_HASH"] = prompt_value("CAS_TELETHON_API_HASH", "CAS Telethon API hash", d["CAS_TELETHON_API_HASH"], secret=True, validator=validate_nonempty())
        values["CAS_TELETHON_SESSION_STRING"] = prompt_value("CAS_TELETHON_SESSION_STRING", "CAS Telethon session string", d["CAS_TELETHON_SESSION_STRING"], secret=True, validator=validate_nonempty())
        values["CAS_FEED_CHANNEL"] = prompt_value("CAS_FEED_CHANNEL", "CAS feed channel username", d["CAS_FEED_CHANNEL"], validator=validate_nonempty())
    else:
        for k in ["CAS_TELETHON_API_ID", "CAS_TELETHON_API_HASH", "CAS_TELETHON_SESSION_STRING", "CAS_FEED_CHANNEL"]:
            # Preserve existing if present
            values[k] = existing.get(k, d.get(k, ""))

    # Logging (optional)
    if yes_no("Configure logging options?", default=True):
        print("\n--- Logging ---")
        values["LOGGING_FORMAT"] = prompt_value("LOGGING_FORMAT", "Logging format", d["LOGGING_FORMAT"])  # Allow spaces
        values["LOGGING_CONSOLE_ENABLED"] = ("true" if yes_no("Console logging enabled?", default=d["LOGGING_CONSOLE_ENABLED"].lower()=="true") else "false")
        values["LOGGING_TELEGRAM_1_ENABLED"] = ("true" if yes_no("Telegram logger #1 enabled?", default=d["LOGGING_TELEGRAM_1_ENABLED"].lower()=="true") else "false")
        values["LOGGING_TELEGRAM_1_CHAT_ID"] = prompt_value("LOGGING_TELEGRAM_1_CHAT_ID", "Logger #1 chat id (optional)", d["LOGGING_TELEGRAM_1_CHAT_ID"], validator=validate_int(nonempty=False))
        values["LOGGING_TELEGRAM_2_ENABLED"] = ("true" if yes_no("Telegram logger #2 enabled?", default=d["LOGGING_TELEGRAM_2_ENABLED"].lower()=="true") else "false")
        values["LOGGING_TELEGRAM_2_CHAT_ID"] = prompt_value("LOGGING_TELEGRAM_2_CHAT_ID", "Logger #2 chat id (optional)", d["LOGGING_TELEGRAM_2_CHAT_ID"], validator=validate_int(nonempty=False))
        values["LOGGING_SENTRY_ENABLED"] = ("true" if yes_no("Logging to Sentry enabled?", default=d["LOGGING_SENTRY_ENABLED"].lower()=="true") else "false")
        values["LOGGING_SENTRY_DSN"] = prompt_value("LOGGING_SENTRY_DSN", "Logging Sentry DSN (optional)", d["LOGGING_SENTRY_DSN"], secret=True)
    else:
        for k in [
            "LOGGING_FORMAT", "LOGGING_CONSOLE_ENABLED",
            "LOGGING_TELEGRAM_1_ENABLED", "LOGGING_TELEGRAM_1_CHAT_ID",
            "LOGGING_TELEGRAM_2_ENABLED", "LOGGING_TELEGRAM_2_CHAT_ID",
            "LOGGING_SENTRY_ENABLED", "LOGGING_SENTRY_DSN",
        ]:
            values[k] = existing.get(k, d.get(k, ""))

    # Sentry (top-level)
    if yes_no("Configure Sentry SDK DSN?", default=False):
        print("\n--- Sentry ---")
        values["SENTRY_DSN"] = prompt_value("SENTRY_DSN", "Sentry DSN", d["SENTRY_DSN"], secret=True)
        # If LOGGING_SENTRY_DSN empty, mirror it
        if not values.get("LOGGING_SENTRY_DSN"):
            values["LOGGING_SENTRY_DSN"] = values["SENTRY_DSN"]
    else:
        values["SENTRY_DSN"] = existing.get("SENTRY_DSN", d.get("SENTRY_DSN", ""))

    # Misc
    if yes_no("Configure optional proxy and Heroku settings?", default=False):
        print("\n--- Misc ---")
        values["BRIGHTDATA_PROXY"] = prompt_value("BRIGHTDATA_PROXY", "BrightData proxy (user:pass@host:port)", d["BRIGHTDATA_PROXY"], secret=True)
        values["HEROKU_APP_NAME"] = prompt_value("HEROKU_APP_NAME", "Heroku app name (optional)", d["HEROKU_APP_NAME"]) 
        values["HEROKU_API_KEY"] = prompt_value("HEROKU_API_KEY", "Heroku API key (optional)", d["HEROKU_API_KEY"], secret=True)
    else:
        for k in ["BRIGHTDATA_PROXY", "HEROKU_APP_NAME", "HEROKU_API_KEY"]:
            values[k] = existing.get(k, d.get(k, ""))

    return values


def write_env_file(path: Path, values: dict):
    # Compose with sections as comments
    groups = [
        ("Core Bot", [
            "ENV_BOT_MODE", "ENV_BOT_KEY", "ENV_BOT_ADMIN_ID", "ENV_INFO_CHAT_ID", "ENV_ERROR_CHAT_ID", "ENV_BOT_CONCURRENCY", "PORT"
        ]),
        ("Database", [
            "ENV_DB_HOST", "ENV_DB_PORT", "ENV_DB_USER", "ENV_DB_PASSWORD", "ENV_DB_DATABASE", "ENV_DB_NAME"
        ]),
        ("OpenAI", [
            "ENV_OPENAI_KEY", "ENV_OPENAI_MODEL", "ENV_OPENAI_EMBEDDING_MODEL", "OPENAI_API_KEY", "EMBEDDING_MODEL"
        ]),
        ("Telethon Main", [
            "TELETHON1_API_ID", "TELETHON1_API_HASH", "TELETHON1_PHONE_NUMBER", "TELETHON1_SESSION_STRING", "TELETHON1_SESSION", "TELETHON2_SESSION"
        ]),
        ("CAS Listener", [
            "CAS_TELETHON_API_ID", "CAS_TELETHON_API_HASH", "CAS_TELETHON_SESSION_STRING", "CAS_FEED_CHANNEL"
        ]),
        ("Logging", [
            "LOGGING_FORMAT", "LOGGING_CONSOLE_ENABLED", "LOGGING_TELEGRAM_1_ENABLED", "LOGGING_TELEGRAM_1_CHAT_ID",
            "LOGGING_TELEGRAM_2_ENABLED", "LOGGING_TELEGRAM_2_CHAT_ID", "LOGGING_SENTRY_ENABLED", "LOGGING_SENTRY_DSN"
        ]),
        ("Sentry", ["SENTRY_DSN"]),
        ("Misc", ["BRIGHTDATA_PROXY", "HEROKU_APP_NAME", "HEROKU_API_KEY"]),
    ]

    lines = []
    lines.append(f"# Generated by setenv.py at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    for title, keys in groups:
        # Only write section if any key present (including empty) from values
        present = [k for k in keys if k in values]
        if not present:
            continue
        lines.append(f"# --- {title} ---")
        section_env = {k: (values.get(k, "") or "") for k in present}
        lines.append(serialize_env(section_env).rstrip("\n"))
        lines.append("")
    # Append any leftover keys not in groups
    leftover = {k: v for k, v in values.items() if k not in {kk for _, keys in groups for kk in keys}}
    if leftover:
        lines.append("# --- Other ---")
        lines.append(serialize_env(leftover).rstrip("\n"))
        lines.append("")

    data = "\n".join(lines)
    path.write_text(data, encoding="utf-8")


def main():
    existing = read_env(ENV_PATH)

    print(f"This wizard will create/update: {ENV_PATH}")
    if ENV_PATH.exists():
        print("An existing .env was found.")
        if not yes_no("Do you want to continue and overwrite it?", default=True):
            print("Aborted.")
            return
        # Backup
        backup = ENV_PATH.with_suffix(".env.bak")
        # Avoid clobbering if multiple runs; add timestamp
        backup = ENV_PATH.parent / f".env.bak.{int(time.time())}"
        ENV_PATH.replace(backup)
        print(f"Backed up existing file to: {backup}")

    values = collect_values(existing)

    # Summary (mask secrets)
    print("\nSummary of values to write:")
    secret_like = re.compile(r"(KEY|TOKEN|PASSWORD|SECRET|HASH|DSN|API|SESSION|PROXY)", re.IGNORECASE)
    for k, v in values.items():
        display = "***" if (v and secret_like.search(k)) else v
        print(f"  {k} = {display}")

    if not yes_no("Write these values to config/.env?", default=True):
        print("Aborted.")
        return

    write_env_file(ENV_PATH, values)
    print(f"\nWrote {ENV_PATH}")
    print("To load into your shell: source config/setenv.sh")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted by user.")
        sys.exit(1)
