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
import logging
import re

from pyquery import PyQuery
import requests

from blackdog.plugin import Plugin, PluginStage, PluginVersion


class BukkitDev(object):

    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        self.base = 'http://dev.bukkit.org'
        self.logger = logging.getLogger('BukkitDev')

    def save_plugin(self, plugin: Plugin):
        return plugin.save(self.cache_dir)

    def load_plugin(self, plugin: Plugin):
        return plugin.load(self.cache_dir)

    def _fill_version_meta(self, version: PluginVersion, metalink):
        d = PyQuery(url=self.base + metalink)
        path = '#bd section.main .main-body .main-body-inner .line .lastUnit .content-box .content-box-inner dl'
        info = d(path).children()
        meta = dict([(PyQuery(dt).text(), PyQuery(dd)) for dt, dd in zip(info[::2], info[1::2])])

        version.md5(meta['MD5'].text())
        version.stage(meta['Type'].text())
        version.date(meta['Uploaded on'].text())
        version.game_versions([v.text() for v in meta['Game version']('ul li').items()])
        version.url(meta['Filename']('a').eq(0).attr('href'))

    def _fill_plugin_meta(self, plugin: Plugin, version=None):
        self.logger.info('Getting metadata for plugin %s...', plugin.name)
        try:
            if not requests.head('/'.join([self.base, 'bukkit-plugins', plugin.name, ''])).ok:
                plugin.exists(False)
                return

            page = 1
            while True:
                page_url = '/'.join([self.base,
                                     'bukkit-plugins',
                                     plugin.name,
                                     'files',
                                     '?page=%s' % page if page > 1 else ''])

                code = requests.head(page_url).status_code
                if code != 200:
                    break

                d = PyQuery(url=page_url)
                list = [tr for tr in d('table.listing tbody tr').items()
                        if tr('td.col-filename').text().endswith('.jar')]

                for tr in list:
                    version_str = ''
                    try:
                        version_str = re.sub(r'.*?([0-9]+(\.[0-9]+)+).*', '\\1', tr('td.col-file').text())
                        metalink = tr('td.col-file a').attr('href')
                        version_found = version == version_str or version == 'latest'
                        if metalink and version_str and (not version or version_found):
                            pversion = PluginVersion(plugin, version_str)
                            self.logger.info('\tRetrieving informations for version %s...', version_str)
                            self._fill_version_meta(pversion, metalink)
                            plugin.add_version(pversion)
                            if version_found:
                                break
                    except:
                        self.logger.error('\tCould not retrieve metadata for version %s', version_str)
                        continue
                else:
                    page += 1
                    continue
                break
        finally:
            self.save_plugin(plugin)

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

    def get_plugin(self, name, version=None, no_query=False):
        """
        Gets a plugin info from its name and version
        :param name: the plugin name
        :param version: the plugin version
        :return: the plugin
        """

        plugin = Plugin(name).load(self.cache_dir)

        if not no_query:
            self._fill_plugin_meta(plugin, version)

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
            plugin.display_name(re.sub('</?mark>', '', info('td.col-project h2 a').html()))
            plugin.stage(PluginStage.from_string(info('td.col-status').text()))
            plugin.summary(re.sub('</?mark>', '', PyQuery(summary)('td.summary').html()))

            results.append(plugin)

        return results

    def scan(self, stages=None):
        if not stages:
            stages = [PluginStage.release, PluginStage.mature]

        self.logger.info('Scanning http://dev.bukkit.org/...')
        for stage in stages:
            self.logger.info('Processing plugins for stage \'%s\'', stage.name)
            page = 1
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