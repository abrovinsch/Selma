# -*- coding: utf-8 -*-
#!/usr/bin/python

import random, selma_parser, selma_file_reader

class SelmaCharacter:
    def __init__(self):
        self.name= "no name"
        self.gender= ""
        self.age = 0
        self.attributes = list()
        self.personality = list()
        self.inventory = list()
        self.mood = "neutral"
        self.job = ""
        self.happiness = 0
        self.var = {}
        self.world = 0

    def __str__(self):
        result = "<---Character %s--->" % self.name;

        if len(self.attributes):
            result += "  effects=%s\n" % self.attributes

        if len(self.personality):
            result += "  personality=%s\n" % self.personality

        if len(self.inventory):
            result += "  inventory=%s\n" % self.inventory

        if len(self.var):
            var += "  var=%s\n" % self.var

        return result

class SelmaEventCard:

    'At initialization, copy all of the supplied variables'
    def __init__(self,
                name="unnamed event card",
                conditions=list(),
                effects=list(),
                next_cards=list(),
                roles=list()):

        self.name = name

        self.conditions = conditions.copy()
        self.effects = effects.copy()
        self.next_cards = next_cards.copy()

        self.text_out = "#%s#" % name

        self.roles = {}
        for role_tuple in roles:
            role_name, role_conditions = role_tuple
            if len(role_name) > 0:
                self.roles[role_name] = role_conditions

    'Returns true if all the condtions on this card are met'
    def fullfill_conditions(self,obj,_attributes,card_name):

        # Empty the roles dictionary
        obj.roles = {}

        if not len(self.conditions) and not len(self.roles) :
            return True

        # Pick a random character in the cast until
        # we find someone to fill the role
        taken_characters = list()

        for role in self.roles:

            conditions = self.roles[role]
            characters_to_try = list(obj.cast)

            # We don't test any characters that has already gotten a role
            for taken_character in taken_characters:
                if taken_character in characters_to_try:
                    characters_to_try.remove(taken_character)

            # Loop until we find someone to fill the role or we run out of
            # characters to try for it
            while len(characters_to_try) > 0 and not role in obj.roles:

                # This is done because it is very important
                # that the characters are tested in random order!
                candidate = random_item_from_list(characters_to_try)

                passes_all_conditions = True
                for condition in conditions:
                    try:
                        evaluation_result = selma_parser.evaluate_condition(
                                                obj.cast[candidate],
                                                condition)
                    except Exception as e:
                        print ("Error while testing condition '%s' on card '%s'"
                                % (condition, card_name))
                        raise selma_parser.SelmaParseException(e)

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
            if not selma_parser.evaluate_condition(obj,condition):
                return False

        return True

    def __str__(self):
        result = "<---%s--->\n" % self.name;

        if len(self.effects):
            result += "  effects=%s\n" % self.effects

        if len(self.conditions):
            result += "  conditions=%s\n" % self.conditions

        if len(self.roles):
            result += "  <- Roles ->\n"
            for role in self.roles:
                result += "    %s=%s\n" % (role[0],role[1])


        if len(self.next_cards):
            result += "  next=%s\n" % self.next_cards

        return result

class SelmaStorySimulation:

    def __init__(self,debug_mode=True,allow_output=True):


        self.draw_deck = list()
        self.event_cards = {}

        self.all_card_names = list()

        self.draw_deck_size = 5

        self.attributes = list()
        self.var = {}

        self.cast = {}
        self.roles = {}

        self.past_events = list()

        self.debug_mode = debug_mode
        self.allow_output = allow_output
        selma_parser.allow_print_out = allow_output

        self.past_events = list()
        self.steps_count = 0

        if(self.allow_output):
            print ("\n<------SELMA STORY SIMULATION------>\n")

    "Loads cards and characters into this simulation from a .selma file"
    def load_from_file(self, path):

        if self.allow_output:
            print("<-Load file '%s'->\n" % path)

        selma_file_reader.load_selma_file(self,path)

        if self.allow_output:
            print("")

    'This function makes a copy of the supplied'
    'card and add n instances of it to the deck'
    def add_to_deck(self,
                    name="unnamed card",
                    effects=list(),
                    conditions=list(),
                    next_cards=list(),
                    roles=list(),
                    amount=1):

        if self.debug_mode:
            print("Add card '%s' to deck" % name)

        # Add as many copies of the card as defined
        for i in range(0,amount):
            self.event_cards[name] = SelmaEventCard(name,
                                                    conditions,
                                                    effects,
                                                    next_cards,
                                                    roles)

        # Reset the list of all card names
        self.all_card_names = list()
        for card_name in self.event_cards.keys():
            for i in range(0,amount):
                self.all_card_names.append(card_name)

    'Adds a character to the cast'
    def add_character_to_cast(self,
                             name,
                             init_effects,
                             attributes,
                             inventory):
        if self.debug_mode:
            print("Add character '%s' to cast" % name)

        self.cast[name] = SelmaCharacter()
        self.cast[name].name = name
        self.cast[name].world = self
        self.cast[name].attributes = attributes.copy()
        self.cast[name].inventory = inventory.copy()

        # Execute the init "script" to set variables etc.
        for fx in init_effects:
            try:
                selma_parser.execute_effect(self.cast[name],fx)
            except Exception as e:
                raise selma_parser.SelmaParseException(e)

        # Recreate the character list
        self.all_character_names = list(self.cast.keys())

    'Do a single step of the simulation'
    def sim_step(self):
        if(self.debug_mode):
            print("<Simstep %s>" % self.steps_count)

        have_found_card = False

        # If there is a "start" card, execute it's effects before
        # the simulation begins, and then remove it
        start_card_name = "start"
        if self.steps_count == 0 and start_card_name in self.all_card_names:
            # Execute the effects of the start card
            for fx in self.event_cards[start_card_name].effects:
                try:
                    selma_parser.execute_effect(self,fx)
                except Exception as e:
                    print ("Error in start card")
                    raise selma_parser.SelmaParseException(e)

            # Add the start cards "next"s to the draw deck
            for card_name in self.event_cards[start_card_name].next_cards:
                self.add_card_to_draw_deck(card_name)

            self.all_card_names.remove(start_card_name)

        # Take a new card until we have found one that fulfill the condtions
        while not have_found_card:

            # Check if we need to add new cards to the draw deck
            while len(self.draw_deck) < self.draw_deck_size:
                self.draw_deck.append("#")

            # Take a new random card from the draw deck
            picked_card_string = random_item_from_list(self.draw_deck)
            if picked_card_string == "#":
                picked_card_string = random_item_from_list(self.all_card_names)
            picked_card = self.event_cards[picked_card_string]

            # Discard any card we have tried and failed
            if picked_card.name in self.draw_deck:
                self.draw_deck.remove(picked_card_string)

            if picked_card.fullfill_conditions(self,
                                               self.attributes,
                                               picked_card.name):
                have_found_card = True

        #Add the next cards to the draw deck
        for card_name in picked_card.next_cards:
            self.add_card_to_draw_deck(card_name)

        #Execute the effects of the card
        for fx in picked_card.effects:
            try:
                selma_parser.execute_effect(self,fx)
            except Exception as e:
                print ("Error while executing effect '%s' on card '%s'"
                        % (fx, picked_card_string))
                raise selma_parser.SelmaParseException(e)


        if(self.debug_mode):
            print("Picked card: '%s'" % picked_card.name)
            print("Attributes: %s" % self.attributes)
            print("Cast: %s" % list(self.cast.keys()))
            print("Draw deck: %s\n" % self.draw_deck)


        # Log this event
        event = SelmaEvent(event_card=picked_card,
                           roles= self.roles,
                           previous_events=self.past_events,
                           id=len(self.past_events))
        self.past_events.append(event)

        self.steps_count += 1

    'Adds the card named "card_name" to the deck of possible cards'
    def add_card_to_draw_deck(self, card_name):
        if card_name == "#" or card_name in self.all_card_names:
            self.draw_deck.append(card_name)
            del self.draw_deck[0] # Discard the oldest card in the deck
        else:
            raise SelmaException(
                "Cannot add card name '%s'(on card '%s'.next) to the draw deck because there is no card with that name"
                % (card_name, picked_card_string)
            )

    'Execute an effect on this scope'
    def execute_effect(self,effect):
        selma_parser.execute_effect(self,effect)

    'Evaluates a condition on this scope'
    def evaluate_condition(self,condition):
        return selma_parser.evaluate_condition(self,condition)

'Returns a random item from any list'
def random_item_from_list(l):
    if len(l) == 0:
        raise SelmaException("Can't grab random item from an empty list!")
    index = random.randint(0,len(l)-1)
    return l[index]

class SelmaException (Exception):
    pass

'This class contains information about an event which has occured'
class SelmaEvent:

    def __init__(self, event_card, roles, previous_events, id=0):
        self.event_name = event_card.name
        self.id = id
        self.roles = {}
        self.subject = 0
        self.object = 0

        self.set_roles(roles)

        self.values_affecting = self.get_values_affecting(event_card)
        self.values_modified = self.get_values_modified(event_card.effects)

        self.causing_events = list()

        for prev_event in previous_events:
            for val in self.values_affecting:
                if val in prev_event.values_modified:
                    if not prev_event in self.causing_events and len(self.causing_events) < 4:
                        self.causing_events.append(prev_event)


    def __str__(self):
        return "EVENT %s: '%s'" % (self.id,self.as_sentence())

    "Returns a sentence which describes the event"
    def as_sentence(self):
        if self.subject and self.object:
            name = "%s %s to %s" % (self.subject, self.event_name, self.object)
            return name
        elif self.subject:
            name = "%s %s" % (self.subject, self.event_name)
            return name
        else:
            return self.event_name


    "Copy the the name of the roles and the character into a new dictionary"
    def set_roles(self, roles):
        for r in roles:
            self.roles[r] = roles[r].name

        if len(self.roles) > 0:
            self.subject = self.roles[list(self.roles.keys())[0]]
        if len(self.roles) > 1:
            self.object = self.roles[list(self.roles.keys())[1]]

    "Returns a list(string) of every value that is affected by this event"
    def get_values_modified(self,event_effects):
        values = list()

        for fx in event_effects:
            value = fx[:fx.index(" ")]

            # Replace role references to a global refernce to
            # the character who filled that role
            for r in self.roles:
                value = value.replace("roles.%s" % r, "cast.%s" % self.roles[r])

            if not value in values:
                values.append(value)
        return values

    "Returns a list(string) of every value that played a role"
    "in selecting this event"
    def get_values_affecting(self,event_card):
        values = list()

        for condition in event_card.conditions:
            value = condition[:condition.index(" ")]

            if not value in values:
                values.append(value_name)

        # Convert the scope to global in the strings and replace
        # role references with the character who filled that role
        for role in event_card.roles:
            role_requirements = event_card.roles[role]

            character_name = self.roles[role]

            for req in role_requirements:
                value_name = req[:req.index(" ")]
                value = "cast.%s.%s"%(character_name , value_name)

                if not value in values:
                    values.append(value)

        return values
