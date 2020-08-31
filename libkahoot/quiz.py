import json
import asyncio
from types import SimpleNamespace

from libkahoot.knet import URLWrap
from urllib.parse import urlencode

"""
Tools for keeping quiz info,
and fetching answers from Kahoot.
"""


class NestedNamespace(SimpleNamespace):

    """
    Allows for the creation of nested Namespaces.
    This means you can pass dictionaries with sub dictionaries,
    and still get a valid Namespace.
    """

    def __init__(self, dictonary, **kwargs):

        # Start up the parent namespace:

        super().__init__(**kwargs)

        # Iterate over each value to check if it is a sub-dict:

        for key, value in dictonary.items():

            if isinstance(value, dict):

                # Have a sub-dict, add it to our attributes

                self.__setattr__(key, NestedNamespace(value))

            else:

                # Normal value, map it to our attributes

                self.__setattr__(key, value)


class SearchOptions:

    """
    Class for managing Kahoot Search Options.
    Allows for the addition, subtraction, and generation of Kahoot search parameters.
    """

    TOPIC_OPTS = NestedNamespace({'MATH': {'ELEMENTARY': 1,
                                           'ALGEBRA': 2,
                                           'Geometry': 3,
                                           'Trigonometry': 4,
                                           'Calculus': 5,
                                           'APPLIED_STATISTICS': 6},
                                  'SCIENCES': {'BIOLOGY': 7,
                                               'CHEMISTRY': 8,
                                               'PHYSICS': 9,
                                               'EARTH_SCIENCES': 10},
                                  'ENGLISH': {'SPELLING_VOCABULARY': 11,
                                              'GRAMMAR': 12,
                                              'LITERATURE_DRAMA': 13},
                                  'FOREIGN_LANGUAGE': {'SPANISH': 14,
                                                       'FRENCH': 15,
                                                       'LATIN': 16,
                                                       'GERMAN': 17,
                                                       'OTHER': 18},
                                  'SOCIAL_STUDIES': {'ECONOMICS': 19,
                                                     'WORLD_HISTORY': 20,
                                                     'US_HISTORY': 21,
                                                     'CIVICS': 22},
                                  'TRIVIA': {'GENERAL': 23,
                                             'MUSIC': 24,
                                             'SPORTS': 25,
                                             'MOVIES': 26,
                                             'COMPUTERS': 27}})  # Collection of all search topics

    ORDER_OPTS = NestedNamespace({'RELEVANT': 'relevance', 'MOST_PLAYED': 'plays',
                                  'HIGHEST_QUALITY': 'quality'})  # Collection of orderings

    CREATOR_OPTS = NestedNamespace({'TEACHERS': 'teacher', 'STUDENTS': 'student', 'BUSINESS': 'business',
                                    'SOCIAL': 'social'})  # Collection of creators

    TOPIC = 1
    ORDER = 2
    CREATOR = 3
    GRADE = 4
    DEPTH = 5
    LIMIT = 6

    def __init__(self):

        self._topic = []  # List of topics to search for
        self._order = ''  # Order to search for
        self._creator = []  # List of creators to search for
        self._grade = []  # List of grades to search for

    def set_param(self, param, *args):

        """
        Sets a given parameter to the given values.
        The grade parameter MUST be an integer between 1-12.

        :param param: Parameter to set
        :type param: int
        :param args: Values to set
        :type args: int, str
        """

        # Get the parameter we are trying to set:

        param = self._resolve_id(param)

        if param == SearchOptions.CREATOR:

            # Make sure we only have one argument, and it is a string

            if not len(args) == 1 and not args[0] is str:

                # Invalid value for order

                raise Exception("Invalid type for order! Must be a single string.")

        if param == SearchOptions.GRADE:

            # Make sure the numbers provided are valid.

            for item in args:

                if type(item) != int and (item > 12 or item < 1):
                    # Invalid number!

                    raise Exception("Invalid number provided! Must be an integer between 1 and 12.")

        # Set the parameter to the value:

        param = args

    def clear_param(self, param):

        """
        Clears a given parameter from all values.

        :param param: Parameter to clear
        :type param: int
        """

        param = self._resolve_id(param)

        if param is str:
            # Working with  string, set it to nothing

            param = ''

            return

        # Working with a list, set it to nothing

        param = []

    def get_param(self):

        """
        Returns the parameters as a dictionary.

          - Topic will be stored under "topic"
          - Order will be stored under "order"
          - Creator will be stored under "creator"
          - Grades will be stored under "grade"

        :return: Dictionary of parameters.
        :rtype: dict
        """

        return {"topic": self._topic, "order": self._order, "creator": self._creator, "grade": self._grade}

    def _resolve_id(self, id_param):

        """
        Resolves an ID to the value it represents.

        :param id_param: ID to resolve
        :type id_param: int
        :return: Value of ID
        """

        return {1: self._topic, 2: self._order, 3: self._creator, 4: self._grade}[id_param]


class InfoFetch(object):

    """
    Fetches quiz info from Kahoot.
    The info fetched is usually author name, topics,
    and more importantly, answers.
    """

    def __init__(self):

        super().__init__()  # Initialise the parent class

        self.depth = 3  # How deep we go when searching
        self.limit = 12  # How many Kahoots we load per page
        self.url = 'https://create.kahoot.it/rest/kahoots/'  # Base URL to build of off
        self._separator = '%2C'  # Separator used by the Kahoot search API
        self._depth = 3  # How deep we go while searching
        self._limit = 12  # How many items to load per page
        self.req = URLWrap(None)  # URLWrap instance for getting quiz info
        self.search = SearchOptions()  # Search Options object
        self.fetched = False  # Boolean determining if we successfully fetched or not.
        self.answers = []  # List of quiz answers
        self.title = ''  # Title of the Kahoot quiz
        self.type = ''  # Quiz Type
        self.author = ''  # Author of the Kahoot quiz
        self.description = ''  # Description of the Kahoot quiz
        self.uuid = ''  # UUID of the Kahoot game

    async def get_info_by_uuid(self, uuid):

        # Frontend function for fetching quiz info, and parsing said info by quiz uuid

        data = await self._fetch_uuid(uuid)

        if not await self._uuid_request_check(data):

            # Data failed integrity check, returning

            return False

        # Fetched our stuff!

        self.fetched = True

        return data

    # TODO: Rename this function
    # Terrible name!

    async def get_info_by_info(self, name, ans_map, quiz_type, params=None):

        """
        Gets quiz info by searching the Kahoot search API for a match.
        If a match is found, then it will be fetched and loaded into the FetchAnswers instance
        (And by extension, then KahootInfo instance that inherits this class).
        All required information for searching is given to us at the start of the match.

        This search method has variable results. It is not nearly as fast or accurate as searching by UUID,
        as we have to individually check every result to see if it matches.

        :param name: Name of the Kahoot
        :type name: str
        :param ans_map: Answer map of the Kahoot(Given to use at the start of the game)
        :type ans_map: list
        :param quiz_type: Type of quiz we are searching for
        :type quiz_type: str
        :param params: Search parameters to use. See 'SearchParameters' for getting and setting params.
        If not specified, uses the default SearchParameters class(Usually empty)
        :type params: SearchOptions
        :return: True if successful, False otherwise.
        :rtype: bool
        """

        for i in range(0, self.depth):

            # Generating URL:

            url = f"{self.url}?{urlencode(await self._gen_params(name, i, params=params))}"

            # Getting data:

            _, resp = self.req.send(url=url)

            for card in resp['entities']:

                # Iterating over all search results

                current_card = card['card']

                # Checking if names and type matches:

                if current_card['title'] == name and current_card['type'] == quiz_type:

                    # Name and type match, comparing with answer map

                    uuid = current_card['uuid']

                    data = await self._fetch_uuid(uuid)

                    if not await self._uuid_request_check(data):

                        # Data failed integrity check, returning

                        return False

                    if await self._compare_answers(data, ans_map):

                        # Found our matching quiz

                        self.fetched = True

                        return data

                # No match found, continuing

                continue

        return False

    async def _compare_answers(self, ques, ans_map):

        """
        Compares questions from fetched quiz with the provided answer map.

        :param ques: Quiz to check
        :type ques: dict
        :param ans_map: Master answer map to compare
        :type ans_map: list
        :return: True if matching, False otherwise.
        :rtype: bool
        """

        # Checking question count

        if len(ques['questions']) == len(ans_map):

            for num, val in enumerate(ques['questions']):

                # Checking option count

                if len(val['choices']) != ans_map[num]:

                    # Number of options do not match

                    return False

            # Question number and options match:

            return True

        # No match, return

        return False

    async def _gen_params(self, name, depth, params=None):

        """
        Generates the necessary parameters for fetching Kahoot quizzes.

        :param name: Name of Kahoot to search for
        :type name: str
        :param depth: Depth we are on, i.e page to get
        :type depth: int
        :param params: Search parameters to user
        :type params: SearchOptions
        :return: Search parameters in a dictionary, ready for URL encoding
        :rtype: dict
        """

        # Generating and returning search parameters

        if params is None:

            # Use our internal parameter object:

            param = self.search.get_param()

        else:

            # Working with user given object:

            param = params.get_param()

        return {
            'query': name,
            'cursor': depth * self._limit,
            'limit': self._limit,
            'topics': await self._prepare_options(param['topic']),
            'grades': await self._prepare_options(param['grade']),
            'orderBy': param['order'],
            'searchCluster': 1,
            'includeExtendedCounters': False,
            'usage': await self._prepare_options(param['creator'])
        }

    async def _prepare_options(self, opts):

        """
        Prepares options for URL encoding.

        :param opts: Options to encode
        :type opts: list
        :return: Encoded options
        :rtype: str
        """

        final = ''

        for num, opt in enumerate(opts):

            if num == 0:
                # First value, no value in front

                final = opt

                continue

            # Including search separator

            final = self._separator + opt

        return final

    async def _uuid_request_check(self, data):

        """
        Checks the data for errors.
        Useful for checking the integrity of the data.

        :param data: Data to check
        :type data: dict
        :return: True is valid, False if invalid
        :rtype: bool
        """

        if "error" in data:

            # Error found

            raise Exception("Error fetching quiz data!")

        return True

    async def _fetch_uuid(self, uuid):

        """
        Backend function for requesting quiz info with given UUID.

        :param uuid: UUID of quiz
        :type uuid: str
        :return: Data from Kahoot on quiz
        :rtype: dict
        """

        return await self.req.send(url='{}{}'.format(self.url, uuid))

    async def _question_parse(self, data):

        """
        Parses question subdata from Kahoot,
        and loads it's values into the FetchAnswers object.

        This allows us to retrieve the answers, Kahoot author, ect.

        :param data: Kahoot data to parse
        :type data: dict
        """

        # Setting info junk here:

        self.title = data['title']
        self.description = data['description']
        self.author = data['creator_username']
        self.uuid = data['uuid']

        for i, val in enumerate(data['questions']):

            for j in range(0, data['questions'][i]['numberOfAnswers']):

                if data['questions'][i]['choices'][j]['correct']:

                    # Appending our answer to the list:

                    self.answers.append(j)

                    break

        self.num_questions = len(self.answers)

        self.fetched = True


class KahootInfo(InfoFetch):

    """
    Class containing all info on the given Kahoot game.
    """

    def __init__(self, game_pin, name, queue):

        # Initialise the AnswerFetch class:

        super().__init__()

        self._info_queue = queue  # Queue instance
        self.answer_dict = [['1', 'r'], ['2', 'b'], ['3', 'y'], ['4', 'g']]  # A list mapping inputs to answers
        self.question_dict = [['1', 'Red', '/\\'], ['2', 'Blue', '<>'], ['3', 'Yellow', '()'],
                              ['4', 'Green', '[]']]  # A list mapping questions to output
        self.num_questions = 0  # Number of questions in the Kahoot
        self.question = 0  # Question number we are on
        self.question_correct = 0  # Number of questions answered correctly
        self.question_incorrect = 0  # Number of questions answered incorrectly
        self.question_unanswered = 0  # Number of questions unanswered
        self.score = 0  # Score of this Kahoot instance
        self.rank = 0  # Rank of this Kahoot instance
        self.game_pin = game_pin  # ID of the Kahoot game
        self.name = name  # Name of the Kahoot user

    def get_answer(self, num=None):

        """
        Returns the ID of the answer for the question we are currently on.
        This ID will be the question number(i.e answer 1 will have an id of 0, and so on...).
        The answer list MUST be fetched, or else an exception will be raised!

        :param num: Question number we want to fetch. If not specified, we use the internal question number.
        :type num: int
        :return: The answer ID for that question.
        :rtype: int
        """

        if num is None:

            # Use internal question count

            num = self.question

        if len(self.answers) == 0:

            # Answer list empty

            raise Exception("Empty Answer List")

        if len(self.answers) < num:

            # Not a valid question number

            raise Exception("Invalid Question Number")

        return self.answers[num]

    def set_question_num(self, num):

        """
        Sets the question number.
        This is useful for updating the internal question count,
        for example if we move on to a new question.

        :param num: Question number to set
        :type num: int
        """

        self.question = num

    def next_question(self):

        """
        Increments the internal question count by one.
        Useful for if we are moving on to the next question.
        """

        # Increment question number by one

        self.question += 1
