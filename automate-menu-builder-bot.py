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
    "TELEGRAM_API_ID"), env.get("TELEGRAM_API_HASH"))
process = deque([
    # "/start",
    # "/langen",
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


def get_message():
    try:
        message = process.popleft()
    except:
        logging.info("Alhamdulilah, all are done 💚")
        return
    return message


@debounce_async(0.1)
async def send_message(event=None):
    message = get_message()
    if not message:
        await telegram_client.disconnect()  # we are done
        return
    if type(message) == str:
        logging.info("sending: " + message)
        await telegram_client.send_message(BOT_USERNAME, message)
    elif type(message) == dict:
        if message.get("type") == "file":
            file_path = message.get("path")
            logging.info("sending file: " + file_path)
            await telegram_client.send_file(BOT_USERNAME, file_path)
        elif message.get("type") == "click-button":
            buttons = await event.get_buttons()
            if not buttons:
                logging.error("can't find buttons to click: " +
                              message.get("name"))
                exit(1)
            for bline in buttons:
                for button in bline:
                    if message.get("name") == button.button.text:
                        logging.info("clicking: " + button.button.text)
                        await button.click()


with telegram_client:
    @telegram_client.on(events.NewMessage(from_users=BOT_USERNAME))
    async def on_message_recieved(event):
        await send_message(event)
    telegram_client.loop.run_until_complete(send_message())
    telegram_client.run_until_disconnected()
