name = 'rez'
version = 'mikros2.7.1'

requires = ['python-2.7'] # for logging

# Mikros specific
custom = {
    'description': 'Package configuration and resolution system',
    # 'doc': 'http://docsanim.mikros.int/docs/libPkg',
    # 'wiki': 'http://wiki.mikros.int/doku.php?id=anim:dev:libpkg',
    'authors': ['gou', 'jbi'],
    'maintainers': ['gou', 'jbi'],
}


def commands():
    env.PYTHONPATH.append('{root}/src')

#    env.PATH.append('{root}/bin')
