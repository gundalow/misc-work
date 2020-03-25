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


def parse_pieces_file(pieces_file):
    with open(pieces_file, 'r') as f:
        # One collection per line, ignoring comments and empty lines
        collections = [c.strip() for line in f.readlines()
                       if (c := line.strip()) and not c.startswith('#')]
    return collections


def write_deps_file(deps_file, acd_version, ansible_base_version, included_versions):
    """Write a list of all the dependent collections included in this ACD release"""
    records = []
    for dep, version in included_versions.items():
        records.append(f'{dep}: {version}')
    records.sort()

    with open(deps_file, 'w') as f:
        f.write(f'_acd_version: {acd_version}\n')
        f.write(f'_ansible_base_version: {ansible_base_version[0]}\n')
        f.write('\n'.join(records))
        f.write('\n')


class BuildFile:
    def __init__(self, build_file):
        self.filename = build_file

    def parse(self):
        """
        Parse the build from a dependency file
        """
        deps = {}
        ansible_base_version = acd_version = None
        with open(self.filename, 'r') as f:
            for line in f:
                record = [entry.strip() for entry in line.split(':', 1)]

                if record[0] == '_acd_version':
                    if acd_version is not None:
                        raise InvalidFileFormat(f'{self.filename} specified _acd_version'
                                                ' more than once')
                    acd_version = record[1]
                    continue

                if record[0] == '_ansible_base_version':
                    if ansible_base_version is not None:
                        raise InvalidFileFormat(f'{self.filename} specified _ansible_base_version'
                                                ' more' ' than once')
                    ansible_base_version = record[1]
                    continue

                deps[record[0]] = record[1]

        if ansible_base_version is None or acd_version is None:
            raise InvalidFileFormat(f'{self.filename} was invalid.  It did not contain'
                                    ' required fields')

        return acd_version, ansible_base_version, deps

    def write(self, acd_version, ansible_base_version, dependencies):
        """
        Write a build dependency file

        """
        records = []
        for dep, version in dependencies.items():
            records.append(f'{dep}: >={version.major}.0.0,<{version.next_major()}')
        records.sort()

        with open(self.filename, 'w') as f:
            f.write(f'_acd_version: {acd_version.major}.{acd_version.minor}\n')
            f.write(f'_ansible_base_version: {ansible_base_version}\n')
            f.write('\n'.join(records))
            f.write('\n')
