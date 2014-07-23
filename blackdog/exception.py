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
from string import Template


class BlackDogException(Exception):
    def __init__(self, message, *args, **kargs):
        super().__init__(*args)
        self.message = Template(message).substitute(**kargs)


class ServerAlreadyRunningException(BlackDogException):
    def __init__(self):
        super().__init__('Server is already running')


class ServerNotRunningException(BlackDogException):
    def __init__(self):
        super().__init__('Server is not running')


class NoSuchPluginException(BlackDogException):
    def __init__(self, plugin):
        super().__init__('Plugin ${name} could not be found', plugin, name=plugin.name)


class NoSuchPluginVersionException(BlackDogException):
    def __init__(self, version):
        super().__init__('Version ${version} could not be found', version, version=version)