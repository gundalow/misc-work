#!/usr/bin/python3 -tt
import os
import pathlib
import sys
from pprint import pprint
from collections.abc import Mapping, Sequence

from six import string_types
from ansible.parsing.dataloader import DataLoader

def parse_yaml_for_modules(ydata):

    keywords = ['args', 'beome', 'become', 'bocome_users', 'become_user',
                'name',
                'register', 'regrister', 'any_errors_fatal', 'change_when',
                'update_cache', 'warn', 'validate',
                'become_method', 'accelerate', 'max_fail_percentage',
                'delegate_facts', 'ignore_error', 'ignore_errors',
                'changed_when', 'notify', 'always_run',
                'serial', 'dependencies', 'src', 'path', 'version',
                'handlers', 'vars_files', 'ignore_errors',
                'loop_control', 'delay', 'retries', 'until',
                'hosts', 'remote_user', 'roles', 'vars', 'sudo',
                'async', 'poll', 'gather_facts', 'connection',
                'repo', 'sha', 'hooks', 'tag', 'first_available_file',
                'no_log', 'gather_facts', 'pre_tasks', 'no_log',
                'sudo_user', 'delegate_to', 'run_once', 'failed_when',
                'env', 'environment', 'tags', 'tasks', 'when', 'with_items',
                'with_flattened', 'with_dict', 'with_subelements', 'listen',
                'check_mode', 'static', 'cron_file', 'become_flags', 'items',
                'state', 'changed_when', 'wait_timeout', 'wait', 'mode',
                'update_cache']

    mrefs = set()

    if ydata:
        # skip files that are not task lists
        if not isinstance(ydata, Sequence) or isinstance(ydata, string_types):
            return mrefs

        for x in ydata:

            if not isinstance(x, Mapping):
                continue

            if x is None:
                continue

            if 'hosts' in x or 'tasks' in x or 'post_tasks' in x or 'pre_tasks' in x or 'handlers' in x:

                tasks = []
                if 'tasks' in x and x['tasks']:
                    tasks += x['tasks']
                if 'pre_tasks' in x and x['pre_tasks']:
                    tasks += x['pre_tasks']
                if 'post_tasks' in x and x['post_tasks']:
                    tasks += x['post_tasks']
                if 'handlers' in x and x['handlers']:
                    tasks += x['handlers']

            else:
                tasks = [x]

            if not tasks:
                continue

            if not isinstance(tasks, list):
                continue

            iterations = 0
            while tasks and iterations <= 100:

                iterations += 1

                for task in tasks[:]:

                    #if 'homebrew' in str(task) and 'darwin-family' in cp:
                    #    import epdb; epdb.st()

                    tasks.remove(task)

                    module = None

                    if not task:
                        continue

                    # 'include ../tasks/main.yml'
                    if not hasattr(task, 'keys'):
                        continue

                    if 'block' in task:
                        if 'block' not in mrefs:
                            mrefs.add('block')
                            tasks += task['block']
                        if 'rescue' in task:
                            tasks += task['rescue']
                        if 'always' in task:
                            tasks += task['always']
                        continue

                    keys = [k for k in task.keys() if k not in keywords]
                    keys = [k for k in keys if not k.startswith('with_')]

                    #print keys
                    if not keys:
                        continue

                    elif len(keys) == 1:
                        module = keys[0]

                        if module == 'action':
                            module = task[module]
                            if isinstance(module, dict) and 'module' in module:
                                module = module['module']
                            elif module.startswith('{{'):
                                # action: {{ ansible_pkg_mgr }}
                                module = module.split('}}')[0]
                                module = module.replace('{{', '')
                                module = module.strip()
                            elif ' ' in module:
                                module = module.split()[0].strip()
                            #else:
                            #    import epdb; epdb.st()

                        if isinstance(module, Mapping):
                            if 'module' in module:
                                module = module['module']
                            #import epdb; epdb.st()

                        if module == 'local_action':
                            if isinstance(task['local_action'], Mapping):
                                module = task['local_action']['module']
                            elif isinstance(task['local_action'], string_types):
                                module = task['local_action'].split()[0].strip()
                        if module == 'action':
                            if iinstance(task['action'], Mapping):
                                module = task['action']['module']
                            elif isinstance(task['action'], string_types):
                                module = task['action'].split()[0].strip()

                        if '{{' in module:
                            module = module.replace('{{', '')
                            module = module.replace('}}', '')

                        #if not module in mrefs:
                        #    mrefs[module] = 0
                        #mrefs[module] += 1

                    elif 'vars_prompt' in keys:
                        module = 'vars_prompt'

                    else:

                        module = None
                        if 'include' in keys:
                            module = 'include'
                        elif 'action' in keys:
                            #import epdb; epdb.st()
                            if isinstance(task['action'], Mapping):
                                module = task['action']['module']
                                #import epdb; epdb.st()
                            elif isinstance(task['action'], string_types):
                                module = task['action'].split()[0].strip()
                            else:
                                import epdb; epdb.st()
                        elif len(keys) == 1:
                            module = keys[0]

                        else:

                            known = False
                            for key in keys:
                                if key in mrefs:
                                    known = True
                                    module = key
                                    break

                            '''
                            if not known:
                                print('#    Too many keys left ...')
                                print('\t' + ','.join(keys))
                                import epdb; epdb.st()
                                module = keys[0]
                                #pass
                            '''

                    if module:
                        mrefs.add(module)

    return mrefs


def main():
    modules = set()
    for target in sys.argv[1:]:
        for root, directories, files in os.walk(target):
            root = pathlib.Path(root)
            for potential_file in files:
                if not (potential_file.endswith('.yml') or potential_file.endswith('.yaml')):
                    continue

                with open(root / potential_file) as f:
                    data = DataLoader().load(f.read())

                new_modules = parse_yaml_for_modules(data)
                modules.update(new_modules)
    pprint(modules)

if __name__ == '__main__':
    main()
