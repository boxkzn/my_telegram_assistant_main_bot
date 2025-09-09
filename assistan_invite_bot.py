import logging
import csv
import re
from telegram import Update, Bot, ChatInviteLink
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackContext

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define states
APARTMENT, NAME, PHONE = range(3)

# File to save user data
USER_DATA_FILE = 'user_data.csv'

# Your group chat ID (replace with actual chat ID)
GROUP_CHAT_ID = 

# Ensure the CSV file has the correct headers
def ensure_csv_headers():
    try:
        with open(USER_DATA_FILE, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            if reader.fieldnames != ['apartment', 'name', 'phone']:
                raise ValueError("CSV file headers do not match expected headers")
    except (FileNotFoundError, ValueError):
        with open(USER_DATA_FILE, 'w', newline='') as csvfile:
            fieldnames = ['apartment', 'name', 'phone']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

# Function to check if apartment number exists in CSV
def apartment_exists(apartment_number: str) -> bool:
    try:
        with open(USER_DATA_FILE, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['apartment'] == apartment_number:
                    return True
    except FileNotFoundError:
        return False
    return False

# Validate phone number
def is_valid_phone(phone: str) -> bool:
    return re.match(r'^\+7\(\d{3}\)\d{3}-\d{2}-\d{2}$', phone) is not None

# Command handler for /start
async def start(update: Update, context: CallbackContext) -> int:
    if update.message.chat.type != 'private':
        return ConversationHandler.END
    
    await update.message.reply_text('Здравствуйте! Вас приветствует ассистент администратора группы "". Для вступления в группу Вам необходимо рассказать немного о себе. Пожалуйста, введите номер вашей квартиры:')
    return APARTMENT

# Handler to capture apartment number
async def apartment(update: Update, context: CallbackContext) -> int:
    if update.message.chat.type != 'private':
        return ConversationHandler.END

    user = update.message.from_user
    apartment_number = update.message.text

    if apartment_exists(apartment_number):
        await update.message.reply_text('Этот номер квартиры уже зарегистрирован.')
        logger.info("User %s tried to register an existing apartment number: %s", user.first_name, apartment_number)
        return ConversationHandler.END

    context.user_data['apartment'] = apartment_number
    logger.info("Apartment number of %s: %s", user.first_name, apartment_number)
    await update.message.reply_text('Спасибо! Теперь введите ваше имя:')
    return NAME

# Handler to capture user's name
async def name(update: Update, context: CallbackContext) -> int:
    if update.message.chat.type != 'private':
        return ConversationHandler.END

    user = update.message.from_user
    context.user_data['name'] = update.message.text
    logger.info("Name of %s: %s", user.first_name, update.message.text)
    await update.message.reply_text('Спасибо! Теперь введите ваш номер мобильного телефона:(пример: +7(XXX)XXX-XX-XX)')
    return PHONE

# Handler to capture phone number and save user data
async def phone(update: Update, context: CallbackContext) -> int:
    if update.message.chat.type != 'private':
        return ConversationHandler.END

    user = update.message.from_user
    phone_number = update.message.text

    if not is_valid_phone(phone_number):
        await update.message.reply_text('Неправильный формат номера телефона. Пожалуйста, введите номер в формате +7(XXX)XXX-XX-XX. Спасибо.')
        return PHONE

    context.user_data['phone'] = phone_number
    logger.info("Phone number of %s: %s", user.first_name, phone_number)
    
    # Save user data to CSV
    with open(USER_DATA_FILE, 'a', newline='') as csvfile:
        fieldnames = ['apartment', 'name', 'phone']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({'apartment': context.user_data['apartment'], 'name': context.user_data['name'], 'phone': context.user_data['phone']})
    
    # Create an invite link for the group
    bot: Bot = context.bot
    invite_link: ChatInviteLink = await bot.create_chat_invite_link(chat_id=GROUP_CHAT_ID)
    await update.message.reply_text(f'Спасибо! Теперь вы можете присоединиться к нам в группу. Вот ваша личная ссылка для вступления в группу: {invite_link.invite_link}')

    return ConversationHandler.END

# Command handler for /cancel
async def cancel(update: Update, context: CallbackContext) -> int:
    if update.message.chat.type != 'private':
        return ConversationHandler.END
    
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text('Операция отменена. Если хотите попробовать снова, введите /start.')
    return ConversationHandler.END

def main() -> None:
    # Ensure the CSV file has the correct headers
    ensure_csv_headers()

    # Replace 'YOUR_TOKEN' with your bot's token
    application = ApplicationBuilder().token("").build()

    # Define conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            APARTMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, apartment)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
