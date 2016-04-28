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
              type=click.Path(readable=True, resolve_path=True))
@click.option('--frequency-dict',
              type=click.Path(readable=True, resolve_path=True))
@click.option('--min-hits', type=click.INT, default=0)
@click.pass_context
def convert(ctx, sphinx_dump=None, frequency_dict=None, min_hits=0):
    """
    A converter from sphinx format to internal corrector format.
    Use indextool --dumpdict to dump the sphinx dictionary.

    Frequency dict for Russian can be downloaded from
    http://www.ruscorpora.ru/corpora-freq.html.
    """
    assert bool(sphinx_dump) ^ bool(frequency_dict)

    if frequency_dict:
        convert_frequency(ctx, frequency_dict, min_hits=min_hits)
    else:
        convert_sphinx(ctx, sphinx_dump, min_hits=min_hits)


def convert_frequency(ctx, frequency_dict=None, min_hits=0):
    def progress(file):
        stat = os.stat(file.name)
        with click.progressbar(length=stat.st_size, label='Converting') as bar:
            for line in file.readlines():
                bar.update(len(line))
                yield line

    def clean(lines):
        for line in lines:
            hits, keyword = line.strip().split('\t')
            hits = int(hits)
            if hits < min_hits:
                continue
            yield WordTuple(keyword.decode('utf-8'), None, hits, None)

    corrector = ctx.obj['corrector']
    click.echo("Convert indextool format to \"{}\" corrector format"
               .format(corrector.__name__))

    corrector_index = ctx.obj['corrector_index']
    if not is_writable(corrector_index):
        raise RuntimeError('do not have write permission to {}'
                           .format(corrector_index))

    with open(frequency_dict) as fd, open(corrector_index, 'w') as fd_out:
        items = clean(progress(fd))
        result = corrector.convert(items)
        click.echo("Export result to {}".format(corrector_index))
        fd_out.write(marshal.dumps(result))
    click.echo("//EOE")


def convert_sphinx(ctx, sphinx_dump=None, min_hits=0):
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
            hits = int(hits)
            if hits < min_hits:
                continue
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


