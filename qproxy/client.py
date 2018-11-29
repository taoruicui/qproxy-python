import tornado.ioloop
import tornado.gen
import pycurl
import ujson
import urllib
import copy
import requests

from qproxy.http import HttpClientSingleton
from functools import partial

# TODO: Codegen
OPERATIONS = {
    'qproxy/listqueues' : True,
    'qproxy/getqueue' : False,
    'qproxy/createqueue' : False,
    'qproxy/deletequeue' : False,
    'qproxy/modifyqueue' : False,
    'qproxy/purgequeue' : False,
    'qproxy/ackmessages' : False,
    'qproxy/getmessages' : False,
    'qproxy/publishmessages' : False,
    'qproxy/modifyackdeadline' : False,
    'qproxy/healthcheck' : False,
}

class WrappedBuffer(object):

    def __init__(self):
        self.buf = []

class Client(object):

    REQUESTS_CHUNK_SIZE = 1024 * 1024

    def __init__(self, host, port, use_curl=True, secure=False,
            version='v1'):
        self.host = host
        self.port = port
        self.use_curl = use_curl
        self.secure = secure
        self.version = version

        for op_path, streaming in OPERATIONS.iteritems():
            # TODO: ugly for now, cleaner when code gened
            op = op_path.split("/")[-1]
            path = self._path(op_path)
            if streaming:
                sync_func = partial(self._make_streaming_request_sync, path, "POST")
                setattr(self, op + "_sync", sync_func)
                func = partial(self._make_streaming_request,path,"POST")
            else:
                func = partial(self._make_request,path,"POST")
            setattr(self, op, func)

    @classmethod
    def _prepare_request_args(cls, method, **params):
        body = params.pop('body', None)
        auth = params.pop('auth', None)

        params['method'] = method
        # These are the default tornado timeout values.
        params['request_timeout'] = params.get('request_timeout', 20.0)
        params['connect_timeout'] = params.get('connect_timeout', 20.0)

        if 'use_curl' in params:
            params['prepare_curl_callback'] = lambda c: c.setopt(pycurl.TCP_NODELAY, 1)

        if 'headers' not in params:
            params['headers'] = {}

        if method in ('PUT', 'POST', 'PATCH'):
            params['body'] = body or ''

        if auth:
            params['headers']['Authorization'] = auth

        return params

    def _path(self, path):
        return '{scheme}://{host}:{port}/{version}/{path}'.format(
                scheme = 'http' if not self.secure else 'https',
                host   = self.host,
                port   = self.port,
                version = self.version,
                path   = path,
            )

    @tornado.gen.coroutine
    def _make_request(self, path, method, **kwargs):
        async = kwargs.pop('async',True)
        kwargs = self._prepare_request_args(method, **kwargs)

        client = HttpClientSingleton.instance().async_curl if async else \
            HttpClientSingleton.instance().sync_curl
        if not self.use_curl:
            client = HTTPClientSingleton.instance().async if async else \
                HttpClientSingleton.instance().sync

        if not async:
            resp = client.fetch(path, **kwargs)
        else:
            resp = yield client.fetch(path, **kwargs)
        raise tornado.gen.Return(resp)

    # NOTE: The streaming_callback will be passed full chunks, and does not
    # have to deal with piecing them together.
    @tornado.gen.coroutine
    def _make_streaming_request(self, path, method, streaming_callback, **kwargs):
        if not callable(streaming_callback):
            raise ValueError("Must pass in a callable streaming_callback")
        kwargs['streaming_callback'] = partial(
            self._handle_chunked_streaming_response,
            WrappedBuffer(),
            streaming_callback
        )
        resp = yield self._make_request(path, method, **kwargs)
        raise tornado.gen.Return(resp)

    # Convenience method for dealing with chunked-encoded streams
    @classmethod
    def _handle_chunked_streaming_response(cls, buf, callback, chunk):
        if "\n" not in chunk:
            buf.buf.append(chunk)
            return

        lines = chunk.split("\n")
        lines[0] = "".join(buf.buf) + lines[0]
        buf.buf = []

        if not chunk.endswith("\n"):
            buf.buf = [lines.pop(len(lines) - 1)]

        for line in lines:
            if line == "":
                continue
            # We schedule the callback on the ioloop since for certain
            # execution models (like greenlets) there's no guarantee
            # that we'll switch back here. For only one line, it's fine
            # but for multiple lines, we need to add the callbacks to the ioloop
            # so they all eventually get called in order.
            tornado.ioloop.IOLoop.current().add_callback(
                partial(callback,line))

    # This is specifically to allow for a pattern a streaming request can be called
    # without a streaming callback. This allows for iterator patterns in a synchronous
    # context
    def _make_streaming_request_sync(self, path, method, **kwargs):
        body = kwargs.pop("body",None)
        # Map tornado httpclient timeout arg -> requests timeout arg
        request_timeout = kwargs.pop('request_timeout',20)
        kwargs['timeout'] = request_timeout
        streamed_response = getattr(requests,method.lower())(path, data=body, stream=True, **kwargs)
        for chunk in streamed_response.iter_lines(chunk_size=self.REQUESTS_CHUNK_SIZE):
            yield chunk

