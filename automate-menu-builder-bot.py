#!python

import os
import json
import asyncio
from tqdm import tqdm
from datetime import datetime
from dateutil.relativedelta import relativedelta

from telethon.sync import TelegramClient, events
from dotenv import dotenv_values
from menu import get_main_menu
from collections import deque
from utils.logging import logging, logging_setup_file, logging_setup_tqdm

logging_setup_tqdm()
logging_setup_file("automate-menu-builder-bot.log")

BOT_USERNAME = 'ZagEngTaskSimpleTelegramBot'
# BOT_USERNAME = 'Da7ee7_Civil_1st_Year_Bot'
env = dotenv_values(".env")
telegram_client = TelegramClient('telethon', env.get(
    "TELEGRAM_API_ID"), env.get("TELEGRAM_API_HASH"))  # type: ignore

# we need this global `error_occured` because we are running
# different threads and async  code if an error occured,  we
# should stop the next process step
error_occured = False
process_file = "automate-menu-builder-bot.process.log"
parent_button = None
# parent_button = "الترم الأول 🥇"
process: deque[str | dict[str, str]] = deque([
    "/start",
    "/langen",
])


def build_button(button, first_in_row=False):
    process.append("➕ Add Button")
    process.append(button["name"])
    if not first_in_row:
        process.append({"type": "click-button", "name": "⬆"})
    if command := button.get("command"):
        process.append({"type": "click-button", "name": "*⃣"})
        process.append("Assign Command")
        process.append(command)
        process.append("Move by Command (▶️ On)")
        process.append("✅ Confirm")
        process.append("🔚 Exit Button Settings")
        # to select it again so that the new
        # button will be underneath it
        process.append(button["name"])


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
            if submenu := button.get("submenu"):
                process.append(f'[ {button["name"]} ]')
                build_menu_buttons(submenu)


def build_menu_messages(menu):
    for row_buttons in menu:
        for button in row_buttons:
            if messages := button.get("messages"):
                process.append(button["name"])
                for message in messages:
                    process.append("➕ Add Message")
                    process.append(message)
            if sub_menu := button.get("submenu"):
                build_menu_messages(sub_menu)


def confirm_process_file():
    print(f"Process file exists: {process_file}")
    print("Do you want to continue (y)? ", end="")
    ans = input()
    return ans.lower() == 'y' or ans == ''


if os.path.exists(process_file) and confirm_process_file():
    with open(process_file, "r") as f:
        process = deque(json.loads(f.read()))
else:
    main_menu = get_main_menu()
    process.append("🎛 Buttons Editor")
    if parent_button:
        process.append(f"[ {parent_button} ]")
    build_menu_buttons(main_menu)

    process.append("🛑 Stop Editor")
    process.append("📝 Posts Editor")
    build_menu_messages(main_menu)
    process.append("🛑 Stop Editor")

    process.append("/langar")

progress_len = len(process)
progress = tqdm(total=progress_len)


def update_process_file():
    """ this is a queque but stored in a file to continue
    if the process stoped because of some error """
    with open(process_file, "w") as f:
        f.write(json.dumps(list(process), indent=2, ensure_ascii=False))


def get_message():
    """ get the next process step, return None if an error occured occured
    we ran out of the step and all are done """

    try:
        update_process_file()
        message = process.popleft()
        progress.update(progress_len - len(process))
        if len(process) == 0:
            if os.path.exists(process_file):
                os.remove(process_file)
            logging.info("Alhamdulilah, all are done 💚")
        return message
    except:
        pass


async def click_inline_button(button_name: str, event: events.NewMessage.Event | None):
    global error_occured
    if not event:
        logging.error("an event is required to click an inline button")
        error_occured = True
        return

    buttons = await event.get_buttons()

    if not buttons:
        error_occured = True
        logging.warning("can't find the button to click, " + button_name)
        logging.warning("no buttons found to click")
        return

    for buttons_row in buttons:
        for button in buttons_row:
            if button_name != button.button.text:
                continue
            logging.info("clicking: " + button.button.text)
            await button.click()
            return

    all_buttons = ", ".join(
        [", ".join([button.button.text for button in buttons_row])
         for buttons_row in buttons] if buttons else [])
    logging.warning("can't find the button to click, " + button_name)
    # all the buttons chained
    logging.warning("here are the buttons: " + all_buttons)
    error_occured = True

done = False
recieved = []


async def send_message(event: events.NewMessage.Event | None = None):
    message = get_message()
    if type(message) is str:
        logging.info("sending: " + message)
        # type: ignore
        await telegram_client.send_message(BOT_USERNAME, message)
    elif type(message) is dict:
        if message["type"] == "file":
            file_path: str = message["path"]
            logging.info("sending file: " + file_path)
            # await telegram_client.send_file(BOT_USERNAME, file_path) # type: ignore
            logging.warning("ignore sending the file")
        elif message["type"] == "click-button":
            button_name = message["name"]
            await click_inline_button(button_name, event)


async def start_process():
    global recieved
    await send_message()
    # 300 milliseconds
    debouncing_time = relativedelta(microseconds=int(3e5))
    debouncing_time_seconds = debouncing_time.seconds + \
        debouncing_time.microseconds / 1e6
    while not done:
        if recieved:
            last = recieved[-1]
            if datetime.now() > last["date"] + debouncing_time:
                recieved = []
                await send_message(last["event"])
        await asyncio.sleep(debouncing_time_seconds)


with telegram_client:
    @telegram_client.on(events.NewMessage(from_users=BOT_USERNAME))
    async def _(event):
        global done, recieved
        recieved_message = event.message.message.split("\n")[
            0]  # first line only
        logging.info("recieved: " + recieved_message)
        if error_occured or len(process) == 0 or recieved_message[0] == "❌":
            done = True
        else:
            recieved.append({'date': datetime.now(), 'event': event})
    telegram_client.loop.run_until_complete(start_process())
