from urllib import parse, request
from urllib.error import URLError
from http import cookiejar
import json
import asyncio
from functools import partial

"""
This file contains low-level tools for communicating with kahoot.
"""


class URLWrap:

    """
    A class that acts as a wrapper to the urllib module,
    Providing some functionality convenient for communicating with the Kahoot API.
    This module uses long-pulling to interact with kahoot.
    """

    def __init__(self, queue):

        self.url = 'https://kahoot.it/'  # Base URL to build off of
        self.headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:43.0) Gecko/20100101 Firefox/43.0',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Referer': 'https://kahoot.it/'
        }  # Headers to ensure that we receive data that is in json format, english,
        # and to 'trick' kahoot into thinking we are an actual user instead of a bot
        self.response = None  # http.response object of the last made request
        self.kahoot_session = ''  # Session of Kahoot game, allows for automatic URL generation
        self.pin = 0  # Game pin of Kahoot game, allows for automatic URL generation
        self.cj = cookiejar.CookieJar()  # Cookie Jar instance for handling cookies
        self.opener = request.build_opener(request.HTTPCookieProcessor(self.cj))  # URLLIB opener for handling cookies
        self._urllib_queue = queue  # Queue of Kahoot Events

    def get_headers(self):

        # Function for returning headers of last made request

        return dict(self.response.getheaders())

    async def send(self, url=None, data=None):

        # Wrapper method for the urllib module
        # Leave data blank for get request

        # Generating URL if fields are blank

        if url is None:

            url = self.url + 'cometd/' + str(self.pin) + '/' + self.kahoot_session + '/'

        # Encoding data into JSON format:

        if data is not None:

            data = self._json_encode(data)

        # Generating Request object:

        req = request.Request(url, data=data, headers=self.headers)

        try:

            # Sending request to Kahoot

            self.response = await asyncio.get_event_loop().run_in_executor(None, partial(self.opener.open, req))

        except URLError as e:

            # Some errors occurred...

            if hasattr(e, 'reason'):

                # Connection problem

                extra = e.reason
                error_type = -3

            elif hasattr(e, 'code'):

                # Non-okay status code

                extra = e.code
                error_type = -4

            self._gen_error_payload(error_type, self._json_decode(self.response.read()), extra)

            return False, data

        # Returning contents in standard python format

        data = self._json_decode(self.response.read())

        #print(data)

        return True, data

    def _json_encode(self, data):

        # Encodes data(usually a python dictionary/list) into JSON format

        return json.dumps(data).encode('utf-8')

    def _json_decode(self, data):

        # Encodes JSON data into local python data types(Usually a list/dictionary)

        return json.loads(data)

    def _gen_error_payload(self, error_type, contents, extra):

        # Generates error payload, adds it to the event queue
        # 'error_type' - Connection Issue/Server Issue
        # 'contents' - Contents of the error
        # 'extra' - Extra information about the error

        self._urllib_queue.put({'data': {'id': error_type, 'content': {'errorInfo': contents, 'extra': extra}}})