from rez._version import _rez_version
import logging.config
import os


__version__ = _rez_version
__author__ = "Allan Johns"
__license__ = "LGPL"

module_root_path = __path__[0]

logging_conf_file = os.environ.get(
    'REZ_LOGGING_CONF',
    os.path.join(module_root_path, 'logging.conf'))
#logging.config.fileConfig(logging_conf_file, disable_existing_loggers=False)

from rez.colorize import ColorizedStreamHandler
consoleHandler = ColorizedStreamHandler()
consoleHandler.name = 'console'

logging.config.dictConfig(
{
    'version': 1,
    'incremental': True,
    'disable_existing_loggers': False,

    'formatters':
    {
        'custom':
        {
            'format': '%(asctime)s %(levelname)-8s %(message)s',
            'datefmt': '%X',
            'class': 'logging.Formatter',
        },
    },
    'handlers':
    {
        'console':
        {
            'class': 'rez.colorize.ColorizedStreamHandler',
            #'class': 'ColorStreamHandler.ColorStreamHandler',
            'formatter': 'custom',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers':
    {
        'root':
        {
            'handlers': logging.root.handlers, # Keep previous handlers
        },
        'rez':
        {
            'level': 'DEBUG',
            'handlers': ['console'],
            'qualname': 'rez',
            'propagate': False,
        }
    }
})
