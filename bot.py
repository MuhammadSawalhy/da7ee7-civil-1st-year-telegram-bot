import os
import sys
import telebot
from telebot import types
from dotenv import dotenv_values
from menu import get_main_menu

env = dotenv_values(".env")
bot = telebot.TeleBot(env.get("BOT_TOKEN"))

GO_BACK = "◀️"
REFRESH = "🔄"
MAIN_MENU = "🔼"
current_path = []
all_buttons = {}
main_menu = []
is_prod = os.environ.get("BOT_ENV") == "production"


def update():
    global all_buttons, main_menu

    try:
        main_menu = get_main_menu()
    except Exception as e:
        print(e, file=sys.stderr)

    main_menu_copy = main_menu.copy()
    all_buttons = {}

    while len(main_menu_copy):
        row = main_menu_copy.pop()
        for button in row:
            all_buttons[button["name"]] = button
            if submenu := button.get("submenu"):
                main_menu_copy.extend(submenu)


def get_menu_markup(menu):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for row in menu:
        markup.row(*[types.KeyboardButton(button["name"]) for button in row])
    navigation_row = [
        GO_BACK,
        MAIN_MENU,
    ]
    if not is_prod:
        navigation_row.insert(0, REFRESH)
    markup.row(*[types.KeyboardButton(button) for button in navigation_row])
    return markup


@bot.message_handler(commands=['start'])
def command_start(message):
    if not is_prod:
        update()
    markup = get_menu_markup(main_menu)
    bot.send_message(message.chat.id, message.text, reply_markup=markup)


@bot.message_handler()
def any_message(message):
    global current_path
    button = None
    submenu = None
    button_name = message.text

    if not is_prod:
        update()

    if button_name == REFRESH and len(current_path):
        button_name = current_path.pop()
    if button_name == GO_BACK and len(current_path) > 1:
        button_name = current_path.pop()
        button_name = current_path.pop()
    elif button_name == MAIN_MENU or (button_name == GO_BACK and len(current_path) == 1):
        if current_path:
            current_path.pop()
        elif button_name == MAIN_MENU:
            current_path = []
        button_name = None
        submenu = main_menu

    if button_name:
        button = all_buttons.get(button_name)

    if button:
        submenu = button.get("submenu")
        if submenu:
            current_path.append(button_name)

    if submenu:
        markup = get_menu_markup(submenu)
    else:
        markup = None

    bot.send_message(
        message.chat.id,
        button_name if button_name else message.text,
        reply_markup=markup
    )
    messages = button.get("messages") if button else None
    if messages:
        for msg in messages:
            if type(msg) is str:
                bot.send_message(message.chat.id, msg,
                                 disable_web_page_preview=True)


update()
bot.remove_webhook()
bot.polling(True)
