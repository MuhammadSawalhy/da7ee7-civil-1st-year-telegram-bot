#!python

import yaml
import json
import sys
from os import path


__dirname__ = path.dirname(__file__)

entry_file_path = sys.argv[1] if len(sys.argv) > 1 else \
    path.join(__dirname__, "./main.yml")


def polish_message_file_path(menu, yaml_file_path):
    if type(menu) is not list:
            menu = [[menu]]
    for i, button_or_row in enumerate(menu):
        if type(button_or_row) is not list:
            button_or_row = [button_or_row]
        for button in button_or_row:
            if messages := button.get("messages"):
                for msg in messages:
                    if type(msg) is dict and msg["type"] == "file":
                        dirname = path.dirname(yaml_file_path)
                        msg["path"] = path.join(dirname, msg["path"])


class YamlIncludeLoader(yaml.SafeLoader):

    def __init__(self, stream):
        self._root = path.split(stream.name)[0]
        super(YamlIncludeLoader, self).__init__(stream)

    def include(self, node):
        filename = path.join(self._root, self.construct_scalar(node))
        with open(filename, 'r') as f:
            menu = yaml.load(f, YamlIncludeLoader)
            polish_message_file_path(menu, filename)
            return menu


YamlIncludeLoader.add_constructor('!include', YamlIncludeLoader.include)
all_buttons = []


def polish_menu(menu, menu_path=[]):
    for i, button_or_row in enumerate(menu):
        if type(button_or_row) is not list:
            menu[i] = [button_or_row]
            button_or_row = [button_or_row]
        for button in button_or_row:
            if button["name"] in all_buttons:
                print("dublicated button:", button["name"], file=sys.stderr)
                exit(1)
            all_buttons.append(button["name"])
            button_path = menu_path.copy()
            button_path.append(button["name"])
            button["path"] = button_path
            if submenu := button.get("submenu"):
                if type(submenu) is not list:
                    submenu = [[submenu]]
                polish_menu(submenu, button_path)


with open(entry_file_path, 'r') as f:
    main_menu = yaml.load(f, YamlIncludeLoader)
    if type(main_menu) is not list:
        main_menu = [[main_menu]]
    polish_message_file_path(main_menu, entry_file_path)
    polish_menu(main_menu)

if __name__ == "__main__":
    print(json.dumps(main_menu))
