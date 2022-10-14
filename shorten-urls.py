import re
import sys
import requests
from dotenv import dotenv_values
from os import path
import inquirer

env = dotenv_values(".env")

API_URL = "https://api-ssl.bitly.com/v4/shorten"
BITLY_TOKEN = env.get("BITLY_TOKEN")


def shorten_url(url):
    payload = {
        "long_url": url,
        "tags": [
            "da7ee7-python-shortening"
        ]
    }
    headers = {
        'Authorization': f'Bearer {BITLY_TOKEN}',
        'Content-Type': 'application/json',
    }
    r = requests.post(f"{API_URL}", json=payload, headers=headers)
    res = r.json()
    return res["link"]


def handle_file(file):
    # source: https://stackoverflow.com/a/3809435
    link_re = re.compile(
        r"(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})")
    bitly_re = re.compile(r"^https?://bit.ly")
    with open(file, "r+") as f:
        content = f.read()
        links = set()
        for link in link_re.findall(content):
            if bitly_re.match(link) or len(link) <= 60: # the link length is objective
                continue
            links.add(link)

        if not links:
            print("No links found!")
            return

        questions = [inquirer.Checkbox(
            'links',
            message="What links to shorten?",
            choices=links,
            default=links
        )]
        answers = inquirer.prompt(questions)

        if not answers:
            print("No links found!")
            return

        for link in answers['links']:
            short = shorten_url(link)
            print(f"{link} => {short}")
            content = content.replace(link, short)

        f.seek(0)
        f.write(content)
        f.truncate()


if __name__ == "__main__":
    file = sys.argv[1]
    if not path.exists(file):
        print(f"file doesn't exist: {file}", file=sys.stderr)
        sys.exit(1)
    handle_file(file)
