import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

from utils import get_bot_token

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome to Pay-Split-Bot!"
    )

async def poll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text

    sent_poll = await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=message,
        options=["Apple", "Orange", "Banana"],
        is_anonymous= False,
        allows_multiple_answers=True,
    )

if __name__ == "__main__":
    bot_token = get_bot_token()
    app = ApplicationBuilder().token(bot_token).build()

    start_handler = CommandHandler('start', start)
    poll_handler = CommandHandler('poll', poll)
    app.add_handlers([start_handler, poll_handler])

    app.run_polling()