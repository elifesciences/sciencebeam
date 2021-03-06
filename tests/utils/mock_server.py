import logging
import os
from threading import Thread
from uuid import uuid4
from typing import List

from flask import Flask, jsonify, Response, request
import requests


LOGGER = logging.getLogger(__name__)


# based on https://gist.github.com/eruvanos/f6f62edb368a20aaa880e12976620db8
class MockServer:
    def __init__(self, port=12345):
        self.thread = Thread(target=self._run)
        self.port = port
        self.app = Flask(__name__)
        self.url = "http://localhost:%s" % self.port
        self.app.add_url_rule("/shutdown", view_func=self._shutdown_server)

    def _shutdown_server(self):
        request.environ['werkzeug.server.shutdown']()
        return 'Server shutting down...'

    def _run(self):
        self.app.run(port=self.port)

    def start(self):
        self.thread.start()

    def stop(self):
        requests.get("http://localhost:%s/shutdown" % self.port)
        self.thread.join()

    def add_callback_response(
            self, url: str, callback: callable, methods=('GET',)):
        callback.__name__ = str(uuid4())  # change name of method to mitigate flask exception
        self.app.add_url_rule(url, view_func=callback, methods=methods)
        return os.path.join(self.url, url.lstrip('/'))

    def add_multiple_callbacks_response(
            self, url: str, callbacks: List[callable], methods=('GET',)):
        callback_it = iter(callbacks)

        def _callback():
            next_callback = next(callback_it)
            response = next_callback()
            LOGGER.debug('responding with: %s (callback: %s)', response, next_callback)
            return response
        return self.add_callback_response(url, _callback, methods=methods)

    def add_json_response(self, url, serializable, methods=('GET',)):
        def _callback():
            return jsonify(serializable)
        return self.add_callback_response(url, _callback, methods=methods)

    def add_response(self, url, body, methods=('GET',), **kwargs):
        def _callback():
            return Response(body, **kwargs)
        return self.add_callback_response(url, _callback, methods=methods)
