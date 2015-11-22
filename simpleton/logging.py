#!/usr/bin/env python3

## Standard modules
import logging

logging._levelToName = {
    logging.CRITICAL: '!',
    logging.ERROR:    '?',
    logging.WARNING:  '*',
    logging.INFO:     '~',
    logging.DEBUG:    '+',
}

SIMPLETON_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            #'format': '%(levelname)s %(message)s',
            'format': '%(asctime)s.%(msecs)03d %(levelname)s %(message)s',
            'datefmt': '%s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'console',
        },
    },
    'loggers': {
        'default': {
            'handlers': ['console'],
            'level': logging.DEBUG,
            'propagate': True,
        }
    }
}
