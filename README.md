# Telegram SSV Operator Bot

This bot provides real-time updates about SSV operators on the Ethereum network. Users can subscribe to updates for a specific operator and configure notification times.

## Features
- Set and store operator IDs for updates.
- Configure custom notification times.
- Receive daily updates with operator status and performance.
- Automatically alerts users if the operator is not active or performance drops below 98%.

# Usage:
Bot located here: https://t.me/ssv_operator_checker_bot

Commands:

`/start:` Display welcome message and instructions.

`/set_operator <ID>:` Set the operator ID to receive updates (e.g., /set_operator 634).

`/set_time <HH:MM>:` Set the daily notification time (e.g., /set_time 12:30).

`/get_data:` Retrieve the current status and performance of the operator.


# Developement:

## Prerequisites
- Docker and Docker Compose installed on your machine.
- Python dependencies listed in `requirements.txt`.

## Setup

### Environment Variables
Create a `.env` file in the project root and add the following:
```env
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

### Database
The bot uses SQLite to store user data (users.db). The database is automatically initialized when the bot starts.

### Build and run the bot:
```
docker-compose build
docker-compose up -d
```
