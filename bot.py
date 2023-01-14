import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, PollHandler, PollAnswerHandler
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

from utils import get_bot_token
from receipt_split import ReceiptSplit

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

POLL_OPEN_TIME = 24 * 60 * 60 # 24 hours
REMINDER_DELAY = 120 # 2 min
REMINDER_INTERVAL = 300 # 5 min

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome to Pay-Split-Bot!"
    )

async def send_split(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    poll_name = message.text.split(" ")[1]

    # Send poll
    items = ["Apple", "Orange", "Banana"] # TODO: Replace

    chat_id = update.effective_chat.id
    sent_poll = await context.bot.send_poll(
        chat_id=chat_id,
        question=poll_name,
        options=items,
        is_anonymous= False,
        allows_multiple_answers=True,
        open_period=POLL_OPEN_TIME,
    )

    # Add to polls DB
    if "polls" not in context.bot_data:
        logging.debug("Starting polls in this chat")
        context.bot_data["polls"] = {}

    chat_polls = context.bot_data.get("polls")
    split_obj = ReceiptSplit(
        chat_id=chat_id,
        message_id=sent_poll.message_id,
        items=items
    )
    chat_polls[sent_poll.poll.id] = split_obj

    # Schedule reminder
    reminder_job = context.job_queue.run_repeating(split_reminder, interval=REMINDER_INTERVAL, first=REMINDER_DELAY, data={"poll_message_id": sent_poll.message_id, "split_obj": split_obj}, chat_id=chat_id)
    split_obj.reminder_job = reminder_job

    logging.debug(chat_polls)
    logging.info(f"Created poll {sent_poll.poll.id}")

async def split_reminder(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    split_obj = data.get("split_obj")

    if split_obj.closed == True:
        return

    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=f'Receipt Split is still open!',
        reply_to_message_id=data.get("poll_message_id")
    )

async def poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    poll_ans = update.poll_answer
    poll_id = poll_ans.poll_id
    user_name = poll_ans.user.username

    chat_polls = context.bot_data.get("polls")
    split_obj = chat_polls.get(poll_id)
    split_obj.update_response(user_name, poll_ans.option_ids)

    logging.debug(poll_ans)
    logging.info(split_obj)

async def finalize_split(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    past_message = message.reply_to_message
    past_id = past_message.message_id

    poll = past_message.poll
    if poll is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please reply to a poll"
        )
        return

    poll_id = poll.id
    chat_polls = context.bot_data.get("polls", {})
    if poll_id not in chat_polls:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please reply to a Receipt Split"
        )
        return

    split_obj = chat_polls[poll_id]

    # Stop poll
    await context.bot.stop_poll(
        chat_id=split_obj.chat_id,
        message_id=split_obj.message_id
    )

    # Send summary
    summary = split_obj.get_summary()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=escape_markdown(summary, version=2),
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_to_message_id=past_id
    )


if __name__ == "__main__":
    bot_token = get_bot_token()
    app = ApplicationBuilder().token(bot_token).build()

    start_handler = CommandHandler('start', start)
    split_handler = CommandHandler('split', send_split)
    poll_answer_handler = PollAnswerHandler(poll_answer)
    finalize_handler = CommandHandler('final', finalize_split)
    app.add_handlers([start_handler, split_handler, poll_answer_handler, finalize_handler])

    app.run_polling()