import telebot
from telebot import types
from menu import main_menu
from dotenv import dotenv_values

env = dotenv_values(".env")
bot = telebot.TeleBot(env.get("BOT_TOKEN"))

current_path = []
all_buttons = {}
main_menu_copy = main_menu.copy()
while len(main_menu_copy):
    row = main_menu_copy.pop()
    for button in row:
        all_buttons[button["name"]] = button
        if submenu := button.get("submenu"):
            main_menu_copy.extend(submenu)


def get_menu_markup(menu):
    markup = types.ReplyKeyboardMarkup()
    for row in menu:
        markup.row(*[types.KeyboardButton(button["name"]) for button in row])
    markup.row(types.KeyboardButton("◀️"), types.KeyboardButton("🔼"))
    return markup


@bot.message_handler(commands=['start'])
def command_start(message):
    markup = get_menu_markup(main_menu)
    bot.send_message(message.chat.id, message.text, reply_markup=markup)


@bot.message_handler()
def any_message(message):
    global current_path
    button = None
    submenu = None
    button_name = message.text

    if button_name == "◀️" and len(current_path) > 1:
        button_name = current_path.pop()
        button_name = current_path.pop()
        button = all_buttons.get(button_name)
    elif button_name == "🔼" or (button_name == "◀️" and len(current_path) == 1):
        if current_path:
            current_path.pop()
        elif button_name == "🔼":
            current_path = []
        submenu = main_menu
    else:
        button = all_buttons.get(button_name)

    if button:
        submenu = button.get("submenu")
        if submenu:
            current_path.append(button_name)
            
    if submenu:
        markup = get_menu_markup(submenu)
    else:
        markup = None

    bot.send_message(message.chat.id, message.text, reply_markup=markup)
    messages = button.get("messages") if button else None
    if messages:
        for msg in messages:
            if type(msg) is str:
                bot.send_message(message.chat.id, msg, disable_web_page_preview=True)


bot.set_webhook()
bot.polling()
