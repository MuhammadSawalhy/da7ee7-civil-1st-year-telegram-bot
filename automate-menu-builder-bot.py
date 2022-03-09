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


def build_button(button, first_in_row=False):
    process.append("➕ Add Button")
    process.append(button["name"])
    command = button.get("command")
    if command:
        process.append({"type": "click-button", "name": "*⃣"})
        process.append("Assign Command")
        process.append(command)
        process.append("✅ Confirm")
        process.append("🔚 Exit Button Settings")
        if not first_in_row:
            # because we want to click ⬆️
            process.append(button["name"])
    if not first_in_row:
        process.append({"type": "click-button", "name": "⬆️"})


def build_row(row):
    if row:
        build_button(row[0], first_in_row=True)
    for button in row[1:]:
        build_button(button)


def build_menu_buttons(menu):  # recursively
    for row_buttons in menu:
        build_row(row_buttons)
    for row_buttons in menu:
        for button in row_buttons:
            if submenu := button.get("menu_buttons"):
                process.append(f'[ {button["name"]} ]')
                build_menu_buttons(submenu)


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


with open("./menu_buttons/main.json", "r") as file:
    main_menu = json.loads(file.read())

process.append("🎛 Buttons Editor")
build_menu_buttons(main_menu)

process.append("🛑 Stop Editor")
process.append("📝 Posts Editor")
build_menu_messages(main_menu)
process.append("🛑 Stop Editor")

process.append("/langar")
# TODO: test with snapshots instead
# print(*process, sep="\n")
# exit()


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
                return

    all_buttons = ", ".join([", ".join([button.button.text for button in buttons_row]) for buttons_row in buttons])
    logging.error("can't find the button to click, " + button_name)
    logging.error("here are the buttons: " + all_buttons) # all the buttons chained
    error_occured = True


@debounce_async(0.5)
async def send_message(event: events.NewMessage.Event | None = None):
    message = get_message()
    if type(message) is str:
        logging.info("sending: " + message)
        await telegram_client.send_message(BOT_USERNAME, message) # type: ignore
    elif type(message) is dict:
        if message["type"] == "file":
            file_path: str = message["path"]
            logging.info("sending file: " + file_path)
            await telegram_client.send_file(BOT_USERNAME, file_path) # type: ignore
        elif message["type"] == "click-button":
            button_name = message["name"]
            await click_inline_button(button_name, event)


with telegram_client:
    @telegram_client.on(events.NewMessage(from_users=BOT_USERNAME))
    async def on_message_recieved(event):
        recieved_message = event.message.message.split("\n")[0] # first line only
        logging.info("recieved message: " + recieved_message)
        if error_occured or len(process) == 0 or recieved_message == "❌ Unknown Command!":
            disconn_coro = telegram_client.disconnect()
            if disconn_coro:
                await disconn_coro
        else:
            await send_message(event)

    telegram_client.loop.run_until_complete(send_message())
    telegram_client.run_until_disconnected()
