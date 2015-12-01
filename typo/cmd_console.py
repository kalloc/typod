# -*- coding: utf-8 -*-
import logging
import time
import resource

import click

logger = logging.getLogger(__name__)


def do_execute(inst):
    while True:
        value = click.prompt('Phrase', type=str)
        start = time.time()
        suggestion, is_success = inst.suggestion(value)
        end = time.time() - start
        mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        click.echo(u"Result is {} ({}) spend time {:.6f}, {:.2f} mb usage"
                   .format(suggestion, is_success, end, mem/1024.0/1024))


@click.group()
def console_group():
    pass


@console_group.command()
@click.pass_context
def console(ctx):
    """console typo"""

    corrector_index = ctx.obj['corrector_index']
    corrector_cls = ctx.obj['corrector']
    inst = corrector_cls(corrector_index)
    do_execute(inst)
