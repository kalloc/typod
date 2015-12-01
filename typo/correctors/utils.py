# -*- coding: utf-8 -*-
import logging
from collections import namedtuple

logger = logging.getLogger(__name__)

WordTuple = namedtuple('WordTuple', 'keyword, docs, hits, offset')
TYPO_CLASSES = {}


def register_typo(cls):
    if not hasattr(cls, 'typo_name'):
        raise RuntimeError('{} without __name__, maybe is not a typo'
                           .format(cls))
    TYPO_CLASSES[cls.typo_name] = cls
    return cls
