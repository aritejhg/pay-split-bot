import argparse
import errno
import logging

import os
import time

import img_preprocess
import postprocess
import cv2

import config
import pytesseract
import telegram
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          filters, MessageHandler, PollHandler, PollAnswerHandler, Updater)
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
from utils import get_bot_token
from receipt_split import ReceiptSplit

from receipt_split import ReceiptSplit

from collections import deque


try:
	import Image
except ImportError:
	from PIL import Image

group_photos = {}
picQueue = deque([1,2,3])



def resolve_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('-v', '--verbose', action='store_true')
	args = parser.parse_args()

	if args.verbose:
		logging.basicConfig(level=logging.DEBUG,
							format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

try:
	import Image
except ImportError:
	from PIL import Image

group_photos = {}

def resolve_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('-v', '--verbose', action='store_true')
	args = parser.parse_args()

	if args.verbose:
		logging.basicConfig(level=logging.DEBUG,
							format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

POLL_OPEN_TIME = 5 # 24 hours
REMINDER_DELAY = 120 # 2 min
REMINDER_INTERVAL = 300 # 5 min

# POLL_OPEN_TIME = 24 * 60 * 60 # 24 hours
# REMINDER_DELAY = 120 # 2 min
# REMINDER_INTERVAL = 300 # 5 min

async def send_split(update: Update, context: ContextTypes.DEFAULT_TYPE, orderItems):
    message = update.message
    # poll_name = message.text.split(" ")[1]
    poll_name = "Bill Split"

    # Send poll
    items = [item[0] for item in orderItems if item[1] != 0]

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
    if context.job_queue:
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

    logging.info("Finalizing")

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
    logging.info("Finalizing", poll_id)

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

help_text = """
Send me an image and I will run Google's Tesseract OCR tool on it \
and send you back the results.

In groups, I will not automatically parse the images, \
I will wait for someoneto use the /splitpayments command, \
then I'll parse the last image sent.
"""

async def start(update, context):
	await context.bot.send_message(chat_id=update.message.chat_id,
		text="Hello! I'm Pay-Splits-Bot!\n\n"+help_text,
		disable_web_page_preview=True)

async def help(update, context):
	await context.bot.send_message(chat_id=update.message.chat_id,
		text=help_text,
		disable_web_page_preview=True)

async def unknown(update, context):
	await context.bot.send_message(chat_id=update.message.chat_id,
		text="Sorry, I didn't understand that command :(")

async def message(update, context):
    #nonlocal group_photos

    if not update.message.photo:
        return

    photosize = await context.bot.get_file(update.message.photo.file_id)


    group_photos[update.message.chat_id] = photosize



async def split_payments(update, context):
    print("group photos", group_photos)

    await _photosize_to_parsed(update, context, group_photos.get(update.message.chat_id))


async def _photosize_to_parsed(update, context, photosize):
	# try:
    #filename = config.CACHE_DIR+'/photo_'+''.join(str(time.time()).split('.'))+'.jpg'
    #print(photosize)

    picIndex = picQueue.popleft()

    filename = config.CACHE_DIR+ str(picIndex) + '.jpg'

    await context.bot.send_message(chat_id=update.message.chat_id, text="file received. processing now.")

    #photosize.download(filename)

    out_img = img_preprocess.preprocess_img(cv2.imread(filename))
    image_text = pytesseract.image_to_string(out_img)
    items, taxes, total = postprocess.openai_call(image_text)

    #print(items)
    await send_split(update, context, items)


    if config.CACHE_TEMP:
        os.remove(filename)

    sanitized_string = _sanitize_string(image_text)

    if sanitized_string:
        response_msg = sanitized_string
    else:
        response_msg = 'Nothing found'

    #await context.bot.send_message(chat_id=update.message.chat_id, text=response_msg)


async def _something_wrong(update, context, e):

    await context.bot.send_message(chat_id=update.message.chat_id,
		text="Sorry, something went wrong. Please try again. ")


def _sanitize_string(string):
	illegal_chars = '_*`[]()\\'

	sanitized = ''

	for char in string:
		sanitized += '\\' + char if char in illegal_chars else char

	return sanitized


# async def uploadReceipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     message = update.message.text

#     # uploaded_receipt = await context.bot.send_document(chat_id=update.effective_chat.id, document='tests/test.png')


if __name__ == "__main__":
    os.chdir(os.path.split(os.path.abspath(__file__))[0])

    try:
        os.mkdir(config.CACHE_DIR)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e

    bot_token = '5815060511:AAEk25nNBcnHc-utraWJigxQzDEkFQwv4jc'
    app = ApplicationBuilder().token(bot_token).build()

    start_handler = CommandHandler('start', start)
    #poll_handler = CommandHandler('poll', poll)
    upload_handler = CommandHandler('splitpayments', split_payments)
    help_handler = CommandHandler('help', help)
    split_handler = CommandHandler('split', send_split)
    poll_answer_handler = PollAnswerHandler(poll_answer)
    finalize_handler = CommandHandler('final', finalize_split)
    app.add_handlers([start_handler, split_handler, poll_answer_handler,upload_handler, finalize_handler, message_handler])

    app.run_polling()