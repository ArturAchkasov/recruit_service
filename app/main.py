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
BACK_TO_MAIN_MENU = 'Главное меню'
NEW_SEARCH = 'Новый поиск'
NEXT_PAGE = '>'#'Следующая страница'
PREVIOUS_PAGE = '<'#'Предыдущая страниц'

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

BACK_TO_MAIN_MENU_BTN = [InlineKeyboardButton(BACK_TO_MAIN_MENU, callback_data=BACK_TO_MAIN_MENU)]
NEW_SEARCH_BTN = [InlineKeyboardButton(NEW_SEARCH, callback_data=NEW_SEARCH)]
NEXT_PAGE_BTN = [InlineKeyboardButton(NEXT_PAGE, callback_data=NEXT_PAGE)]
PREVIOUS_PAGE_BTN = [InlineKeyboardButton(PREVIOUS_PAGE, callback_data=PREVIOUS_PAGE)]
PREVIOUS_NEXT_PAGE_BTN = [InlineKeyboardButton(PREVIOUS_PAGE, callback_data=PREVIOUS_PAGE), InlineKeyboardButton(NEXT_PAGE, callback_data=NEXT_PAGE)]
PAGE_SIZE = 10

START_ROUTES, END_ROUTES, SELECTING_OPTION, VACANCY_SEARCH = range(4)
# Callback data
ONE, TWO, THREE, FOUR = range(4)
IN_FIRST_PAGE, IN_MIDDLE_PAGE, IN_LAST_PAGE = range(3)
VACANCIES_LIST = [f'механик{i}' for i in range(25)]


def get_page_navigation_keyboard(paginated_found_data, navigation):
    keyboard = [[InlineKeyboardButton(value, callback_data=value)] for value in paginated_found_data['pages'][paginated_found_data['current_page']-1]]
    if not navigation:
        if paginated_found_data['pages_count'] > 1:
            keyboard.append(NEXT_PAGE_BTN)
        keyboard.append(NEW_SEARCH_BTN)
        keyboard.append(BACK_TO_MAIN_MENU_BTN)
        return keyboard
    if paginated_found_data['pages_count'] > 1 and navigation:
        if navigation == IN_LAST_PAGE:
            keyboard.append(PREVIOUS_PAGE_BTN)
        if navigation == IN_MIDDLE_PAGE:
            if paginated_found_data['current_page'] < paginated_found_data['pages_count'] or paginated_found_data['current_page'] > 1:
                keyboard.append(PREVIOUS_NEXT_PAGE_BTN)
        if paginated_found_data['current_page'] == 1 and navigation == IN_FIRST_PAGE:
            keyboard.append(NEXT_PAGE_BTN)
    keyboard.append(NEW_SEARCH_BTN)
    keyboard.append(BACK_TO_MAIN_MENU_BTN)
    #if navigation == IN_FIRST_PAGE:
    return keyboard


def paginate(found_data, page_size=PAGE_SIZE):
    sublists = []
    for i in range(0, len(found_data), page_size):
        sublists.append(found_data[i: i + page_size])
    paginated_data = {
      'pages': sublists,
      'pages_count': len(sublists),
      'current_page': 1
    }
    return paginated_data

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
    if query.data == COMPANY_FIND:
        print('111111')
    if query.data == BACK_TO_MAIN_MENU:
        print('33333333')
    #    return ConversationHandler.END
    #print(query.data)
    if query.data == VACANCY_FIND or (context.user_data["choice"] == VACANCY_FIND and query.data == NEW_SEARCH):
        print('22222')
        context.user_data["choice"] = VACANCY_FIND
        keyboard = [BACK_TO_MAIN_MENU_BTN]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text('Введите данные для поиска:', reply_markup=reply_markup)
        
        return VACANCY_SEARCH
    
    return SELECTING_OPTION

async def handle_input_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    found_data = list(filter(lambda x: user_input.lower() in x, VACANCIES_LIST))
    if not found_data:
        keyboard = [NEW_SEARCH_BTN, BACK_TO_MAIN_MENU_BTN]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f'По вашему запросу ничего не найдено', reply_markup=reply_markup)
        return SELECTING_OPTION
    context.user_data['found_data'] = paginate(found_data)
    data = context.user_data['found_data']
    context.user_data['page_navigation'] = ''
    reply_markup = InlineKeyboardMarkup(get_page_navigation_keyboard(data, context.user_data['page_navigation']))
    await update.message.reply_text(f'По вашему запросу найдено {len(found_data)} вакансий.', reply_markup=reply_markup)
    return SELECTING_OPTION


async def handle_next_page_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = context.user_data['found_data']
    data['current_page'] += 1
    if data['current_page'] == data['pages_count']:# and data['pages_count'] == 1:
        context.user_data['page_navigation'] = IN_LAST_PAGE
        #keyboard = [[InlineKeyboardButton(value, callback_data=value)] for value in data['pages'][data['current_page']-1]]
        #if data['pages_count'] > 1:
        #    keyboard.append(PREVIOUS_PAGE_BTN)
        #keyboard.append(NEW_SEARCH_BTN)
        #keyboard.append(BACK_TO_MAIN_MENU_BTN)
        #reply_markup = InlineKeyboardMarkup(keyboard)
        reply_markup = InlineKeyboardMarkup(get_page_navigation_keyboard(data, context.user_data['page_navigation']))
        await query.edit_message_text(f"Cтраница №{data['current_page']}", reply_markup=reply_markup)
    if data['current_page'] < data['pages_count']:
        context.user_data['page_navigation'] = IN_MIDDLE_PAGE
        #keyboard = [[InlineKeyboardButton(value, callback_data=value)] for value in data['pages'][data['current_page']-1]]
        #keyboard.append(PREVIOUS_NEXT_PAGE_BTN)
        #keyboard.append(NEW_SEARCH_BTN)
        #keyboard.append(BACK_TO_MAIN_MENU_BTN)
        #reply_markup = InlineKeyboardMarkup(keyboard)
        reply_markup = InlineKeyboardMarkup(get_page_navigation_keyboard(data, context.user_data['page_navigation']))
        await query.edit_message_text(f"Cтраница №{data['current_page']}", reply_markup=reply_markup)

    print('sled str')
    return SELECTING_OPTION


async def handle_previous_page_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = context.user_data['found_data']
    data['current_page'] -= 1
    if data['current_page'] == 1:
        context.user_data['page_navigation'] = IN_FIRST_PAGE
        #keyboard = [[InlineKeyboardButton(value, callback_data=value)] for value in data['pages'][data['current_page']-1]]
        #keyboard.append(NEXT_PAGE_BTN)
        #keyboard.append(NEW_SEARCH_BTN)
        #keyboard.append(BACK_TO_MAIN_MENU_BTN)
        #reply_markup = InlineKeyboardMarkup(keyboard)
        reply_markup = InlineKeyboardMarkup(get_page_navigation_keyboard(data, context.user_data['page_navigation']))
        await query.edit_message_text(f"Cтраница №{data['current_page']}", reply_markup=reply_markup)
    if data['current_page'] > 1:
        context.user_data['page_navigation'] = IN_MIDDLE_PAGE
        #keyboard = [[InlineKeyboardButton(value, callback_data=value)] for value in data['pages'][data['current_page']-1]]
        #keyboard.append(PREVIOUS_NEXT_PAGE_BTN)
        #keyboard.append(NEW_SEARCH_BTN)
        #keyboard.append(BACK_TO_MAIN_MENU_BTN)
        #reply_markup = InlineKeyboardMarkup(keyboard)
        reply_markup = InlineKeyboardMarkup(get_page_navigation_keyboard(data, context.user_data['page_navigation']))
        await query.edit_message_text(f"Cтраница №{data['current_page']}", reply_markup=reply_markup)

    print('sled str')
    return SELECTING_OPTION


async def back_to_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    print(query)
    await query.answer()
    reply_markup = InlineKeyboardMarkup(MAIN_MENU_KEYBOARD)
    await query.message.reply_text('Выберите необходимый пункт', reply_markup=reply_markup)
    return SELECTING_OPTION
    

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
                CallbackQueryHandler(handle_selected_button, rf'{VACANCY_FIND}|{COMPANY_FIND}|{NEW_SEARCH}'), #pattern=rf'[{VACANCY_FIND}]|[{COMPANY_FIND}]'),# pattern="^" + VACANCY_FIND + "$"),
                #MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input_data),
                CallbackQueryHandler(handle_next_page_button, rf'{NEXT_PAGE}'),
                CallbackQueryHandler(handle_previous_page_button, rf'{PREVIOUS_PAGE}'),
                CallbackQueryHandler(back_to_main_menu),#, pattern="^" + BACK_TO_MAIN_MENU + "$"),
                
            ],
            #[application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_selected_button))],#[CallbackQueryHandler(handle_selected_button)],
            VACANCY_SEARCH: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input_data),
                CallbackQueryHandler(back_to_main_menu)
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
