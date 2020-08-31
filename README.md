# libkahoot

An asynchronous Kahoot framework written in python. 

# Disclaimer

libkahoot is a work in progress!
This means your experience will be buggy, and some of the features I would like to see might not be 
implemented. You can see a list of everything I want to add/change below.

libkahoot is for educational purposes ONLY! I take no responsibility for damages, banns, or trouble you might get into
for using libkahoot. Use at your own risk!

# Introduction

libkahoot allows you to interact with Kahoot games, and create asynchronous applications that can react to said games.

libkahoot allows you to do the following:

 - Bypass two factor authentication
 - Bypass the name generator, allowing you to specify custom names(Vulgar/inappropriate names are still not allowed)
 - Join games, answer questions, view quiz statistics, ect.
 - Fetch answers to quizzes
 - Use our plugin system to create custom bots
 
 libkahoot handles all the details! For example, we automatically get and solve challenge tokens for joining games, 
 fetch and index quiz answers, provide a handler framework, and other low-level networking stuff, just to name a few. 
 You just have to focus on the game!
 
 # Example
 
 Load the default handlers and join a Kahoot game with pin 12345 and name 'Testing':
 
 ```python
# Import our Kahoot master class and handlers:

from libkahoot.kahoot import Kahoot
from libkahoot.handlers import DEFAULT_HANDLERS

# Create a Kahoot instance:

kah = Kahoot(12345, "Testing")

# Load the default handlers:

kah.handlers.add_handlers(DEFAULT_HANDLERS)

# Start the instance and let the handlers take over:

kah.start()
```
 This will start a very basic bot that will prompt you for a play style, and a UUID for answer fetching.
 
 Here is an example of creating a handler to print game data:
 
 ```python
# Import the BaseHandler and the Kahoot masterclass:

from libkahoot.handlers import BaseKahootHandler
from libkahoot.kahoot import Kahoot

# Create a handler(Must inherit the BaseKahootHandler!):

class PrintHandler(BaseKahootHandler):

    def __init__(self):

        super().__init__(3)  # Pass the ID of the event we are handling to the BaseKahootHandler

    async def start(self):

        """
        This function is called when the handler is started.
        """

        print("Started PrintHandler!")

    async def stop(self):

        """
        This function is called when the handler is stopped.
        """

        print("Stopped PrintHandler!")

    async def handel(self, data):

        """
        This function is called when their is relevant data to handel.
        The 'data' parameter is the relevant game data.
        """

        print(data)

# Create a Kahoot instance:
kah = Kahoot(12345, "Testing")


# Add the handler to the Kahoot masterclass:

kah.handlers.add_handler(PrintHandler(), 3)

# Start the Kahoot instance:

kah.start()
```
 
 # Instillation
 
 libkahoot is not available on [PyPi](https://pypi.org/) yet, but it soon will be!
 
 In the meantime, you can clone this repository and reference the code locally.
 Just move the 'libkahoot' directory to your application's working directory, and then you should be able to use
 and import libkahoot.
 
 You need python to run this library. You can find information on python [here](https://www.python.org/downloads/).
 You need at least python 3.5. Python 3.7 or 3.8 would be ideal.
 
 # Bot Development
 
 libkahoot is heavily centered around Kahoot bot development. However, libkahoot comes with some good default handlers
 that can do everything that the library promises. Play from the command line, auto answer questions, solve two-factor 
 challenges, ect. 
 
 Be aware that these handlers user basic stdin/stdout, meaning that you must invoke libkahoot and it's handlers
 from a command line. I know, this is very basic and lackluster, but I would like to change this at a later time,
 possibly using curses or some GUI framework, such as [tkinter](https://docs.python.org/3/library/tkinter.html).
 
 # TODO
 
  - Clean up comments(Specifically add reStructured text docstrings so we can be sphinx compliant).
  - Clean up code(Most of this code is ported from an earlier project of mine, and it definitely has some areas 
  that can be improved upon).
  - Create and host documentation.
  - Add support for websocket communication.
  - Fix up search parameter configuration.
  - Add Kahoot Groups - Group of instances that are optimised and controlled by one master bot. 
  Great for spamming games with bots.
  - Optimise networking operations(websockets will help greatly with this).
  - Add custom datatypes for representing certain objects(questions, players, ect.).
  - CLI application for creating bots with the default handlers.
  - Custom exceptions.
  - Better output - default handlers offer a very basic and ugly command line experience.
  - Better error handling - For recoverable and irrecoverable errors.
  - Handler overhaul - Decorator based handler registration, meta handlers(for keeping track of state, question number, 
  score, ect. and converting Kahoot data into easy to use datatypes, as mentioned above).
  - Contributing rules and guidelines.
  - Upload to PyPi as a Python package.
  - Better default handlers and front end - curses and tkinter would be good options.
  
  Again, this project is a big work in progress. The biggest task will be documenting all of this. 
 
 # Conclusion
 
 libkahoot offers a simple, pythonic way to interact with Kahoot games. Expect bugs and poor performance until 
 the library is complete.
 
 Thank you for reading!