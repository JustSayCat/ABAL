from custom_errors import LangError
from copy import deepcopy

NEXT_ID = 0

def getNextFreeId():
    global NEXT_ID
    current = NEXT_ID
    NEXT_ID += 1
    return current

# TODO: consider optimising conditional statements to evalute comaprisons directly instead of evalutating a boolean
# and then evalute if that boolean is true, would reduce program size and speed up execution

# Upon this being called internally, we must ensure that at the end we resolve the current_stack_pointer to its initial value
def compileAST(nodes, stack_tracker=None, current_stack_pointer=None, top_of_stack=None, function_tracker=None, func_name=None):
    instructions = []
    outer_most = False
    if stack_tracker == None:
        stack_tracker = {}
    if current_stack_pointer == None:
        outer_most = True
        current_stack_pointer = 0
    if top_of_stack == None:
        top_of_stack = 0
    if function_tracker == None:
        function_tracker = {}
    started_at = deepcopy(current_stack_pointer)
    i = 0
    functionless_nodes = []
    for node in nodes:
        if node[0] == "FUNC":
            function_id = getNextFreeId()
            pop_arguments_instructions, function_stack_pointer, function_top_of_stack, function_stack_tracker, func_args = getFuncArgs(node)
            function_tracker.update({node[1][0]: {"TYPE": node[1][2], "ARGS": func_args, "ID": function_id}})
            function_instructions = compileAST(node[1][3], function_stack_tracker, function_stack_pointer, function_top_of_stack, function_tracker, node[1][0])
            if function_instructions[-1] != "ret;":
                function_instructions.append("ret;")
            instructions.extend([f"@{function_id}"]+pop_arguments_instructions+function_instructions) # The function should have an instruction to cal ret; but we add it for safety and for void functions
        else:
            functionless_nodes.append(node)
    if outer_most:
        start_id = getNextFreeId()
        instructions = [f"bra #{start_id};"] + instructions + [f"@{start_id}"]
    nodes = functionless_nodes
    while i < len(nodes):
        node = nodes[i]
        if node[0] == "DEFINE_ASSIGNMENT":
            if node[1][0] == "int":
                value_assignment, current_stack_pointer = resolveIntValue(node[1][2], current_stack_pointer, top_of_stack, stack_tracker, function_tracker) # Get the instructions to load the value of the variable into A
                instructions.extend(value_assignment)
                stack_tracker.update({node[1][1]: {"LOCATION": top_of_stack, "TYPE": node[1][0]}})
                top_of_stack += 1
                memory_save, current_stack_pointer = putValueInStack(node[1][1], stack_tracker, current_stack_pointer)
                instructions.extend(["pop A;"] + memory_save)
            elif node[1][0] == "bool":
                value_assignment, current_stack_pointer = resolveBoolValue(node[1][2], current_stack_pointer, top_of_stack, stack_tracker, function_tracker) # Get the instructions to load the value of the variable into A
                instructions.extend(value_assignment)
                stack_tracker.update({node[1][1]: {"LOCATION": top_of_stack, "TYPE": node[1][0]}})
                top_of_stack += 1
                memory_save, current_stack_pointer = putValueInStack(node[1][1], stack_tracker, current_stack_pointer)
                instructions.extend(["pop A;"] + memory_save)
            i += 1
        elif node[0] == "ASSIGNMENT":
            if node[1][0] not in stack_tracker.keys():
                raise LangError(f"Assing value to {node[1][0]} without defining it first!")
            value_type = stack_tracker[node[1][0]]["TYPE"]
            if value_type == "int":
                value_assignment, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker) # Get the instructions to load the value of the variable into A
                instructions.extend(value_assignment)
                memory_save, current_stack_pointer = putValueInStack(node[1][0], stack_tracker, current_stack_pointer)
                instructions.extend(["pop A;"] + memory_save)
            elif value_type == "bool":
                value_assignment, current_stack_pointer = resolveBoolValue(node[1][1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker) # Get the instructions to load the value of the variable into A
                instructions.extend(value_assignment)
                memory_save, current_stack_pointer = putValueInStack(node[1][0], stack_tracker, current_stack_pointer)
                instructions.extend(["pop A;"] + memory_save)
            i += 1
        elif node[0] == "IF":
            resolve_bool_instructions, current_stack_pointer = resolveBoolValue(node[1][0][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
            skip_id = getNextFreeId()
            end_id = getNextFreeId()
            branch_decision_instructions = ["pop A;", "ldim B 1;", "and A;", f"brz #{skip_id};"]
            internal_if_instructions = compileAST(node[1][1], deepcopy(stack_tracker), deepcopy(current_stack_pointer), deepcopy(top_of_stack), function_tracker, func_name)
            all_if_instructions = resolve_bool_instructions+branch_decision_instructions+internal_if_instructions+[f"bra #{end_id};"]
            i+=1
            last_skip_id = skip_id
            while i<len(nodes) and nodes[i][0] == "ELIF":
                elif_skip_id = getNextFreeId()
                resolve_elif_bool_instructions, current_stack_pointer = resolveBoolValue(nodes[i][1][0][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
                elif_branch_decision_instructions = ["pop A;", "ldim B 1;", "and A;", f"brz #{elif_skip_id};"]
                internal_elif_instructions = compileAST(nodes[i][1][1], deepcopy(stack_tracker), deepcopy(current_stack_pointer), deepcopy(top_of_stack), function_tracker, func_name)
                all_if_instructions.extend([f"@{last_skip_id}"]+resolve_elif_bool_instructions+elif_branch_decision_instructions+internal_elif_instructions+[f"bra #{end_id};"])
                last_skip_id = elif_skip_id
                i += 1
            if i<len(nodes) and nodes[i][0] == "ELSE":
                internal_else_instructions = compileAST(nodes[i][1], deepcopy(stack_tracker), deepcopy(current_stack_pointer), deepcopy(top_of_stack), func_name)
                all_if_instructions.extend([f"@{last_skip_id}"]+internal_else_instructions+[f"@{end_id}"])
                i += 1
            else:
                all_if_instructions.extend([f"@{last_skip_id}", f"@{end_id}"])
            instructions.extend(all_if_instructions)
        elif node[0] == "WHILE":
            start_pointer = deepcopy(current_stack_pointer)
            resolve_bool_instructions, current_stack_pointer = resolveBoolValue(node[1][0][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
            loop_id = getNextFreeId()
            skip_id = getNextFreeId()
            branch_decision_instructions = ["pop A;", "ldim B 1;", "and A;", f"brz #{skip_id};"]
            internal_while_instructions = compileAST(node[1][1], deepcopy(stack_tracker), deepcopy(current_stack_pointer), deepcopy(top_of_stack), function_tracker, func_name)
            instructions.extend([f"@{loop_id}"]+resolve_bool_instructions+branch_decision_instructions+internal_while_instructions+navigateStackPointer(current_stack_pointer, start_pointer)+[f"bra #{loop_id};", f"@{skip_id}"])
            i += 1
        elif node[0] == "ELSE":
            raise LangError("Encounted Else statement without an if statement before it!")
        elif node[0] == "ELIF":
            raise LangError("Encounted Elif statement without an if statement before it!")
        elif node[0] == "RETURN":
            if func_name is None:
                raise LangError("Returning when not in a function!")
            func_data = function_tracker[func_name]
            if func_data["TYPE"].upper() != getValueTypeOfNode(node[1], stack_tracker, function_tracker):
                raise LangError("Return type doesn't match function type!")
            if func_data["TYPE"] == "int":
                get_return_value_inst, current_stack_pointer = resolveIntValue(node[1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
                instructions.extend(get_return_value_inst+navigateStackPointer(current_stack_pointer, started_at)+["pop A;", "push A;", "ret;"])
            elif func_data["TYPE"] == "bool":
                get_return_value_inst, current_stack_pointer = resolveBoolValue(node[1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
                instructions.extend(get_return_value_inst+navigateStackPointer(current_stack_pointer, started_at)+["pop A;", "push A;", "ret;"])
            return instructions
        elif node[0] == "CALL":
            function_setup_instructions, current_stack_pointer = callFunction(node, current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
            if function_tracker[node[1][0]]["TYPE"] != None:
                function_setup_instructions.append("pop A;")
            instructions.extend(function_setup_instructions)
            i += 1   
    if not outer_most:
        instructions.extend(navigateStackPointer(current_stack_pointer, started_at))
    return instructions

# This will manipulate data until we have the value we want in a register (this being the literal value for bools and ints and a pointer for strings)
# This has to leave the current_stack_pointer back to where it came from when exiting
# TODO: When this can compile functions add them into this as well, however they get implemented
# TODO: Implement Divide and Multiply functions into the CPU for usage here
def resolveIntValue(node, current_stack_pointer, top_of_stack, stack_tracker, function_tracker):
    if node[0] == "PLUS":
        left_side_load_instructions, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        right_side_load_instructions, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        return left_side_load_instructions+right_side_load_instructions+["pop B;", "pop A;", "add A;", "push A;"], current_stack_pointer
    elif node[0] == "MINUS":
        left_side_load_instructions, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        right_side_load_instructions, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        return left_side_load_instructions+right_side_load_instructions+["pop B;", "pop A;", "sub A;", "push A;"], current_stack_pointer
    elif node[0] == "BITWISE_OR":
        left_side_load_instructions, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        right_side_load_instructions, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        return left_side_load_instructions+right_side_load_instructions+["pop B;", "pop A;", "or A;", "push A;"], current_stack_pointer
    elif node[0] == "BITWISE_AND":
        left_side_load_instructions, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        right_side_load_instructions, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        return left_side_load_instructions+right_side_load_instructions+["pop B;", "pop A;", "and A;", "push A;"], current_stack_pointer
    elif node[0] == "BITWISE_XOR":
        left_side_load_instructions, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        right_side_load_instructions, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        return left_side_load_instructions+right_side_load_instructions+["pop B;", "pop A;", "xor A;", "push A;"], current_stack_pointer
    elif node[0] == "LEFT_SHIFT":
        left_side_load_instructions, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        right_side_load_instructions, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        return left_side_load_instructions+right_side_load_instructions+["pop B;", "pop A;", "rolr A;", "push A;"], current_stack_pointer
    elif node[0] == "RIGHT_SHIFT":
        left_side_load_instructions, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        right_side_load_instructions, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        return left_side_load_instructions+right_side_load_instructions+["pop B;", "pop A;", "rorr A;", "push A;"], current_stack_pointer
    elif node[0] == "BITWISE_NOT":
        left_side_load_instructions, current_stack_pointer = resolveIntValue(node[1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        return left_side_load_instructions+["pop A;", "not A;", "push A;"], current_stack_pointer
    elif node[0] == "INT":
        return [f"ldim A {node[1]};", "push A;"], current_stack_pointer # TODO: this only works up to 22bit numbers unsigned, so this needs to check if the number is out of that range and thus store it elsewhere to be loaded
    elif node[0] == "UNKNOWN":
        if node[1] in stack_tracker.keys():
            if stack_tracker[node[1]]["TYPE"] != "int":
                raise LangError(f"Variable: {node[1]}: Adding integer with {stack_tracker[node[1]]["TYPE"]}!", node[2])
            return getValueFromStack(node[1], stack_tracker, current_stack_pointer)
        else:
            raise LangError(f"Variable {node[1]} not defined", node[2])
    elif node[0] == "CALL":
        function = function_tracker[node[1][0]] 
        if function["TYPE"] != "int":
            raise LangError(f"Called Function {node[1][0]} has a return type of {function["RETURN_TYPE"]} when an int is needed!", node[2])
        function_setup_instructions, current_stack_pointer = callFunction(node, current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        return function_setup_instructions, current_stack_pointer # because return pushes the output value to the stack for us we don't need to do anything more than prepare and call the function
    else:
        raise LangError(f"Trying to maths with a non maths node: {node}")

def resolveBoolValue(node, current_stack_pointer, top_of_stack, stack_tracker, function_tracker):
    if node[0] == "BOOL":
        if node[1] == "true":
            return ["ldim A 1;", "push A;"], current_stack_pointer
        else:
            return ["ldim A 0;", "push A;"], current_stack_pointer
    elif node[0] == "AND":
        load_bool_left, current_stack_pointer = resolveBoolValue(node[1][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        load_bool_right, current_stack_pointer = resolveBoolValue(node[1][1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        return load_bool_left+load_bool_right+["pop B;", "pop A;", "and A;", "push A;"], current_stack_pointer
    elif node[0] == "OR":
        load_bool_left, current_stack_pointer = resolveBoolValue(node[1][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        load_bool_right, current_stack_pointer = resolveBoolValue(node[1][1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        return load_bool_left+load_bool_right+["pop B;", "pop A;", "or A;", "push A;"], current_stack_pointer
    elif node[0] == "NOT":
        load_bool, current_stack_pointer = resolveBoolValue(node[1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        return load_bool+["pop A;", "not A;", "push A;"], current_stack_pointer
    elif node[0] == "LESS_THAN":
        load_int_left, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        load_int_right, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        jump_id = getNextFreeId()
        skip_id = getNextFreeId()
        return load_int_left+load_int_right+["pop B;", "pop A;", "sub A;", f"brp #{jump_id};", "ldim A 1;", "push A;", f"bra #{skip_id};", f"@{jump_id}", "ldim A 0;", "push A;", f"@{skip_id}"], current_stack_pointer
    elif node[0] == "MORE_THAN":
        load_int_left, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        load_int_right, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        jump_id = getNextFreeId()
        skip_id = getNextFreeId()
        return load_int_left+load_int_right+["pop A;", "pop B;", "sub A;", f"brp #{jump_id};", "ldim A 1;", "push A;", f"bra #{skip_id};", f"@{jump_id}", "ldim A 0;", "push A;", f"@{skip_id}"], current_stack_pointer
    elif node[0] == "LESS_THAN_OR_EQUAL_TO":
        load_int_left, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        load_int_right, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        jump_eq_id = getNextFreeId()
        jump_gt_id = getNextFreeId()
        skip_id = getNextFreeId()
        return load_int_left+load_int_right+["pop B;", "pop A;", "sub A;", f"brz #{jump_eq_id};", f"brp #{jump_gt_id};", f"@{jump_eq_id}", "ldim A 1;", "push A;", f"bra #{skip_id};", f"@{jump_gt_id}", "ldim A 0;", "push A;", f"@{skip_id}"], current_stack_pointer
    elif node[0] == "MORE_THAN_OR_EQUAL_TO":
        load_int_left, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        load_int_right, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        jump_eq_id = getNextFreeId()
        jump_lt_id = getNextFreeId()
        skip_id = getNextFreeId()
        return load_int_left+load_int_right+["pop A;", "pop B;", "sub A;", f"brz #{jump_eq_id};", f"brp #{jump_lt_id};", f"@{jump_eq_id};", "ldim A 1;", "push A;", f"bra #{skip_id};", f"@{jump_lt_id}", "ldim A 0;", "push A;", f"@{skip_id}"], current_stack_pointer
    elif node[0] == "EQUAL_TO":
        left_type = getValueTypeOfNode(node[1][0], stack_tracker, function_tracker)
        right_type = getValueTypeOfNode(node[1][1], stack_tracker, function_tracker)
        if left_type != right_type:
            raise LangError(f"Equal Comparison of mismatching types: {left_type} and {right_type}!")
        if left_type == "INT":
            load_int_left, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
            load_int_right, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
            jump_id = getNextFreeId()
            skip_id = getNextFreeId()
            return load_int_left+load_int_right+["pop B;", "pop A;", "sub A;", f"brz #{jump_id};", "ldim A 0;", "push A;", f"bra #{skip_id};", f"@{jump_id}", "ldim A 1;", "push A;", f"@{skip_id}"], current_stack_pointer
        elif left_type == "BOOL":
            load_bool_left, current_stack_pointer = resolveBoolValue(node[1][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
            load_bool_right, current_stack_pointer = resolveBoolValue(node[1][1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
            return load_bool_left+load_bool_right+["pop B;", "pop A;", "xnor A;", "ldim B 1;", "and A;", "push A;"], current_stack_pointer
    elif node[0] == "NOT_EQUAL_TO":
        left_type = getValueTypeOfNode(node[1][0], stack_tracker, function_tracker)
        right_type = getValueTypeOfNode(node[1][1], stack_tracker, function_tracker)
        if left_type != right_type:
            raise LangError(f"Not Equal Comparison of mismatching types: {left_type} and {right_type}!")
        if left_type == "INT":
            load_int_left, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
            load_int_right, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
            jump_id = getNextFreeId()
            skip_id = getNextFreeId()
            return load_int_left+load_int_right+["pop B;", "pop A;", "sub A;", f"brz #{jump_id};", "ldim A 1;", "push A;", f"bra #{skip_id};", f"@{jump_id}", "ldim A 0;", "push A;", f"@{skip_id}"], current_stack_pointer
        elif left_type == "BOOL":
            load_bool_left, current_stack_pointer = resolveBoolValue(node[1][0], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
            load_bool_right, current_stack_pointer = resolveBoolValue(node[1][1], current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
            return load_bool_left+load_bool_right+["pop B;", "pop A;", "xor A;", "ldim B 1;", "and A;", "push A;"], current_stack_pointer
    elif node[0] == "UNKNOWN":
        if node[1] in stack_tracker.keys():
            if stack_tracker[node[1]]["TYPE"] != "bool":
                raise LangError(f"Variable: {node[1]}: Adding integer with {stack_tracker[node[1]]["TYPE"]}!", node[2])
            return getValueFromStack(node[1], stack_tracker, current_stack_pointer)
        else:
            raise LangError(f"Variable {node[1]} not defined")
    elif node[0] == "CALL":
        function = function_tracker[node[1][0]]
        if function["TYPE"] != "bool":
            raise LangError(f"Called Function {node[1][0]} has a return type of {function["RETURN_TYPE"]} when an bool is needed!", node[2])
        function_setup_instructions, current_stack_pointer = callFunction(node, current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
        return function_setup_instructions, current_stack_pointer # because return pushes the output value to the stack for us we don't need to do anything more than prepare and call the function
    else:
        raise LangError(f"Trying to bool with a non boolean node: {node}")

# Gives the instructions to go from where we are on the stack to the variable and load it into A
def getValueFromStack(valueName, stack_tracker, current_stack_pointer):
    wanted_pointer = stack_tracker[valueName]["LOCATION"]
    difference = wanted_pointer-current_stack_pointer
    if difference == 0:
        return ["ldfr A VMem R13;", "push A;"], current_stack_pointer
    instructions = ["cpy A R13;"]
    if difference > 0:
        instructions.extend([f"ldim B {difference};", "add R13;"])
    else:
        instructions.extend([f"ldim B {abs(difference)};", "sub R13;"])
    instructions.extend(["ldfr A VMem R13;", "push A;"])
    current_stack_pointer = wanted_pointer
    return instructions, current_stack_pointer

# Gives the instructions to go from where we are on the stack to the variable and load it into A
def putValueInStack(valueName, stack_tracker, current_stack_pointer):
    instructions = ["push A;", "cpy A R13;"]
    wanted_pointer = stack_tracker[valueName]["LOCATION"]
    difference = wanted_pointer-current_stack_pointer
    if difference == 0:
        return ["stfr A VMem R13;"], current_stack_pointer
    elif difference > 0:
        instructions.extend([f"ldim B {difference};", "add R13;"])
    else:
        instructions.extend([f"ldim B {abs(difference)};", "sub R13;"])
    instructions.extend(["pop A;", "stfr A VMem R13;"])
    current_stack_pointer = wanted_pointer
    return instructions, current_stack_pointer

def getValueTypeOfNode(node, stack_tracker, function_tracker):
    if node[0] in ("PLUS", "MINUS", "INT"):
        return "INT"
    elif node[0] in ("BOOL", "AND", "OR", "NOT", "LESS_THAN", "MORE_THAN", "LESS_THAN_OR_EQUAL_TO", "MORE_THAN_OR_EQUAL_TO", "EQUAL_TO", "NOT_EQUAL_TO"):
        return "BOOL"
    elif node[0] == "UNKNOWN":
        return stack_tracker[node[1]]["TYPE"].upper()
    elif node[0] == "CALL":
        return function_tracker[node[1][0]]["TYPE"].upper()

def navigateStackPointer(current_pointer, wanted_pointer):
    instructions = ["cpy A R13;"]
    difference = wanted_pointer-current_pointer
    if difference == 0:
        return []
    if difference > 0:
        instructions.extend([f"ldim B {difference};", "add R13;"])
    else:
        instructions.extend([f"ldim B {abs(difference)};", "sub R13;"])
    return instructions

# Pops off the function args, assuming the current stack pointer is at the relative "0" for the function 
def getFuncArgs(func_node):
    args = func_node[1][1]
    instructions = []
    current_stack_pointer = 0
    top_of_stack = 0
    stack_tracker = {}
    for arg in args[::-1]:
        stack_tracker.update({arg[1]: {"LOCATION": top_of_stack, "TYPE": arg[0]}})
        top_of_stack += 1
        arg_inst, current_stack_pointer = putValueInStack(arg[1], stack_tracker, current_stack_pointer)
        instructions.extend(["pop A;"] + arg_inst)
    nav_inst = navigateStackPointer(current_stack_pointer, 0)
    current_stack_pointer = 0
    instructions.extend(nav_inst)
    return instructions, current_stack_pointer, top_of_stack, stack_tracker, args

# This pushes the arguments of the function on the processor stack to be used and calls the function
def callFunction(call_node, current_stack_pointer, top_of_stack, stack_tracker, function_tracker):
    instructions = []
    function_data = function_tracker[call_node[1][0]]
    for i, arg in enumerate(call_node[1][1]):
        valueType = getValueTypeOfNode(arg, stack_tracker, function_tracker)
        if valueType != function_data["ARGS"][i][0].upper():
            raise LangError("Passed argument and function argument type don't match!")
        if valueType == "INT":
            arg_load_instructions, current_stack_pointer = resolveIntValue(arg, current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
            instructions.extend(arg_load_instructions)
        elif valueType == "BOOL":
            arg_load_instructions, current_stack_pointer = resolveBoolValue(arg, current_stack_pointer, top_of_stack, stack_tracker, function_tracker)
            instructions.extend(arg_load_instructions)
    instructions.extend(navigateStackPointer(current_stack_pointer, top_of_stack))
    instructions.append(f"cal #{function_data["ID"]};")
    return instructions, deepcopy(top_of_stack)