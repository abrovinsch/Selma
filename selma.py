# -*- coding: utf-8 -*-
#!/usr/bin/python

from collections import defaultdict
import random, selma_parser

class SelmaCharacter:
    def __init__(self):
        self.name= "no name"
        self.age = 0
        self.attributes = list()
        self.inventory = list()
        self.mood = "neutral"

class SelmaEventCard:

    'At initialization, copy all of the supplied variables'
    def __init__(self,name="unnamed event card",conditions=list(),effects=list()):

        self.name = name

        self.conditions = conditions.copy()
        self.effects = effects.copy()

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

        return result

class SelmaStorySimulation:


    steps_count = 0
    log = ""

    debug_mode = True

    event_cards = list()
    draw_deck = list()

    def __init__(self):
        print ("\n<------SELMA STORY SIMULATION------>\n")
        self._draw_deck = list()
        self._event_cards = list()

        self.attributes = list()
        self.character1 = SelmaCharacter()
        self.character2 = SelmaCharacter()
        self.custom_vars = defaultdict()

    'This function makes a copy of the supplied'
    'card and add n instances of it to the deck'
    def add_to_deck(self,name="unnamed card",effects=list(),conditions=list(),amount=1):
        for i in range(0,amount):
            self.event_cards.append(
                SelmaEventCard(name,conditions,effects)
            )


    'Do a single step of the simulation'
    def sim_step(self):
        if(self.debug_mode):
            print("<Simstep %s>" % self.steps_count)

        # Take a new card until we have found one that fulfill the condtions
        have_found_card = False
        while not have_found_card:
            # Check if we need to reshuffle the event cards
            if len(self.draw_deck) == 0:
                for card in self.event_cards:
                    self.draw_deck.append(card)

            # Take a new random card from the pile
            picked_card = random_item_from_list(self.draw_deck)

            # Discard any card we have tried and failed
            self.draw_deck.remove(picked_card)

            if picked_card.fullfill_conditions(self,self.attributes):
                have_found_card = True

        #Execute the effects of the card
        if(self.debug_mode):
            print ("Picked card: '%s'" % picked_card.name)

        for fx in picked_card.effects:
            selma_parser.execute_effect(self,fx)

        if(self.debug_mode):
            print("Attributes: %s\n" % self.attributes)
        self.log += picked_card.text_out + "\n"
        self.steps_count += 1

'Returns a random item from any list'
def random_item_from_list(l):

    if len(l) == 0:
        print("Error: Can't grab item from empty list")
        return

    index = random.randint(0,len(l)-1)
    return l[index]
