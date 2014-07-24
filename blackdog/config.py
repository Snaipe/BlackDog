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
import re
from configparser import ConfigParser
from enum import Enum
from functools import wraps


def config_node(node, type=str, section=None):
    def decorator(fun):
        config_field = '__config__' + re.sub(r'[^a-zA-Z0-9_]', '_', node)

        @wraps(fun)
        def wrapper(self, *args, **kwargs):
            if len(args) == 1:
                setattr(self, config_field, args[0])
            elif 'value' in kwargs:
                setattr(self, config_field, kwargs['value'])
            else:
                if not hasattr(self, config_field) or 'default' in kwargs and kwargs['default']:
                    ret = fun(self)
                    return ret

                return getattr(self, config_field)

        wrapper.config_node = node
        wrapper.config_type = type
        wrapper.config_section = section

        return wrapper
    return decorator


def load(config: ConfigParser, obj, section):
    attrs = [(f, getattr(obj, f)) for f in dir(obj)]
    for name, method in [(n, m) for (n, m) in attrs if callable(m) and hasattr(m, 'config_node')]:
        real_section = method.config_section if method.config_section else section
        val = config.get(real_section, method.config_node, fallback=None)

        if val:
            if method.config_type == list:
                val = [e.strip() for e in val.split(',')]
            elif method.config_type == bool:
                try:
                    val = config.getboolean(real_section, method.config_node, fallback=None)
                except ValueError:
                    val = None
            elif issubclass(method.config_type, Enum):
                val = method.config_type.from_string(val)

            method(val)
        else:
            method(method(default=True))


def save(config: ConfigParser, obj, section):
    attrs = [(f, getattr(obj, f)) for f in dir(obj)]
    nodes = [(n, m) for (n, m) in attrs if callable(m) and hasattr(m, 'config_node')]
    for name, method in nodes:
        real_section = method.config_section if method.config_section else section
        val = method()

        if val:
            if method.config_type == list:
                val = ', '.join(val)
            elif isinstance(val, Enum):
                val = val.name
            else:
                val = str(val)

            if not config.has_section(real_section):
                config.add_section(real_section)
            config.set(real_section, method.config_node, val)