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
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from urllib.request import URLopener
import requests


class HTTPServer(object):

    def __init__(self, port):
        self.port = port

    def __enter__(self):
        self.server = TCPServer(("", self.port), RequestHandler)
        return self.server

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.server.server_close()


class RequestHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from blackdog import BlackDog
        self.blackdog = BlackDog.instance()

    def do_GET(self):

        dir_path = self.path.split('/')[:-1]

        plugin_version = dir_path[-1]
        plugin_name = dir_path[-2]

        plugin = self.blackdog.bukkitdev.get_plugin(plugin_name)
        version = plugin.get_version(plugin_version)

        if self.path.endswith('.jar'):
            r = requests.head(version.url)

            pass
        if self.path.endswith('.jar.sha1'):
            pass
        if self.path.endswith('.jar.md5'):
            pass
        if self.path.endswith('.pom'):
            pass
        if self.path.endswith('.pom.sha1'):
            pass
        if self.path.endswith('.pom.md5'):
            pass
        pass