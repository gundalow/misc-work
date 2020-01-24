#!/usr/bin/python3 -tt
import requests
import yaml


def get_migration_scenario(name):
    url = f'https://raw.githubusercontent.com/ansible-community/collection_migration/master/scenarios/{name}/ansible.yml'
    data = requests.get(url)

    parsed_data = yaml.safe_load(data.text)

    return parsed_data['_core']


def main():
    # get tasks (modules and actions) in the minimal set
    minimal_plugins = get_migration_scenario('minimal')
    bcs_plugins = get_migration_scenario('bcs')

    for plugin_type, bcs_plugin_list in bcs_plugins.items():
        bcs_plugins_of_type = set(bcs_plugin_list)
        minimal_plugins_of_type = set(minimal_plugins.get(plugin_type, []))

        only_in_minimal = minimal_plugins_of_type.difference(bcs_plugins_of_type)
        if only_in_minimal:
            print(f'{plugin_type} plugins in minimal but not bcs:')
            print(yaml.dump(list(only_in_minimal)))
            print()

        only_in_bcs = bcs_plugins_of_type.difference(minimal_plugins_of_type)
        if only_in_bcs:
            print(f'{plugin_type} plugins in bcs but not minimal:')
            print(yaml.dump(list(only_in_bcs)))
            print()

    for plugin_type, minimal_plugin_list in minimal_plugins.items():
        if plugin_type not in bcs_plugins:
            print(f'{plugin_type} plugins in minimal but not in bcs:')
            print(yaml.dump(list(minimal_plugin_list)))
            print()


if __name__ == '__main__':
    main()
