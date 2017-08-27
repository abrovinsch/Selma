# -*- coding: utf-8 -*-
#!/usr/bin/python

import re, sys
from selma_parser import SelmaParseException
from selma import SelmaEventCard
"Loads a .selma file and adds all it's data"
def load_selma_file(path):

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
    # Remove
    #file_content = re.sub(r'\n *','',file_content)

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
    cards = list()

    separate_cards_regex = r'card\s*(_LITERAL_\d+)\s*\{([^\}]*)\}'
    card_text_pieces = re.findall(separate_cards_regex,file_content,flags=0)

    # Parse each card_text_pieces into a SelmaEventCard
    index = 0
    while index < len(card_text_pieces):
        card_name, card_text = card_text_pieces[index]
        card_name = literal_dictionary[card_name][1:-1]
        cards.append(parse_text_to_card(card_name,card_text,literal_dictionary))
        index += 1

    return cards

"Parses a string into a SelmaEventCard"
def parse_text_to_card(name, card_text,literal_dictionary):

    conditions = get_string_from_card_group("conditions",card_text,literal_dictionary)
    effects =    get_string_from_card_group("effects",   card_text,literal_dictionary)

    if len(effects) == 0:
        raise SelmaParseException("Card '%s' must have at least one effect!" % name)

    card = SelmaEventCard(name, conditions, effects)
    return card

"Returns every line from inside a group () statement"
def get_string_from_card_group(group_name, card_text,literal_dictionary):
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
