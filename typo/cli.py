#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import click

from correctors import TYPO_CLASSES
from cmd_console import console_group
from cmd_server import server_group
from cmd_convert import convert_group

logger = logging.getLogger(__name__)


@click.command(cls=click.CommandCollection,
               sources=[server_group, convert_group, console_group])
@click.option('--debug', is_flag=True, default=False)
@click.option('--corrector-index',
              type=click.Path(readable=True, resolve_path=True),
              default="index.data",
              required=True)
@click.option('--corrector', type=click.Choice(TYPO_CLASSES.keys()),
              default='default')
@click.pass_context
def cli(ctx, debug, corrector_index, corrector):
    ctx.obj['corrector'] = TYPO_CLASSES.get(corrector)
    ctx.obj['corrector_index'] = corrector_index
    ctx.obj['debug'] = debug
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)

if __name__ == '__main__':
    cli(obj={})
