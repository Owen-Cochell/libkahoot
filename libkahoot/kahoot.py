import asyncio

from libkahoot.api import KahootAPI
from libkahoot.quiz import KahootInfo
from libkahoot.handlers import KahootHandler

"""
Kahoot class binds all classes together.
Some minor notes:

    - Library will use asyncio for running multiple things at once(?)
    - Library makeup:
        * kahoot.py - Main files
        * quiz.py - Maintaining quiz state and fetching quiz info
        * api.py - Tools for interacting with kahoot
        * knet.py(Bad name?) - Low-level protocol objects for interacting with Kahoot
        * handlers.py - Registering and working with Kahoot handlers
    
"""


class Kahoot:

    def __init__(self, pin, name, no_handlers=False, queue_maxsize=0):

        self.queue = asyncio.Queue(maxsize=queue_maxsize)  # asyncio queue for requests
        self.no_handlers = no_handlers  # Boolean value determining if we want to use handlers
        self._auto_fetch_answers = False  # Value determining if we should fetch answers

        self.info = KahootInfo(pin, name, self.queue)  # Kahoot info class
        self.api = KahootAPI(pin, self.queue, name)  # Kahoot API
        self.handlers = KahootHandler(self.queue, self)  # Kahoot Handler
        self.loop = None  # asyncio event loop

    def start(self):

        """
        Starts the Kahoot object and all subclasses.
        See documentation for each component to see what this entails.
        """

        # Set the asyncio event loop:

        self.loop = asyncio.get_event_loop()

        self.api.start()

        if not self.no_handlers:

            self.handlers.start()

        # Start up the loop:

        self.loop.run_forever()

    def stop(self):

        """
        Stops the Kahoot class and all subclasses.
        Will disconnect you from the game you are playing.
        """

        self.api.stop()

        if not self.no_handlers:

            # Stopping the Kahoot Handler

            print("Stopping Kahoot Handler...")

            self.handlers.stop()

        # Stopping event loop and generators:

        self.loop.run_untill_complete(self.loop.shutdown_asyncgens())
        self.loop.stop()
        self.loop.close()

    async def get(self):

        """
        Gets an item from the event queue.

        :return: Item from event queue
        """

        return await self.queue.get()

    async def put(self, item):

        """
        Puts an item into the Kahoot event queue.

        :param item: Item to put into the queue
        """

        await self.queue.put(item)

    async def qsize(self):

        """
        Returns the number of items in the Kahoot queue.

        :return: Number of items in the queue
        :rtype: int
        """

        return self.queue.qsize()

    async def empty(self):

        """
        Returns a boolean value determining if the Kahoot queue is empty.
        True for empty, False otherwise.

        :return: Boolean
        :rtype: bool
        """

        return self.queue.empty()

    async def join(self):

        """
        Blocks until all queue items are removed and processed.
        """

        await self.queue.join()
