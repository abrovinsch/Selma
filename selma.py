# -*- coding: utf-8 -*-
#!/usr/bin/python
"""
This is the main module of 'Selma'
by Oskar Lundqvist / Abrovinsch (c) 2017

Selma is a program used to generate story plots,
by using a dynamic world-state which gets altered
by user defined 'event cards'. The event cards
involves characters and has requirements of the world
state to be picked.
"""
import random
import operator
from collections import defaultdict
import selma_file_reader
import selma_parser as parser

class SelmaCharacter:
    """
    A SelmaCharacter is a character which can be picked
    to play roles in the simulation.
    """

    def __init__(self):
        """This Initializes the SelmaCharacter"""
        self.name = "no name"
        self.gender = ""
        self.age = 0
        self.attributes = []
        self.personality = []
        self.inventory = []
        self.mood = "neutral"
        self.job = ""
        self.happiness = 0
        self.var = {}
        self.world = 0

    def __str__(self):
        """This returns a multiline string representation of
        the SelmaCharacter"""
        result = "<---Character %s--->" % self.name

        if self.attributes:
            result += "  effects=%s\n" % self.attributes

        if self.personality:
            result += "  personality=%s\n" % self.personality

        if self.inventory:
            result += "  inventory=%s\n" % self.inventory

        if self.var:
            result += "  var=%s\n" % self.var

        return result


class SelmaEventCard:
    """
    A SelmaEventCard is a 'template' for a possible event
    which can randomly be drawn by the simulation.

    The card has 'conditions', which are statements about
    the world-state which must be true for the car to be picked

    The card also have 'roles'. Every role on the card must
    be matched by a character who fullfills certain condition.
    If no character can fill a role on the card, the card
    cannot be picked.

    Finally, a card also has 'effects', which are statements
    which alter the world-state if this card gets picked.
    """

    def __init__(self,
                 name="unnamed event card",
                 conditions=0,
                 effects=0,
                 next_cards=0,
                 role_tuples=0):
        """
        This Initializes the object.
        At initialization, we copy all of the supplied variables
        """

        self.name = name

        if conditions:
            self.conditions = conditions.copy()
        else:
            self.conditions = []

        if effects:
            self.effects = effects.copy()
        else:
            self.effects = []

        if next_cards:
            self.next_cards = next_cards.copy()
        else:
            self.next_cards = []

        self.text_out = "#%s#" % name

        self.roles = {}
        if role_tuples:
            for role_name, role_conditions in role_tuples:
                if role_name:
                    self.roles[role_name] = role_conditions

    def fullfill_conditions(self, obj, _attributes, card_name):
        """
        Returns true if all the condtions on this card are met
        and every role can be filled
        """

        # Empty the roles dictionary
        obj.roles = {}

        if not self.conditions and not self.roles:
            return True

        # Pick a random character in the cast until
        # we find someone to fill the role
        taken_characters = []

        for role in self.roles:

            conditions = self.roles[role]
            characters_to_try = list(obj.cast)

            # We don't test any characters that has already gotten a role
            for taken_character in taken_characters:
                if taken_character in characters_to_try:
                    characters_to_try.remove(taken_character)

            # Loop until we find someone to fill the role or we
            # run out of characters to try for it
            while characters_to_try and not role in obj.roles:

                # This is done because it is very important
                # that the characters are tested in random order!
                candidate = random_item_from_list(characters_to_try)

                passes_all_conditions = True
                for condition in conditions:
                    try:
                        evaluation_result = parser.evaluate_condition(obj.cast[candidate],
                                                                      condition)
                    except Exception as exception:
                        print("Error while testing condition '%s' on card '%s'"
                              % (condition, card_name))
                        raise parser.SelmaParseException(exception)

                    # If this guy doesn't cut it, ignore him and try the next one
                    if not evaluation_result:
                        passes_all_conditions = False
                        characters_to_try.remove(candidate)
                        break

                # This person gets the role
                if passes_all_conditions:
                    obj.roles[role] = obj.cast[candidate]
                    taken_characters.append(candidate)

            # No one could fill the role, so return False
            if not role in obj.roles:
                obj.roles = {}
                return False

        # Test every condition on the card itself
        for condition in self.conditions:
            if not parser.evaluate_condition(obj, condition):
                return False

        return True

    def __str__(self):
        result = "<---%s--->\n" % self.name

        if self.effects:
            result += "  effects=%s\n" % self.effects

        if self.conditions:
            result += "  conditions=%s\n" % self.conditions

        if self.roles:
            result += "  <- Roles ->\n"
            for role in self.roles:
                result += "    %s=%s\n" % (role[0], role[1])

        if self.next_cards:
            result += "  next=%s\n" % self.next_cards

        return result


class SelmaStorySimulation:
    """
    A SelmaStorySimulation object contains all the data of a
    Selma simulation.
    """

    def __init__(self,
                 debug_mode=True,
                 allow_output=True):
        """This Initializes the object."""
        self.draw_deck = []
        self.event_cards = {}

        self.all_card_names = []
        self.all_character_names = []

        self.draw_deck_size = 5

        self.attributes = []
        self.var = {}
        self.cast = {}
        self.roles = {}

        self.past_events = []

        self.debug_mode = debug_mode
        self.allow_output = allow_output
        parser.allow_print_out = allow_output

        self.past_events = []
        self.steps_count = 0

        if self.allow_output:
            print("\n👵🏻---👵🏻--SELMA STORY SIMULATION--👵🏻---👵🏻\n")

    def load_from_file(self, path):
        """Loads cards and characters into this simulation from a .selma file"""

        if self.allow_output:
            print("<-Load file '%s'->\n" % path)

        selma_file_reader.load_selma_file(self, path)

        if self.allow_output:
            print("")

    def add_to_deck(self,
                    name="unnamed card",
                    effects=0,
                    conditions=0,
                    next_cards=0,
                    role_tuples=0,
                    amount=1):
        """This function makes a copy of the supplied
        card and add n instances of it to the deck"""

        if self.debug_mode:
            print("Add card '%s' to deck" % name)

        self.event_cards[name] = SelmaEventCard(name,
                                                conditions,
                                                effects,
                                                next_cards,
                                                role_tuples)

        # Reset the list of all card names
        self.all_card_names = []
        for card_name in self.event_cards:
            for _ in range(0, amount):
                self.all_card_names.append(card_name)

    def add_character_to_cast(self,
                              name,
                              init_effects,
                              attributes,
                              inventory):
        """Adds a character to the cast"""

        if self.debug_mode:
            print("Add character '%s' to cast" % name)

        self.cast[name] = SelmaCharacter()
        self.cast[name].name = name
        self.cast[name].world = self
        self.cast[name].attributes = attributes.copy()
        self.cast[name].inventory = inventory.copy()

        # Execute the init "script" to set variables etc.
        for effect in init_effects:
            try:
                parser.execute_effect(self.cast[name], effect)
            except Exception as exception:
                raise parser.SelmaParseException(exception)

        # Recreate the character list
        self.all_character_names = list(self.cast.keys())


    def sim_step(self):
        """Do a single step of the simulation"""

        if self.debug_mode:
            print("<Simstep %s>" % self.steps_count)

        # If there is a "start" card, execute it's effects before
        # the simulation begins, and then remove it
        start_card_name = "start"
        if self.steps_count == 0 and start_card_name in self.all_card_names:
            # Execute the effects of the start card
            for effect in self.event_cards[start_card_name].effects:
                try:
                    parser.execute_effect(self, effect)
                except Exception as exception:
                    print("Error in start card")
                    raise parser.SelmaParseException(exception)

            # Add the start cards "next"s to the draw deck
            for card_name in self.event_cards[start_card_name].next_cards:
                self.add_card_to_draw_deck(card_name)

            self.all_card_names.remove(start_card_name)

        # Take a new card until we have found one that fulfill the condtions
        have_found_card = False
        while not have_found_card:

            # Add any cards needed to fill the draw deck
            while len(self.draw_deck) < self.draw_deck_size:
                self.draw_deck.append("#")

            # Take a new random card from the draw deck
            picked_card_string = random_item_from_list(self.draw_deck)
            if picked_card_string == "#":
                picked_card_string = random_item_from_list(self.all_card_names)
            picked_card = self.event_cards[picked_card_string]

            # Test if the card can be chosen
            if picked_card.fullfill_conditions(self,
                                               self.attributes,
                                               picked_card.name):
                have_found_card = True

            # Discard any card we have tried
            if picked_card.name in self.draw_deck:
                self.draw_deck.remove(picked_card_string)

        # Add the next cards to the draw deck
        for next_card_name in picked_card.next_cards:
            self.add_card_to_draw_deck(next_card_name)

        # Save all the requirements of this card in a list
        # so we can use it to determine which cards caused event
        requirements = []
        for req in picked_card.conditions:
            requirements.append(parser.SelmaStatement(self, req))

        for role in picked_card.roles:
            for line in picked_card.roles[role]:
                requirements.append(parser.SelmaStatement(self.roles[role], line))

        effect_statements = {}

        # Execute the effects of the card
        for effect in picked_card.effects:
            try:
                statement = parser.SelmaStatement(self, effect)
                val_before = statement.var_holder[statement.var_name]
                parser.execute_statement(statement)
                val_after = statement.var_holder[statement.var_name]

                if statement.var_type == "float":
                    delta = val_after - val_before
                elif val_before == val_after:
                    delta = 0.0
                else:
                    delta = 1.0

                effect_statements[statement] = delta

            except Exception as exception:
                print("Error while executing effect '%s' on card '%s'"
                      % (effect, picked_card_string))
                raise parser.SelmaParseException(exception)

        if self.debug_mode:
            print("Picked card: '%s'" % picked_card.name)
            print("Attributes: %s" % self.attributes)
            print("Cast: %s" % list(self.cast.keys()))
            print("Draw deck: %s\n" % self.draw_deck)

        # Log this event
        event = SelmaEvent(event_name=picked_card.name,
                           roles=self.roles,
                           effects=effect_statements,
                           requirements=requirements,
                           previous_events=self.past_events,
                           event_id=len(self.past_events))

        self.past_events.append(event)
        self.steps_count += 1

    def add_card_to_draw_deck(self, card_name):
        """Adds the card named "card_name" to the deck of possible cards"""

        if card_name == "#" or card_name in self.all_card_names:
            self.draw_deck.append(card_name)
            del self.draw_deck[0] # Discard the oldest card in the deck
        else:
            raise SelmaException(
                """Cannot add card name '%s to the draw deck /
                because there is no card with that name"""
                % (card_name))

    def execute_effect(self, effect):
        """Execute an effect on this scope"""
        parser.execute_effect(self, effect)

    def evaluate_condition(self, condition):
        """Evaluates a condition on this scope, returns True/False"""
        return parser.evaluate_condition(self, condition)


class SelmaException(Exception):
    """A class for general Exceptions within selma"""
    pass


class SelmaEvent:
    """This class contains information about an event which has occured"""

    def __init__(self,
                 event_name,
                 effects,
                 requirements,
                 roles,
                 previous_events,
                 event_id=-1):

        self.event_name = event_name
        self.event_id = event_id
        self.subject = 0
        self.object = 0
        self.causing_events = []
        self.values_affecting = []
        self.importance = 0

        # We save a record of who played what role in this event
        self.roles = {}
        for role in roles:
            self.roles[role] = roles[role].name

        if self.roles:
            self.subject = self.roles[list(self.roles.keys())[0]]
        if len(self.roles) > 1:
            self.object = self.roles[list(self.roles.keys())[1]]

        # Go through every conditional statement which allowed
        # this event to be executed and all values it depended on.
        # Then find any previous events, which also edited that value.
        # Those events may be considered causing events.
        causing_events_raw = defaultdict(lambda: 0)
        for requirement in requirements:
            if not requirement.full_var_name in self.values_affecting:
                self.values_affecting.append(requirement.full_var_name)

                # When it comes to lists and strings, OR numbers which
                # must have a precise value, only the latest edit
                # of the value is considered to be causing this event
                if (requirement.argument_type == parser.TYPE_STRING or
                        requirement.argument_type == parser.TYPE_LIST or
                        requirement.operator == parser.EQUAL or
                        requirement.operator == parser.NOT_EQUAL):

                    # Note: we reverse the list here so that newest
                    # items comes first, because we are looking for
                    # NEWEST event
                    for event in reversed(previous_events):
                        if requirement.full_var_name in event.values_modified:
                            causing_events_raw[event] = 1
                            break

                # When it comes to numbers, we treat cards that have to be as
                # large as possible or
                else:
                    for event in previous_events:
                        if requirement.full_var_name in event.values_modified:

                            delta = event.values_modified[requirement.full_var_name]

                            if (requirement.operator == parser.GREATER_EQUAL or
                                    requirement.operator == parser.GREATER):
                                if delta >= 0:
                                    causing_events_raw[event] += delta
                            elif (requirement.operator == parser.LESS_EQUAL or
                                  requirement.operator == parser.LESS):
                                if delta <= 0:
                                    causing_events_raw[event] += delta

        # We weight the causation by how big the differnce was.
        # Example: if one event added 50 to happiness and  another one only 5,
        # the weight of the first event will be  10x as big
        change_sum = {}
        causing_events_weighted = defaultdict(lambda:0)
        for requirement in requirements:
            req_name = requirement.full_var_name
            change_sum[req_name] = 0

            # First we calculate the value of all changes
            # made to the value we are examining
            for event in causing_events_raw:
                strength = causing_events_raw[event]
                if requirement.full_var_name in event.values_modified:
                    change_sum[req_name] += abs(strength)

            # Then we divide the strength of each causing event
            # with the total of all changes to produce a value from 0 to 1.
            for event in causing_events_raw:
                strength = causing_events_raw[event]
                if (requirement.full_var_name in event.values_modified and
                        change_sum[req_name] and
                        strength):
                    weighted_strength = abs(strength) / change_sum[req_name]
                    weighted_strength /= len(requirements)
                    causing_events_weighted[event] = weighted_strength

        # Finally we set the causing events to be the weighted version and
        # sort them by descending size so it becomes easy for users to remove
        # the least important events
        self.causing_events += causing_events_weighted.items()
        self.causing_events.sort(key=operator.itemgetter(1))
        self.causing_events.reverse()


        self.values_modified = {}
        for effect in effects:
            if not effect.full_var_name in self.values_modified:
                self.values_modified[effect.full_var_name] = effects[effect]

    def __str__(self):
        return "EVENT %s: '%s'" % (self.event_id, self.as_sentence())

    def as_sentence(self):
        """Returns a sentence which describes the event"""

        if self.subject and self.object:
            name = "%s %s %s" % (self.subject, self.event_name, self.object)
            return name
        elif self.subject:
            name = "%s %s" % (self.subject, self.event_name)
            return name

        return self.event_name

def random_item_from_list(list_in):
    """Returns a random item from any list"""
    if not list_in:
        raise SelmaException("Can't grab random item from an empty list!")
    index = random.randint(0, len(list_in)-1)
    return list_in[index]
