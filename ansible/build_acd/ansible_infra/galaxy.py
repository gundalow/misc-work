# coding: utf-8
# Author: Toshio Kuratomi <tkuratom@redhat.com>
# License: GPLv3+
# Copyright: Ansible Project, 2020

"""
Functions to work with Galaxy
"""

import asyncio
from urllib.parse import urljoin

import aiohttp


class NoSuchCollection(Exception):
    pass


class GalaxyClient:
    def __init__(self, galaxy_server, aio_session):
        self.galaxy_server = galaxy_server
        self.aio_session = aio_session
        self.params = {'format': 'json'}

    async def _get_galaxy_versions(self, galaxy_url):
        async with self.aio_session.get(galaxy_url, params=self.params) as response:
            if response.status == 404:
                raise NoSuchCollection(f'No collection found at: {galaxy_url}')
            collection_info = await response.json()

        versions = []
        for version_record in collection_info['results']:
            versions.append(version_record['version'])

        if collection_info['next']:
            versions.extend(await self._get_galaxy_versions(collection_info['next']))

        return versions

    async def get_collection_version_info(self, collection):
        collection = collection.replace('.', '/')
        galaxy_url = urljoin(self.galaxy_server, f'api/v2/collections/{collection}/versions')
        return await self._get_galaxy_versions(galaxy_url)

    async def get_best_version(self, collection, version_spec):
        galaxy_url = urljoin(self.galaxy_server, f'api/v2/collections/{collection}/')
        params = {'format': 'json'}
        async with self.aio_session.get(galaxy_url, params=params) as response:
            if response.status == 404:
                raise NoSuchCollection(f'No collection found at: {galaxy_url}')
            collection_info = await response.json()

        versions = []
        for version_record in collection_info['results']:
            versions.append(version_record['version'])

        if collection_info['next']:
            versions.extend(await self._get_galaxy_versions(collection_info['next']))

        return versions

    async def download_collection(self, collection, version_spec):
        concrete_deps = self.get_best_version(collection, version_spec)
