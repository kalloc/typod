# -*- coding: utf-8 -*-
import cgi
import sys

import click

from correctors import TYPO_CLASSES


def make_app(corrector):
    def application(env, start_response):
            method = env['REQUEST_METHOD']
            if method == 'GET':
                qs = cgi.parse_qs(env['QUERY_STRING'])
                typo = qs.get('query', [''])[0]
            elif method == 'POST':
                typo = env['wsgi.input'].read()
            else:
                start_response('405 Method Not Allowed')
                return []
            start_response('200 OK',
                           [('Content-Type', 'text/plain; charset=UTF-8')])
            typo = typo.decode('utf-8').strip()
            corrected, _ = corrector.suggestion(typo)
            result = corrected.encode('utf-8')
            return [result]
    return application


@click.command()
@click.option('--index',
              type=click.Path(readable=True, resolve_path=True),
              default="index.data", required=True)
@click.option('--corrector', type=click.Choice(TYPO_CLASSES.keys()),
              default='default')
def cli(*a, **kw):
    pass


ctx = cli.make_context('wsgi', sys.argv[1:])
corrector_inst = TYPO_CLASSES.get(ctx.params['corrector'])(ctx.params['index'])
application = make_app(corrector_inst)

__all__ = ['application']
