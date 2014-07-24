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
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

import requests

from blackdog import PluginVersion, BlackDogException


class HTTPServer(TCPServer):

    def __init__(self, port):
        super().__init__(("", port), RequestHandler, bind_and_activate=False)
        from blackdog import BlackDog
        self.blackdog = BlackDog.instance
        self.port = port

    def __enter__(self):
        self.server_bind()
        self.server_activate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.server_close()


def pattern(pattern):
    def decorator(func):
        func.pattern = pattern
        return func
    return decorator


class RequestHandler(SimpleHTTPRequestHandler):

    def get_groupid(self):
        return '.'.join(self.path.split('/')[1:-3])

    def handle_pattern(self, path, *args, **kwargs):
        handles = []
        for m in [m for m in [getattr(self, m) for m in dir(self)] if hasattr(m, 'pattern')]:
            handles.append((m.pattern, m))

        for p, m in handles:
            if re.match(p, path):
                m(*args, **kwargs)
                return True
        return False

    def handle_text(self, content, mime='text/plain'):
        if not content:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header('Content-type', mime)
        self.send_header('Content-length', len(content))
        self.end_headers()
        self.wfile.write(content.encode('ascii'))

    @pattern(r'.*\.jar$')
    def handle_jar(self, version: PluginVersion):
        if not version.url():
            self.send_response(404)
            self.end_headers()
            return

        r = requests.get(version.url(), stream=True)
        if r.status_code != 200:
            self.send_response(404)
            self.end_headers()
            r.close()
            return

        self.send_response(200)
        self.send_header('Content-type', 'application/java-archive')
        self.send_header('Content-length', r.headers['content-length'])
        self.end_headers()

        if not version.sha1():
            sha1 = hashlib.sha1()
            for chunk in r.iter_content(16 * 1024):
                self.wfile.write(chunk)
                sha1.update(chunk)
            version.sha1(sha1.hexdigest())
            self.server.blackdog.bukkitdev.save_plugin(version.get_plugin())
        else:
            for chunk in r.iter_content(16 * 1024):
                self.wfile.write(chunk)

    @pattern(r'.*\.pom$')
    def handle_pom(self, version: PluginVersion):
        self.handle_text(version.get_pom(self.get_groupid()), mime='text/xml')

    @pattern(r'.*\.jar.sha1$')
    def handle_jar_sha1(self, version: PluginVersion):
        self.handle_text(version.sha1)

    @pattern(r'.*\.jar.md5$')
    def handle_jar_md5(self, version: PluginVersion):
        self.handle_text(version.md5)

    @pattern(r'.*\.pom.sha1$')
    def handle_pom_sha1(self, version: PluginVersion):
        self.handle_text(version.get_pom_sha1(self.get_groupid()))

    @pattern(r'.*\.pom.md5$')
    def handle_pom_md5(self, version: PluginVersion):
        self.handle_text(version.get_pom_md5(self.get_groupid()))

    def do_GET(self):
        from blackdog import BlackDog
        blackdog = BlackDog.instance

        try:
            dir_path = self.path.split('/')[:-1]
            plugin_version = dir_path[-1]
            plugin_name = dir_path[-2]
        except:
            self.send_response(404)
            self.end_headers()
            return

        try:
            plugin = blackdog.bukkitdev.get_plugin(plugin_name, no_query=True)
            if not plugin.has_version(plugin_version) or not plugin.get_version(plugin_version).can_download():
                plugin = blackdog.bukkitdev.get_plugin(plugin_name, version=plugin_version)

            version = plugin.get_version(plugin_version)

            if not self.handle_pattern(self.path, version):
                self.send_response(404)
                self.end_headers()

        except BlackDogException as e:
            blackdog.logger.error(e.message)
            self.send_response(404)
            self.end_headers()
        except Exception as e:
            blackdog.logger.exception(e)
            self.send_response(404)
            self.end_headers()