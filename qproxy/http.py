from tornado.curl_httpclient import CurlAsyncHTTPClient
from tornado.httpclient import AsyncHTTPClient, HTTPClient
from threading import local
import os

class SingletonMixin(object):

    @classmethod
    def _instance_name(cls):
        if hasattr(cls, '_disable_fork_protection'):
            identifier = 0
        else:
            identifier = os.getpid()
        return "_%s_Singleton_%d" % (cls.__name__, identifier)

    @classmethod
    def instance(cls, *args, **kwargs):
        attr_name = cls._instance_name()
        if hasattr(cls, attr_name) and (args or kwargs):
            logger.warning('Arguments are passed to instance(), but '
               'pre-constructed instance is returned as singleton.')
        if not hasattr(cls, attr_name):
            instance = cls(*args, **kwargs)
            setattr(cls, attr_name, instance)
        return getattr(cls, attr_name)

# Threadsafe / Forksafe HTTPSingleton
class HttpClientSingleton(SingletonMixin):
    MAX_CLIENTS = 100
    '''Singleton to hold http clients.'''
    def __init__(self):
        self.thread_local_clients = local()

    @property
    def async(self):
        if not hasattr(self.thread_local_clients, "async"):
            self.thread_local_clients.async = \
                AsyncHTTPClient(max_clients=self.MAX_CLIENTS,
                                force_instance=True)
        return self.thread_local_clients.async

    @property
    def sync(self):
        if not hasattr(self.thread_local_clients, "sync"):
            self.thread_local_clients.sync = HTTPClient()
        return self.thread_local_clients.sync

    @property
    def async_curl(self):
        if not hasattr(self.thread_local_clients, "async_curl"):
            self.thread_local_clients.async_curl = \
                CurlAsyncHTTPClient(max_clients=self.MAX_CLIENTS,
                                    force_instance=True)
        return self.thread_local_clients.async_curl

    @property
    def sync_curl(self):
        if not hasattr(self.thread_local_clients, "sync_curl"):
            self.thread_local_clients.sync_curl = \
                HTTPClient(async_client_class=CurlAsyncHTTPClient)
        return self.thread_local_clients.sync_curl
