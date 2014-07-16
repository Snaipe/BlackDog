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

import logging
import os
from blackdog.config import Config, config_node
from blackdog.exception import TequilaException
from blackdog.bukkitdev import BukkitDev
from blackdog.server import Server, HTTPServer
from blackdog.command import Commands, command, arg


class BlackDog(object):

    @classmethod
    def instance(cls):
        return cls._instance

    def __init__(self):
        self.__class__._instance = self

        logging.basicConfig(level='INFO', format="[%(name)s] %(message)s")

        self.logger = logging.getLogger('BlackDog')
        self.bukkitdev = BukkitDev()

    def main(self):
        self.start_server() # temporary
        pass

    def start_server(self, port=8140):
        with HTTPServer(port) as server:
            self.logger.info('Starting server...')
            server.serve_forever()