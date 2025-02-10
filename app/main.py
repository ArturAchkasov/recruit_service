import asyncio
import logging
import os
import re
from typing import Dict

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      Update)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, ConversationHandler, MessageHandler,
                          filters)


load_dotenv()
token = os.getenv('TOKEN')
IS_ADMIN = True

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

ADMIN_AUTH = 'Вход в административную часть'
VACANCY_FIND = 'Вакансии'
COMPANY_FIND = 'Компании'
COLLEAGUE_FIND = 'Коллеги'
BACK_TO_MAIN_MENU = 'Вернуться в главное меню'

FIND_HELP_TEXT = {
    ADMIN_AUTH: 'Введите ваш логин:',
    VACANCY_FIND: 'Введите ключевые и стоп слова:',
    COMPANY_FIND: 'Введите название компании:',
    COLLEAGUE_FIND: 'Введите имя и/или фамилию коллеги:'
}

MAIN_MENU_KEYBOARD = [
    [InlineKeyboardButton(ADMIN_AUTH, callback_data=ADMIN_AUTH)],
    [InlineKeyboardButton(VACANCY_FIND, callback_data=VACANCY_FIND)],
    [InlineKeyboardButton(COMPANY_FIND, callback_data=COMPANY_FIND)],
    [InlineKeyboardButton(COLLEAGUE_FIND, callback_data=COLLEAGUE_FIND)]
]

PAGE_SIZE = 10

START_ROUTES, END_ROUTES, SELECTING_OPTION = range(3)
# Callback data
ONE, TWO, THREE, FOUR = range(4)

VACANCIES_LIST = [f'механик{i}' for i in range(15)]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    user = update.message.from_user
    #reply_markup = InlineKeyboardMarkup(keyboard)
    reply_markup = InlineKeyboardMarkup(MAIN_MENU_KEYBOARD)
    # Send message with text and appended InlineKeyboard
    await update.message.reply_text('Выберите необходимый пункт', reply_markup=reply_markup)
    # Tell ConversationHandler that we're in state `FIRST` now
    return SELECTING_OPTION
    return START_ROUTES


async def start_over(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Prompt same text & keyboard as `start` does but not as new message"""
    # Get CallbackQuery from Update
    query = update.callback_query
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("1", callback_data=str(ONE)),
            InlineKeyboardButton("2", callback_data=str(TWO)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Instead of sending a new message, edit the message that
    # originated the CallbackQuery. This gives the feeling of an
    # interactive menu.
    await query.edit_message_text(text="Start handler, Choose a route", reply_markup=reply_markup)
    return START_ROUTES


async def handle_selected_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
    query = update.callback_query
    #print(query)
    await query.answer()
    if query.data == BACK_TO_MAIN_MENU:
        return ConversationHandler.END
    #print(query.data)
    if query.data == VACANCY_FIND:
        context.user_data["choice"] = VACANCY_FIND
        keyboard = [[InlineKeyboardButton(BACK_TO_MAIN_MENU, callback_data=BACK_TO_MAIN_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text('Введите данные для поиска:', reply_markup=reply_markup)
        
        return SELECTING_OPTION
    
    return START_ROUTES

async def handle_input_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    filtering = list(filter(lambda x: user_input.lower() in x, VACANCIES_LIST))
    if filtering:
        if len(filtering) > PAGE_SIZE:
            new_filtering = filtering[0:PAGE_SIZE]
            keyboard = [[InlineKeyboardButton(value, callback_data=value)] for value in new_filtering]
            keyboard.append([InlineKeyboardButton('Следующая страница', callback_data='next_page')])
            keyboard.append([InlineKeyboardButton(BACK_TO_MAIN_MENU, callback_data=BACK_TO_MAIN_MENU)])
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(f'По вашему запросу найдено {len(filtering)} вакансий.', reply_markup=reply_markup)
    # Здесь можно добавить логику для обработки введенных данных
    await update.message.reply_text(f'Вы ввели: {user_input}{context.user_data["choice"]}')
    return SELECTING_OPTION

async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    print(query)
    await query.answer()
    reply_markup = InlineKeyboardMarkup(MAIN_MENU_KEYBOARD)
    # Send message with text and appended InlineKeyboard
    await query.message.reply_text('Выберите необходимый пункт', reply_markup=reply_markup)
    # Tell ConversationHandler that we're in state `FIRST` now
    return SELECTING_OPTION
    return START_ROUTES
    

async def one(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("3", callback_data=str(THREE)),
            InlineKeyboardButton("4", callback_data=str(FOUR)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="First CallbackQueryHandler, Choose a route", reply_markup=reply_markup
    )
    return START_ROUTES


async def two(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("1", callback_data=str(ONE)),
            InlineKeyboardButton("3", callback_data=str(THREE)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Second CallbackQueryHandler, Choose a route", reply_markup=reply_markup
    )
    return START_ROUTES


async def three(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons. This is the end point of the conversation."""
    query = update.callback_query
    print(update.message)
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("Yes, let's do it again!", callback_data=str(ONE)),
            InlineKeyboardButton("Nah, I've had enough ...", callback_data=str(TWO)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Third CallbackQueryHandler. Do want to start over?", reply_markup=reply_markup
    )
    # Transfer to conversation state `SECOND`
    return END_ROUTES


async def four(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show new choice of buttons"""
    query = update.callback_query
    await query.answer()
    keyboard = [
        [
            InlineKeyboardButton("2", callback_data=str(TWO)),
            InlineKeyboardButton("3", callback_data=str(THREE)),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="Fourth CallbackQueryHandler, Choose a route", reply_markup=reply_markup
    )
    return START_ROUTES


async def end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over.
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="See you next time!")
    return ConversationHandler.END





def main() -> None:
    application = Application.builder().token(token).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_OPTION: [
                CallbackQueryHandler(handle_selected_button, pattern="^" + VACANCY_FIND + "$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input_data),
                CallbackQueryHandler(back_to_main_menu),
            ],
            
            #[application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_selected_button))],#[CallbackQueryHandler(handle_selected_button)],
            START_ROUTES: [
                CallbackQueryHandler(one, pattern="^" + ADMIN_AUTH + "$"),
                CallbackQueryHandler(two, pattern="^" + str(TWO) + "$"),
                CallbackQueryHandler(three, pattern="^" + str(THREE) + "$"),
                CallbackQueryHandler(four, pattern="^" + str(FOUR) + "$"),
            ],
            END_ROUTES: [
                CallbackQueryHandler(start_over, pattern="^" + str(ONE) + "$"),
                CallbackQueryHandler(end, pattern="^" + str(TWO) + "$"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )
    application.add_handler(conv_handler)
    application.run_polling(allowed_updates=Update.ALL_TYPES)



if __name__ == "__main__":
    main()
