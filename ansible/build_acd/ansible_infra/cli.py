#!/usr/bin/python3 -tt
# coding: utf-8
# Author: Toshio Kuratomi <tkuratom@redhat.com>
# License: GPLv3+
# Copyright: Ansible Project, 2020


import argparse
import asyncio
import os.path
import sys
from urllib.parse import urljoin

import aiohttp
import semantic_version as semver

from .dependency_files import InvalidFileFormat, write_build_file, parse_build_file
from .galaxy import GalaxyClient#, get_best_versions


PIECES_FILE = 'acd.in'
BUILD_FILE_TMPL = os.path.splitext(PIECES_FILE)[0] + '-{acd_version}.build'
DEPS_FILE_TMPL = os.path.splitext(PIECES_FILE)[0] + '-{acd_complete_version}.lst'

PYPI_SERVER_URL = 'https://test.pypi.org/'
GALAXY_SERVER_URL = 'https://galaxy.ansible.com/'


def parse_args(program_name, args):
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument('acd_version',
                               help='The version of ACD that this will be for')

    parser = argparse.ArgumentParser(prog=program_name,
                                     description='Script to manage building ACD')
    subparsers = parser.add_subparsers(title='Subcommands', dest='command',
                                       help='for help use build-acd.py SUBCOMMANDS -h')

    new_parser = subparsers.add_parser('new-acd', parents=[common_parser],
                                       description='Generate a new build description from the'
                                       ' latest available versions of ansible-base and the'
                                       ' included collections')

    build_single_parser = subparsers.add_parser('build-single', parents=[common_parser],
                                                description='Build a single-file ACD')

    build_multiple_parser = subparsers.add_parser('build-multiple', parents=[common_parser],
                                                  description='Build a multi-file ACD')

    args = parser.parse_args(args)

    #
    # Validation
    #
    if args.command is None:
        print('Please specify a subcommand to run')
        sys.exit(2)

    return args


def parse_pieces(pieces_file):
    with open(pieces_file, 'r') as f:
        # One collection per line, ignoring comments and empty lines
        collections = [c.strip() for line in f.readlines()
                       if (c := line.strip()) and not c.startswith('#')]
    return collections


async def get_ansible_base_version(aio_session, pypi_server_url=PYPI_SERVER_URL):
    # Retrieve the ansible-base package info from pypi
    query_url = urljoin(pypi_server_url, 'pypi/ansible-base/json')
    async with aio_session.get(query_url) as response:
        pkg_info = await response.json()

    # Calculate the newest version of the package
    return [pkg_info['info']['version']]


def display_exception(loop, context):
    print(context.get('exception'))


async def get_version_info(collections):
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(display_exception)
    requestors = {}
    async with aiohttp.ClientSession() as aio_session:
        requestors['_ansible_base'] = asyncio.create_task(get_ansible_base_version(aio_session))
        galaxy_client = GalaxyClient(GALAXY_SERVER_URL, aio_session)

        for collection in collections:
            requestors[collection] = asyncio.create_task(
                galaxy_client.get_collection_version_info(collection))

        collection_versions = {}
        for collection_name, request in requestors.items():
            await request
            collection_versions[collection_name] = request.result()

    return collection_versions


def version_is_compatible(ansible_base_version, collection, version):
    # Metadata for this is not currently implemented.  So everything is rated as compatible
    return True


def find_latest_compatible(ansible_base_version, raw_dependency_versions):
    # Note: ansible-base compatibility is not currently implemented.  It will be a piece of
    # collection metadata that is present in the collection but may not be present in galaxy.  We'll
    # have to figure that out once the pieces are finalized

    # Order versions
    reduced_versions = {}
    for dep, versions in raw_dependency_versions.items():
        # Order the versions
        versions = [semver.Version(v) for v in versions]
        versions.sort(reverse=True)

        # Step through the versions to select the latest one which is compatible
        for version in versions:
            if version_is_compatible(ansible_base_version, dep, version):
                reduced_versions[dep] = version
                break

    return reduced_versions


def new_acd(args):
    collections = parse_pieces(PIECES_FILE)
    dependencies = asyncio.run(get_version_info(collections))

    ansible_base_version = dependencies.pop('_ansible_base')
    dependencies = find_latest_compatible(ansible_base_version, dependencies)

    build_file = BUILD_FILE_TMPL.format(acd_version=args.acd_version)
    write_build_file(build_file, args.acd_version, ansible_base_version, dependencies)

    return 0


async def download_collections(deps):
    requestors = []
    async with aiohttp.ClientSession() as aio_session:
        for collection_name, version_spec in deps:
            requestors.append(asyncio.create_task(download_collection(name, version_spec)))

    await asyncio.gather(requestors)


def build_single(args):
    build_file = BUILD_FILE_TMPL.format(acd_version=args.acd_version)
    acd_version, ansible_base_version, deps = parse_build_file(build_file)

    with tempfile.TemporaryDirectory() as download_dir:
        asyncio.run(download_collections(concrete_deps, download_dir))
        install_collections(download_dir, install_path)
        write_out_setup()
        make_dist()

    return 0


def build_multiple(args):
    raise NotImplemented('build_multiple is not yet implemented')
    pass


ARGS_MAP = {'new-acd': new_acd,
            'build-single': build_single,
            'build-multiple': build_multiple,
            }


def main(args):
    program_name = os.path.basename(args[0])
    args = parse_args(program_name, args[1:])

    return ARGS_MAP[args.command](args)
