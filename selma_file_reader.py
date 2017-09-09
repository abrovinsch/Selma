# -*- coding: utf-8 -*-
#!/usr/bin/python

"""
This is a module of 'Selma'
by Oskar Lundqvist / Abrovinsch (c) 2017

This module is responsible reading a .selma
file and add it's contents to the simulation
"""

import re
from selma_parser import SelmaParseException

def load_selma_file(selma_sim_object, path):
    """Loads a .selma file and adds all it's data"""
    # Extract the name of the file and the directory from the path
    search_object = re.search(r'/([^/]+\.selma)', path, flags=0)
    file_name = search_object.group(1)

    # Ignore files that does not have a .selma extension
    if not file_name.endswith(".selma"):
        raise SelmaParseException("Cannot only read files with a .selma extension (%s)" % path)

    # This is where we find other files to load
    #TODO: dictionary_directory = path.replace(file_name, "")

    # Load the contents of the original file
    source_file = open(path)
    file_content = source_file.read()
    source_file.close()

    # Insert any referenced files
    #TODO: file_content = insert_external_files(file_content, dictionary_directory)

    # Remove double spaces
    file_content = re.sub(r'  *', ' ', file_content)
    # Remove whitespace in beginning of lines
    file_content = re.sub(r'\n\s*', '\n', file_content)
    # Remove empty lines
    file_content = re.sub(r'\n+', '\n', file_content)
    # Remove inline comments
    file_content = re.sub(r'//.*', '\n', file_content)
    # Remove multiline comments
    file_content = re.sub(r'/\*[\S|\s]*\*/', '', file_content)

    # Replace string literals
    find_string_literals_regex = r'\"[^\"]*\"'
    all_string_literals = re.findall(find_string_literals_regex,
                                     file_content,
                                     flags=0)
    literal_dictionary = {}

    index = 0
    for literal in all_string_literals:
        if not literal in literal_dictionary.values():
            literal_name = "_LITERAL_%s" % index
            literal_dictionary[literal_name] = literal
            file_content = file_content.replace(literal, literal_name)
            index += 1

    # Separate each card into different strings
    cards = get_definitions_of_type_in_text("card",
                                            file_content,
                                            literal_dictionary)

    for card_tuple in cards:
        card_name, card_text = card_tuple
        name, conditions, effects, next_cards, roles = text_to_card_contents(card_name, card_text, literal_dictionary)
        selma_sim_object.add_to_deck(name, effects, conditions, next_cards, roles)

    # Separate each character into different strings
    characters = get_definitions_of_type_in_text("char",
                                                 file_content,
                                                 literal_dictionary)

    for character_tuple in characters:
        character_name, character_text = character_tuple
        init_effects, attributes, inventory = text_to_char_contents(character_text, literal_dictionary)
        selma_sim_object.add_character_to_cast(character_name, init_effects, attributes, inventory)



def text_to_card_contents(name, card_text, literal_dictionary):
    """Parses a string for a event card"""
    conditions = get_strings_inside_parentheses("conditions",
                                                card_text,
                                                literal_dictionary)
    effects = get_strings_inside_parentheses("effects",
                                             card_text,
                                             literal_dictionary)
    next_cards = get_strings_inside_parentheses("next",
                                                card_text,
                                                literal_dictionary)

    # Find all roles
    roles = list() # list of tuples of type name:string, lines:list(string)
    find_roles_regex = r'role\s*(_LITERAL_\d+)\s*(\([^\)]*\))'
    role_strings = re.findall(find_roles_regex, card_text, flags=0)

    for role_string in role_strings:
        role_name, role_content = role_string
        role_name = literal_dictionary[role_name][1:-1]
        role_lines = get_strings_inside_parentheses("", role_content, literal_dictionary)
        role_tuple = role_name, role_lines
        roles.append(role_tuple)

    # Remove the quotes from the next card strings
    cleaned_next_cards = list()
    for card in next_cards:
        cleaned_next_cards.append(card[1:-1])

    return name, conditions, effects, cleaned_next_cards, roles


def text_to_char_contents(character_text, literal_dictionary):
    """Parses a string for a event card"""

    init_effects = get_strings_inside_parentheses("init",
                                                  character_text,
                                                  literal_dictionary)
    attributes = get_strings_inside_parentheses("attributes",
                                                character_text,
                                                literal_dictionary)
    inventory = get_strings_inside_parentheses("inventory",
                                               character_text,
                                               literal_dictionary)

    return init_effects, attributes, inventory


def get_strings_inside_parentheses(group_name,
                                   card_text,
                                   literal_dictionary,
                                   use_string=False):
    """Returns every line from inside a () statement"""
    results = list()

    find_group_regex = r'%s\s*\(([^\)]*)\)' % group_name
    search_object = re.search(find_group_regex, card_text, flags=0)

    whole_group_string = ""
    if search_object:
        if use_string:
            whole_group_string = search_object.group(2)
        else:
            whole_group_string = search_object.group(1)

        for line in whole_group_string.split("\n"):
            if line:   #Ignore empty lines
                line = line.strip()
                find_literal_regex = r'(_LITERAL_\d+)'

                # Replace every literal on the line
                match_literal_object = re.search(find_literal_regex, line, flags=0)
                while match_literal_object:
                    literal = match_literal_object.group(1)
                    line = line.replace(literal, literal_dictionary[literal])
                    match_literal_object = re.search(find_literal_regex, line, flags=0)
                results.append(line)
        return results
    else:
        return list()

def get_definitions_of_type_in_text(type_string, text, literal_dictionary):
    """Returns every definition{} in the text as a list of tuples,
    each containing the name of the definition and it's text"""

    all_instances = list()
    find_defintions_regex = r'%s\s*(_LITERAL_\d+)\s*\{([^\}]*)\}' % type_string

    all_definitions = re.findall(find_defintions_regex, text, flags=0)

    # Parse each definition into a tuple containing name and it's text
    index = 0
    while index < len(all_definitions):
        def_name, def_text = all_definitions[index]
        def_name = literal_dictionary[def_name][1:-1]
        _tuple = def_name, def_text
        all_instances.append(_tuple)
        index += 1

    return all_instances
