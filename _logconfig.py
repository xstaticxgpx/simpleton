#!/usr/bin/env python3

## Standard modules
import logging, logging.config, logging.handlers
import time
from queue import Queue

logging.Formatter.converter = time.gmtime

logging._levelToName = {
    logging.CRITICAL: '#!#',
    logging.ERROR:    '#*#',
    logging.WARNING:  '#+#',
    logging.INFO:     '#~#',
    logging.DEBUG:    '#?#',
}

SIMPLETON_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            #'format': '%(levelname)s %(message)s',
            'format': '%(levelname)s [%(asctime)s.%(msecs)03dZ] %(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S',
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

# Configure logging
logging.config.dictConfig(SIMPLETON_LOGGING)
log = logging.getLogger("default")

# Startup logging thread
_log_queue = Queue()
log_async = logging.handlers.QueueHandler(_log_queue)
log_queue = logging.handlers.QueueListener(_log_queue, *log.handlers)

log_queue.start()
log.handlers = [log_async,]
