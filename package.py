# -*- coding: utf-8 -*-

__version__ = '2.23.1'

name = 'rez_install'

version = __version__ + '+wwfx.1.0.0'

description = 'Cross-platform package manager with a difference.'

authors = ['Allan Johns']

variants = [['python-2']]

tools = ['rez']

requires = ['future', 'qt_py']


build_command = r'''
set -euf -o pipefail

curl -L https://github.com/nerdvegas/rez/archive/{version}.tar.gz | tar xz

if [[ $REZ_BUILD_INSTALL -eq 1 ]]
then
    python rez-{version}/install.py $REZ_BUILD_INSTALL_PATH
fi

'''.format(version=__version__)
