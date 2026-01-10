# tg-community-manager

The tg-community-manager is a robust Python bot that helps maintain and moderate a supergroup chat on Telegram. It is built using the python-telegram-bot library and offers functionalities such as member handling, user status updates, thank you message handling, report handling, chat join requests, and a robust spam checking mechanism.

This bot employs a PostgreSQL database for persistent data storage and SQLAlchemy ORM for database operations. The **db_helper.py** file contains all the database-related operations including SQLAlchemy ORM model definitions, database connection establishment, session handling, and more.

## Features

- **New Member Management**: Deletes new member messages to keep the chat clean and uncluttered.
- **User Status Updates**: Monitors all chat messages and member additions in the supergroup and updates the user status accordingly.
- **Thank You Message Handling**: Checks if a user sends a thank you message in the chat.
- **Report Handling**: Processes member reports of messages using the /report command.
- **Chat Join Requests**: Handles new chat join requests and processes them accordingly.
- **Ban Commands**: Supports /ban, /global_ban, and /gban commands in the supergroup to ban offending users.
- **Spam Checking**: Checks each text and document message for spam and takes appropriate action if spam is detected.

## Database Model

The bot uses several database tables to handle its operations:
 - Chat: Stores the chat configurations and details.
 - Qna: Holds data for question and answer pairs.
 - User: Keeps track of user data, such as first and last names, whether they are a bot, and whether they are anonymous.
 - User_Status: Keeps track of the status of users in various chats, their ratings, and the time of their last message.
 - User_Global_Ban: Contains information about global bans applied to users.
 - Report: Stores report details of users reporting other users' messages.

## Usage
To run the tg-community-manager bot, make sure you have Python 3 and pip installed on your system. Then, install the required dependencies using pip:
    
    pip install -r requirements.txt

Then, you can run the bot with the following command:

    python3 main.py

Remember to replace 'BOT_KEY' in the config dictionary with your actual bot token obtained from BotFather on Telegram.

## Environment Setup (.env)
- `config/setenv.py`: Interactive wizard that creates or updates `config/.env` with all required variables (Telegram, database, OpenAI, logging, etc.).
  - Run: `python3 config/setenv.py`
  - To load the resulting environment into your current shell: `source config/setenv.sh`

The `.env` file is used by both local runs and Docker Compose. You can rerun the wizard any time; it backs up an existing `.env`.

## Docker Compose
- `docker-compose.yml`: Local development stack with:
  - `db` (PostgreSQL with pgvector)
  - `bot` (main Telegram bot)
  - `cas_feed_listener` (optional CAS feed listener)
- `docker-compose-utils.sh`: Helper entrypoint used by the `bot` and `cas_feed_listener` services to install deps, run migrations, and start the processes.

Common commands:
- Start everything (requires `config/.env`): `docker compose up -d --build`
- Start only DB: `docker compose up -d db`
- Follow logs: `docker compose logs -f`
- Stop and remove: `docker compose down`

Note: The Compose services read variables from `config/.env`. Inside containers the app connects to the DB host `db` (set via `ENV_DB_HOST`).

## Justfile (task runner)
- `Justfile`: Convenience commands for common workflows. Examples:
  - `just env-setup` – run the interactive `.env` wizard
  - `just run` – run the bot locally (`src/dispatcher.py`) using your current environment
  - `just migrate` – apply alembic migrations (loads vars from `config/.env`)
  - `just dc-up` / `just dc-up-bot` / `just dc-up-db` – start services via Docker Compose
  - `just dc-logs` / `just dc-down` / `just dc-ps` – inspect or stop Compose services
  - `just psql` – open a psql shell into the Compose DB service

List all recipes with `just --list`. If you need the environment in your current shell, you can use `source config/setenv.sh` before invoking local commands.

## Contributing
Contributions, issues, and feature requests are welcome. Feel free to check the [issues page](https://github.com/rvnikita/tg_community_manager/issues) if you want to contribute.

For major changes, please open an issue first to discuss what you would like to change. Please make sure to update tests as appropriate.

## License
This project is licensed under the terms of the Apache License 2.0.
