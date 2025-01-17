from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, JobQueue
import requests
import sqlite3
from datetime import time, datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API URL
BASE_URL = "https://api.ssv.network/api/v4/mainnet/operators/"

# Database setup
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS users (chat_id INTEGER PRIMARY KEY, operator_id TEXT, time_to_send TEXT)"
    )
    conn.commit()
    conn.close()

# Start command handler
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Welcome! Please set your operator ID using the /set_operator command. For example: /set_operator 634\n"
        "You can also set a custom notification time using /set_time HH:MM"
    )

# Set operator command handler
def set_operator(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1 or not context.args[0].isdigit():
        update.message.reply_text("Invalid ID. Please provide a valid numeric operator ID. Example: /set_operator 634")
        return

    operator_id = context.args[0]
    chat_id = update.message.chat_id

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO users (chat_id, operator_id, time_to_send) VALUES (?, ?, ?)",
        (chat_id, operator_id, "12:00"),
    )
    conn.commit()
    conn.close()

    update.message.reply_text(f"Operator ID set to {operator_id}. Use /get_data to fetch operator details.")

# Set notification time command handler
def set_time(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1:
        update.message.reply_text("Please provide a time in HH:MM format. Example: /set_time 14:30")
        return

    try:
        notification_time = datetime.strptime(context.args[0], "%H:%M").time()
    except ValueError:
        update.message.reply_text("Invalid time format. Please use HH:MM format. Example: /set_time 14:30")
        return

    chat_id = update.message.chat_id

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET time_to_send = ? WHERE chat_id = ?",
        (notification_time.strftime("%H:%M"), chat_id),
    )
    conn.commit()
    conn.close()

    update.message.reply_text(f"Notification time set to {notification_time.strftime('%H:%M')}.")

# Get operator data command handler
def get_data(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT operator_id FROM users WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        update.message.reply_text("Operator ID is not set. Use /set_operator to set an ID.")
        return

    operator_id = row[0]

    try:
        response = requests.get(BASE_URL + operator_id)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') != "Active":
                update.message.reply_text(f"Error: Operator status is '{data.get('status')}'.")
                return

            if data['performance']['24h'] < 98:
                update.message.reply_text(f"Warning: Operator performance is below 98%. Current: {data['performance']['24h']}%.")

            message = (
                f"Operator Name: {data.get('name')}\n"
                f"Status: {data.get('status')}\n"
                f"Location: {data.get('location')}\n"
                f"Setup Provider: {data.get('setup_provider')}\n"
                f"Performance (24h): {data['performance']['24h']}%\n"
                f"Validators Count: {data['validators_count']}\n"
                f"Website: {data.get('website_url')}\n"
                f"Description: {data.get('description')}"
            )
            update.message.reply_text(message)
        else:
            update.message.reply_text("Failed to fetch data. Please check the operator ID and try again.")
    except Exception as e:
        update.message.reply_text(f"An error occurred: {str(e)}")

# Job to send daily updates
def daily_update(context: CallbackContext) -> None:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, operator_id, time_to_send FROM users")
    rows = cursor.fetchall()
    conn.close()

    current_time = datetime.now().strftime("%H:%M")

    for chat_id, operator_id, time_to_send in rows:
        if time_to_send != current_time:
            continue

        try:
            response = requests.get(BASE_URL + operator_id)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') != "Active":
                    context.bot.send_message(chat_id=chat_id, text=f"Error: Operator status is '{data.get('status')}'.")
                    continue

                if data['performance']['24h'] < 98:
                    context.bot.send_message(chat_id=chat_id, text=f"Warning: Operator performance is below 98%. Current: {data['performance']['24h']}%.")

                message = (
                    f"Daily Update:\n"
                    f"Operator Name: {data.get('name')}\n"
                    f"Status: {data.get('status')}\n"
                    f"Location: {data.get('location')}\n"
                    f"Performance (24h): {data['performance']['24h']}%\n"
                    f"Validators Count: {data['validators_count']}\n"
                )
                context.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            context.bot.send_message(chat_id=chat_id, text=f"An error occurred: {str(e)}")

# Main function to start the bot
def main():
    # Load the Telegram bot token from environment variables
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Telegram bot token is missing in .env file.")

    updater = Updater(token)

    # Initialize the database
    init_db()

    dispatcher = updater.dispatcher

    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("set_operator", set_operator))
    dispatcher.add_handler(CommandHandler("set_time", set_time))
    dispatcher.add_handler(CommandHandler("get_data", get_data))

    # Schedule daily updates
    job_queue = updater.job_queue
    job_queue.run_repeating(daily_update, interval=60, first=0)

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
