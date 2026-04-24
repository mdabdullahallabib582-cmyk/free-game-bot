import requests
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8677083783:AAE5uIQ_7y_DMuwACksjYgTleTa1UO-z6S0"

# ---------------- DATABASE ----------------
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# Users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    chat_id INTEGER PRIMARY KEY
)
""")

# Sent games table
cursor.execute("""
CREATE TABLE IF NOT EXISTS sent_games (
    game_id INTEGER PRIMARY KEY
)
""")

conn.commit()

# ---------------- USER FUNCTIONS ----------------
def add_user(chat_id):
    cursor.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
    conn.commit()

def get_users():
    cursor.execute("SELECT chat_id FROM users")
    return [row[0] for row in cursor.fetchall()]

# ---------------- GAME FUNCTIONS ----------------
def is_game_sent(game_id):
    cursor.execute("SELECT 1 FROM sent_games WHERE game_id = ?", (game_id,))
    return cursor.fetchone() is not None

def save_sent_game(game_id):
    cursor.execute("INSERT OR IGNORE INTO sent_games (game_id) VALUES (?)", (game_id,))
    conn.commit()

def get_free_games():
    url = "https://www.gamerpower.com/api/giveaways"
    res = requests.get(url).json()
    return [game for game in res if game["type"] == "Game"]

# ---------------- BOT ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_user(chat_id)
    await update.message.reply_text("✅ তুমি এখন Free Game Alert সাবস্ক্রাইব করেছো!")

async def check_games(app):
    games = get_free_games()
    users = get_users()

    for game in games:
        game_id = game["id"]

        if not is_game_sent(game_id):
            msg = f"🎮 {game['title']}\n\n{game['description']}\n\n👉 {game['open_giveaway_url']}"

            for user in users:
                try:
                    await app.bot.send_message(chat_id=user, text=msg)
                except:
                    pass

            save_sent_game(game_id)

async def job(context: ContextTypes.DEFAULT_TYPE):
    await check_games(context.application)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.job_queue.run_repeating(job, interval=3600, first=10)

app.run_polling()