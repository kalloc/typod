# -*- coding: utf-8 -*-
import logging
import os
from collections import namedtuple

import click
import marshal

logger = logging.getLogger(__name__)

ClientTuple = namedtuple('ClientTuple', 'timeout, reader, writer')
WordTuple = namedtuple('WordTuple', 'keyword, docs, hits, offset')


def is_writable(file):
    try:
        open(file, 'a')
    except IOError:
        pass
    else:
        return True
    return False


@click.group()
def convert_group():
    pass


@convert_group.command()
@click.option('--sphinx-dump',
              type=click.Path(readable=True, resolve_path=True),
              required=True)
@click.pass_context
def convert(ctx, sphinx_dump):
    """
    A converter from sphinx format to internal corrector format.
    Use indextool --dumpdict to dump the sphinx dictionary.
    """
    def progress(file):
        stat = os.stat(file.name)
        with click.progressbar(length=stat.st_size, label='Converting') as bar:
            for line in file.readlines():
                bar.update(len(line))
                yield line

    def skip_header(lines):
        had_header = False
        for line in lines:
            if had_header:
                yield line
                continue
            atoms = line.strip().split(',')
            if len(atoms) == 4:
                had_header = True
                if atoms[-1] != 'offset':
                    yield line

    def clean(lines):
        for line in lines:
            keyword, docs, hits, offset = line.strip().split(',')
            if keyword[0] == '\x02':
                keyword = keyword[1:]
            yield WordTuple(keyword.decode('utf-8'), docs, hits, offset)

    corrector = ctx.obj['corrector']
    click.echo("Convert indextool format to \"{}\" corrector format"
               .format(corrector.__name__))

    corrector_index = ctx.obj['corrector_index']
    if not is_writable(corrector_index):
        raise RuntimeError('do not have write permission to {}'
                           .format(corrector_index))

    with open(sphinx_dump) as fd, open(corrector_index, 'w') as fd_out:
        items = clean(skip_header(progress(fd)))
        result = corrector.convert(items)
        click.echo("Export result to {}".format(corrector_index))
        fd_out.write(marshal.dumps(result))
    click.echo("//EOE")
