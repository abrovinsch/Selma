# -*- coding: utf-8 -*-
#!/usr/bin/python

import ast, re


"This defines every operator"
op = {
    "append":"add",
    "append-list":"add-these",
    "remove-from-list":"remove",
    "remove-from-list-many":"remove-these",

    "set-value":"=",
    "value-equals":"=",
    "add-numeric":"+=",
    "subtract-numeric":"-=",
    "multiply-numeric":"*=",
    "divide-numeric":"/=",

    "greater-than":">",
    "lesser-than":"<",
    "greater-than-or-equal":">=",
    "lesser-than-or-equal":"<=",

    "list-contains":"has",
    "list-doesnt-contain":"has-not",

    "print-value":"print",

    "define-numeric-variable":"create-num",
    "define-string-variable":"create-string",
    "define-list-variable":"create-list"
}

error_no_such_variable = "There is no variable named '%s' on object %s"

allow_print_out = True

"Execute the effect in 'line' on the object 'obj'"
def execute_effect(obj,line):

    var_name, parent_object, operator, value, var_type, value_type = parse_line_to_parts(obj,line)
    var_holder = get_var_holder(parent_object)

    if operator == op["set-value"]:
        if value_type == "float" or value_type == "int":
            var_holder[var_name] = parse_as_number(operator,value)
        elif var_type == "list" and value_type == "string":
            var_holder[var_name] = parse_as_list(value)
        else:
            var_holder[var_name] = value

    elif operator == op["append"]:
        if var_type == "list":
            var_holder[var_name].append(value)
        else:
            raise parse_error_wrong_type(operator,var_holder[var_name].__class__.__name__,var_name)

    elif operator == op["append-list"]:
        if var_type == "list":
            list_to_append = parse_as_list(value)
            for item in list_to_append:
                var_holder[var_name].append(item)
        else:
            raise parse_error_wrong_type(operator,value,var_name)

    elif operator == op["remove-from-list"]:
        if var_type == "list":
            if value in var_holder[var_name]:
                var_holder[var_name].remove(value)
        else:
            raise parse_error_wrong_type(operator,value,var_name)

    elif operator == op["remove-from-list-many"]:
        if var_type == "list":
            list_to_remove = parse_as_list(value)
            for item in list_to_remove:
                if item in var_holder[var_name]:
                    var_holder[var_name].remove(item)
        else:
            raise parse_error_wrong_type(operator,value,var_name)

    elif operator == op["add-numeric"]:
        var_holder[var_name] += parse_as_number(operator,value)

    elif operator == op["subtract-numeric"]:
        var_holder[var_name] -= parse_as_number(operator,value)

    elif operator == op["divide-numeric"]:
        var_holder[var_name] /= parse_as_number(operator,value)

    elif operator == op["multiply-numeric"]:
        var_holder[var_name] *= parse_as_number(operator,value)

    elif operator == op["print-value"]:
        if value == "":
            value = "$"
        if(allow_print_out):
            print(value.replace("$",str(var_holder[var_name])))

    elif operator == op["define-numeric-variable"]:
        add_variable_to_dict(var_holder[var_name],var_name,value,0)

    elif operator == op["define-list-variable"]:
        add_variable_to_dict(var_holder[var_name],var_name,value,list())

    elif operator == op["define-string-variable"]:
        add_variable_to_dict(var_holder[var_name],var_name,value,"")

    else:
        raise SelmaParseException("Unknown operator '%s'" % operator)

"Return true if the statement in 'line' is true on object 'obj'"
def evaluate_condition(obj,line):

    var_name, parent_object, operator, value, var_type, value_type = parse_line_to_parts(obj,line)
    var_holder = get_var_holder(parent_object)

    if operator == op["value-equals"]:
        if value_type == "int" or value_type == "float":
            return var_holder[var_name] == parse_as_number(operator,value)
        elif var_type == "list":
            return var_holder[var_name] == parse_as_list(value)
        else:
            return var_holder[var_name] == value

    elif operator == op["greater-than"]:
        return var_holder[var_name] > parse_as_number(operator,value)

    elif operator == op["lesser-than"]:
        return var_holder[var_name] < parse_as_number(operator,value)

    elif operator == op["greater-than-or-equal"]:
        if var_type == "int" or var_type == "float":
            return var_holder[var_name] >= parse_as_number(operator,value)
        else:
            parse_error_wrong_type(operator,value,var_name)

    elif operator == op["greater-than-or-equal"]:
        return var_holder[var_name] <= parse_as_number(operator,value)

    elif operator == op["list-doesnt-contain"]:
        if var_type == "list":
            return not value in var_holder[var_name]
        else:
            parse_error_wrong_type(operator,value,var_name)

    elif operator == op["list-contains"]:
        if var_type == "list":
            return value in var_holder[var_name]
        else:
            parse_error_wrong_type(operator,value,var_name)

    else:
        raise SelmaParseException("Unknown operator '%s'" % operator)

"Returns all the parts of a line: var_name, parent_object, operator, value, var_type, value_type"
def parse_line_to_parts(calling_object,line):
    line = line.strip()

    match_object = re.match(r'(\S+)\s+(\S+)\s+(.*)',line,flags=0)

    if not match_object:
        raise SelmaParseException("invalid syntax '%s'" % line)
    matches = match_object.groups()

    parent_object, var_name = get_variable_reference(calling_object,matches[0])

    operator = matches[1]

    if not operator in op.values():
        raise SelmaParseException("Unknown operator '%s' in line '%s'" % (operator, line))

    value    = matches[2]

    value_type = get_type_from_literal(value)

    if value_type == "reference":
        value = get_value_from_reference(calling_object,value)
        value_type = value.__class__.__name__
    elif value_type == "str":
        value = value[1:-1]

    var_holder = get_var_holder(parent_object)

    if not var_name in var_holder:
            raise SelmaParseException(error_no_such_variable % (var_name, var_holder.__class__.__name__))

    var_type = var_holder[var_name].__class__.__name__

    return var_name, parent_object, operator, value, var_type, value_type

"Returns a reference to the variable which a string is refering to"
def get_variable_reference(parent_object, string):

    rest_string = ""
    var_name = string

    if "." in string:
        var_name = string[:string.index(".")]

        type_name = parent_object.__class__.__name__

        if type_name == "dict":
            var_holder = parent_object
        else:
            var_holder = parent_object.__dict__

        if var_name in var_holder:
            parent_object = var_holder[var_name]
            var_name = string[string.index(".")+1:]

        else:
            t = parent_object.__class__.__name__
            raise SelmaParseException(error_no_such_variable % (var_name, var_holder.__class__.__name__))

        rest_string   = string[string.index(".")+1:]

    if "." in rest_string:

        parent_object, var_name = get_variable_reference(parent_object, rest_string)

    return parent_object, var_name

"Returns the value from a string reference to a variable"
def get_value_from_reference(parent_object, string):
    parent_object, v_name = get_variable_reference(parent_object,string)

    var_holder = get_var_holder(parent_object)

    if v_name in var_holder:
        return var_holder[v_name]
    else:
        raise SelmaParseException(error_no_such_variable % (v_name, var_holder.__class__.__name__))

"Call when a line uses an invalid operator"
def parse_error_wrong_type(operator,type_name,var_name):
    raise SelmaParseException("cannot use operator '%s' on a '%s' because it is of type %s" % (operator, var_name, type_name))

"Returns the Type of a literal statement"
def get_type_from_literal(value):
    value = value.strip()

    match_object = re.match(r'^\d+\.?\d*$',value,flags=0)
    if match_object:
        return "float"

    match_object = re.match(r'^\[\".*\"\]$',value,flags=0)
    if match_object:
        return "list"

    match_object = re.match(r'^\"[^\"]*\"$',value,flags=0) or re.match(r'^\'[^\']*\'$',value,flags=0)
    if match_object:
        return "str"

    return "reference"

    return value_type

"Parses a string into a list"
def parse_as_list(s):
    try:
        return ast.literal_eval(s)
    except ValueError:
        raise SelmaParseException("Can't parse '%s' as list" % s)
    except:
        raise SelmaParseException("Unknown exception when parsing list from string '%s'" % s)

"Parses a string into a number"
def parse_as_number(operator,value):
    try:
        return float(value)
    except:
        raise SelmaParseException("operator %s must be used with a numeric value (not %s)" % (operator,value))

"Returns whichever object holds child variables."
def get_var_holder(obj):

    obj_type = obj.__class__.__name__

    if obj_type == "dict":
        return obj
    elif obj.__dict__:
        return obj.__dict__
    else:
        raise SelmaParseException("Object of type %s can't hold variables!" % obj_type)

"Adds a new entry into a variable holding dict"
def add_variable_to_dict(dictionary, dictionary_name, variable_name, value):

    if dictionary.__class__.__name__ != "dict":
        raise SelmaParseException("Can only create variables on dict type objects but %s is of type '%s'" % (var_name, var_type))
    if variable_name.__class__.__name__ != "str":
        raise SelmaParseException("Name of variable must be a string literal")
    if dictionary_name != "var":
        raise SelmaParseException("You can only create custom variables in the 'var' dictionaries (You tried %s)" % dictionary_name)
    dictionary[variable_name] = value


"Exception to use for parsing errors"
class SelmaParseException(Exception):
    pass
