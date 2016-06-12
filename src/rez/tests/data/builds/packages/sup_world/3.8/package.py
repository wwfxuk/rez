name = 'sup_world'
version = '3.8'
authors = ["snoop.dogg"]
uuid = "040c80c135c142479d47e756bdbbddf5"
description = "A C++ executable that links to a library that is part of this " \
              "package, and a library from a different package. Word."

requires = ['translate_lib-2.2']

tools = ['test_ghetto']

def commands():
    env.PATH.append('{root}/bin')


# Copyright 2016 Allan Johns.
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