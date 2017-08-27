# -*- coding: utf-8 -*-
#!/usr/bin/python

import ast, re

"Execute the effect in 'line' on the object 'obj'"
def execute_effect(obj,line):

    var_name, var_holder, operator, value, var_type, value_type = parse_line_to_parts(obj,line)

    if operator == "=":
        if value_type == "float" or value_type == "int":
            var_holder.__dict__[var_name] = parse_as_number(operator,value)
        elif var_type == "list":
            var_holder.__dict__[var_name] = parse_as_list(value)
        else:
            var_holder.__dict__[var_name] = value

    elif operator == "append":
        if var_type == "list":
            var_holder.__dict__[var_name].append(value)
        else:
            raise parse_error_wrong_type(operator,value,var_name)

    elif operator == "append-list":
        if var_type == "list":
            list_to_append = parse_as_list(value)
            for item in list_to_append:
                var_holder.__dict__[var_name].append(item)
        else:
            raise parse_error_wrong_type(operator,value,var_name)

    elif operator == "remove":
        if var_type == "list":
            if value in var_holder.__dict__[var_name]:
                var_holder.__dict__[var_name].remove(value)
        else:
            raise parse_error_wrong_type(operator,value,var_name)

    elif operator == "remove-list":
        if var_type == "list":
            list_to_remove = parse_as_list(value)
            for item in list_to_remove:
                var_holder.__dict__[var_name].remove(item)
        else:
            raise parse_error_wrong_type(operator,value,var_name)

    elif operator == "+=":
        var_holder.__dict__[var_name] += parse_as_number(operator,value)
    else:
        raise SelmaParseException("Unknown operator '%s'" % operator)

"Return true if the statement in 'line' is true on object 'obj'"
def evaluate_condition(obj,line):
    var_name, var_holder, operator, value, var_type, value_type = parse_line_to_parts(obj,line)

    if operator == "=":
        if value_type == "int" or value_type == "float":
            return var_holder.__dict__[var_name] == parse_as_number(operator,value)
        elif var_type == "list":
            return var_holder.__dict__[var_name] == parse_as_list(value)
        else:
            return var_holder.__dict__[var_name] == value

    elif operator == ">":
        return var_holder.__dict__[var_name] > parse_as_number(operator,value)

    elif operator == "<":
        return var_holder.__dict__[var_name] < parse_as_number(operator,value)

    elif operator == ">=":
        if var_type == "int" or var_type == "float":
            return var_holder.__dict__[var_name] >= parse_as_number(operator,value)
        else:
            parse_error_wrong_type(operator,value,var_name)

    elif operator == "<=":
        return var_holder.__dict__[var_name] <= parse_as_number(operator,value)

    elif operator == "doesnt-contain":
        if var_type == "list":
            return not value in var_holder.__dict__[var_name]
        else:
            parse_error_wrong_type(operator,value,var_name)

    elif operator == "contains":
        if var_type == "list":
            return value in var_holder.__dict__[var_name]
        else:
            parse_error_wrong_type(operator,value,var_name)

    else:
        raise SelmaParseException("Unknown operator '%s'" % operator)

"Returns all the parts of a line: var_name, var_holder, operator, value, var_type, value_type"
def parse_line_to_parts(obj,line):
    line = line.strip()

    match_object = re.match(r'(\S+)\s+(\S+)\s+(.*)',line,flags=0)

    if not match_object:
        raise SelmaParseException("invalid syntax '%s'" % line)
    matches = match_object.groups()

    var_holder, var_name = get_variable_reference(obj,matches[0])
    operator = matches[1]
    value    = matches[2]

    value_type = get_type_from_literal(value)

    if value_type == "reference":
        value = get_value_from_reference(obj,value)
        value_type = value.__class__.__name__
    if value_type == "str":
        value = value[1:-1]

    if not var_name in var_holder.__dict__:
        t = var_holder.__class__.__name__
        raise SelmaParseException("There is no variable named '%s' on type %s" % (var_name, t))

    var_type = var_holder.__dict__[var_name].__class__.__name__

    return var_name, var_holder, operator, value, var_type, value_type

"Returns a reference to the variable which a string is refering to"
def get_variable_reference(parent_object, string):
    rest_string = ""
    var_name = string

    if "." in string:
        var_name = string[:string.index(".")]

        if var_name in parent_object.__dict__:
            parent_object = parent_object.__dict__[var_name]
            var_name = string[string.index(".")+1:]
        else:
            t = parent_object.__class__.__name__
            raise SelmaParseException("Object of type %s has no child variable named '%s'" % (t,var_name))

        rest_string   = string[string.index(".")+1:]


    if "." in rest_string:
        parent_object, var_name = get_variable_reference(parent_object, rest_string)
    else:
        return parent_object, var_name

"Returns the value from a string reference to a variable"
def get_value_from_reference(obj, string):
    o, v_name = get_variable_reference(obj,string)
    if v_name in o.__dict__:
        if not v_name.startswith("_"):
            return o.__dict__[v_name]
        else:
            raise SelmaParseException("You cannot edit '%s' on object %s because it is an internal variable" % (v_name, o))
    else:
        raise SelmaParseException("There is no variable named '%s' on object %s" % (v_name, o))

"Call when a line uses an invalid operator"
def parse_error_wrong_type(operator,value,var_name):
    raise SelmaParseException("cannot use operator '%s' on a '%s' because it is of type %s" % (operator, var_name, value.__class__.__name__))

"Returns the Type of a literal statement"
def get_type_from_literal(value):
    value = value.strip()

    match_object = re.match(r'^\"[^\"]*\"$',value,flags=0) or re.match(r'^\'[^\']*\'$',value,flags=0)
    if match_object:
        return "str"

    match_object = re.match(r'^\d+\.?\d*$',value,flags=0)
    if match_object:
        return "float"

    match_object = re.match(r'^\[[\"\'].*[\"\']\]$',value,flags=0)
    if match_object:
        return "list"

    return "reference"

    return value_type

"Parses a string into a list"
def parse_as_list(s):
    if not "[" in s and not "]" in s:
        raise SelmaParseException("expected list, got '%S'" % s)

    return ast.literal_eval(s)

"Parses a string into a number"
def parse_as_number(operator,value):
    try:
        return float(value)
    except:
        raise SelmaParseException("operator %s must be used with a numeric value (%s)" % (operator,value))

"Exception to use for parsing errors"
class SelmaParseException(Exception):
    pass
