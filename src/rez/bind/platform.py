"""
Creates the system platform package.
"""
from __future__ import absolute_import
from rez.package_maker import make_package
from rez.vendor.version.version import Version
from rez.bind._utils import check_version
from rez.system import system


def bind(path, version_range=None, opts=None, parser=None):
    version = Version(system.platform)
    check_version(version, version_range)

    def post_commands():
        """Setup default XDG_* environment variables.

        https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html#variables
        """
        import os
        xdg_defaults = (
            ('XDG_DATA_HOME', ['$HOME/.local/share']),
            ('XDG_DATA_DIRS', ['/usr/local/share', '/usr/share']),
            ('XDG_CONFIG_HOME', ['$HOME/.config']),
            ('XDG_CONFIG_DIRS', ['/etc/xdg']),
            ('XDG_CACHE_HOME', ['$HOME/.cache']),
        )
        for xdg_var, defaults in xdg_defaults:
            invalid_var = undefined(xdg_var) or not str(env[xdg_var])
            paths = [] if invalid_var else str(env[xdg_var]).split(os.pathsep)
            append = len(defaults) != 1

            for default_path in defaults:
                expanded = expandvars(default_path)
                if not(default_path in paths or expanded in paths):
                    if append:
                        env[xdg_var].append(expanded)
                    else:
                        env[xdg_var] = expanded

    with make_package("platform", path) as pkg:
        pkg.version = version
        pkg.relocatable = True
        if system.platform == 'linux':
            pkg.post_commands = post_commands

    return pkg.installed_variants


# Copyright 2013-2016 Allan Johns.
#
# This library is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.
