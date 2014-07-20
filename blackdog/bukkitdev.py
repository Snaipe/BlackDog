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
from enum import Enum
from pyquery import PyQuery
import re


class Plugin(object):
    def __init__(self, name):
        self.name = name
        self.summary = None
        self.stage = None
        self.display = None
        self.versions = {}
        self.exists = None

    def add_version(self, version):
        self.versions[version.version] = version

    def load(self, directory):
        """
        Loads all available plugin metadata from cache
        :param directory: the cache root directory
        :return: the plugin itself
        """
        return self

    def save(self, directory):
        """
        Saves all available plugin metadata to cache
        :param directory: the cache root directory
        :return: the plugin itself
        """
        return self


class PluginVersion(object):
    def __init__(self, plugin, version):
        self.plugin = plugin
        self.version = version
        self.url = None
        self.sha1 = None
        self.md5 = None
        self.exists = None


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

    def get_plugin(self, name, version, no_query=False):
        """
        Gets a plugin info from its name and version
        :param name: the plugin name
        :param version: the plugin version
        :return: the plugin
        """

        plugin = Plugin(name, version).load(self.cache_dir)

        if not no_query and plugin.url is None and plugin.exists is not None:
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
            plugin = Plugin(name=Plugin(info('td.col-project h2 a').attr('href').split('/')[2]))
            plugin.stage = PluginStage.from_string(info('td.col-status').text())
            plugin.summary = PyQuery(summary)('td.summary').text()
            results.append(plugin)

        return results
