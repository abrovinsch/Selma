# -*- coding: utf-8 -*-
#!/usr/bin/python

class SelmaOperation:

    def __init__(self,var_name, var_holder, operator, value, var_type, value_type):
        self.var_name = var_name
        self.operator = operator
        self.value = value
        self.var_type = var_type
        self.value_type = value_type
        self.var_holder = var_holder

    def get_var_value(self,):
        return self.var_holder[self.var_name]

    def set_var_to(self,val):
        self.var_holder[self.var_name] = val

    def append(self,val):
        self.var_holder[self.var_name].append(val)

    def remove(self,val):
        self.var_holder[self.var_name].remove(val)

    def add(self,val):
        self.var_holder[self.var_name] += val

import ast, re

"This defines every operator"
operator = {
    "append":"add",
    "append-list":"add-these",
    "remove-from-list":"remove",
    "remove-from-list-many":"remove-these",

    "set-value":"=",
    "value-equals":"=",
    "value-not-equals":"!=",
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
    "define-list-variable":"create-list",
    "define-variable-on-all":"create-on-everyone"
}

error_no_such_variable = "There is no variable named '%s' on object %s"

allow_print_out = True

"Execute the effect in 'line' on the object 'obj'"
def execute_effect(obj,line):

    op = parse_line_to_parts(obj,line)

    if op.operator == operator["set-value"]:
        if op.value_type == "float" or op.value_type == "int":
            op.set_var_to(parse_as_number(op.operator,op.value))
        elif op.var_type == "list" and op.value_type == "string":
            op.set_var_to(parse_as_list(op.value))
        else:
            op.set_var_to(op.value)

    elif op.operator == operator["append"]:
        if op.var_type == "list":
            op.append(op.value)
        else:
            raise parse_error_wrong_type(op.operator,op.var_holder[op.var_name].__class__.__name__,op.var_name)

    elif op.operator == operator["append-list"]:
        if op.var_type == "list":
            list_to_append = parse_as_list(op.value)
            for item in list_to_append:
                op.append(item)
        else:
            raise parse_error_wrong_type(op.operator,op.value,op.var_name)

    elif op.operator == operator["remove-from-list"]:
        if op.var_type == "list":
            if op.value in op.get_var_value():
                op.remove(value)
        else:
            raise parse_error_wrong_type(op.operator,op.value,op.var_name)

    elif op.operator == operator["remove-from-list-many"]:
        if op.var_type == "list":
            list_to_remove = parse_as_list(op.value)
            for item in list_to_remove:
                if item in op.get_var_value():
                    op.remove(item)
        else:
            raise parse_error_wrong_type(op.operator,op.value,op.var_name)

    elif op.operator == operator["add-numeric"]:
        op.add(parse_as_number(operator,value))

    elif op.operator == operator["subtract-numeric"]:
        op.var_holder[var_name] -= parse_as_number(op.operator,op.value)

    elif operator == operator["divide-numeric"]:
        op.var_holder[var_name] /= parse_as_number(op.operator,op.value)

    elif operator == operator["multiply-numeric"]:
        op.var_holder[var_name] *= parse_as_number(op.operator,op.value)

    elif op.operator == operator["print-value"]:
        if op.value == "":
            value = "$"
        if(allow_print_out):
            print(op.value.replace("$",str(op.get_var_value())))

    elif op.operator == operator["define-numeric-variable"]:
        add_variable_to_dict(op.var_holder[op.var_name],op.var_name,op.value,0)

    elif op.operator == operator["define-list-variable"]:
        add_variable_to_dict(op.var_holder[op.var_name],op.var_name,op.value,list())

    elif operator == operator["define-string-variable"]:
        add_variable_to_dict(var_holder[var_name],var_name,value,"")

    elif op.operator == operator["define-variable-on-all"]:

        if op.var_type == "list":
            for item in op.get_var_value():
                if("var" in item.__dict__):
                    item.var[op.value] = 0
                else:
                    raise SelmaParseException("Cannot create variables on %s becuase it's members has no variable field" % op.var_holder[op.var_name])
                    return
        elif op.var_type == "dict":
            for item_name in op.var_holder[op.var_name]:
                item = op.var_holder[op.var_name][item_name]
                if("var" in item.__dict__):
                    item.var[op.value] = 0
                else:
                    raise SelmaParseException("Cannot create variables on %s becuase it's members has no variable field" % op.var_holder[op.var_name])
                    return
        else:
            raise parse_error_wrong_type(op.operator,var_type,var_name)
    else:
        raise SelmaParseException("Unknown operator '%s'" % op.operator)

"Return true if the statement in 'line' is true on object 'obj'"
def evaluate_condition(obj,line):

    op = parse_line_to_parts(obj,line)

    if op.operator == operator["value-equals"]:
        if not op.var_name in op.var_holder:
            return False
        if op.value_type == "int" or op.value_type == "float":
            return op.var_holder[op.var_name] == parse_as_number(op.operator,op.value)
        elif op.var_type == "list":
            return op.var_holder[op.var_name] == parse_as_list(op.value)
        else:
            return op.var_holder[op.var_name] == op.value

    if op.operator == operator["value-not-equals"]:
        if not op.var_name in op.var_holder:
            return True
        if op.value_type == "int" or op.value_type == "float":
            return op.var_holder[op.var_name] != parse_as_number(op.operator,op.value)
        elif op.var_type == "list":
            return op.var_holder[op.var_name] != parse_as_list(op.value)
        else:
            return op.var_holder[op.var_name] != op.value

    elif op.operator == operator["greater-than"]:
        return var_holder[var_name] > parse_as_number(operator,value)

    elif op.operator == operator["lesser-than"]:
        return op.var_holder[op.var_name] < parse_as_number(op.operator,op.value)

    elif op.operator == operator["greater-than-or-equal"]:
        if op.var_type == "int" or op.var_type == "float":
            return op.var_holder[op.var_name] >= parse_as_number(op.operator,op.value)
        else:
            parse_error_wrong_type(op.operator,op.value,op.var_name)

    elif op.operator == operator["greater-than-or-equal"]:
        return op.var_holder[op.var_name] <= parse_as_number(op.operator,op.value)

    elif op.operator == operator["list-doesnt-contain"]:
        if op.var_type == "list":
            return not op.value in op.var_holder[op.var_name]
        else:
            parse_error_wrong_type(op.operator,op.value,op.var_name)

    elif op.operator == operator["list-contains"]:
        if var_type == "list":
            return op.value in op.var_holder[op.var_name]
        else:
            parse_error_wrong_type(op.operator,op.value,op.var_name)

    else:
        raise SelmaParseException("Unknown operator '%s'" % op.operator)

"Returns all the parts of a line: var_name, parent_object, operator, value, var_type, value_type"
def parse_line_to_parts(calling_object,line):
    line = line.strip()

    match_object = re.match(r'(\S+)\s+(\S+)\s+(.*)',line,flags=0)

    if not match_object:
        raise SelmaParseException("invalid syntax '%s'" % line)
    matches = match_object.groups()

    parent_object, var_name = get_variable_reference(calling_object,matches[0])

    operator_string = matches[1]

    if not operator_string in operator.values():
        raise SelmaParseException("Unknown operator '%s' in line '%s'" % (operator_string, line))

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

    return SelmaOperation(var_name, var_holder, operator_string, value, var_type, value_type)

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
