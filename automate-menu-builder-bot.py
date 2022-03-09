#!python

import json
import logging

from telethon.sync import TelegramClient, events
from dotenv import dotenv_values
from collections import deque
from utils import debounce_async

logging.basicConfig(format='[%(levelname)-7s %(asctime)s] %(name)s: %(message)s',
                    level=logging.INFO)

BOT_USERNAME = 'Da7ee7_Civil_1st_Year_Bot'
env = dotenv_values(".env")
telegram_client = TelegramClient('telethon', env.get(
    "TELEGRAM_API_ID"), env.get("TELEGRAM_API_HASH"))  # type: ignore

# we need this global `error_occured` because we are running different threads
# and async code if an error occured, we should stop the next process step
error_occured = False
process: deque[str | dict[str, str]] = deque([
    "/start",
    "/langen",
])

with open("./menu_buttons/main.json", "r") as file:
    main_menu = json.loads(file.read())


def build_row(row):
    if row:
        button = row[0]
        process.append("➕ Add Button")
        process.append(button.get("name"))
    for button in row[1:]:
        process.append("➕ Add Button")
        process.append(button.get("name"))
        process.append({"type": "click-button", "name": "⬆️"})


def build_menu_buttons(menu):  # recursively
    for row_buttons in menu:
        build_row(row_buttons)
    for row_buttons in menu:
        for button in row_buttons:
            if (button.get("menu_buttons")):
                process.append(f'[ {button.get("name")} ]')
                build_menu_buttons(button.get("menu_buttons"))


def build_menu_messages(menu):
    for row_buttons in menu:
        for button in row_buttons:
            name = button.get("name")
            messages = button.get("messages")
            sub_menu = button.get("menu_buttons")
            if messages:
                process.append(name)
                for message in messages:
                    process.append("➕ Add Message")
                    process.append(message)
            if sub_menu:
                build_menu_messages(sub_menu)


process.append("🎛 Buttons Editor")
build_menu_buttons(main_menu)

process.append("🛑 Stop Editor")
process.append("📝 Posts Editor")
build_menu_messages(main_menu)
process.append("🛑 Stop Editor")

process.append("/langar")
# print(*process, sep="\n")
# exit()

process = deque([
    "🎛 Buttons Editor",
    "➕ Add Button",
    "الترم الأول a",
    "➕ Add Button",
    "الترم الثاني a",
    {'type': 'click-button', 'name': '⬆️'}
])


def get_message():
    """ get the next process step, return None if an error occured occured
    we ran out of the step and all are done """

    try:
        message = process.popleft()
        if len(process) == 0:
            logging.info("Alhamdulilah, all are done 💚")
        return message
    except:
        return


async def click_inline_button(button_name: str, event: events.NewMessage.Event | None):
    global error_occured
    if not event:
        logging.error("an event is required to click an inline button")
        error_occured = True
        return

    buttons = await event.get_buttons()

    if not buttons:
        logging.error("can't find buttons to click: " +
                      button_name)
        error_occured = True
        return
    for buttons_row in buttons:
        for button in buttons_row:
            if button_name == button.button.text:
                logging.info("clicking: " + button.button.text)
                await button.click()


@debounce_async(0.3)
async def send_message(event: events.NewMessage.Event | None = None):
    message = get_message()
    if type(message) is str:
        logging.info("sending: " + message)
        await telegram_client.send_message(BOT_USERNAME, message) # type: ignore
    elif type(message) is dict:
        if message.get("type") == "file":
            file_path: str = message["path"]
            logging.info("sending file: " + file_path)
            await telegram_client.send_file(BOT_USERNAME, file_path) # type: ignore
        elif message.get("type") == "click-button":
            button_name = message["name"]
            await click_inline_button(button_name, event)


with telegram_client:
    @telegram_client.on(events.NewMessage(from_users=BOT_USERNAME))
    async def on_message_recieved(event):
        logging.info("recieved message: " + event.message.message.split("\n")[0])
        if error_occured or len(process) == 0:
            disconn_coro = telegram_client.disconnect()
            if disconn_coro: await disconn_coro
        else:
            await send_message(event)

    telegram_client.loop.run_until_complete(send_message())
    telegram_client.run_until_disconnected()
