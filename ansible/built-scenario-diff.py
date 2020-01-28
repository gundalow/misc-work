#!/usr/bin/python3 --
import os
import sys
from pprint import pprint

import yaml


PLUGIN_TYPES = ('modules', 'module_utils', 'action', 'become', 'cache', 'callback', 'cliconf',
                'connection', 'doc_fragments', 'filter', 'httpapi', 'inventory', 'lookup',
                'netconf', 'shell', 'strategy', 'terminal', 'test', 'vars')


def assemble_plugins(directory):
    plugins = {k: set() for k in PLUGIN_TYPES}

    # Walk modules
    # Record all of the files and directories that are in there
    module_dir = os.path.join(directory, 'lib', 'ansible', 'modules')
    for root, directories, files in os.walk(module_dir):
        for filename in files:
            if filename in plugins['modules'] and filename != '__init__.py':
                raise Exception(f'Module {filename} with a conflicting name!')
            plugins['modules'].add(filename)

    # Walk the module_utils
    # Record all of the files and directories that are in there
    module_dir = os.path.join(directory, 'lib', 'ansible', 'module_utils')
    for root, directories, files in os.walk(module_dir):
        module_offset = root[len(module_dir) + 1:]
        for filename in files:
            plugins['module_utils'].add(os.path.join(module_offset, filename))

    # Record all of the files that are in the other plugins
    plugin_dir = os.path.join(directory, 'lib', 'ansible', 'plugins')
    for plugin_type in (t for t in PLUGIN_TYPES if t not in ('modules', 'module_utils')):
        for root, directories, files in os.walk(os.path.join(plugin_dir, plugin_type)):
            if directories:
                raise Exception(f'There were directories, {directories}, in the {plugin_type}'
                                ' directory')
            for filename in files:
                plugins[plugin_type].add(filename)

    return plugins

def main():
    try:
        base = sys.argv[1]
    except IndexError:
        base = '/var/tmp/ansible-base'
    try:
        minimal = sys.argv[2]
    except IndexError:
        minimal = '/var/tmp/ansible-minimal'

    base_plugins = assemble_plugins(base)
    minimal_plugins = assemble_plugins(minimal)

    print('***************************')
    print('In minimal but not in base:')
    for plugin_type, plugins in minimal_plugins.items():
        extra_plugins = plugins.difference(base_plugins[plugin_type])
        if extra_plugins:
            print(f'## {plugin_type} ##')
            print(yaml.dump(sorted(list(extra_plugins))))
            print()

    print('***************************')
    print('In base but not in minimal:')
    for plugin_type, plugins in base_plugins.items():
        extra_plugins = plugins.difference(minimal_plugins[plugin_type])
        if extra_plugins:
            print(f'## {plugin_type} ##')
            print(yaml.dump(sorted(list(extra_plugins))))
            print()

    print('********************************')
    print('Complete list of what is in base')
    pprint(base_plugins)


if __name__ == '__main__':
    main()
