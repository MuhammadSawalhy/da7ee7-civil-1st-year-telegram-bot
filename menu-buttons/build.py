#!python

import yaml
import json
import sys
import os


class YamlIncludeLoader(yaml.SafeLoader):

    def __init__(self, stream):
        self._root = os.path.split(stream.name)[0]
        super(YamlIncludeLoader, self).__init__(stream)

    def include(self, node):
        filename = os.path.join(self._root, self.construct_scalar(node))
        with open(filename, 'r') as f:
            return yaml.load(f, YamlIncludeLoader)


YamlIncludeLoader.add_constructor('!include', YamlIncludeLoader.include)


with open(sys.argv[1], 'r') as f:
    data = yaml.load(f, YamlIncludeLoader)
    print(json.dumps(data))
