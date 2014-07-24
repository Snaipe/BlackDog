"""
BlackDog

Copyright (C) 2014 Snaipe, Therozin

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
import hashlib
import re
from configparser import ConfigParser
from enum import Enum
from string import Template

from blackdog import NoSuchPluginVersionException
from blackdog.config import load, save, config_node


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
        return getattr(PluginStage, string.lower(), None) if string else None


class Plugin(object):
    def __init__(self, name):
        self.name = name
        self.path_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name)
        self.versions = {}

    @config_node('summary')
    def summary(self):
        return None

    @config_node('display-name')
    def display_name(self):
        return self.name

    @config_node('stage')
    def stage(self):
        return None

    @config_node('exists', type=bool)
    def exists(self):
        return None

    def add_version(self, version):
        self.versions[version.get_version()] = version

    def get_version(self, version):
        try:
            return self.versions[version]
        except KeyError as e:
            raise NoSuchPluginVersionException(e.args[0])

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

        load(config, self, 'plugin')
        for section in [s for s in config.sections() if s != 'plugin']:
            version = PluginVersion(self, section)
            load(config, version, section)
            self.versions[section] = version

        return self

    def save(self, directory):
        """
        Saves all available plugin metadata to cache
        :param directory: the cache root directory
        :return: the plugin itself
        """
        config = ConfigParser()

        save(config, self, 'plugin')
        for vstr, version in self.versions.items():
            save(config, version, vstr)

        with open(self._get_config(directory), 'w') as fd:
            config.write(fd)

        return self


class PluginVersion(object):
    __POM_BASE = """
        <project xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
            <modelVersion>4.0.0</modelVersion>
            <groupId>${groupid}</groupId>
            <artifactId>${artifactid}</artifactId>
            <version>${version}</version>
        </project>
        """

    def __init__(self, plugin: Plugin, version):
        if not version or not plugin:
            raise ValueError('plugin or version cannot be None')
        self.__plugin = plugin
        self.__version = version

    @config_node('url')
    def url(self):
        return None

    @config_node('sha1')
    def sha1(self):
        return None

    @config_node('md5')
    def md5(self):
        return None

    @config_node('date')
    def date(self):
        return None

    @config_node('stage', type=PluginStage)
    def stage(self):
        return None

    @config_node('game-versions', type=list)
    def game_versions(self):
        return None

    def get_version(self):
        return self.__version

    def get_plugin(self):
        return self.__plugin

    def get_pom(self, groupid):
        return Template(PluginVersion.__POM_BASE).substitute(
            groupid=groupid,
            artifactid=self.__plugin.name,
            version=self.__version
        )

    def __get_pom_hash(self, groupid, hash):
        hash.update(self.get_pom(groupid))
        return hash.digest()

    def get_pom_md5(self, groupid):
        return self.__get_pom_hash(groupid, hashlib.md5())

    def get_pom_sha1(self, groupid):
        return self.__get_pom_hash(groupid, hashlib.sha1())