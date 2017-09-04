# -*- coding: utf-8 -*-
#!/usr/bin/python
import ast, re

"This defines every operator"
operator = {
    "append":"add",
    "append-list":"add-these",
    "remove-from-list":"remove",
    "remove-from-list-many":"remove-these",

    "set-value":"=",
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

error_no_such_variable = "There is no variable named '%s' on object %s"
allow_print_out = True

class SelmaOperation:

    "Initializes a new SelmaOperation object by parsing a line and grabbing references from the parent object"
    def __init__(self,calling_object,line):

        # Remove any unneccesary whitespace
        line = line.strip()

        # Search for a operation pattern
        match_object = re.match(r'(\S+)\s+(\S+)\s+(.*)',line,flags=0)
        if not match_object:
            raise SelmaParseException("invalid syntax '%s'" % line)
        matches = match_object.groups()

        # Get the variable name and variable holder object
        parent_object, self.var_name = get_variable_reference(calling_object,matches[0])
        self.var_holder = get_var_holder(parent_object)

        # Check that the variable actually exists
        if not self.var_name in self.var_holder:
            raise SelmaParseException(error_no_such_variable % (self.var_name, self.var_holder.__class__.__name__))

        self.var_type = self.var_holder[self.var_name].__class__.__name__

        # Get the operator and make sure it is defined
        self.operator = matches[1]
        if not self.operator in operator.values():
            raise SelmaParseException("Unknown operator '%s' in line '%s'" % \
                                        (self.operator, line)
                                        )

        # Get the argument and it's type
        self.argument = matches[2]
        self.argument_type = get_type_from_literal(self.argument)

        if self.argument_type == "reference":
            self.argument = get_value_from_reference(calling_object,self.argument)
            self.argument_type = self.argument.__class__.__name__

        elif self.argument_type == "str":
            #if the argument is a string, we need to remove the quotes
            self.argument = self.argument[1:-1]

    "Returns the value of the variable"
    def get_var_value(self,):
        return self.var_holder[self.var_name]

    "Sets the value of the variable"
    def set_var_to(self,val):
        self.var_holder[self.var_name] = val

    "Appends a value to the variable"
    def append(self,val):
        self.var_holder[self.var_name].append(val)

    "Removes a value from the variable"
    def remove(self,val):
        self.var_holder[self.var_name].remove(val)

    "Adds a value to the variable"
    def add(self,val):
        self.var_holder[self.var_name] += val

"Execute the effect in 'line' on the object 'obj'"
def execute_effect(obj,line):

    op = SelmaOperation(obj,line)

    if op.operator == operator["set-value"]:
        if op.argument_type == "float" or op.argument_type == "int":
            op.set_var_to(parse_as_number(op.operator,op.argument))
        elif op.var_type == "list" and op.argument_type == "string":
            op.set_var_to(parse_as_list(op.argument))
        else:
            op.set_var_to(op.argument)

    elif op.operator == operator["append"]:
        if op.var_type == "list":
            op.append(op.argument)
        else:
            raise parse_error_wrong_type(op.operator,
                                        op.get_var_value().__class__.__name__,
                                        op.var_name)

    elif op.operator == operator["append-list"]:
        if op.argument_type == "literal-list":
            list_to_append = parse_as_list(op.argument)
            for item in list_to_append:
                op.append(item)
        elif op.argument_type == "list":
            list_to_append = op.argument
            for item in list_to_append:
                op.append(item)
        else:
            raise parse_error_wrong_type(op.operator,op.argument,op.var_name)

    elif op.operator == operator["remove-from-list"]:
        if op.var_type == "list":
            if op.argument in op.get_var_value():
                op.remove(op.argument)
        else:
            raise parse_error_wrong_type(op.operator,op.argument,op.var_name)

    elif op.operator == operator["remove-from-list-many"]:
        if op.var_type == "list":
            list_to_remove = parse_as_list(op.argument)
            for item in list_to_remove:
                if item in op.get_var_value():
                    op.remove(item)
        else:
            raise parse_error_wrong_type(op.operator,op.argument,op.var_name)

    elif op.operator == operator["add-to"]:
        if op.var_type == "str":
            op.var_holder[op.var_name] += op.argument
        else:
            op.add(parse_as_number(op.operator,op.argument))

    elif op.operator == operator["subtract-from"]:
        op.var_holder[op.var_name] -= parse_as_number(op.operator,op.argument)

    elif op.operator == operator["divide-numeric"]:
        op.var_holder[op.var_name] /= parse_as_number(op.operator,op.argument)

    elif op.operator == operator["multiply-numeric"]:
        op.var_holder[op.var_name] *= parse_as_number(op.operator,op.argument)

    elif op.operator == operator["print-value"]:
        if op.argument == "":
            op.argument = "$"
        if(allow_print_out):
            print(op.argument.replace("$",str(op.get_var_value())))

    elif op.operator == operator["define-numeric-variable"]:
        add_variable_to_dict(op.get_var_value(),
                            op.var_name,
                            op.argument,
                            0)

    elif op.operator == operator["define-list-variable"]:
        add_variable_to_dict(op.get_var_value(),
                            op.var_name,
                            op.argument,
                            list()
                            )

    elif op.operator == operator["define-string-variable"]:
        add_variable_to_dict(op.get_var_value(),
                            op.var_name,
                            op.argument,
                            "")

    elif op.operator == operator["define-number-on-all"] or op.operator == operator["define-string-on-all"] or op.operator == operator["define-list-on-all"]:

        if op.operator == operator["define-string-on-all"]:
            default_value = ""
        elif op.operator == operator["define-list-on-all"]:
            default_value = list()
        else:
            default_value = 0

        if op.var_type == "list":
            for item in op.get_var_value():
                if("var" in item.__dict__):
                    item.var[op.argument] = default_value
                else:
                    raise SelmaParseException("Cannot create variables on %s becuase it's members has no variable field" % op.get_var_value())
                    return
        elif op.var_type == "dict":
            for item_name in op.get_var_value():
                item = op.get_var_value()[item_name]
                if("var" in item.__dict__):
                    item.var[op.argument] = default_value
                else:
                    raise SelmaParseException("Cannot create variables on %s becuase it's members has no variable field" % op.get_var_value())
                    return
        else:
            raise parse_error_wrong_type(op.operator,var_type,var_name)
    else:
        raise SelmaParseException("Unknown operator '%s'" % op.operator)

"Return true if the statement in 'line' is true on object 'obj'"
def evaluate_condition(obj,line):

    op = SelmaOperation(obj,line)

    if op.operator == operator["value-equals"]:
        if not op.var_name in op.var_holder:
            return False
        if op.argument_type == "int" or op.argument_type == "float":
            return op.get_var_value() == parse_as_number(op.operator,op.argument)
        elif op.var_type == "list":
            return op.get_var_value() == parse_as_list(op.argument)
        else:
            return op.get_var_value() == op.argument

    if op.operator == operator["value-not-equals"]:
        if not op.var_name in op.var_holder:
            return True
        if op.argument_type == "int" or op.argument_type == "float":
            return op.get_var_value() != parse_as_number(op.operator,op.argument)
        elif op.var_type == "list":
            return op.get_var_value() != parse_as_list(op.argument)
        else:
            return op.get_var_value() != op.argument

    elif op.operator == operator["greater-than"]:
        return op.get_var_value() > parse_as_number(op.operator,op.argument)

    elif op.operator == operator["lesser-than"]:
        return op.get_var_value() < parse_as_number(op.operator,op.argument)

    elif op.operator == operator["greater-than-or-equal"]:
        if op.var_type == "int" or op.var_type == "float":
            return op.get_var_value() >= parse_as_number(op.operator,op.argument)
        else:
            parse_error_wrong_type(op.operator,op.argument,op.var_name)

    elif op.operator == operator["lesser-than-or-equal"]:
        return op.get_var_value() <= parse_as_number(op.operator,op.argument)

    elif op.operator == operator["list-doesnt-contain"]:
        if op.var_type == "list":
            return not op.argument in op.get_var_value()
        else:
            parse_error_wrong_type(op.operator,op.argument,op.var_name)

    elif op.operator == operator["list-contains"]:
        if op.var_type == "list":
            return op.argument in op.get_var_value()
        else:
            parse_error_wrong_type(op.operator,op.argument,op.var_name)

    else:
        raise SelmaParseException("Unknown operator '%s'" % op.operator)


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
            print(string, t)
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
        return "literal-list"

    match_object = re.match(r'^\"[^\"]*\"$',value,flags=0) or re.match(r'^\'[^\']*\'$',value,flags=0)
    if match_object:
        return "str"

    return "reference"

    return value_type

"Parses a string into a list"
def parse_as_list(string):
    try:
        return ast.literal_eval(string)
    except ValueError:
        raise SelmaParseException("Can't parse '%s' as list" % string)
    except:
        raise SelmaParseException("Unknown exception when parsing list from string '%s'" % string)

"Parses a string into a number"
def parse_as_number(operator,string):
    try:
        return float(string)
    except:
        raise SelmaParseException("operator %s must be used with a numeric value (not %s)" % (operator,string))

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
