import time
import json
import re
import base64
import threading  # TODO: REMOVE THREADING SUPPORT
import array
import asyncio

from libkahoot import knet

"""
Tools for interacting with the Kahoot API.
Answer questions, join games, ect.
"""


class KahootAPI(object):

    def __init__(self, pin, queue, name):

        self.name = name  # Name to use
        self.pin = pin  # Game pin of our Kahoot Game
        self._req = knet.URLWrap(queue)  # Instance of our URLWrapper for HTTP Requests
        self._raw_kahoot_session = ''  # Raw session token, to be decoded
        self._kahoot_session = ''  # Decoded session token
        self._challenge = ''  # Challenge string used to decode raw Kahoot session
        self._client_id = ''  # Our unique client ID
        self._ack_id = 1  # Acknowledgement ID
        self._sub_id = 12  # Subscription ID
        self._url = "https://kahoot.it/"  # Base URL that we can build off of
        self._active_api = False  # Value determining if we are actively connected/connecting
        self.two_auth = False  # Boolean determining if we have authenticated using two factor authentication
        self._queue_api = queue  # Queue of game play packets from the Kahoot API
        self._thread_api = None  # Instance of our continuous connection thread

    def _get_timecode(self):

        # Getting time code to ensure that we are in sync with Kahoot.

        return int(time.time() * 1000)

    def _get_ack_id(self):

        # Getting Acknowledgement value here

        self._ack_id += 1

        return self._ack_id

    def _get_id_payload(self):

        # Generates payload for getting the Kahoot client ID

        return [{"advice": {"interval": 0, "timeout": 60000}, "channel": "/meta/handshake",
                 "ext": {"ack": self._get_ack_id(), "timesync":
                     {"l": 1, "o": -14, "tc": self._get_timecode()}}, "id": "2",
                 "minimumVersion": "1.0", "supportedConnectionTypes": ["long-polling"], "version": "1.0"}]

    def _get_name_payload(self, name):

        # Generates payload for setting our name

        return [{"channel": "/service/controller", "clientId": self._client_id,
                 "data": {"gameid": str(self.pin), "host": "kahoot.it",
                          "name": str(name), "type": "login"}, "id": "14"}]

    def _get_disconnect_payload(self):

        # Generates payload for disconnecting from a Kahoot game

        return [{"channel": "/meta/disconnect", "clientId": self._client_id}]

    def _get_sub_payload(self, chan, sub):

        # Generates payload for subscribing to a specified channel

        self._sub_id += 1

        sub_id = str(self._sub_id)

        return [{"channel": "/meta/" + chan, "clientId": self._client_id,
                 "ext": {"timesync": {"l": 0, "o": -14, "tc": self._get_timecode()}}, "id": sub_id,
                 "subscription": "/service/" + sub}]

    def _get_con_payload(self):

        sub_id = str(self._sub_id)

        return [{"channel": "/meta/connect", "clientId": self._client_id, "connectionType": "long-polling",
                 "ext": {"ack": self._get_ack_id(), "timesync": {"l": 0, "o": -14, "tc": self._get_timecode()}},
                 "id": sub_id}]

    def _get_answer_payload(self, choice):

        # Generates payload for answering a question
        # 'choice' MUST be an integer and it MUST be a valid option!

        sub_id = int(self._sub_id)

        innerdata = {"choice": choice, "meta": {"lag": 13, "device": {"userAgent": "bigup_UK_grime",
                                                                      "screen": {"width": 1920, "height": 1080}}}}

        innerdata = json.dumps(innerdata)

        return [{"channel": "/service/controller", "clientId": self._client_id,
                 "data": {"content": innerdata, "gameid": self.pin, "host": "kahoot.it", "id": 6, "type": "message"},
                 "id": sub_id}]

    def _get_two_auth_payload(self, seq):

        # Generates two factor authentication payload
        # 'seq' MUST be a valid Kahoot two-factor-auth sequence!

        innerdata = str(json.dumps({"sequence": seq}))

        return [{"channel": "/service/controller", "clientId": self._client_id,
                 "data": {"id": 50, "type": "message", "gameid": self.pin, "host": "kahoot.it",
                          "content": innerdata}, "id": self._sub_id}]

    async def _continuous_connect(self):

        # Function for fetching game packets
        # Continuously polls kahoot for more game information

        while self._active_api:

            self._sub_id += 1

            data = self._get_con_payload()
            url = self._url + 'cometd/' + str(self.pin) + '/' + self._kahoot_session + '/connect'

            val, response = await self._req.send(url=url, data=data)

            if not val:

                # Error occurred, stopping

                return

            if len(response) > 0:

                for i, x in enumerate(response):

                    if x['channel'] != '/meta/connect':

                        #print(x)

                        await self._queue_api.put(x)

    async def get_session(self):

        # This function gets a session ID

        url = self._url + "reserve/session/" + str(self.pin)

        val, data = await self._req.send(url=url)

        if not val:

            # Error occurred:

            raise Exception("Session Grab Failed!")

        self._raw_kahoot_session = self._req.get_headers()['x-kahoot-session-token']

        print("Raw session: {}".format(self._raw_kahoot_session))

        self._challenge = self._solve_challenge(data['challenge'])

        print("Challenge: {}".format(self._challenge))

        self._kahoot_session = self._session_format()

        # Setting session values in URLWrap

        self._req.pin = self.pin
        self._req.kahoot_session = self._kahoot_session

        return

    def _solve_challenge(self, chall):

        # Function for solving Kahoot challenge

        # Cleaning up string by removing un-wanted contents:

        chall = re.sub('[^!-~]+', ' ', chall).strip()

        print("CHall: {}".format(chall))

        # Split up contents to get relevant bits:

        chall_list = chall.split(';')

        print("List of data: {}".format(chall_list))

        # Getting encoded string:

        chall_str = chall_list[0][chall_list[0].find("'") + len("'"):chall_list[0].rfind("'")]

        print("Encoded string: {}".format(chall_str))

        # Getting challenge expression:

        chall_exprs = eval(chall_list[1][chall_list[1].find(" = ") + len(" = ")::])

        print("CHall expression: {}".format(chall_exprs))

        # Solving expression:

        final = ""

        for i in range(len(chall_str)):
            # Applying pattern to the challenge expression:

            curr = chr(((((ord(chall_str[i]) * i) + chall_exprs) % 77) + 48))
            final = final + curr

        return final

    def _session_format(self):

        # Function for formatting session

        # Decoding the raw session bytes

        raw_session_bytes = base64.b64decode(self._raw_kahoot_session)

        # Encoding our challenge bytes to ASCII format

        challenge_bytes = str(self._challenge).encode("ASCII")

        session_bytes = []

        for i in range(len(raw_session_bytes)):

            # Applying operation to the raw session bytes

            session_bytes.append(raw_session_bytes[i] ^ challenge_bytes[i % len(challenge_bytes)])

        # TODO: Find better way to do this
        return array.array('B', session_bytes).tostring().decode("ASCII")

    async def get_client_id(self):

        # Function for getting client ID

        url = self._url + 'cometd/' + str(self.pin) + '/' + self._kahoot_session

        data = self._get_id_payload()

        val, response = await self._req.send(url=url, data=data)

        if not val:
            # Error occurred

            raise Exception("Client ID grab failed!")

        self._client_id = str(response[0]["clientId"])

        return

    async def set_name(self, name=None):

        # Function for setting the bot's name
        # Returns True on success, False on failure

        if name is None:

            # Name is none, using default name

            name = self.name

        val, response = await self._req.send(data=self._get_name_payload(name))

        if not val:
            # An error occurred when attempting to set the name

            raise Exception("Invalid Name")

        return True

    async def disconnect(self):

        # Function for disconnecting bot from Kahoot game

        url = self._url + "cometd/" + str(self.pin) + "/" + self._client_id + "/disconnect"
        data = self._get_disconnect_payload()

        await self._req.send(url=url, data=data)

    async def start_session(self):

        # Function for starting Kahoot session

        channels = ['controller', 'player', 'status']

        response = await self._req.send(data=self._get_sub_payload('unsubscribe', 'controller'))

        # self._first_connection()

        # Subscribing to the necessary channels

        for i in channels:

            val, response = await self._req.send(data=self._get_sub_payload('subscribe', i))

            if not val:

                # Error occurred

                raise Exception()

    async def solve_twofactor(self, seq):

        # Function for solving Two Factor authentication with the given sequence
        # sequence MUST be a valid Kahoot Two-Factor-Authentication sequence!

        await self._req.send(data=self._get_two_auth_payload(seq))

    def _start_continuous_connection(self):

        # Function for starting the continuous connection
        # TODO: Get rid of threading support!
        self._thread_api = threading.Thread(target=self._continuous_connect)
        self._thread_api.daemon = True
        self._thread_api.start()

    async def answer_question(self, choice):

        # Sends answer to Kahoot game

        await self._req.send(data=self._get_answer_payload(choice))

    async def start_async(self):

        """
        Starts connection to Kahoot, and starts the continuous connection.
        """

        print("Started")

        self._active_api = True

        await self.get_session()
        await self.get_client_id()
        await self.set_name()
        await self.start_session()

        # Getting asyncio event loop and adding continuous connection:

        asyncio.ensure_future(self._continuous_connect())

    async def stop_async(self):

        """
        Stops the API instance, and all asynchronous features.
        We also disconnect from the game here.
        """

        # Stop the running producer:

        self._active_api = False

        # Disconnect from the game:

        await self.disconnect()

    def start(self):

        """
        Runs the 'start_async' as a task in the event loop.
        This is meant to be a synchronous way to start the underlying asynchronous
        features of KahootAPI.
        """

        print("Starting connection")

        task = asyncio.get_event_loop().create_task(self.start_async())

        print(task)

        asyncio.ensure_future(task)

    def stop(self):

        """
        Function for stopping the KahootAPI.
        This means disconnecting from the current Kahoot game.
        """

        asyncio.ensure_future(self.stop_async())
