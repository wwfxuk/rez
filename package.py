name = 'rez'
version = 'rc.2.0.rc1.39.mikros1.0'

requires = ['python-2.7'] # for logging

def commands():
    env.PYTHONPATH.append('{root}/src')

