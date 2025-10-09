PREDEFINED_FUNCTIONS = {
    "length": {
        "ARGUMENTS": [("a", "ARRAY")],
        "RETURN_TYPE": "int",
        "FUNCTION": lambda function_vars: mylength(function_vars)
    },
    "print": {
        "ARGUMENTS": [("a", "ARRAY_CHAR")],
        "RETURN_TYPE": None,
        "FUNCTION": lambda function_vars: myprint(function_vars)
    },
    "array_to_str": {
        "ARGUMENTS": [("a", "ARRAY")],
        "RETURN_TYPE": "ARRAY_CHAR",
        "FUNCTION": lambda function_vars: cast_to_str(function_vars)
    },
    "int_to_str": {
        "ARGUMENTS": [("a", "INT")],
        "RETURN_TYPE": "ARRAY_CHAR",
        "FUNCTION": lambda function_vars: cast_to_str(function_vars)
    },
    "bool_to_str": {
        "ARGUMENTS": [("a", "BOOL")],
        "RETURN_TYPE": "ARRAY_CHAR",
        "FUNCTION": lambda function_vars: cast_to_str(function_vars)
    },
    "str_to_int": {
        "ARGUMENTS": [("a", "ARRAY_CHAR")],
        "RETURN_TYPE": "int",
        "FUNCTION": lambda function_vars: cast_to_int(function_vars)
    },
    "mod": {
        "ARGUMENTS": [("a", "INT"), ("b", "INT")],
        "RETURN_TYPE": "int",
        "FUNCTION": lambda function_vars: mod(function_vars)
    },
    "input": {
        "ARGUMENTS": [("a", "ARRAY_CHAR")],
        "RETURN_TYPE": "ARRAY_CHAR",
        "FUNCTION": lambda function_vars: myinput(function_vars)
    }
}

DEBUG = False

def mylength(function_vars):
    return ("int", len(function_vars["a"]["VALUE"]))

def myinput(function_vars):
    question = ""
    for l in function_vars["a"]["VALUE"]:
        question += l
    user_input = input(question)
    out_array = []
    for l in user_input:
        out_array.append(l)
    return ("ARRAY_CHAR", out_array)

def myprint(function_vars):
    toPrint = ""
    for l in function_vars["a"]["VALUE"]:
        toPrint += l
    if DEBUG:
        print("PRINT:" + toPrint)
    else:
        print(toPrint)
    return ("", None)

def cast_to_str(function_vars):
    casted = str(function_vars["a"]["VALUE"])
    out = []
    for l in casted:
        out.append(l)
    return ("ARRAY_CHAR", out)

def cast_to_int(function_vars):
    return ("int", int(function_vars["a"]["VALUE"]))

def mod(funcntion_vars):
    return ("int", int(funcntion_vars["a"]["VALUE"]%funcntion_vars["b"]["VALUE"]))
