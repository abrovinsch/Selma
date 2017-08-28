# -*- coding: utf-8 -*-
#!/usr/bin/python

import re, sys
from selma_parser import SelmaParseException

"Loads a .selma file and adds all it's data"
def load_selma_file(selma_sim_object,path):

    # Extract the name of the file and the directory from the path
    search_object = re.search(r'/([^/]+\.selma)',path,flags=0)
    file_name = search_object.group(1)

    # Ignore files that does not have a .selma extension
    if not file_name.endswith(".selma"):
        raise SelmaParseException("Cannot only read files with a .selma extension (%s)" % path)

    # This is where we find other files to load
    dictionary_directory = path.replace(file_name,"")

    # Load the contents of the original file
    source_file = open(path)
    file_content = source_file.read()
    source_file.close()

    # Insert any referenced files
    #TODO: file_content = insert_external_files(file_content, dictionary_directory)

    # Remove double spaces
    file_content = re.sub(r'  *',' ',file_content)

    # Remove starting spaces
    file_content = re.sub(r'\n *','\n',file_content)

    # Replace string literals
    find_string_literals_regex = r'\"[^\"]*\"'
    all_string_literals = re.findall(find_string_literals_regex,file_content,flags=0)
    literal_dictionary = {}

    index = 0
    for s in all_string_literals:
        if not s in literal_dictionary.values():
            literal_name = "_LITERAL_%s" % index
            literal_dictionary[literal_name] = s
            file_content = file_content.replace(s,literal_name)
            index += 1

    # Separate each card into different strings
    cards = get_definitions_of_type_in_text("card",file_content,literal_dictionary)

    for card_tuple in cards:
        card_name, card_text = card_tuple
        name, conditions, effects, next_cards = parse_text_to_card_contents(card_name,card_text,literal_dictionary)
        selma_sim_object.add_to_deck(name, effects, conditions, next_cards)

    # Separate each character into different strings
    characters = get_definitions_of_type_in_text("char",file_content,literal_dictionary)

    for character_tuple in characters:
        character_name, character_text = character_tuple

        selma_sim_object.add_character_to_cast(character_name)


"Parses a string into a SelmaEventCard"
def parse_text_to_card_contents(name, card_text,literal_dictionary):

    conditions =    get_strings_inside_parentheses("conditions",card_text,literal_dictionary)
    effects    =    get_strings_inside_parentheses("effects",   card_text,literal_dictionary)
    next_cards =    get_strings_inside_parentheses("next",      card_text,literal_dictionary)

    cleaned_next_cards = list()
    for card in next_cards:
        cleaned_next_cards.append(card[1:-1])

    if len(cleaned_next_cards) == 0:
        cleaned_next_cards.append("#")

    return name, conditions, effects, cleaned_next_cards


"Returns every line from inside a () statement"
def get_strings_inside_parentheses(group_name, card_text,literal_dictionary):
    results = list()

    find_group_regex = r'%s\s*\(([^\)]*)\)' % group_name
    search_object = re.search(find_group_regex,card_text,flags=0)

    whole_group_string = ""
    if(search_object):
        whole_group_string = search_object.group(1)

        for line in whole_group_string.split("\n"):
            if len(line) > 0:
                line = line.strip()
                find_literal_regex = r'(_LITERAL_\d)+'
                match_literal_object = re.search(find_literal_regex,line,flags=0)

                if match_literal_object:
                    literal = match_literal_object.group(1)
                    line = line.replace(literal,literal_dictionary[literal])
                results.append(line)
        return results
    else:
         return list()

"Returns every definition{} in the text as a list of tuples,"
"each containing the name of the definition and it's text"
def get_definitions_of_type_in_text(type,text,literal_dictionary):
    all_instances = list()
    find_defintions_regex = r'%s\s*(_LITERAL_\d+)\s*\{([^\}]*)\}' % type

    all_definitions = re.findall(find_defintions_regex,text,flags=0)

    # Parse each definition into a tuple containing name and it's text
    index = 0
    while index < len(all_definitions):
        def_name, def_text = all_definitions[index]
        def_name = literal_dictionary[def_name][1:-1]
        _tuple = def_name, def_text
        all_instances.append(_tuple)
        index += 1

    return all_instances
