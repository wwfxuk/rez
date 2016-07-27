name = 'rez'
version = 'rc.20160619_master.mikros1.0'

requires = ['python-2.7'] # for logging

def commands():
    env.PYTHONPATH.append('{root}/src')

