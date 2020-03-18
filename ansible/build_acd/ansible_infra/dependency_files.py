# coding: utf-8
# Author: Toshio Kuratomi <tkuratom@redhat.com>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Build dependency files list the dependencies of an ACD release along with the
versions that are compatible with that release.

When we initially build an ACD major release, we'll use certain versions of collections.
We don't want to install backwards incompatible collections until the next major ACD release.
"""


class InvalidFileFormat(Exception):
    pass


def parse_build_file(build_file):
    """
    Parse the build from a dependency file
    """
    deps = {}
    ansible_base_version = acd_version = None
    with open(build_file, 'r') as f:
        for line in f:
            record = line.strip().split(':', 1)

            if record[0] == '_acd_version':
                if acd_version is not None:
                    raise InvalidFileFormat(f'{build_file} specified _acd_version more than once')
                acd_version = record[1]
                continue

            if record[0] == '_ansible_base_version':
                if ansible_base_version is not None:
                    raise InvalidFileFormat(f'{build_file} specified _ansible_base_version more'
                                            ' than once')
                ansible_base_version = record[1]
                continue

            versions = record[1].split(',')
            deps[record[0]] = versions

    if ansible_base_version is None or acd_version is None:
        raise InvalidFileFormat(f'{build_file} was invalid.  It did not contain required fields')

    return acd_version, ansible_base_version, deps


def write_build_file(build_file, acd_version, ansible_base_version, dependencies):
    """
    Write a build dependency file

    """
    with open(build_file, 'w') as f:
        f.write(f'_acd_version:{acd_version}\n')
        f.write(f'_ansible_base_version:{ansible_base_version[0]}\n')
        for dep, version in dependencies.items():
            major_ver = version.major
            next_major_ver = major_ver + 1
            f.write(f'{dep}:>={major_ver}.0.0,<{next_major_ver}.0.0\n')


