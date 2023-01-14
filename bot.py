import argparse
import errno
import logging
import os
import time

import config
import pytesseract
import telegram
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          filters, MessageHandler, Updater)
from utils import get_bot_token

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

async def start2(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    # if not update.check_update():
    #     return
    # else:
    #     if not update.message.photo:
    #         return
    if not update.message.document:
        return

    photosize = await context.bot.get_file(update.message.document.file_id)
    #photosize = context.bot.getFile(update.message.photo[-1].file_id)
    # if update.message.chat_id > 0: # user	
    # 	_photosize_to_parsed(bot, update, photosize)

    # else: # group
    group_photos[update.message.chat_id] = photosize


async def split_payments(update, context):
	# if update.message.chat_id > 0:
	# 	bot.send_message(chat_id=update.message.chat_id, text='/splitpayments command is only available to groups.')
	# else:
	await _photosize_to_parsed(update, context, group_photos[update.message.chat_id])


async def _photosize_to_parsed(update, context, photosize):
	# try:
    #filename = config.CACHE_DIR+'/photo_'+''.join(str(time.time()).split('.'))+'.jpg'

    filename = config.CACHE_DIR+'/photo_16737215687738645.jpg'

    await context.bot.send_message(chat_id=update.message.chat_id, text="file received. processing now.")

    #photosize.download(filename)

    language = 'eng'

    image_text = pytesseract.image_to_string(Image.open(filename), language)

    if config.CACHE_TEMP:
        os.remove(filename)

    sanitized_string = _sanitize_string(image_text)

    if sanitized_string:
        response_msg = sanitized_string
    else:
        response_msg = 'Nothing found'
    
    await context.bot.send_message(chat_id=update.message.chat_id, text=response_msg)

		# bot.send_message(chat_id=update.message.chat_id,
		# 				text=response_msg,
		# 			parse_mode=telegram.ParseMode.MARKDOWN)

	# except Exception as e:
    #     _something_wrong(bot, update, e)

async def _something_wrong(update, context, e):

    await context.bot.send_message(chat_id=update.message.chat_id,
		text="Sorry, something went wrong. Please try again. ")


def _sanitize_string(string):
	illegal_chars = '_*`[]()\\'

	sanitized = ''

	for char in string:
		sanitized += '\\' + char if char in illegal_chars else char

	return sanitized

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
    poll_handler = CommandHandler('poll', poll)
    message_handler = MessageHandler(filters.ALL, message)
    upload_handler = CommandHandler('splitpayments', split_payments)
    help_handler = CommandHandler('help', help)
    app.add_handlers([start_handler, poll_handler, upload_handler, message_handler])
    
    app.run_polling()