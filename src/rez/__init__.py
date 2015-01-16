from rez._version import _rez_version
import logging
import logging.config
import os
import sys

__version__ = _rez_version
__author__ = "Allan Johns"
__license__ = "LGPL"

module_root_path = __path__[0]

logging_conf_file = os.environ.get(
    'REZ_LOGGING_CONF',
    os.path.join(module_root_path, 'logging.conf'))
#logging.config.fileConfig(logging_conf_file, disable_existing_loggers=False)

custom = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                           datefmt='%X')

from rez.colorize import ColorizedStreamHandler
console = ColorizedStreamHandler(sys.stderr)
console.name = 'console'
console.setFormatter(custom)

logging.config.dictConfig(
{
    'version': 1,
    'incremental': True,
    'disable_existing_loggers': False,

    'loggers':
    {
        'root':
        {
            'handlers': logging.root.handlers, # Keep previous handlers
        },
        'rez':
        {
            'level': 'DEBUG',
            'handlers': console,
            'qualname': 'rez',
            'propagate': False,
        }
    }
})
