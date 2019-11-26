#!/usr/bin/python3 -tt
import itertools
import os
import pathlib
import sys
from pprint import pprint
from collections import defaultdict
from collections.abc import Mapping, Sequence

import requests
import yaml
from six import string_types
from ansible.parsing.dataloader import DataLoader


# Tests for core features
CORE_FEATURE_TARGETS = frozenset((
    'ansiballz_python',
    'ansible',
    'ansible-doc',
    'ansible-galaxy',
    'ansible-runner',
    'any_errors_fatal',
    'args',
    'async',
    'async_extra_data',
    'async_fail',
    'become',
    'binary',
    'binary_modules',
    'binary_modules_posix',
    'blocks',
    'callback_default',
    'callback_retry_task_name',
    'changed_when',
    'check_mode',
    'cli',
    'collections_plugin_namespace',
    'collections_relative_imports',
    'command_shell',
    'collections',
    'conditionals',
    'config',
    'connection',
    'connection_local',
    'connection_paramiko_ssh',
    'connection_posix',
    'connection_ssh',
    'setup_deb_repo',  # needed by apt
    'delegate_to',
    'embedded_module',
    'environment',
    'error_from_connection',
    'facts_d',
    'failed_when',
    'filters',
    'gathering',
    'gathering_facts',
    'groupby_filter',
    'handlers',
    'hash',
    'hosts_field',
    'ignore_errors',
    'ignore_unreachable',
    'include_import',
    'include_parent_role_vars',
    'includes',
    'interpreter_discovery_python',
    'inventory',
    'inventory_limit',
    'inventory_path_with_comma',
    'inventory_plugin_config',
    'inventory_yaml',
    'iterators',
    'jinja2_native_types',
    'lookup_inventory_hostnames',
    'lookups',
    'lookup_paths',  # Testing the file lookup
    'loop_control',
    'loops',
    'meta_tasks',
    'module_defaults',
    'module_precedence',
    'module_tracebacks',
    'module_utils',
    'no_log',
    'old_style_cache_plugins',
    'old_style_modules_posix',
    'omit',
    'order',
    'parsing',
    'plugin_filtering',
    'plugin_loader',
    'plugin_namespace',
    'prepare_http_tests',  # For uri
    'pull',
    'rel_plugin_loading',
    'remote_tmp',
    'remote_tmp_dir',
    'roles',
    'run_modules',
    'setup_cron',  # cron is in minimal
    'setup_epel',  # setup_rpm_repo
    'setup_nobody',
    'setup_paramiko',  # Because the paramiko connection plugin is currently in minimal
    'setup_passlib',   # For vars_prompt
    'setup_pexpect',
    'setup_remote_constraints',  # For uri
    'setup_remote_tmp_dir',  # For remote_tmp_dir test
    'setup_rpm_repo',  # dnf and yum
    'special_vars',
    'strategy_linear',
    'tags',
    'task_ordering',
    'template_jinja2_latest',
    'templating_settings',
    'test_infra',
    'tests',
    'throttle',
    'unicode',
    'until',
    'var_blending',
    'var_precedence',
    'var_templating',
    'vars_prompt',
    'vault',
    'want_json_modules_posix',
    'windows-paths',
))


SPECIAL_CASES = {
    'virt_net': ['virt_net'],
    'vsphere_file': ['vmware'],
    'vcenter_folder': ['vmware'],
    'vcenter_license': ['vmware'],
    'setup_tls': ['rabbitmq', 'mqtt'],
    'setup_win_device': ['win'],
    'setup_win_psget': ['win'],
    'prepare_win_tests': ['win'],
    'setup_wildfly_server': ['jboss'],
    'setup_sshkey': ['aws', 'hcloud'],
    'setup_ssh_keygen': ['openssh'],
    'read_csv': ['read_csv'],
    'python_requirements_info': ['python_requirements_info'],
    'prepare_tests': [],  # Empty main.yml.  Skip
    'prepare_ios_tests': ['ios'],
    'prepare_iosxr_tests': ['iosxr'],
    'prepare_junos_tests': ['junos'],
    'prepare_nios_tests': ['nios'],
    'prepare_nuage_tests': ['nuage'],
    'prepare_nxos_tests': ['nxos'],
    'prepare_ovs_tests': ['openvswitch'],
    'prepare_sros_tests': ['netconf'],
    'prepare_vmware_tests': ['vmware'],
    'prepare_vyos_tests': ['vyos'],
    'setup_postgresql_replication': ['postgresql'],
    'setup_postgresql_db': ['postgresql'],
    'osx_defaults': ['osx_defaults'],
    'setup_opennebula': ['one_host'],
    'one_host': ['one_host'],
    'setup_mysql_replication': ['mysql'],
    'setup_mysql_db': ['mysql'],
    'setup_mysql8': ['mysql'],
    'setup_mosquitto': ['mqtt'],
    'locale_gen': ['locale_gen'],
    'listen_ports_facts': ['listen_ports_facts'],
    'known_hosts': ['known_hosts'],
    'java_cert': ['java_cert'],
    'iso_extract': ['iso_extract'],
    'ipify_facts': ['ipify_facts'],
    'inventory_vmware_vm_inventory': ['vmware'],
    'inventory_docker_swarm': ['docker'],
    'inventory_docker_machine': ['docker'],
    'inventory_cloudscale': ['cloudscale'],
    'ini_file': ['ini_file'],
    'github_issue': ['github_issue'],
    'git_config': ['git_config'],
    'get_certificate': ['crypto'],
    'setup_flatpak_remote': ['flatpak'],
    'deploy_helper': ['deploy_helper'],
    'connection_winrm': ['win'],
    'connection_windows_ssh': ['win'],
    'connection_psrp': ['win'],
    'connection_podman': ['podman'],
    'connection_docker': ['docker'],
    'cloud_init_data_facts': ['cloud_init'],
    'certificate_complete_chain': ['crypto'],
    'binary_modules_winrm': ['win'],
    'authorized_key': ['authorized_key'],
    'apache2_module': ['apache2_module'],
    'docker-registry': ['docker'],
    'cronvar': ['cron'],
    'synchronize-buildah': ['synchronize'],
}


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
                            #mrefs.add('block')
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
                            if isinstance(task['action'], Mapping):
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
                                module = task['action']
                                if module.startswith('{{'):
                                    # action: {{ ansible_pkg_mgr }}
                                    module = module.split('}}')[0]
                                    module = module.replace('{{', '')
                                    module = module.strip()
                                elif ' ' in module:
                                    module = module.split()[0].strip()
                                else:
                                    import epdb; epdb.st()
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


def get_minimal_set():
    url = 'https://raw.githubusercontent.com/ansible-community/collection_migration/master/scenarios/minimal/ansible.yml'
    data = requests.get(url)

    parsed_data = yaml.safe_load(data.text)

    return parsed_data['_core']
def format_tasks(tasks):
    return (os.path.splitext(os.path.basename(t))[0] for t in tasks)


def get_minimal_tasks(minimal_plugins):
    minimal_actions = minimal_plugins['action']
    minimal_modules = minimal_plugins['modules']
    minimal_tasks = frozenset(itertools.chain(format_tasks(minimal_actions), format_tasks(minimal_modules)))
    return minimal_tasks


def which_groups(target, core_targets):
    """
    Return the groups a target belongs to
    """
    # The first conditions are all special cases
    if target in SPECIAL_CASES:
        return SPECIAL_CASES[target]
    elif target.startswith('digital_'):
        return ['digital_ocean']
    elif target.startswith('sts_'):
        return ['aws']
    elif target.startswith('sqs_'):
        return ['aws']
    elif target.startswith('s3_'):
        return ['aws']
    elif target.startswith('rds_'):
        return ['aws']
    elif target.startswith('lambda_'):
        return ['aws']
    elif target.startswith('inventory_aws_'):
        return ['aws']
    elif target.startswith('iam_'):
        return ['aws']
    elif target.startswith('elb_'):
        return ['aws']
    elif target.startswith('ecs_'):
        return ['aws']
    elif target.startswith('ec2_'):
        return ['aws']
    elif target.startswith('dms_'):
        return ['aws']
    elif target in ('sns', 'sns_topic'):
        return ['aws']
    elif target == 'setup_ec2':
        return ['aws']
    elif target == 'route53':
        return ['aws']
    elif False:
        # These are other potential special cases but I'm not sure how to deal with them:
        #
        # lookup_properties (?) uses ini lookup plugin but is that what it's testing(?)
        # lookup_passwordstore (?)
        # lookup_lmdb_kv
        # lookup_hashi_vault
        # netconf_config netconf_get netconf_rpc (?) netconf is a plugin type but all of these
        #   tests require a specific device (junos, iosxr sros)
        # inventory_kubevirt_conformance
        # inventory_foreman_script
        # inventory_foreman
        # connection_lxd
        # connection_lxc
        # connection_libvirt_lxc
        # connection_jail
        # connection_chroot
        # connection_buildah
        # callback_log_plays
        pass
    elif target in CORE_FEATURE_TARGETS:
        # test targets for core features (vars_prompt, strategy)
        return ['_core']
    elif target in core_targets:
        # The minimal set
        return ['_core']
    elif target.startswith('setup_'):
        return [target[6:]]
    elif target.startswith('prepare_'):
        return [target[8:]]
    elif '_' in target:
        subject = target.index('_')
        return [target[:subject]]
    else:
        return [target]

def get_groups_of_tests(integration_dir, core_targets):
    target_dir = os.path.join(integration_dir, 'targets')

    groups = defaultdict(set)
    for directory in os.listdir(target_dir):
        # The first conditions are all special cases
        directory_groups = which_groups(directory, core_targets)
        for group in directory_groups:
            groups[group].add(os.path.join(target_dir, directory))

    return groups




def main():
    # get tasks (modules and actions) in the minimal set
    minimal_plugins = get_minimal_set()
    minimal_tasks = get_minimal_tasks(minimal_plugins)

    groups = get_groups_of_tests(sys.argv[1], minimal_tasks)

    # for each of the targets in the integration tests, figure out what modules are used.
    modules = defaultdict(set)
    for group, test_targets in groups.items():
        for target in test_targets:
            for root, _dummy, files in os.walk(target):
                root = pathlib.Path(root)
                for potential_file in files:
                    if not (potential_file.endswith('.yml') or potential_file.endswith('.yaml')):
                        continue

                    with open(root / potential_file) as f:
                        try:
                            data = DataLoader().load(f.read())
                        except Exception:
                            print('Error while parsing yaml file %s' % (root / potential_file))
                            raise

                    new_modules = parse_yaml_for_modules(data)
                    modules[group].update(new_modules)

    for group_name, task_list in modules.items():
        # Filter out modules already in minimal
        task_list.difference_update(minimal_tasks)

        # Filter out modules we're testing
        tested_modules = set()
        for task in task_list:
            groups = which_groups(task, minimal_tasks)
            if group_name in groups:
                tested_modules.add(task)
        task_list.difference_update(tested_modules)

    # Filter out empty groups [no cross-group deps]
    modules = {k: v for k, v in modules.items() if v}
    # print a report
    pprint(modules)


if __name__ == '__main__':
    main()
