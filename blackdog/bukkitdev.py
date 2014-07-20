"""
BlackDog

Copyright (C) 2014 Snaipe, Ojukashi

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import logging
import re

from configparser import ConfigParser
from enum import Enum
from pyquery import PyQuery


class Plugin(object):
    def __init__(self, name):
        self.name = name
        self.path_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)
        self.summary = None
        self.stage = None
        self.display = None
        self.versions = {}
        self.exists = None

    def add_version(self, version):
        self.versions[version.version] = version

    def _get_config(self, directory):
        from os.path import join
        return join(directory, self.path_name + '.data')

    def load(self, directory):
        """
        Loads all available plugin metadata from cache
        :param directory: the cache root directory
        :return: the plugin itself
        """
        config = ConfigParser()
        config.read(self._get_config(directory))

        self.stage = PluginStage.from_string(config.get('plugin', 'stage', fallback=None))
        self.display = config.get('plugin', 'display', fallback=None)
        self.exists = config.get('plugin', 'exists', fallback=None)

        for section in [s for s in config.sections() if s != 'plugin']:
            version = PluginVersion(self, section)
            version.url = config.get(section, 'url', fallback=None)
            version.sha1 = config.get(section, 'sha1', fallback=None)
            version.md5 = config.get(section, 'md5', fallback=None)
            self.versions[section] = version

        return self

    @staticmethod
    def _set_if_exists(config, section, option, value):
        if value:
            if not config.has_section(section):
                config.add_section(section)
            config.set(section, option, value)

    def save(self, directory):
        """
        Saves all available plugin metadata to cache
        :param directory: the cache root directory
        :return: the plugin itself
        """
        config = ConfigParser()
        self._set_if_exists(config, 'plugin', 'stage', self.stage.name)
        self._set_if_exists(config, 'plugin', 'display', self.display)
        self._set_if_exists(config, 'plugin', 'exists', self.exists)

        for version in self.versions:
            self._set_if_exists(config, version.version, 'url', version.url)
            self._set_if_exists(config, version.version, 'sha1', version.sha1)
            self._set_if_exists(config, version.version, 'md5', version.md5)

        with open(self._get_config(directory), 'w') as fd:
            config.write(fd)

        return self


class PluginVersion(object):
    def __init__(self, plugin, version):
        self.plugin = plugin
        self.version = version
        self.url = None
        self.sha1 = None
        self.md5 = None


class PluginStage(Enum):
    planning = 'p'
    alpha = 'a'
    beta = 'b'
    release = 'r'
    mature = 'm'
    inactive = 'i'
    abandoned = 'x'
    deleted = 'd'

    @classmethod
    def from_string(cls, string):
        return getattr(PluginStage, string.lower(), None)


class BukkitDev(object):

    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        self.base = 'http://dev.bukkit.org'
        self.logger = logging.getLogger('BukkitDev')

    def _fill_plugin_meta(self, plugin):
        # TODO: analyze the html and set the plugin's url, and whenever it exists or not.

        plugin.save(self.cache_dir)

    @staticmethod
    def _to_post_arg(args):
        """
        Transforms a dictionary to POST parameters:
        {a: 1, b: '2', c='a b'} -> 'a=1&b=2&c=a+b'
        :param args: the dictionary to transform
        :return: the POST parameters
        """
        arg_list = []
        for key, value in args.items():
            arg_list.append(key + '=' + re.sub(r'[ \t\r\n]+', '+', str(value)))
        return '&'.join(arg_list)

    def get_plugin(self, name, no_query=False):
        """
        Gets a plugin info from its name and version
        :param name: the plugin name
        :param version: the plugin version
        :return: the plugin
        """

        plugin = Plugin(name).load(self.cache_dir)

        if not no_query and plugin.exists is not None:
            self._fill_plugin_meta(plugin)

        return plugin

    def search(self, **kwargs):
        """
        Searchs for a plugin
        :param search: the query string
        :param page: the result page number, first page by default
        :param category: the plugin category, or all categories if None
        :param stage: the development stage
        :return: a list of matching plugins
        """

        results = []
        page_content = PyQuery(url='/'.join([self.base, 'bukkit-plugins', '?%s' % self._to_post_arg(kwargs)]))
        plugin_table = page_content('#bd .line .unit .listing-container .listing-container-inner table tbody tr')

        for (info, summary) in zip(plugin_table[::2], plugin_table[1::2]):
            info = PyQuery(info)
            plugin = Plugin(name=info('td.col-project h2 a').attr('href').split('/')[2])
            plugin.stage = PluginStage.from_string(info('td.col-status').text())
            plugin.summary = PyQuery(summary)('td.summary').text()
            results.append(plugin)

        return results

    def scan(self, stages=None):
        if not stages:
            stages = [PluginStage.release, PluginStage.mature]

        self.logger.info('Scanning http://dev.bukkit.org/...')
        for stage in stages:
            self.logger.info('Processing plugins for stage \'%s\'', stage.name)
            page = 0
            more = True
            while more:
                self.logger.info('processing page %s...', page)
                plugins = self.search(stage=stage.value, page=page)
                for plugin in plugins:
                    try:
                        self._fill_plugin_meta(plugin)
                    except Exception:
                        self.logger.error('Could not process plugin %s', plugin.name)

                more = len(plugins) > 0
                page += 1