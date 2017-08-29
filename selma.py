# -*- coding: utf-8 -*-
#!/usr/bin/python

from collections import defaultdict
import random, selma_parser, selma_file_reader

class SelmaCharacter:
    def __init__(self):
        self.name= "no name"
        self.age = 0
        self.attributes = list()
        self.inventory = list()
        self.mood = "neutral"
        self.var = {}

    def __str__(self):
        result = "<---Character %s--->" % self.name;
        return result

class SelmaEventCard:

    'At initialization, copy all of the supplied variables'
    def __init__(self,name="unnamed event card",conditions=list(),effects=list(),next_cards=list()):

        self.name = name

        self.conditions = conditions.copy()
        self.effects = effects.copy()
        self.next_cards = next_cards.copy()

        self.character1 = SelmaCharacter()
        self.character2 = SelmaCharacter()
        self.text_out = "#%s#" % name

    'Returns true if all the condtions on this card are met'
    def fullfill_conditions(self,obj,_attributes):

        if len(self.conditions) == 0:
            return True

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

        if len(self.next_cards):
            result += "  next=%s\n" % self.next_cards

        return result

class SelmaStorySimulation:

    def __init__(self):
        print ("\n<------SELMA STORY SIMULATION------>\n")

        self.draw_deck = list()
        self.event_cards = {}

        self.all_card_names = list()

        self.draw_deck_size = 5

        self.attributes = list()
        self.var = {}

        self.cast = {}

        self.debug_mode = True
        self.log = ""
        self.steps_count = 0

    "Loads cards and characters into this simulation from a .selma file"
    def load_from_file(self, path):
        print("<-Load file '%s'->\n" % path)
        selma_file_reader.load_selma_file(self,path)
        print("")

    'This function makes a copy of the supplied'
    'card and add n instances of it to the deck'
    def add_to_deck(self,name="unnamed card",effects=list(),conditions=list(),next_cards=list(),amount=1):

        if self.debug_mode:
            print("Add card '%s' to deck" % name)

        for i in range(0,amount):
            self.event_cards[name] = SelmaEventCard(name,conditions,effects,next_cards)


        self.all_card_names = list()
        for card_name in self.event_cards.keys():
            self.all_card_names.append(card_name)

    'Adds a character to the cast'
    def add_character_to_cast(self,name, init_effects, attributes, inventory):
        if self.debug_mode:
            print("Add character '%s' to cast" % name)

        self.cast[name] = SelmaCharacter()
        self.cast[name].name = name
        self.cast[name].attributes = attributes.copy()
        self.cast[name].inventory = inventory.copy()

        # Set all the variables
        for fx in init_effects:
            selma_parser.execute_effect(self.cast[name],fx)

        self.all_character_names = list()
        for character_name in self.cast.keys():
            self.all_character_names.append(character_name)

    'Do a single step of the simulation'
    def sim_step(self):
        if(self.debug_mode):
            print("<Simstep %s>" % self.steps_count)

        have_found_card = False

        # If there is a "start" card, execute it's effects before the simulation begins, and then remove it
        start_card_name = "start"
        if self.steps_count == 0 and start_card_name in self.all_card_names:
            # Execute the effects of the start card
            for fx in self.event_cards[start_card_name].effects:
                selma_parser.execute_effect(self,fx)

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

            if picked_card.fullfill_conditions(self,self.attributes):
                have_found_card = True

        #Add the next cards to the draw deck
        for card_name in picked_card.next_cards:
            self.add_card_to_draw_deck(card_name)

        #Execute the effects of the card
        for fx in picked_card.effects:
            selma_parser.execute_effect(self,fx)

        if(self.debug_mode):
            print ("Picked card: '%s'" % picked_card.name)
            print("Attributes: %s" % self.attributes)
            print("Cast: %s" % self.cast)
            print("Draw deck: %s\n" % self.draw_deck)

        self.log += picked_card.text_out + "\n"
        self.steps_count += 1

    'Adds the card named "card_name" to the deck of possible cards'
    def add_card_to_draw_deck(self, card_name):
        if card_name == "#" or card_name in self.all_card_names:
            self.draw_deck.append(card_name)
            del self.draw_deck[0]
        else:
            raise SelmaException("Cannot add card name '%s'(on card '%s'.next) to the draw deck because there is no card with that name" % (card_name, picked_card_string))

'Returns a random item from any list'
def random_item_from_list(l):

    if len(l) == 0:
        raise SelmaException("Can't grab from empty list!")
    index = random.randint(0,len(l)-1)
    return l[index]

class SelmaException (Exception):
    pass
