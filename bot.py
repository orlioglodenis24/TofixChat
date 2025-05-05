from dotenv import load_dotenv
import os
import logging
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

WAITING, CHATTING = range(2)
user_pairs = {}
waiting_users = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Добро пожаловать в анонимный чат-бот! 👋\n\n"
        "Здесь вы можете общаться с случайными собеседниками анонимно.\n\n"
        "Команды:\n"
        "/start - информация о боте\n"
        "/search - поиск собеседника\n"
        "/stop - завершение текущего чата\n"
        "/help - получение помощи\n\n"
        "Для начала поиска собеседника отправьте /search."
    )
    return ConversationHandler.END

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    
    if user_id in user_pairs:
        await update.message.reply_text("Вы уже находитесь в чате! Чтобы завершить чат, отправьте /stop.")
        return CHATTING
    
    if user_id in waiting_users:
        await update.message.reply_text("Вы уже в поиске собеседника. Пожалуйста, подождите.")
        return WAITING
    
    await update.message.reply_text("Поиск собеседника начат... ⏳")
    waiting_users.append(user_id)
    
    if len(waiting_users) >= 2:
        user1 = waiting_users.pop(0)
        user2 = waiting_users.pop(0)
        
        user_pairs[user1] = user2
        user_pairs[user2] = user1
        
        await context.bot.send_message(user1, "Собеседник найден! Можете начинать общение. 🎉")
        await context.bot.send_message(user2, "Собеседник найден! Можете начинать общение. 🎉")
        return CHATTING
    
    return WAITING

async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    
    if user_id in user_pairs:
        partner_id = user_pairs[user_id]
        
        del user_pairs[user_id]
        if partner_id in user_pairs:
            del user_pairs[partner_id]
        
        await update.message.reply_text("Чат завершен. Для поиска нового собеседника отправьте /search.")
        await context.bot.send_message(partner_id, "Собеседник завершил чат. Для поиска нового собеседника отправьте /search.")
        return ConversationHandler.END
    
    if user_id in waiting_users:
        waiting_users.remove(user_id)
        await update.message.reply_text("Поиск собеседника остановлен.")
        return ConversationHandler.END
    
    await update.message.reply_text("Вы не находитесь в чате. Для поиска собеседника отправьте /search.")
    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    
    if user_id in user_pairs:
        partner_id = user_pairs[user_id]
        await context.bot.send_message(partner_id, f"{update.message.text}")
        return CHATTING
    
    if user_id in waiting_users:
        await update.message.reply_text("Пожалуйста, дождитесь собеседника или отправьте /stop для отмены поиска.")
        return WAITING
    
    await update.message.reply_text("Для поиска собеседника отправьте /search.")
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Команды бота:\n"
        "/start - информация о боте\n"
        "/search - поиск собеседника\n"
        "/stop - завершение текущего чата\n"
        "/help - получение этой помощи\n\n"
        "Просто отправляйте сообщения для общения с собеседником, когда найдете его."
    )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Произошла ошибка: {context.error}")

def main() -> None:
    load_dotenv()
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("Токен бота не найден в .env файле")
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("search", search)],
        states={
            WAITING: [
                CommandHandler("stop", stop_chat),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
            ],
            CHATTING: [
                CommandHandler("stop", stop_chat),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
            ],
        },
        fallbacks=[CommandHandler("stop", stop_chat)],
    )
    
    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)
    application.run_polling()

if __name__ == "__main__":
    main()
