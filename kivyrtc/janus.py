import random
import string
import time

import asyncio
import aiohttp
from kivy.logger import Logger

JANUS_VERSION = 73
JANUS_URL = 'https://janus.conf.meetecho.com' + '/janus'
# JANUS_URL = 'http://192.168.1.116:8088' + '/janus'


def transaction_id():
    return "".join(random.choice(string.ascii_letters) for x in range(12))

def handle_error(message, pass_code=[]):
    code = message.get('code', None) or message.get('error_code', None)
    reason = message.get('reason', None) or message.get('error', None)
    if code not in pass_code:
        raise Exception(f"Code: {code} Reason: {reason}")

class JanusPlugin:
    def __init__(self, session, url, plugin_id):
        self._queue = asyncio.Queue()
        self._session = session
        self._url = url + "/" + str(plugin_id)
        self.plugin_id = plugin_id
        self.curr_trans = ''

    async def send(self, payload, pass_code=[]):
        self.curr_trans = transaction_id()
        message = {"janus": "message", "transaction": self.curr_trans}
        message.update(payload)

        async with self._session._http.post(self._url, json=message) as response:
            data = await response.json()
            assert data["transaction"] == message["transaction"]

            if data["janus"] == "success":
                return data
            elif data["janus"] == "error":
                handle_error(data['error'], pass_code)
            elif data["janus"] == "ack":
                pass

        response = await self._queue.get()
        if response["plugindata"]['data'].get('error', None):
            handle_error(response["plugindata"]['data'], pass_code)
        return response

    async def detach(self):
        message = {"janus": "detach", "transaction": transaction_id()}
        async with self._session._http.post(self._url, json=message) as response:
            data = await response.json()
            if data["janus"] == "success":
                return True
            elif data["janus"] == "error":
                handle_error(data['error'])

    async def hangup(self):
        message = {"janus": "hangup", "transaction": transaction_id()}
        async with self._session._http.post(self._url, json=message) as response:
            data = await response.json()
            if data["janus"] == "success":
                return True
            elif data["janus"] == "error":
                handle_error(data['error'])

class JanusSession:
    def __init__(self, url):
        self._version = 0
        self._http = None
        self._version_transport = 0
        self._poll_task = None
        self._plugins = {}
        self._support_plugins = []
        self._version_plugins = {}
        self._root_url = url
        self._session_url = None
        self._queue = asyncio.Queue()

    async def get_info(self):
        message = {"janus": "server_info", "transaction": transaction_id()}
        async with self._http.get(self._root_url + '/info') as response:
            data = await response.json()
            assert data["janus"] == "server_info"

            self._version = data['version']
            self._version_transport = data['transports']['janus.transport.http']['version']
            if self._version >= JANUS_VERSION:
                Logger.warning(f'JanusSession: You connect to new janus server: {self._version}')

            self._support_plugins = list(data['plugins'].keys())
            for i in self._support_plugins:
                self._version_plugins[i] = data['plugins'][i]['version']

    async def attach(self, plugin):
        message = {"janus": "attach", "plugin": plugin, "transaction": transaction_id()}
        async with self._http.post(self._session_url, json=message) as response:
            data = await response.json()
            assert data["janus"] == "success"
            plugin_id = data["data"]["id"]
            plugin = JanusPlugin(self, self._session_url, plugin_id)
            self._plugins[plugin_id] = plugin
            return plugin

    async def create(self):
        self._http = aiohttp.ClientSession()
        await self.get_info()

        message = {"janus": "create", "transaction": transaction_id()}
        async with self._http.post(self._root_url, json=message) as response:
            data = await response.json()
            assert data["janus"] == "success"
            session_id = data["data"]["id"]
            self._session_url = self._root_url + "/" + str(session_id)

        self._poll_task = asyncio.ensure_future(self._poll())

    async def destroy(self):
        if self._poll_task:
            self._poll_task.cancel()
            self._poll_task = None

        if self._plugins != {}:
            for _, j in self._plugins.items():
                await j.detach()

        if self._session_url:
            message = {"janus": "destroy", "transaction": transaction_id()}
            async with self._http.post(self._session_url, json=message) as response:
                data = await response.json()
                assert data["janus"] == "success"
            self._session_url = None

        if self._http:
            await self._http.close()
            self._http = None

    async def _poll(self):
        while True:
            params = {"maxev": 1, "rid": int(time.time() * 1000)}
            async with self._http.get(self._session_url, params=params) as response:
                data = await response.json()
                type_event = data['janus']

                if type_event == "event":
                    plugin = self._plugins.get(data["sender"], None)
                    if plugin and\
                            data.get('transaction', '') == plugin.curr_trans:
                        await plugin._queue.put(data)
                        continue

                await self._queue.put(data)
