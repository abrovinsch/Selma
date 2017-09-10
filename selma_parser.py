# -*- coding: utf-8 -*-
#!/usr/bin/python

"""
This is a module of 'Selma'
by Oskar Lundqvist / Abrovinsch (c) 2017

This module is responsible for all parsing of
selma statements
"""

import ast
import re

#This defines the operators
OPERATOR = {
    "append":"add",
    "append-list":"add-these",
    "remove-from-list":"remove",
    "remove-from-list-many":"remove-these",

    "assign-value":"=",
    "value-equals":"=",

    "add-to":"+=",
    "subtract-from":"-=",

    "multiply-numeric":"*=",
    "divide-numeric":"/=",

    "value-not-equals":"!=",
    "greater-than":">",
    "lesser-than":"<",
    "greater-than-or-equal":">=",
    "lesser-than-or-equal":"<=",

    "list-contains":"has",
    "list-doesnt-contain":"has-not",

    "print-value":"print",

    "define-numeric-variable":"create-num",
    "define-string-variable":"create-string",
    "define-list-variable":"create-list",

    "define-number-on-all":"create-num-all",
    "define-string-on-all":"create-string-all",
    "define-list-on-all":"create-list-all"
}

ERROR_NO_SUCH_VARIABLE = "There is no variable named '%s' on object %s"
ALLOW_PRINT_OUT = True

class SelmaStatement:
    """A selma statement"""

    def __init__(self, calling_object, line):
        """Initializes a new SelmaStatement object by parsing"
        a line and grabbing references from the parent object"""

        # Remove any unneccesary whitespace
        line = line.strip()

        # Search for a statement pattern
        match_object = re.match(r'(\S+)\s+(\S+)\s+(.*)', line, flags=0)
        if not match_object:
            raise SelmaParseException("invalid syntax '%s'" % line)
        matches = match_object.groups()

        # Get the variable name and variable holder object
        parent_object, self.var_name = get_variable_reference(calling_object,
                                                              matches[0])
        self.var_holder = get_var_holder(parent_object)

        # Check that the variable actually exists
        if not self.var_name in self.var_holder:
            raise SelmaParseException(
                ERROR_NO_SUCH_VARIABLE % (self.var_name,
                                          self.var_holder.__class__.__name__))

        self.var_type = self.var_holder[self.var_name].__class__.__name__

        # Get the operator and make sure it is defined
        self.operator = matches[1]
        if not self.operator in OPERATOR.values():
            raise SelmaParseException("Unknown operator '%s' in line '%s'" % \
                                        (self.operator, line))

        # Get the argument and it's type
        self.argument = matches[2]
        self.argument_type = get_type_from_literal(self.argument)

        if self.argument_type == "reference":
            self.argument = get_value_from_reference(calling_object, self.argument)
            self.argument_type = self.argument.__class__.__name__

        # If the argument is a string, we need to remove the quotes
        elif self.argument_type == "str":
            self.argument = self.argument[1:-1]

        # Save the global reference name of the variable
        self.global_var_name = matches[0]
        if calling_object.__class__.__name__ == "SelmaCharacter":
            self.global_var_name = "cast.%s.%s" % (calling_object.name,
                                                   self.global_var_name)
        elif calling_object.__class__.__name__ == "SelmaStorySimulation":
            if self.global_var_name.startswith("roles"):
                role_name = self.global_var_name[6:]
                role_name = role_name[:role_name.index(".")]

                character_name = calling_object.roles[role_name].name
                self.global_var_name = "cast.%s.%s" % (character_name,self.var_name)

        if self.var_type == "list":
            self.global_var_name += ".%s" % self.argument

    def get_var_value(self):
        """Returns the value of the variable"""
        return self.var_holder[self.var_name]

    def set_var_to(self, val):
        """Sets the value of the variable"""
        self.var_holder[self.var_name] = val

    def append(self, val):
        """Appends a value to the variable"""
        self.var_holder[self.var_name].append(val)

    def remove(self, val):
        """Removes a value from the variable"""
        self.var_holder[self.var_name].remove(val)

    def add(self, val):
        """Adds a value to the variable"""
        self.var_holder[self.var_name] += val

def execute_effect(scope_object, line_string):
    """Execute the effect in 'line' on the object 'obj'"""

    statement = SelmaStatement(scope_object, line_string)

    # Do a diffent thing depending on the operator
    if statement.operator == OPERATOR["assign-value"]:
        if statement.argument_type == "float" or statement.argument_type == "int":
            statement.set_var_to(parse_as_number(statement.operator, statement.argument))
        elif statement.var_type == "list" and statement.argument_type == "literal-list":
            statement.set_var_to(parse_as_list(statement.argument))
        else:
            statement.set_var_to(statement.argument)

    elif statement.operator == OPERATOR["append"]:
        if statement.var_type == "list":
            statement.append(statement.argument)
        else:
            raise parse_error_wrong_type(statement.operator,
                                         statement.get_var_value().__class__.__name__,
                                         statement.var_name)

    elif statement.operator == OPERATOR["append-list"]:
        if statement.argument_type == "literal-list":
            list_to_append = parse_as_list(statement.argument)
            for item in list_to_append:
                statement.append(item)
        elif statement.argument_type == "list":
            list_to_append = statement.argument
            for item in list_to_append:
                statement.append(item)
        else:
            raise parse_error_wrong_type(statement.operator,
                                         statement.argument,
                                         statement.var_name)

    elif statement.operator == OPERATOR["remove-from-list"]:
        if statement.var_type == "list":
            if statement.argument in statement.get_var_value():
                statement.remove(statement.argument)
        else:
            raise parse_error_wrong_type(statement.operator,
                                         statement.argument,
                                         statement.var_name)

    elif statement.operator == OPERATOR["remove-from-list-many"]:
        if statement.var_type == "list":
            list_to_remove = parse_as_list(statement.argument)
            for item in list_to_remove:
                if item in statement.get_var_value():
                    statement.remove(item)
        else:
            raise parse_error_wrong_type(statement.operator,
                                         statement.argument,
                                         statement.var_name)

    elif statement.operator == OPERATOR["add-to"]:
        if statement.var_type == "str":
            statement.var_holder[statement.var_name] += statement.argument
        else:
            statement.add(parse_as_number(statement.operator, statement.argument))

    elif statement.operator == OPERATOR["subtract-from"]:
        statement.var_holder[statement.var_name] -= parse_as_number(statement.operator,
                                                                    statement.argument)

    elif statement.operator == OPERATOR["divide-numeric"]:
        statement.var_holder[statement.var_name] /= parse_as_number(statement.operator,
                                                                    statement.argument)

    elif statement.operator == OPERATOR["multiply-numeric"]:
        statement.var_holder[statement.var_name] *= parse_as_number(statement.operator,
                                                                    statement.argument)
    elif statement.operator == OPERATOR["print-value"]:
        if statement.argument == "":
            statement.argument = "$"
        if ALLOW_PRINT_OUT:
            print(statement.argument.replace("$", str(statement.get_var_value())))

    elif statement.operator == OPERATOR["define-numeric-variable"]:
        add_variable_to_dict(statement.get_var_value(),
                             statement.var_name,
                             statement.argument,
                             default_value=0)

    elif statement.operator == OPERATOR["define-list-variable"]:
        add_variable_to_dict(statement.get_var_value(),
                             statement.var_name,
                             statement.argument,
                             default_value=list())

    elif statement.operator == OPERATOR["define-string-variable"]:
        add_variable_to_dict(statement.get_var_value(),
                             statement.var_name,
                             statement.argument,
                             default_value="")

    elif statement.operator == OPERATOR["define-number-on-all"] or statement.operator == OPERATOR["define-string-on-all"] or statement.operator == OPERATOR["define-list-on-all"]:

        if statement.operator == OPERATOR["define-string-on-all"]:
            default_value = ""
        elif statement.operator == OPERATOR["define-list-on-all"]:
            default_value = list()
        else:
            default_value = 0

        if statement.var_type == "list":
            for item in statement.get_var_value():
                if "var" in item.__dict__:
                    add_variable_to_dict(item.var,
                                         "var",
                                         statement.argument,
                                         default_value=default_value)
                else:
                    raise SelmaParseException(
                        """Cannot create variables on %s becuase
                        it's members has no variable field"""
                        % statement.get_var_value())

        elif statement.var_type == "dict":
            for item_name in statement.get_var_value():
                item = statement.get_var_value()[item_name]
                if "var" in item.__dict__:
                    add_variable_to_dict(item.var,
                                         "var",
                                         statement.argument,
                                         default_value=default_value)
                else:
                    raise SelmaParseException(
                        """Cannot create variables on %s
                        becuase it's members has no variable field"""
                        % statement.get_var_value())

        else:
            raise parse_error_wrong_type(statement.operator,
                                         statement.argument,
                                         statement.var_name)

    # The operator exists but has not defintion here
    elif statement.operator in OPERATOR.values():
        raise SelmaParseException(
            "Operator '%s' can't be used to execute an effect"
            % statement.operator)

    else:
        raise SelmaParseException("Undefined operator '%s'" % statement.operator)

    return statement

def evaluate_condition(obj, line):
    """Return true if the statement in 'line' is true on object 'obj'"""

    statement = SelmaStatement(obj, line)

    if statement.operator == OPERATOR["value-equals"]:
        if not statement.var_name in statement.var_holder:
            return False
        if statement.argument_type == "int" or statement.argument_type == "float":
            return statement.get_var_value() == parse_as_number(statement.operator,
                                                                statement.argument)
        if statement.var_type == "list":
            return statement.get_var_value() == parse_as_list(statement.argument)

        return statement.get_var_value() == statement.argument

    if statement.operator == OPERATOR["value-not-equals"]:
        if not statement.var_name in statement.var_holder:
            return True
        if statement.argument_type == "int" or statement.argument_type == "float":
            return statement.get_var_value() != parse_as_number(statement.operator,
                                                                statement.argument)
        if statement.var_type == "list":
            return statement.get_var_value() != parse_as_list(statement.argument)

        return statement.get_var_value() != statement.argument

    if statement.operator == OPERATOR["greater-than"]:
        return statement.get_var_value() > parse_as_number(statement.operator,
                                                           statement.argument)

    if statement.operator == OPERATOR["lesser-than"]:
        return statement.get_var_value() < parse_as_number(statement.operator,
                                                           statement.argument)

    if statement.operator == OPERATOR["greater-than-or-equal"]:
        if statement.var_type == "int" or statement.var_type == "float":
            return statement.get_var_value() >= parse_as_number(statement.operator,
                                                                statement.argument)

        parse_error_wrong_type(statement.operator,
                               statement.argument,
                               statement.var_name)

    if statement.operator == OPERATOR["lesser-than-or-equal"]:
        return statement.get_var_value() <= parse_as_number(statement.operator, statement.argument)

    if statement.operator == OPERATOR["list-doesnt-contain"]:
        if statement.var_type == "list":
            return not statement.argument in statement.get_var_value()
        else:
            parse_error_wrong_type(statement.operator,
                                   statement.argument,
                                   statement.var_name)

    if statement.operator == OPERATOR["list-contains"]:
        if statement.var_type == "list":
            return statement.argument in statement.get_var_value()
        else:
            parse_error_wrong_type(statement.operator,
                                   statement.argument,
                                   statement.var_name)

    # The operator exists but has not defintion here
    if statement.operator in OPERATOR.values():
        raise SelmaParseException(
            "Operator '%s' can't be used to evaluate a condition"
            % statement.operator)

    raise SelmaParseException("Undefined operator '%s'" % statement.operator)


def get_variable_reference(parent_object, string):
    """Returns a reference to the variable which a string is refering to"""

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
            raise SelmaParseException(
                ERROR_NO_SUCH_VARIABLE % (var_name,
                                          var_holder.__class__.__name__))

        rest_string = string[string.index(".")+1:]

    if "." in rest_string:
        parent_object, var_name = get_variable_reference(parent_object, rest_string)

    return parent_object, var_name

def get_value_from_reference(parent_object, string):
    """Returns the value from a string reference to a variable"""

    parent_object, v_name = get_variable_reference(parent_object, string)

    var_holder = get_var_holder(parent_object)

    if v_name in var_holder:
        return var_holder[v_name]
    else:
        raise SelmaParseException(
            ERROR_NO_SUCH_VARIABLE % (v_name,
                                      var_holder.__class__.__name__))

def parse_error_wrong_type(operator, type_name, var_name):
    """Call when a line uses an invalid operator"""

    raise SelmaParseException("""cannot use operator '%s' on a '%s'
                              because it is of type %s"""
                              % (operator, var_name, type_name))

def get_type_from_literal(value):
    """Returns the Type of a literal statement"""
    value = value.strip()

    match_object = re.match(r'^-?\d+\.?\d*$', value, flags=0)
    if match_object:
        return "float"

    match_object = re.match(r'^\[\".*\"\]$', value, flags=0)
    if match_object:
        return "literal-list"

    double_quote_regex = r'^\"[^\"]*\"$'
    match_object = re.match(double_quote_regex, value, flags=0)
    if match_object:
        return "str"

    single_quote_regex = r'^\"[^\"]*\"$'
    match_object = re.match(single_quote_regex, value, flags=0)
    if match_object:
        return "str"

    return "reference"

def parse_as_list(string):
    """Parses a string into a list"""
    try:
        return ast.literal_eval(string)
    except ValueError:
        raise SelmaParseException(
            "Can't parse '%s' as list" % string)
    except:
        raise SelmaParseException(
            "Unknown exception when parsing list from string '%s'" % string)

def parse_as_number(operator, string):
    """Parses a string into a number"""
    try:
        return float(string)
    except:
        raise SelmaParseException(
            "operator %s must be used with a numeric value (not %s)"
            % (operator, string))

def get_var_holder(obj):
    """Returns whichever object holds child variables."""

    obj_type = obj.__class__.__name__

    if obj_type == "dict":
        return obj
    elif obj.__dict__:
        return obj.__dict__
    else:
        raise SelmaParseException(
            "Object of type %s can't hold variables!" % obj_type)

def add_variable_to_dict(dictionary,
                         dictionary_name,
                         variable_name,
                         default_value):
    """Adds a new entry into a variable holding dict"""

    if not variable_name:
        raise SelmaParseException("Name of variable must be longer than 0!")

    is_allowed_variable_name(variable_name)

    if dictionary.__class__.__name__ != "dict":
        raise SelmaParseException(
            """Can only create variables on dict type objects but %s is of type '%s'"""
            % (variable_name, dictionary.__class__.__name__))

    if variable_name.__class__.__name__ != "str":
        raise SelmaParseException("Name of variable must be a string!")

    if dictionary_name != "var":
        raise SelmaParseException(
            """You can only create custom variables
            in the 'var' dictionaries (You tried %s)"""
            % dictionary_name)

    dictionary[variable_name] = default_value


def is_allowed_variable_name(name):
    """Returns whether name is an allowed name of a variable"""
    numbers = "0123456789"
    for num in numbers:
        if name.startswith(num):
            raise SelmaParseException("Variable names may not start with numbers (%s)"
                                      % num)

    not_allowed_characters = " \n\"\'-+/*><[]{}()´–§#:;=|^$"
    for character in not_allowed_characters:
        if character in name:
            raise SelmaParseException("Illegal character '%s' in variable name: '%s'"
                                      % (character, name))
    return True

class SelmaParseException(Exception):
    """Exception to use for parsing errors"""
    pass
