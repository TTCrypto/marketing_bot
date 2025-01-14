import logging
import os
import PyPDF2
from flask import Flask, request
import telegram
from config import TOKEN, CHANNEL_ID, CHANNEL_LINK, PDF_PATH, WEBHOOK_URL
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import json

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize bot
bot = telegram.Bot(token=TOKEN)

def verify_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            PyPDF2.PdfReader(file)
        return True
    except Exception as e:
        logging.error(f"PDF verification failed: {e}")
        return False

async def start(update: Update):
    keyboard = [
        [InlineKeyboardButton("Get", callback_data='get_networks')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await bot.send_message(
        chat_id=update.message.chat.id,
        text="Get top 10 free neural networks and instructions on how to work with them",
        reply_markup=reply_markup
    )

async def button_callback(update: Update):
    query = update.callback_query
    await query.answer()

    if query.data == 'get_networks':
        keyboard = [
            [InlineKeyboardButton("Subscribe", url=CHANNEL_LINK)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await bot.edit_message_text(
            chat_id=query.message.chat.id,
            message_id=query.message.message_id,
            text="Subscribe to the AX9 AI channel and get your free gift on neural networks",
            reply_markup=reply_markup
        )

async def check_subscription(update: Update):
    user_id = update.message.from_user.id
    
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            # Send PDF file
            with open(PDF_PATH, 'rb') as pdf:
                await bot.send_document(
                    chat_id=update.message.chat.id,
                    document=pdf,
                    caption="Here's your guide to neural networks!"
                )
            await bot.send_message(
                chat_id=update.message.chat.id,
                text="Stay on the AX9 channel to get free training and new information on neural networks in this bot for free!"
            )
        else:
            await bot.send_message(
                chat_id=update.message.chat.id,
                text="Please subscribe to the channel first!"
            )
    except Exception as e:
        logging.error(f"Error checking subscription: {e}")
        await bot.send_message(
            chat_id=update.message.chat.id,
            text="Please subscribe to the channel first!"
        )

@app.route('/' + TOKEN, methods=['POST'])
async def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(), bot)
        
        try:
            if update.message and update.message.text == '/start':
                await start(update)
            elif update.callback_query:
                await button_callback(update)
            elif update.message and update.message.text:
                await check_subscription(update)
                
        except Exception as e:
            logging.error(f"Error handling update: {e}")
            
    return 'OK'

@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
    s = bot.set_webhook(webhook_url)
    if s:
        return "Webhook setup successful"
    return "Webhook setup failed"

@app.route('/')
def index():
    return 'Bot is running'

if __name__ == '__main__':
    # Verify PDF exists and is valid
    if not verify_pdf(PDF_PATH):
        logging.error("PDF file is missing or invalid")
        exit(1)
        
    # Set webhook
    webhook_url = f"{WEBHOOK_URL}/{TOKEN}"
    bot.set_webhook(webhook_url)
    
    # Run Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)