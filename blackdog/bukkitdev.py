"""
Tequila: a command-line Minecraft server manager written in python

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
import os


class Plugin(object):

    def __init__(self, name, version=None):
        self.name = name
        self.version = version
        self.url = None
        self.sha1 = None
        self.md5 = None
        self.exists = None

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


class BukkitDev(object):

    def __init__(self):
        self.cache_dir = os.path.expanduser('~/.blackdog/')

    def _fill_plugin_meta(self, plugin):
        # TODO: analyze the html and set the plugin's url, and whenever it exists or not.

        plugin.save(self.cache_dir)

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

    def search(self, query, page=1, category=None):
        """
        Searchs for a plugin, from
        :param query: the query string
        :param page: the result page number, first page by default
        :param category: the plugin category, or all categories if None
        :return: a list of matching plugins
        """

        results = [] # TODO: fill with results

        return results