#!/usr/bin/python3 -tt

import os

import yaml


CHECKOUTDIR='/srv/ansible/vanilla'


def main():
    routing_data = yaml.safe_load(open(os.path.join(CHECKOUTDIR, 'lib/ansible/config/routing.yml')).read())

    collections = set()
    for plugin_type, plugins in routing_data['plugin_routing'].items():
        for plugin_data in plugins.values():
            replacement = plugin_data['redirect']
            collection = replacement.split('.')[0:2]
            if collection[0] == 'testns':
                # Blacklist the testns as we only use it for testing.
                # We do not want someone to try to compromize testing infrastructure using this
                continue
            collections.add('.'.join(collection))

    print(yaml.dump(sorted(list(collections))))

if __name__ == '__main__':
    main()
