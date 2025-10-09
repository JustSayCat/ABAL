from predefined import PREDEFINED_FUNCTIONS
from custom_errors import LangError

DEBUG = False

def interpretAST(nodes, in_vars=None, in_funcs=None, in_current_function_name=""):
    current_function_name = in_current_function_name
    variables = {}
    if in_vars != None:
        variables = in_vars
    functions = {}
    if in_funcs != None:
        functions = in_funcs
    if_stack = []
    for node in nodes:
        if DEBUG:
            print("------------------------------")
            print(node)
            print(variables)
            print(functions)
            print()
        if node[0] == "DEFINE_ASSIGNMENT":
            value = None
            if node[1][0] == "int":
                value = processMaths(node[1][2], variables, functions)
            elif node[1][0] == "char":
                value = processChar(node[1][2], variables, functions)
            elif node[1][0] == "bool":
                value = processBoolean(node[1][2], variables, functions)
            elif node[1][0].split("_")[0] == "ARRAY":
                if node[1][2][0] not in ("ARRAY_ID", "CALL") and node[1][2][0].split("_")[0] != "ARRAY":
                    raise LangError(f"Must define an array: {node[1][1]} with array id [#elements] or as a return from a call or as a string (array of chars)", node[1][2][2])
                if node[1][2][0] == "ARRAY_ID":
                    if node[1][2][1][0] != "INT":
                        raise LangError(f"Cannot define array: {node[1][1]} with a non concrete array size!", node[1][2][1][2])
                    if node[1][0].split("_")[1] == "INT":
                        value = [0]*node[1][2][1][1]
                    elif node[1][0].split("_")[1] == "CHAR":
                        value = [""]*node[1][2][1][1]
                    elif node[1][0].split("_")[1] == "BOOL":
                        value = [False]*node[1][2][1][1]
                elif node[1][2][0] == "CALL":
                    out = callFunction(node[1][2], node[1][2][1][0], variables, functions)
                    if out[0] != node[1][0]:
                        raise LangError(f"Function: {node[1][2][1]} needs to return {node[1][0]} not {out[0]}", node[1][2][2])
                    value = out[1]
                else:
                    value = node[1][2][1]
            if node[1][1] not in variables.keys():
                variables.update({node[1][1]: {"TYPE": node[1][0], "VALUE": value}})
            else:
                raise LangError(f"Two variables cannot have the same name! {node[1][1]}", node[0][2])
        elif node[0] == "DEFINE":
            value = None
            if node[1][0] == "int":
                value = 0
            elif node[1][0] == "char":
                value = ""
            elif node[1][0] == "bool":
                value = False
            elif node[1][0].split("_")[0] == "ARRAY":
                raise LangError(f"Must define the array {node[1][1]} with an array size", node[1][2])
            if node[1][1] not in variables.keys():
                variables.update({node[1][1]: {"TYPE": node[1][0], "VALUE": value}})
        elif node[0] == "ASSIGNMENT":
            if node[1][0] not in variables.keys():
                raise LangError(f"Variable {node[1][0]} not defined", node[1][2])
            variable_type = variables[node[1][0]]["TYPE"]
            value = None
            if variable_type == "int":
                value = processMaths(node[1][1], variables, functions)
            elif variable_type == "char":
                value = processChar(node[1][1], variables, functions)
            elif variable_type == "bool":
                value = processBoolean(node[1][1], variables, functions)
            elif variable_type.split("_")[0] == "ARRAY":
                if node[1][1][0] != "CALL":
                    raise LangError(f"Array {node[1][0]} can only be reassigned with a function return", node[1][1][2])
                else:
                    out = callFunction(node[1][1], node[1][1][1][0], variables, functions)
                    if out[0] != node[1][0]:
                        raise LangError(f"Function: {node[1][1][1]} needs to return {variable_type} not {out[0]}", node[1][1][2])
                    value = out[1]
            variables[node[1][0]]["VALUE"] = value
        elif node[0] == "INDEX_ASSIGNMENT":
            if node[1][0] not in variables:
                raise LangError(f"Assigning an index to non existant array {node[1][0]}!", node[1][2])
            if variables[node[1][0]]["TYPE"].split("_")[0] != "ARRAY":
                raise LangError(f"Assigning an index to non array {node[1][0]}!", node[1][2])
            variable_type = variables[node[1][0]]["TYPE"].split("_")[1]
            index = processMaths(node[1][1], variables, functions)
            if variable_type == "INT":
                variables[node[1][0]]["VALUE"][index] = processMaths(node[1][2], variables, functions)
            elif variable_type == "CHAR":
                variables[node[1][0]]["VALUE"][index] = processChar(node[1][2], variables, functions)
            elif variable_type == "BOOL":
                variables[node[1][0]]["VALUE"][index] = processBoolean(node[1][2], variables, functions)
        elif node[0] == "WHILE":
            while processBoolean(node[1][0][0], variables, functions):
                ret = interpretAST(node[1][1], in_vars=variables, in_funcs=functions, in_current_function_name=current_function_name)
                if ret[1] != None and current_function_name != "":
                    return ret
        elif node[0] == "FUNC":
            arguments = []
            if node[1][0] in functions.keys():
                raise LangError(f"Function with name: {node[1][0]} already exists!", node[1][2])
            for argument in node[1][1]:
                arguments.append((argument[1], argument[0]))
            functions.update({node[1][0]: {"ARGUMENTS": arguments, "RETURN_TYPE": node[1][2], "AST": node[1][3]}})
        elif node[0] == "RETURN":
            if current_function_name == "":
                raise LangError("Cannot return outside a function", node[2])
            return getTypeOfNode(node[1], variables, functions), processNode(node[1], variables, functions)
        elif node[0] == "CALL":
            callFunction(node, node[1][0], variables, functions)
        if node[0] == "IF":
            if processBoolean(node[1][0][0], variables, functions):
                if_stack.append(True)
                ret = interpretAST(node[1][1], in_vars=variables, in_funcs=functions, in_current_function_name=current_function_name)
                if ret[1] != None and current_function_name != "":
                    return ret
            else:
                if_stack.append(False)
        elif node[0] == "ELSE":
            if len(if_stack) == 0:
                raise LangError("Else statement not connected to an if statement!", node[2])
            if not if_stack[-1]:
                ret = interpretAST(node[1], in_vars=variables, in_funcs=functions, in_current_function_name=current_function_name)
                if ret[1] != None and current_function_name != "":
                    return ret
            if_stack.pop()
        elif node[0] == "ELIF":
            if len(if_stack) == 0:
                raise LangError("Elif statement not connected to an if statement!", node[2])
            if not if_stack[-1] and processBoolean(node[1][0][0], variables, functions):
                ret = interpretAST(node[1][1], in_vars=variables, in_funcs=functions, in_current_function_name=current_function_name)
                if ret[1] != None and current_function_name != "":
                    return ret
                if_stack[-1] = True
        else:
            if len(if_stack) > 0:
                if_stack.pop()
    if DEBUG:
        print(variables)
        print(functions)
        print()
    return "", None

def checkArrayType(var_name, variables: dict, functions: dict) -> bool:
    if var_name in variables:
        if variables[var_name]["TYPE"].split("_")[0] == "ARRAY":
            return True
    return False

def getTypeOfNode(node, variables: dict, functions: dict) -> str:
    if node == None:
        return None
    if node[0] == "CALL":
        if node[1][0] in PREDEFINED_FUNCTIONS:
            return PREDEFINED_FUNCTIONS[node[1][0]]["RETURN_TYPE"]
        else:
            return functions[node[1][0]]["RETURN_TYPE"]
    if node[0] == "UNKNOWN" and checkArrayType(node[1], variables, functions):
        return variables[node[1]]["TYPE"]
    if node[0].split("_")[0] == "ARRAY":
        return node[0]
    try: 
        processMaths(node, variables, functions)
        return "int"
    except:
        pass
    try:
        processBoolean(node, variables, functions)
        return "bool"
    except:
        pass
    try:
        processChar(node, variables, functions)
        return "char" 
    except:
        pass
    return "None"

def processNode(node, variables: dict, functions: dict, in_node_type = ""):
    if in_node_type == "":
        node_type = getTypeOfNode(node, variables, functions)
    else:
        node_type = in_node_type
    if DEBUG:
        print("!!!!!!!!!!!!!!!!")
        print(node)
        print(node_type)
        print("!!!!!!!!!!!!!!!!")
    if node_type == "int":
        return processMaths(node, variables, functions)
    elif node_type == "bool":
        return processBoolean(node, variables, functions)
    elif node_type == "char":
        return processChar(node, variables, functions)
    elif node_type.split("_")[0] == "ARRAY":
        return processArray(node, variables, functions)
    return None

def callFunction(call_node: tuple, function_name: dict, variables: dict, functions: dict):
    if DEBUG:
        print("+++++++++++++++++")
        print(f"CALLING {function_name}")
        print("+++++++++++++++++")
    using_predefined = False
    function = None
    if function_name in PREDEFINED_FUNCTIONS:
        function = PREDEFINED_FUNCTIONS[function_name]
        using_predefined = True
    else:
        function = functions[function_name]
    if len(function["ARGUMENTS"]) != len(call_node[1][1]):
        raise LangError(f"Number of arguments in function call of {function_name} doesn't match arguments!", call_node[2])
    function_vars = {}
    for i, argument in enumerate(function["ARGUMENTS"]):
        argument_type = getTypeOfNode(call_node[1][1][i], variables, functions)
        if (argument[1] == "ARRAY" and argument_type.split("_")[0] != "ARRAY") and (argument[1] != argument_type):
            raise LangError(f"Argument {argument[0]} has to be a {argument[1]} not a {argument_type}", call_node[2])
        else:
            if argument[0] in function_vars:
                raise LangError(f"Function argument {argument[0]} is repeated!", call_node[2])
            argument_value = processNode(call_node[1][1][i], variables, functions, in_node_type=argument_type)
            function_vars.update({argument[0]: {"TYPE": argument[1], "VALUE": argument_value}})
    returned = None
    if using_predefined:
        returned = function["FUNCTION"](function_vars)
    else:
        returned = interpretAST(function["AST"], in_vars=function_vars, in_funcs=functions, in_current_function_name=function_name)
    if DEBUG:
        print(f"Function: {function_name} Returned: {returned}")
    if returned[1] == None and function["RETURN_TYPE"] != None:
        raise LangError(f"No Return for typed function {function_name}!", call_node[2])
    elif returned[0] != "" and function["RETURN_TYPE"] != returned[0]:
        raise LangError(f"Returned ({returned[0]}) is not of function ({function_name}) type ({function["RETURN_TYPE"]})!", call_node[2])
    else:
        return returned

def processMaths(node: tuple, variables: dict, functions: dict) -> int:
    if node[0] == "PLUS":
        return processMaths(node[1][0], variables, functions) + processMaths(node[1][1], variables, functions)
    elif node[0] == "MINUS":
        return processMaths(node[1][0], variables, functions) - processMaths(node[1][1], variables, functions)
    elif node[0] == "MULTIPLY":
        return processMaths(node[1][0], variables, functions) * processMaths(node[1][1], variables, functions)
    elif node[0] == "DIVIDE":
        return processMaths(node[1][0], variables, functions) / processMaths(node[1][1], variables, functions)
    elif node[0] == "INT":
        return node[1]
    elif node[0] == "UNKNOWN":
        if node[1] in variables.keys():
            if variables[node[1]]["TYPE"] != "int":
                raise LangError(f"Variable: {node[1]}: Adding integer with {variables[node[1]]["TYPE"]}!", node[2])
            return variables[node[1]]["VALUE"]
        else:
            raise LangError(f"Variable {node[1]} not defined", node[2])
    elif node[0] == "CALL":
        function = None
        if node[1][0] in PREDEFINED_FUNCTIONS:
            function = PREDEFINED_FUNCTIONS[node[1][0]]
        else:
            function = functions[node[1][0]]
        if function["RETURN_TYPE"] != "int":
            raise LangError(f"Called Function {node[1][0]} has a return type of {function["RETURN_TYPE"]} when an int is needed!", node[2])
        returned = callFunction(node, node[1][0], variables, functions)[1]
        return returned
    else:
        raise LangError(f"Trying to maths with a non maths node: {node[0]}", node[2])
    
def processChar(node: tuple, variables: dict, functions: dict) -> str:
    if node[0] == "PLUS":
        return processChar(node[1][0], variables, functions) + processChar(node[1][1], variables, functions)
    elif node[0] == "UNKNOWN":
        if node[1] in variables.keys():
            if variables[node[1]]["TYPE"] != "char":
                raise LangError(f"Variable: {node[1]}: Concatinating char with {variables[node[1]]["TYPE"]}!", node[2])
            return variables[node[1]]["VALUE"]
        else:
            raise LangError(f"Variable {node[1]} not defined", node[2])
    elif node[0] == "CHAR":
        return node[1]
    elif node[0] == "CALL":
        function = None
        if node[1][0] in PREDEFINED_FUNCTIONS:
            function = PREDEFINED_FUNCTIONS[node[1][0]]
        else:
            function = functions[node[1][0]]
        if function["RETURN_TYPE"] != "char":
            raise LangError(f"Called Function {node[1][0]} has a return type of {function["RETURN_TYPE"]} when an CHAR is needed!", node[2])
        returned = callFunction(node, node[1][0], variables, functions)[1]
        return returned
    else:
        raise LangError(f"Trying to char with a non char node: {node[0]}", node[2])

def processBoolean(node: tuple, variables: dict, functions: dict) -> bool:
    if node[0] == "AND":
        return processBoolean(node[1][0], variables, functions) and processBoolean(node[1][1], variables, functions)
    elif node[0] == "OR":
        return processBoolean(node[1][0], variables, functions) and processBoolean(node[1][1], variables, functions)
    elif node[0] == "NOT":
        return not processBoolean(node[1][0], variables, functions)
    elif node[0] == "LESS_THAN":
        return processMaths(node[1][0], variables, functions) < processMaths(node[1][1], variables, functions)
    elif node[0] == "MORE_THAN":
        return processMaths(node[1][0], variables, functions) > processMaths(node[1][1], variables, functions)
    elif node[0] == "LESS_THAN_OR_EQUAL_TO":
        return processMaths(node[1][0], variables, functions) <= processMaths(node[1][1], variables, functions)
    elif node[0] == "MORE_THAN_OR_EQUAL_TO":
        return processMaths(node[1][0], variables, functions) >= processMaths(node[1][1], variables, functions)
    elif node[0] == "EQUAL_TO":
        try:
            return processChar(node[1][0], variables, functions) == processChar(node[1][1], variables, functions)
        except:
            pass
        try:
            return processMaths(node[1][0], variables, functions) == processMaths(node[1][1], variables, functions)
        except:
            pass
        try:
            return processBoolean(node[1][0], variables, functions) == processBoolean(node[1][1], variables, functions)
        except:
            pass
        try:
            return processArray(node[1][0], variables, functions) == processArray(node[1][1], variables, functions)
        except:
            pass
        raise LangError(f"Boolean expression gone wrong! {node}", node[2])
    elif node[0] == "NOT_EQUAL_TO":
        try:
            return processChar(node[1][0], variables, functions) != processChar(node[1][1], variables, functions)
        except:
            pass
        try:
            return processMaths(node[1][0], variables, functions) != processMaths(node[1][1], variables, functions)
        except:
            pass
        try:
            return processBoolean(node[1][0], variables, functions) != processBoolean(node[1][1], variables, functions)
        except:
            pass
        try:
            return processArray(node[1][0], variables, functions) == processArray(node[1][1], variables, functions)
        except:
            pass
        raise LangError(f"Boolean expression gone wrong! {node}", node[2])
    elif node[0] == "CALL":
        function = None
        if node[1][0] in PREDEFINED_FUNCTIONS:
            function = PREDEFINED_FUNCTIONS[node[1][0]]
        else:
            function = functions[node[1][0]]
        if function["RETURN_TYPE"] != "bool":
            raise LangError(f"Called Function {node[1][0]} has a return type of {function["RETURN_TYPE"]} when an bool is needed!", node[2])
        returned = callFunction(node, node[1][0], variables, functions)[1]
        return returned
    elif node[0] == "UNKNOWN":
        if node[1] in variables.keys():
            if variables[node[1]]["TYPE"] != "bool":
                raise LangError(f"Variable: {node[1]}: Bool is needed when {variables[node[1]]["TYPE"]} is used!", node[2])
            return variables[node[1]]["VALUE"]
        else:
            raise LangError(f"Variable {node[1]} not defined", node[2])
    else:
        raise LangError(f"Trying to bool with a non boolean node: {node[0]}", node[2])


def processArray(node, variables: dict, functions: dict):
    if node[0] == "CALL":
        function = None
        if node[1][0] in PREDEFINED_FUNCTIONS:
            function = PREDEFINED_FUNCTIONS[node[1][0]]
        else:
            function = functions[node[1][0]]
        if function["RETURN_TYPE"].split("_")[0] != "ARRAY":
            raise LangError(f"Called Function {node[1][0]} has a return type of {function["RETURN_TYPE"]} when an array is needed!", node[2])
        returned = callFunction(node, node[1][0], variables, functions)[1]
        return returned
    elif node[0] == "UNKNOWN":
        if node[1] in variables.keys():
            if variables[node[1]]["TYPE"].split("_")[0] != "ARRAY":
                raise LangError(f"Variable: {node[1]}: Array is needed when {variables[node[1]]["TYPE"]} is used!", node[2])
            return variables[node[1]]["VALUE"]
        else:
            raise LangError(f"Variable {node[1]} not defined", node[2])
    elif node[0].split("_")[0] == "ARRAY":
        return node[1]
    else:
        raise LangError(f"Trying to array with non array node: {node[0]}", node[2])