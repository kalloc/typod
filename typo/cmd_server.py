# -*- coding: utf-8 -*-
import logging
from collections import namedtuple

import click
import trollius as asyncio
from trollius import From

logger = logging.getLogger(__name__)

ClientTuple = namedtuple('ClientTuple', 'timeout, reader, writer')


class TypedServer(object):

    def __init__(self, host, port, timeout, corrector):
        self.server = None
        self.loop = None
        self.corrector = corrector
        self.connections = {}
        self.timers = {}
        self.listen_host = host
        self.listen_port = port
        self.timeout = timeout / 1000

    def on_connect(self, reader, writer):
        client = ClientTuple(timeout=None, reader=reader, writer=writer)
        task = asyncio.Task(self.process(client))
        task.add_done_callback(self.on_disconnect)
        self.connections[task] = client
        timer = self.loop.call_later(self.timeout, self.on_disconnect, task)
        self.timers[task] = timer
        client_ip = self.client_ip(client)
        logger.debug("{client}:connect".format(client=client_ip))

    def client_ip(self, client):
        transport = client.writer.transport
        (remote_ip, remote_port) = transport.get_extra_info('peername')
        return '{ip}:{port}'.format(ip=remote_ip, port=remote_port)

    def on_disconnect(self, task):
        if task in self.timers:
            timer = self.timers[task]
            del self.timers[task]
            timer.cancel()
        if task in self.connections:
            client = self.connections[task]
            client_ip = self.client_ip(client)
            client.writer.close()
            del self.connections[task]
            logger.debug("{client}:disconnect".format(client=client_ip))

    @asyncio.coroutine
    def process(self, client):
        query = (yield From(asyncio.wait_for(client.reader.readline(),
                                             timeout=0.01)))
        if not query:
            return
        query = query.strip()
        client_ip = self.client_ip(client)
        cmd = query.split(' ', 1)
        if cmd[0] == 'RELOAD':
            self.corrector.reload()
            result = 'DONE'
        elif cmd[0] == 'QUERY' and len(cmd) > 1:
            data = cmd[1]
            typo = unicode(data, "utf-8")

            corrected, is_success = self.corrector.suggestion(typo)
            result = corrected.encode('utf-8') if is_success else data
        else:
            result = 'ERROR'

        client.writer.write('{}\n'.format(result))
        yield From(client.writer.drain())
        logger.info("{client}:request:{request}:{result}"
                    .format(client=client_ip, request=query, result=result))

    def start(self, loop):
        server = asyncio.streams.start_server(
            self.on_connect, self.listen_host, self.listen_port, loop=loop
        )
        self.loop = loop
        self.server = loop.run_until_complete(server)

    def stop(self, loop):
        if self.server is not None:
            self.server.close()
            loop.run_until_complete(self.server.wait_closed())
            self.server = None


@click.group()
def server_group():
    pass


@server_group.command()
@click.option('--host', type=str, default='0.0.0.0', required=True)
@click.option('--port', type=click.IntRange(1, 65535), default=3333,
              required=True)
@click.option('--timeout', type=click.IntRange(1, 5000), default=1000,
              required=True)
@click.pass_context
def server(ctx, host, port, timeout):
    """Typod server"""

    corrector_index = ctx.obj['corrector_index']
    corrector_cls = ctx.obj['corrector']
    inst = corrector_cls(corrector_index)
    server = TypedServer(host=host,
                         port=port,
                         timeout=timeout,
                         corrector=inst)

    loop = asyncio.get_event_loop()
    logger.info('Run server on {}:{}, using {} corrector'
                .format(host, port, corrector_cls.typo_name))
    server.start(loop)
    try:
        loop.run_forever()
    finally:
        loop.close()
