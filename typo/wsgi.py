# -*- coding: utf-8 -*-
import cgi
import sys
import json
from itertools import product

import click

from correctors import TYPO_CLASSES


def make_app(corrector, format, limit=10):
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
        suggestions, _ = corrector.suggestion(typo)

        if format == 'json':
            result = json.dumps(suggestions, ensure_ascii=False).encode('utf-8')
        else:
            results = []
            for i, p in enumerate(product(*suggestions)):
                if i > limit:
                    break
                results.append(u"".join(word for word, weight in p))
            result = '\n'.join(results).encode('utf-8')
        return [result]
    return application


@click.command()
@click.option('--index',
              type=click.Path(readable=True, resolve_path=True),
              default="index.data", required=True)
@click.option('--corrector', type=click.Choice(TYPO_CLASSES.keys()),
              default='default')
@click.option('--format', type=click.Choice(['text', 'json']),
              default='text')
@click.option('--lang', type=click.Choice(['ru', 'en', 'other']),
              default='ru')
@click.option('--max-candidates', type=click.INT,
              default=1)
@click.option('--limit', type=click.INT, default=10)
def cli(*a, **kw):
    pass


ctx = cli.make_context('wsgi', sys.argv[1:])
corrector_cls = TYPO_CLASSES.get(ctx.params['corrector'])
corrector_inst = corrector_cls(ctx.params['index'],
                               max_candidates=ctx.params['max_candidates'],
                               lang=ctx.params['lang'])
application = make_app(corrector_inst, ctx.params['format'], ctx.params['limit'])

__all__ = ['application']
