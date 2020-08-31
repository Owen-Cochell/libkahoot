import random
import json
from inspect import isfunction
import asyncio

"""
This file contains all of the built in Kahoot handlers,
as well as methods to handle said handlers.
"""

ANS_TYPE = 0  # Answer type this instance uses


def get_place(place):

    # Method for determining place

    if place == 1:
        return "st"

    if place == 2:
        return "nd"

    if place == 3:
        return "rd"

    return "th"


class BaseKahootHandler(object):

    """
    Base ID handler for handling Kahoot events
    """

    def __init__(self, id_num):

        self.id = id_num  # ID of the event to handle
        self.kahoot = None  # Instance of the Kahoot object

    async def hand(self, data):

        # Method called when a request matching the ID needs to be handled,
        # And data is the relevant game data

        pass

    async def start(self):

        # Called on modules when they are registered

        pass

    async def stop(self):

        # called on modules when they need to be stopped

        pass

    def bind(self, inst=None):

        # Binds the Kahoot object to the handler

        self.kahoot = inst


class NullKahootHandler(BaseKahootHandler):

    """
    Kahoot handler that does nothing.
    Default handler loaded for all ID's,
    To ensure data is always being handled.

    Great for handling information that we don't care about.
    """

    def __init__(self, id_num):

        super().__init__(id_num)

    async def hand(self, data):

        # Do nothing

        pass


class PrintKahootHandler(BaseKahootHandler):

    """
    A Handler that prints message content to the terminal.

    Great for debugging purposes.
    """

    def __init__(self, id_num):

        super().__init__(id_num)

    async def hand(self, data):

        print(data)


class DefaultInfoGrabFail(BaseKahootHandler):

    """
    Default Handler for handling quiz info grab failure
    Also manages the grabbing of Kahoot data
    """

    def __int__(self):

        super().__init__(-3)

        self.error_codes = {41: "Quiz UUID is invalid, please re-enter the correct quiz UUID"}
        self.kahoot._auto_fetch_info = False  # Setting variable for fetching info

    async def hand(self, data):

        # Handling info grab fail

        print("\n+====================================================+")
        print("Error Grabbing Quiz Information:")
        print("\n--== Error Information: ==--")
        print("Error Name: {}".format(data['error']))
        print("Error Code: {}".format(data['errorCode']))
        print("Error ID: {}".format(data['errorId']))
        print("\n--== Argument Errors: ==--")

        for num, field in enumerate(data['fields']):

            # Iterating over arguments:

            print("Argument {}: {}".format(num, field))

        print("\n--== Assessment: ==--\n")

        print(self.error_codes[data['errorCode']])

    async def start(self):

        # Function for prompting for a UUID

        while True:

            print("\n+====================================================+")
            print("This bot requires extra quiz information to function.")
            print("This allows the bot to prompt/automatically answer the question correctly.")
            print("We have a few methods of acquiring this information:")
            print("\n[1]: Manually enter quiz UUID")
            print("   Will fetch quiz information using UUID given by user.")
            print("   Fast and guaranteed to be accurate,")
            print("   Given that the UUID entered is correct.")
            print("[2]: Automatically fetch information ")
            print("   Will use game data given to automatically search for a match.")
            print("   Information may not be accurate, and it may take longer to locate compared to manual search.")
            print("\n(You will be alerted if the given quiz information is incorrect)")

            inp = int(input("\nEnter the number of your option:"))

            if inp == 1:

                # User wants to manually enter quiz UUID

                print("\n+====================================================+")
                print("Please enter the quiz UUID below:")
                print("\nThe quiz UUID can be found by looking at the URL of the Kahoot game")
                print("It should look something like this:")
                print("\nhttps://play.kahoot.it/#/lobby?quizId=[QUIZ ID HERE]")
                print("\nIt is important to be exact, and the UUID is case-sensitive.")
                print("You may return to the previous menu by entering 'return' or 'r'.")

                uuid = str(input("Enter UUID(or 'return'):"))

                if uuid.lower() == 'return':

                    # User wants to return to the previous menu

                    continue

                # Searching for UUID:

                val = await self.kahoot.info.get_info_by_uuid(uuid)

                # We don't care about the returncode, it will be handled if it is incorrect/valid

                return

            if inp == 2:

                # User wants to automatically fetch information

                print("\n+====================================================+")
                print("When we have the necessary game data, we will automatically fetch the quiz information.")
                print("However, please be aware this this method of fetching information may not be accurate.")
                print("Some search parameters can be configured, such as depth, and relevant search topics.")
                print("These values are set at the Kahoot default, "
                      "but they can be changed to increase the chances of finding the Kahoot.")
                print("(It is recommended for most users to keep them at their default values)")

                print("\nAre you sure you want to automatically search for quiz information?")
                print("(You may enter 'no' if you wish to return to the previous screen.")

                inp = str(input("\n(Y/N")).lower()

                if inp not in ['yes', 'y', 'ye']:

                    # User does not want to continue

                    continue

                # TODO: Find a better way to configure search parameters
                # I think some more work needs to go into the SearchParameter object, found in quiz.py
                # We should add features that allows for the listing and iteration of these objects.

                '''
                print("\nWould you like configure these search parameters?")
                print("(Yes to configure, No to keep defaults)")

                inp = str(input("\n(Y/N):")).lower()

                if inp in ['yes', 'y', 'ye']:

                    # User wants to configure search parameters

                    val = await self._configure_search_params()

                    if not val:

                        # User wants to return

                        continue
                '''

                print("\nConfiguration complete.")
                print("Automatically fetching quiz information when game data is available.\n")

                self.kahoot._auto_fetch_info = True

                return

    # TODO: Fix this function!
    # This function is terribly designed and is poorly optimised.
    # Their should be a better way of doing this
    async def _configure_search_params(self):

        # Method for prompting the user to configure search parameters

        order = self.kahoot.selected_order
        topics = self.kahoot.selected_topics
        grade = self.kahoot.selected_grades
        usage = self.kahoot.selected_creators
        depth = self.kahoot.deep

        while True:

            print("\n+====================================================+")
            print("         --== Search Parameter Configuration: ==--")
            print("Please answer the following:")
            print("('None' simply means that the default value is nothing, "
                  "this is the default value for most parameters)")

            while True:

                # Configuring search type:

                print("\n+====================================================+")
                print("          --== Search Sorting Options: ==--\n")

                for num, sort in enumerate(self.kahoot.orders):

                    print("[{}]: Sort by {}".format(num, sort))

                print("\nDefault Value: {}".format(list(self.kahoot.orders.keys())[
                                                     list(self.kahoot.orders.values()).index(
                                                         self.kahoot.default_order)]))
                print("Value Selected: {}".format("Default Value(Most Relevant)" if order == '' else order))
                print("\n+====================================================+")

                print("\nDefinition: How to sort/search for Kahoots.")

                print("\nPlease enter the number of the search sorting method you want:")
                print("(You can leave the prompt blank to accept the currently selected value)")
                print("(You can also enter 'd' to accept the default value)")
                print("You can also enter 'none' or 'n' to set the value to blank)")

                orde = input("Enter number of your choice:")

                # Making sure their are no errors while recovering value

                try:

                    if orde == '':

                        # User wants currently selected value

                        break

                    if str(orde).lower() == "d":

                        # User wants default value, continuing

                        order = self.kahoot.default_order

                        break

                    if str(orde).lower() in ['none', 'n']:

                        # User wants value to be blank

                        order = ''

                        break

                    # Checking value:

                    if 1 > order > len(self.kahoot.orders):

                        # Invalid value

                        print("\nError: Invalid entry, please try again.\n")

                        continue

                    order = self.kahoot.values()[ord]

                    break

                except Exception:

                    # Invalid entry

                    print("\nInvalid entry, please try again.\n")

                    continue

            while True:

                # Configuring topic type:

                print("\n+====================================================+")
                print("         --== Search Topic Options: ==--\n")

                total = 0

                for cat in self.kahoot.topics:

                    # Iterating over categories

                    print("\nCategory: {}".format(cat))

                    for num, val in enumerate(self.kahoot.topics[cat]):

                        print("    [{}]: {}".format(num + total + 1, val))

                    total = len(self.kahoot.topics[cat]) - 1

                print("\nDefault Value(s): {}".format("None" if self.kahoot.default_topics == [] else self.kahoot.default_topics))
                print("Value(s) Selected: {}".format("None" if self.kahoot.selected_topics == [] else self.kahoot.selected_topics))

                print("\n+====================================================+")

                print("\nDefinition: Topics relevant to Kahoot to search for.")

                print("\nPlease enter the number(s) of your option(s).")
                print("Your options may be a single value(1),")
                print("Or they can multiple values separated by spaces(1 2 3 4).")
                print("(You may leave the prompt blank to accept the currently selected value(s))")
                print("(You may enter 'd' to accept the default value(s))")
                print("(You may also enter 'none' or 'n' to set the value to blank)")

                top = input("Enter the number(s) of your options(s):")

                try:

                    # Catch any weird exceptions that may arise

                    if top == '':

                        # User wants currently selected values:

                        break

                    if top.lower() == 'd':

                        # User wants default grade

                        topics = self.kahoot.default_topics

                        break

                    if top.lower() in ['n', 'none']:

                        # User wants blank value

                        topics = ''

                        break

                    selections = top.split()

                    # Checking if selections are valid

                    for sel in selections:

                        if 1 > int(sel) > total + 1:

                            # Invalid value entered

                            print("\nError: Invalid entry, please try again.\n")

                            continue

                    topics = selections

                    break

                except Exception:

                    # Weird exception occurred, handling and retrying

                    print("\nError: Invalid entry, please try again.")

                    continue

            while True:

                # Configuring grade type:

                print("\n+====================================================+")
                print("             --== Search Level Options ==--")

                # Displaying options:

                for grade in range(self.kahoot.grades):

                    print("[{}]: Grade {}".format(grade+1, grade+1))

                print("Value(s) Selected: {}".format("None" if self.kahoot.selected_grades == [] else self.kahoot.selected_grades))
                print("Default Value(s): {}".format("None" if self.kahoot.selected_grades == [] else self.kahoot.selected_grades))

                print("\n+====================================================+")

                print("Definition: The Grade Level the Kahoot is set at.")

                print("\nPlease enter the number(s) of your option(s).")
                print("Your options may be a single value(1),")
                print("Or they can multiple values separated by spaces(1 2 3 4).")
                print("(You may leave the prompt blank to accept the currently selected value(s))")
                print("(You may enter 'd' to accept the default value(s))")
                print("(You may also enter 'none' or 'n' to set the value to blank)")

                grad = input("Enter the number(s) of your options(s):")

                try:

                    # Try block to catch any weird exceptions

                    if top == '':

                        # User wants currently selected values

                        break

                    if top.lower() == 'd':

                        # User wants default values:

                        grade = self.kahoot.default_grades

                        break

                    if top.lower() in ['n', 'none']:

                        # User wants blank value

                        grade = ''

                        break

                    selections = grad.split()

                    for sel in selections:

                        if self.kahoot.grades < int(sel) < 1:

                            # Invalid value entered:

                            print("\nError: Invalid entry, please try again.\n")

                            continue

                    grade = selections

                    break

                except Exception:

                    # Caught a weird exception

                    print("\nError: Invalid entry, please try again.")

                    continue

            while True:

                # Configuring Usage

                print("\n+====================================================+")
                print("             --== Search Usage Options ==--")

                # Displaying options:

                for num, val in enumerate(self.kahoot.creators):

                    print("[{}]: {}".format(num+1, val))

                print("Value(s) Selected: {}".format(
                    "None" if self.kahoot.selected_creators == [] else self.kahoot.selected_creators))
                print("Default Value(s): {}".format(
                    "None" if self.kahoot.selected_creators == [] else self.kahoot.selected_creators))

                print("\n+====================================================+")

                print("\nDefinition: Who the Kahoot was made for.")

                print("\nPlease enter the number(s) of your option(s).")
                print("Your options may be a single value(1),")
                print("Or they can multiple values separated by spaces(1 2 3 4).")
                print("(You may leave the prompt blank to accept the currently selected value(s))")
                print("(You may enter 'd' to accept the default value(s))")

                usag = input("Enter the number(s) of your options(s):")

                try:

                    # Try block to catch any weird exceptions

                    if usag == '':

                        # User wants currently selected values

                        break

                    if usag.lower() == 'd':

                        # User wants default values:

                        usag = self.kahoot.default_creators

                        break

                    selections = usag.split()

                    for sel in selections:

                        if int(sel) > len(self.kahoot.creators) + 1:

                            # Invalid value entered:

                            print("\nError: Invalid value entered, please try again.")

                            continue

                    usage = selections

                    break

                except Exception:

                    # Caught a weird exception

                    print("\nError: Invalid Values entered, please try again.")

                    continue

            while True:

                # Configuring depth

                print("\n+====================================================+")
                print("'Depth' is the value we use when searching for a matching Kahoot.")
                print("The value of depth determines how deep we go while searching.")
                print("The higher the value means more Kahoots will be searched, ")
                print("Meaning that the odds of finding the matching Kahoot will go up.")
                print("However, this also increases the time it takes to search for a match.")

                print("\nExample Value: 3")
                print("This Kahoot will search 3 pages deep while locating a match.")
                print("This parameter has no upper limit, but it cannot be less then 1.")

                print("\nSelected Value: {}".format(self.kahoot.deep))

                try:

                    dee = int(input("\nEnter Depth Value Here:"))

                    if dee < 1:

                        # Invalid entry

                        print("\nError: Invalid value entered, please try again.\n")

                        continue

                    continue

                except Exception:

                    # Invalid entry

                    print("\nError: Invalid value entered, please try again.\n")

                    continue

            print("\n+====================================================+")
            print("You have configured all of the search parameters!")
            print("Your options:\n")

            print("\n+====================================================+")
            print("             --== Search Parameters: ==--")
            print("Search Order {}".format("None" if order == [] else order))
            print("Search Topics: {}".format("None" if topics == [] else topics))
            print("Grade Level: {}".format("None" if grade == [] else grade))
            print("Usage: {}".format("None" if usage == [] else usage))
            print("Depth: {}".format(depth))
            print("\n+====================================================+")

            print("\nAre you sure you want to keep these values?")
            print("If you enter no, your entries will be cleared,")
            print("And you will be returned to the previous screen.")
            print("(It is definitely NOT recommended to alter these variables.")

            inp = input("Keep parameters(Y/N)?:").lower()

            if inp in ['y', 'yes', 'ye']:

                # User wants to commit variables

                self.kahoot.set_search_parameters(order, topics, grade, usage, depth)

                return True

            # User does not want to commit

            return False


class DefaultQuestionStarting(BaseKahootHandler):

    """
    Default Kahoot handler that handles the start of the question
    """

    def __init__(self):

        super().__init__(1)

    async def hand(self, data):

        # Handling start of question

        self.kahoot.info.set_question_num(int(data['questionIndex']))

        print("\n+=-=-=-=-=-=-=-=-=-=-=-=+")
        print("Question number {} out of {}...".format(self.kahoot.info.question + 1, self.kahoot.info.num_questions))


class DefaultAnswerQuestion(BaseKahootHandler):

    """
    Default Kahoot handler that handles questions
    Supports the following answering options:
        1. User Answer - User manually inputs the answer
        2. Auto-Answer Correct - Computer automatically answers question correctly
        (Requires fetching of Kahoot answers)
        3. Auto-Answer Random - Computer randomly selects an answer
        4. AutoAnswer - Hybrid - Computer randomly decides weather to answer correctly or not based on user value
        (Requires fetching of Kahoot answers)
    """

    def __init__(self, ans_type=0, back_type=0):

        # 'ans_type' - Answer type to use, leave at 0 to prompt user
        # 'back_type' - Backup answer type to use, leave at 0 to prompt user

        super().__init__(2)
        self.ans_type = ans_type  # Answer type handler will use
        self.per = 0  # Percentage that bot will answer correctly(Used by Auto-Hybrid)

    async def start(self):

        """
        Prompts players for the answer type they wish to use.
        """

        while True:

            print('''Su pports the following answering options:\n
            1. User Answer - User manually inputs the answer
            2. Auto-Answer Correct - Computer automatically answers question correctly
            (Requires fetching of Kahoot answers)
            3. Auto-Answer Random - Computer randomly selects an answer
            4. AutoAnswer - Hybrid - Computer randomly decides weather to answer correctly or not based on user value
            (Requires fetching of Kahoot answers)''')

            inp = int(input("Please answer the number of the answer type you wish to use:"))

            if inp not in [1, 2, 3, 4]:

                # Incorrect answer! Retry...

                print("Invalid answer type detected!")

                continue

            self.ans_type = inp

            if inp == 4:

                # Prompt for random value

                print("Please enter the probability of answering correctly.")
                print("For example, if you want the computer to answer correctly 45% of the time,\n"
                      "then enter '40' as your value.")

                inp = int(input("Enter probability:"))

                if 100 < inp < 0:

                    # Invalid probability entered!

                    print("Invalid probability entered!")

                    continue

                # Set the probability value:

                self.per = inp

            break

    async def hand(self, data):

        # Handel data and decide which answer type to use

        options = []
        question_num = int(data['questionIndex'])

        for i, x in enumerate(range(data['quizQuestionAnswers'][question_num])):

            options.append(x)

        options = sorted(options)
        ans = None

        if self.ans_type == 1:

            # User Answer

            ans = await self._user_answer(options, question_num)

        if self.ans_type == 2:

            # Auto-correct

            ans = await self._auto_correct(options, question_num)

        if self.ans_type == 3:

            # Auto-random

            ans = await self._auto_random(options, question_num)

        if self.ans_type == 4:

            # Auto-hybrid

            ans = await self._auto_hybrid(options, question_num)

        print("\n+=-=-=-=-=-=-=-=-=-=-=-=-+")
        print("Selecting Answer: {}".format(ans))
        print("+=-=-=-=-=-=-=-=-=-=-=-=-+")

        await self.kahoot.api.answer_question(ans)

    async def _user_answer(self, options, question_num):

        # User answers question

        while self.kahoot.info.question == question_num:

            print("\nOptions:\n")

            for option in options:

                # Displaying options

                print("{} - {}".format(self.kahoot.info.question_dict[option][1],
                                       int(option) + 1))

            print("\nYou may answer using the number, or the first character of the color of your option.")
            answer = input("\nEnter your answer:").lower()

            for num, val in enumerate(self.kahoot.info.answer_dict):

                if answer in val:

                    # Found our answer

                    answer = num

            if answer not in options:

                # Invalid answer

                print("\n+=-=-=-=-=-=-=-=-=+")
                print("! Invalid answer! !")
                print("+=-=-=-=-=-=-=-=-=+\n")

                continue

            return answer

    async def _auto_correct(self, options, question_num):

        # Computer answers question correctly
        # Must have answers fetched

        if not self.kahoot.info.fetched:

            # Answer list not fetched/failed to fetch

            # TODO: Add invalid answer list handling

            print("No questions fetched!")

            return

        ans = self.kahoot.info.get_question(question_num)

        if ans not in options:

            # Invalid answer list

            # TODO: Add invalid answer handling

            print("Answer list invalid!")

            return

        print("Selecting Correct Answer....")

        return ans

    async def _auto_random(self, options, question_num):

        # Computer randomly selects an answer from the given options

        print("Randomly selecting option...")

        return random.choice(options)

    async def _auto_hybrid(self, options, question_num):

        # Computer randomly decided weather to answer correctly based upon value given by user
        # Must have answers fetched

        if not self.kahoot.info.fetched:

            # Answer list not fetched/failed to fetch

            # TODO: Add invalid answer list handling

            print("Answers not fetched!")

            return

        ans = self.kahoot.info.get_answer(question_num)

        if ans not in options:

            # Invalid answer list

            # Todo: Add invalid answer list handling

            print("Invalid answer option")

            return

        if random.randint(1, 101) <= self.per:

            # Answer correctly

            print("Selecting Correct Answer:")

            return ans

        else:

            # Choosing incorrect answer:

            print("Selecting Incorrect Answer:")

            options.remove(ans)

            return random.choice(options)


class DefaultGameOverStats(BaseKahootHandler):

    """
    Default Kahoot Handler that handels game over statistics
    """

    def __init__(self):

        super().__init__(3)

    async def hand(self, data):

        # Handling Game Over statistics

        print("\n+======================================================+")
        print("Game Over!")
        print("\nTest stats for {}:\n".format(data['name']))
        print("You ranked {}{} out of {}!".format(data['rank'],
                                                  get_place(data['rank']),
                                                  data['playerCount']))
        print("You scored {} points!".format(data['totalScore']))
        print("\nQuestions correct: {}".format(data['correctCount']))
        print("Questions incorrect: {}".format(data['incorrectCount']))
        print("Questions unanswered: {}".format(data['unansweredCount']))


class DefaultEndOfQuestion(BaseKahootHandler):

    """
    Default Kahoot Handler that handel's the end of the question
    """

    def __init__(self):

        super().__init__(4)

    async def hand(self, data):

        # Handling end of question

        print("\n+=-=-=-=-=-=-=-=-=-=-=-=+")
        print("End of question {}!".format(data['questionNumber'] + 1))
        print("+=-=-=-=-=-=-=-=-=-=-=-=+")
        
        return


class DefaultQuestionRecieved(BaseKahootHandler):
    
    """
    Default Kahoot Handler that handel's a question received conformation
    """
    
    def __init__(self):
        
        super().__init__(7)
        
    async def hand(self, data):
        
        # Handling question conformation

        print("\n+=-=-=-=-=-=-=-=-=-=-=-=-=+")
        print("\n{}".format(data['primaryMessage']))
        print("\n+=-=-=-=-=-=-=-=-=-=-=-=-=+")


class DefaultQuestionStatistics(BaseKahootHandler):
    
    """
    Default Kahoot Handler that handel's the end of question statistics
    """
    
    def __init__(self):
        
        super().__init__(8)
        
    async def hand(self, data):
        
        # Handling end of question statistics

        print("\n+=============================================+")
        print("Statistics for question number {}:\n".format(self.kahoot.info.question))

        if data['isCorrect']:

            # Question is correct

            print("You answered question {} correctly. Nice job!".format(self.kahoot.info.question))

        else:

            print("You answered question {} incorrectly. Nice try!".format(self.kahoot.info.question))

        if data['choice'] is None:

            print("You didn't choose anything!")

        else:

            print("\nYou answered: {}".format(data['choice']))

        print("\nThe correct answer(s) are:\n")

        for i in data['correctAnswers']:
            print(i)

        self.kahoot.info.score = data['totalScore']

        print("\nYou scored {} points".format(data['points']))
        print("You now have {} points".format(data['totalScore']))

        print("You are in {}{} place!".format(data['rank'],
                                              get_place(data['rank'])))

        if 'nemisis' in data.keys() and data['nemesis'] is not None:
            print("\n{} points behind {}!".format(data['nemesis']['totalScore'] - data['totalScore'],
                                                  data['nemesis']['name']))
        print("+=============================================+")


class DefaultQuizStart(BaseKahootHandler):
    
    """
    Default Kahoot Handler that handel's the start of the quiz
    """
    
    def __init__(self):
        
        super().__init__(9)
        
    async def hand(self, data):
        
        # Handling start of quiz

        self.kahoot.info.num_questions = len(list(data['quizQuestionAnswers']))

        print("\n+=-=-=-=-=-=-=-=-=-=-=-=-=+")
        print("!  The quiz is starting!  !")
        print("+=-=-=-=-=-=-=-=-=-=-=-=-=+\n")
        print("+==========================================+")
        #print("Quiz name: {}".format(data['quizName']))
        print("Quiz type: {}".format(data['quizType']))
        print("Number of questions: {}".format(self.kahoot.info.num_questions))

        # Lets see if we can fetch some questions:

        '''
        if self.kahoot._auto_fetch_info:

            # Lets fetch our questions:

            await self.kahoot.info.get_info_by_info(data['quizName'], data['quizType'], data['quizQuestionAnswers'])
        '''


class DefaultKick(BaseKahootHandler):
    
    """
    Default Kahoot Handler that handles being kicked from the Kahoot game
    """
    
    def __init__(self):
        
        super().__init__(10)
        
    async def hand(self, data):
        
        # Handling being kicked

        print("\n+==========================================+")
        print("We have been kicked!")


class DefaultAbsoluteQuizOver(BaseKahootHandler):
    
    """
    Default Kahoot Handler that handles the absolute end of the quiz
    """
    
    def __init__(self):
        
        super().__init__(12)
        
    async def hand(self, data):
        
        # Handling absolute end of the quiz
        
        print("Complete.")
        
        self.kahoot.stop()


class DefaultQuizOver(BaseKahootHandler):
    
    """
    Default Kahoot Handler that handles the end of the quiz
    """
    
    def __init__(self):
        
        super().__init__(13)
    
    async def hand(self, data):
        
        # Handling end of quiz

        print(data)

        print("You got podium medal type: {}".format(data['podiumMedalType']))

        print("That is the end of this game!")


class DefaultQuizJoin(BaseKahootHandler):
    
    """
    Default Kahoot Handler that handles the joining of the quiz
    """
    
    def __init__(self):
        
        super().__init__(14)
        
    async def hand(self, data):
        
        # Handling quiz join

        print("\n+=============================================+")
        print("You have joined {} with the name {}!".format(data['quizType'], data['playerName']))


class DefaultTwoFactorCodeIncorrect(BaseKahootHandler):
    
    """
    Default Kahoot Handler that handles an incorrect two-factor code
    Will do nothing if we skipped the code
    """
    
    def __int__(self):
        
        super().__init__(51)
        
    async def hand(self, data):
        
        # Handling incorrect two-factor code

        if not self.kahoot.api.two_auth:

            print("\n+=====================================+")
            print("Incorrect Two-Factor Code!")


class DefaultTwoFactorCodeCorrect(BaseKahootHandler):
    
    """
    Default Kahoot Handler that handles a correct two-factor code
    """
    
    def __int__(self):
        
        super().__init__(52)
        
    async def hand(self, data):
        
        # Handling correct two-factor code

        if not self.kahoot.api.two_auth:

            print("\n+=====================================+")
            print("Correct two factor code!")
            print("You are now authenticated.")

            self.kahoot.api.two_auth = True


class DefaultTwoFactorCodeNecessary(BaseKahootHandler):

    """
    Default Handler for handling a Two-Factor Prompt
    Can solve or skip the Two-Factor authentication
    """

    def __int__(self, skip=False):

        super().__init__(53)

    async def hand(self, data):

        # Handling Two-Factor authentication

        if self.kahoot.api.two_auth:

            # Already solved/skipped

            return

        code = await self._two_factor()

        if code is None:

            # User wants to skip Two-Factor Authentication

            print("Skipping Two-Factor Authentication...")

            self.kahoot.api.two_auth = True

            return

        print("Sending Two-Factor Authentication Code: {}".format(code))

        await self.kahoot.api.solve_twofactor(code)

    async def _two_factor(self):

        # Getting two-factor code from user:

        final = ""

        while True:

            print("\n+===========================================+")
            print("Two-Factor authentication necessary to join!")
            print("Please enter the pattern shown on the host screen.")
            print("Enter the first letter of each color.")
            print("\nRed - r\nBlue - b\nYellow - y\nGreen - g")
            print("\nFor example:\n\nIf the pattern is Green-Red-Blue-Yellow,\nYou would enter: grby")
            print("You can also skip the Two-Factor authentication by entering 'skip', or just 's'")

            inp = str(input("\nEnter letters: ").lower())

            if inp in ["skip", "s"]:

                skip = await self._two_skip()

                if skip:

                    # Skipping two-factor-auth

                    return None

                continue

            for i in inp:

                for num, val in enumerate(self.kahoot.info.answer_dict):

                    if i in val:

                        # Found our input

                        final = final + str(num)

                        break

            if len(inp) != 4:

                # Incorrect length

                print("Error: Incorrect input!")
                print("\nBe sure to enter only four characters, and use the proper characters(rbyg)!")

                continue

            return final

    async def _two_skip(self):
        
        # User wants to skip Two-Factor authentication

        print("\n+=====================================================================+")
        print("Are you sure you want to skip Two-Factor Authentication?")
        print("If you skip, you will still receive questions and be placed on the leaderboard.")
        print("However, you will not receive question statistics after you answer,")
        print("Meaning this instance will be unable to track question and score statistics for this game.")
        print("\nIt is also important to note that the game will not start without other people if you skip,")
        print("As Kahoot will not allow the host to start until a user has properly authenticated"
              "(This should not be a problem unless you are playing alone).")

        conf = str(input("\nAre you sure you want to skip(Y/N)?:")).lower()

        if conf in ["y", "yes", "ye"]:

            # User wants to skip Two-Factor-Auth

            print("Skipping two-factor authentication...")

            return True

        else:

            # User dose not want to skip

            return False

# TODO: Fix registration of default handlers:


DEFAULT_HANDLERS = {-2: DefaultInfoGrabFail(-2),
                    1: DefaultQuestionStarting(),
                    2: DefaultAnswerQuestion(),
                    3: DefaultGameOverStats(),
                    4: DefaultEndOfQuestion(),
                    7: DefaultQuestionRecieved(),
                    8: DefaultQuestionStatistics(),
                    9: DefaultQuizStart(),
                    10: DefaultKick(),
                    12: DefaultAbsoluteQuizOver(),
                    13: DefaultQuizOver(),
                    14: DefaultQuizJoin(),
                    51: DefaultTwoFactorCodeIncorrect(51),
                    52: DefaultTwoFactorCodeCorrect(52),
                    53: DefaultTwoFactorCodeNecessary(53)}


class KahootHandler(object):

    def __init__(self, queue, kahoot):

        self.kahoot = kahoot  # Kahoot Masterclass to give to all handlers
        self._queue_handler = queue  # Queue instance that contains all requests
        self.handlers = {}  # Dictionary of registered Kahoot handlers
        self._active_handler = False  # Boolean value determining if we are active
        self._thread_handler = None  # Threading instance of our handler consumer
        self.id_map = {"START_QUESTION": 1,
                       "ANSWER_QUESTION": 2,
                       "GAME_OVER": 3,
                       "QUESTION_OVER": 4,
                       "QUESTION_ANSWERED": 7,
                       "QUESTION_FEEDBACK": 8,
                       "QUIZ_START": 9,
                       "GAME_KICK": 10,
                       "GAME_DISCONNECT": 12,
                       "GAME_RANK": 13,
                       "QUIZ_JOIN": 14,
                       "CODE_WRONG": 51,
                       "CODE_CORRECT": 52,
                       "CODE_NEEDED": 53,
                       "INVALID_NAME": -1,
                       "INFO_GRAB_FAIL": -2,
                       "CONNECTION_ERROR": -3,
                       "SERVER_ERROR": -4}  # Dictionary mapping events to numerical ID's

        self._init_handlers()

    def add_handler(self, hand, id_num, args=None):

        """
        Registers a Kahoot handler to the given ID.
        The handler to add can be a function or a class.
        If the handler to add is a class, it MUST inherit BaseKahootHandler,
        or else it will be ignored.

        We overwrite the handler registered at this position.

        :param hand: Handler instance to add
        :param int, str id_num: ID number to register the handler to. Can be a valid string or integer.
        :param args:
        :return:
        """

        asyncio.ensure_future(self._add_handler(hand, id_num, args=None))

    def add_handlers(self, hands):

        """
        Like 'add_handler', but instead accepts a dictionary so we can add multiple.

        The keys of the dictionary must be valid Kahoot IDs,
        and the values must be instances of the handlers to add.

        :param dict hands: Dictionary of handlers to add
        """

        # Iterate over all handlers

        for id_num in hands:

            # Add the handler to the collection

            self.add_handler(hands[id_num], id_num)

    async def _add_handler(self, hand, id_num, args=None):

        """
        Low-Level asynchronous method for adding handlers.

        :param hand: Handler instance to add
        :param id_num: Number to register handler to
        :param args: Arguments to pass to handler
        :return:
        """

        if args is None:

            args = []

        # Checking if 'id_num' is a string that needs to be resolved to an integer:

        id_num = self._resolve_id(id_num)

        # Checking if "hand" is method:

        if isfunction(hand):

            # Given a function to work with

            self._make_hand_entry(id_num, 1, hand)

            return

        # Checking if hand is class and if it inherits from "BaseKahootHandler"

        elif isinstance(hand, BaseKahootHandler):

            # Is a class inheriting BaseKahootHandler

            self._make_hand_entry(id_num, 0, hand)

            # Binding information to handler:

            hand.bind(inst=self.kahoot)

            # Starting handler

            print("Starting handler : {}".format(hand))

            await hand.start()

            return

        else:

            # Invalid handler type

            raise Exception("Invalid Handler Type(Accepts methods and classes inheriting BaseKahootHandler)")

    async def remove_handler(self, id_num, stop=True):

        """
        Removes the handler at the given ID
        and replaces it with 'NullKahootHandler'.

        If any errors occur during the stop process, we replace the handler and raise them,
        ensuring that our handler environment doesn't get incomplete.

        :param str, int id_num: ID of the handler to remove, can be valid string or integer
        :param stop: Weather we should call the 'stop' method of the handler, if applicable
        :type stop: bool
        """

        # Figure out what we are working with:

        id_num = self._resolve_id(id_num)

        # Ensure that we eventually replace the handler no matter what

        try:

            # Check if we should stop the handler

            if stop:

                # Stop the handler

                await self._stop_handler(id_num)

        finally:

            # Make a new entry at that position.

            self._make_hand_entry(id_num, 0, NullKahootHandler(id_num))

    def start(self):

        """
        Starts the Kahoot handler.
        This schedules the handler consumer as an asyncio task,
        meaning that handlers will start to receive their relevant information.
        """

        self._active_handler = True

        asyncio.ensure_future(self._handle())

    def stop(self):

        """
        Stops the handler instance.
        This means all handlers and the handler consumer will also be stopped.
        """

        self._active_handler = False
        self._thread_handler.join()

        for id_num in self.handlers:

            self._stop_handler(id_num)

        return

    async def _handle(self):

        """
        Methods that pulls items from th event queue and gives them to handlers.
        This function should be ran as an asynchronous task.
        """

        while self._active_handler:

            # Getting value from queue:

            data = await self._queue_handler.get()

            id_num = data['data']['id']
            game_data = json.loads(data['data']['content'])

            # Searching through handlers and using them to handle data

            try:

                hand = self.handlers[id_num]

            except:

                # This exception SHOULD NOT HAPPEN!

                raise Exception("Handler for ID {} not found".format(id_num))

            # Checking handler type:

            if hand['type'] == 0:

                # Handler is KahootHandler class

                try:

                    await hand['inst'].hand(game_data)

                except Exception as e:

                    print("Exception occurred on handler: {} using ID: {}".format(hand['inst'], id_num))

                    print("Exception info: {}".format(e))

            if hand['type'] == 1:

                # Handler is method

                try:

                    inst = hand['inst']

                    await inst(game_data, kahoot_instance=self.kahoot)

                except Exception as e:

                    print("Exception occurred on handler: {} using ID: {}".format(hand['inst'], id_num))

                    print("Exception info: {}".format(e))

    def _resolve_id(self, id_val):

        """
        Resolves string ID to it's numerical value,
        which is what we understand.
        If the ID supplied is a valid integer,
        then we return it with no change.

        :param int, str id_val: ID value to resolve
        :return: Resolved ID number
        :rtype: int
        :raises ValueError: if the ID num is invalid
        """

        if isinstance(id_val, str):

            id_val = self.id_map[id_val]

        elif id_val not in self.id_map.values():

            # Invalid handler, raise an exception!

            raise ValueError("Invalid ID number!")

        return id_val

    def _make_hand_entry(self, id_num, hand_type, inst):

        """
        Makes a handler entry and registers it.

        :param id_num: ID to register handler to
        :type id_num: int
        :param hand_type: Handler type, function(1) or class(0)
        :type hand_type: int
        :param inst: Handler instance to add
        :type inst: class, function
        """

        self.handlers[id_num] = {"type": hand_type, "inst": inst}

    def _init_handlers(self):

        """
        Registers all handlers as 'NullKahootHandler'.
        Is called once at the start of the script.
        """

        for id_num in self.id_map:

            self.add_handler(PrintKahootHandler(self.id_map[id_num]), id_num)

        return

    async def _stop_handler(self, id_num):

        """
        Stops a given Kahoot handler.
        The ID can be an ID string or integer.
        We will only stop the handler if it is a function.

        :param id_num: ID of the handler to stop.
        :type id_num: str, int
        """

        id_num = self._resolve_id(id_num)

        hand = self.handlers[id_num]['inst']

        if isfunction(hand):

            # Is a function, ignoring

            return

        await hand.stop()

        return
