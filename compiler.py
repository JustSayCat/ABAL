from custom_errors import LangError
from copy import deepcopy

NEXT_ID = 0

def getNextFreeId():
    global NEXT_ID
    current = NEXT_ID
    NEXT_ID += 1
    return current

# Upon this being called internally, we must ensure that at the end we resolve the current_stack_pointer to its initial value
def compileAST(nodes, stack_tracker=None, current_stack_pointer=None, top_of_stack=None, function_tracker=None):
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
    started_at = current_stack_pointer
    i = 0
    functionless_nodes = []
    for node in nodes:
        if node[0] == "FUNC":
            function_id = getNextFreeId()
            push_arguments_instructions, current_stack_pointer = resolveFuncArgs()
            function_stack_tracker = deepcopy(stack_tracker)
            # TODO: add the variables to the stack
            function_instructions = compileAST(node[1][3], deepcopy(current_stack_pointer), function_stack_tracker)
            instructions.extend([f"@{function_id}"]+function_instructions+["ret;"])
            function_tracker.update({node[1][0]: {"TYPE": node[1][2], "ARGS": [], "ID": function_id}})
        else:
            functionless_nodes.append(node)
    nodes = functionless_nodes
    while i < len(nodes):
        node = nodes[i]
        if node[0] == "DEFINE_ASSIGNMENT":
            if node[1][0] == "int":
                value_assignment, current_stack_pointer = resolveIntValue(node[1][2], current_stack_pointer, stack_tracker) # Get the instructions to load the value of the variable into A
                instructions.extend(value_assignment)
                stack_tracker.update({node[1][1]: {"LOCATION": top_of_stack, "TYPE": node[1][0]}})
                top_of_stack += 1
                memory_save, current_stack_pointer = putValueInStack(node[1][1], stack_tracker, current_stack_pointer)
                instructions.extend(["pop A;"] + memory_save)
            elif node[1][0] == "bool":
                value_assignment, current_stack_pointer = resolveBoolValue(node[1][2], current_stack_pointer, stack_tracker) # Get the instructions to load the value of the variable into A
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
                value_assignment, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, stack_tracker) # Get the instructions to load the value of the variable into A
                instructions.extend(value_assignment)
                memory_save, current_stack_pointer = putValueInStack(node[1][0], stack_tracker, current_stack_pointer)
                instructions.extend(["pop A;"] + memory_save)
            elif value_type == "bool":
                value_assignment, current_stack_pointer = resolveBoolValue(node[1][1], current_stack_pointer, stack_tracker) # Get the instructions to load the value of the variable into A
                instructions.extend(value_assignment)
                memory_save, current_stack_pointer = putValueInStack(node[1][0], stack_tracker, current_stack_pointer)
                instructions.extend(["pop A;"] + memory_save)
            i += 1
        elif node[0] == "IF":
            resolve_bool_instructions, current_stack_pointer = resolveBoolValue(node[1][0][0], current_stack_pointer, stack_tracker)
            skip_id = getNextFreeId()
            end_id = getNextFreeId()
            branch_decision_instructions = ["pop A;", "ldim B 1;", "and A;", f"brz #{skip_id};"]
            internal_if_instructions = compileAST(node[1][1], deepcopy(stack_tracker), deepcopy(current_stack_pointer), deepcopy(top_of_stack))
            all_if_instructions = resolve_bool_instructions+branch_decision_instructions+internal_if_instructions+[f"bra #{end_id};"]
            i+=1
            last_skip_id = skip_id
            while nodes[i][0] == "ELIF":
                elif_skip_id = getNextFreeId()
                resolve_elif_bool_instructions, current_stack_pointer = resolveBoolValue(nodes[i][1][0][0], current_stack_pointer, stack_tracker)
                elif_branch_decision_instructions = ["pop A;", "ldim B 1;", "and A;", f"brz #{elif_skip_id};"]
                internal_elif_instructions = compileAST(nodes[i][1][1], deepcopy(stack_tracker), deepcopy(current_stack_pointer), deepcopy(top_of_stack))
                all_if_instructions.extend([f"@{last_skip_id}"]+resolve_elif_bool_instructions+elif_branch_decision_instructions+internal_elif_instructions+[f"bra #{end_id};"])
                last_skip_id = elif_skip_id
                i += 1
            if nodes[i][0] == "ELSE":
                internal_else_instructions = compileAST(nodes[i][1], deepcopy(stack_tracker), deepcopy(current_stack_pointer), deepcopy(top_of_stack))
                all_if_instructions.extend([f"@{last_skip_id}"]+internal_else_instructions+[f"@{end_id}"])
                i += 1
            instructions.extend(all_if_instructions)
        elif node[0] == "WHILE":
            resolve_bool_instructions, current_stack_pointer = resolveBoolValue(node[1][0][0], current_stack_pointer, stack_tracker)
            loop_id = getNextFreeId()
            skip_id = getNextFreeId()
            branch_decision_instructions = ["pop A;", "ldim B 1;", "and A;", f"brz #{skip_id};"]
            internal_while_instructions = compileAST(node[1][1], deepcopy(stack_tracker), deepcopy(current_stack_pointer), deepcopy(top_of_stack))
            instructions.extend([f"@{loop_id}"]+resolve_bool_instructions+internal_while_instructions+[f"bra #{loop_id};", f"@{skip_id}"])
            i += 1
        elif node[0] == "ELSE":
            raise LangError("Encounted Else statement without an if statement before it!")
        elif node[0] == "ELIF":
            raise LangError("Encounted Elif statement without an if statement before it!")
    if not outer_most:
        instructions.extend(navigateStackPointer(current_stack_pointer, started_at))
    return instructions

# This will manipulate data until we have the value we want in a register (this being the literal value for bools and ints and a pointer for strings)
# This has to leave the current_stack_pointer back to where it came from when exiting
# TODO: When this can compile functions add them into this as well, however they get implemented
# TODO: Implement Divide and Multiply functions into the CPU for usage here
def resolveIntValue(node, current_stack_pointer, stack_tracker):
    if node[0] == "PLUS":
        left_side_load_instructions, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, stack_tracker)
        right_side_load_instructions, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, stack_tracker)
        return left_side_load_instructions+right_side_load_instructions+["pop B;", "pop A;", "add A;", "push A;"], current_stack_pointer
    elif node[0] == "MINUS":
        left_side_load_instructions, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, stack_tracker)
        right_side_load_instructions, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, stack_tracker)
        return left_side_load_instructions+right_side_load_instructions+["pop B;", "pop A;", "sub A;", "push A;"], current_stack_pointer
    elif node[0] == "INT":
        return [f"ldim A {node[1]};", "push A;"], current_stack_pointer # TODO: this only works up to 22bit numbers unsigned, so this needs to check if the number is out of that range and thus store it elsewhere to be loaded
    elif node[0] == "UNKNOWN":
        if node[1] in stack_tracker.keys():
            if stack_tracker[node[1]]["TYPE"] != "int":
                raise LangError(f"Variable: {node[1]}: Adding integer with {stack_tracker[node[1]]["TYPE"]}!", node[2])
            return getValueFromStack(node[1], stack_tracker, current_stack_pointer)
        else:
            raise LangError(f"Variable {node[1]} not defined", node[2])
    '''
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
    '''

def resolveBoolValue(node, current_stack_pointer, stack_tracker):
    if node[0] == "BOOL":
        if node[1] == "true":
            return ["ldim A 1;", "push A;"], current_stack_pointer
        else:
            return ["ldim A 0;", "push A;"], current_stack_pointer
    elif node[0] == "AND":
        load_bool_left, current_stack_pointer = resolveBoolValue(node[1][0], current_stack_pointer, stack_tracker)
        load_bool_right, current_stack_pointer = resolveBoolValue(node[1][1], current_stack_pointer, stack_tracker)
        return load_bool_left+load_bool_right+["pop B;", "pop A;", "and A;", "push A;"], current_stack_pointer
    elif node[0] == "OR":
        load_bool_left, current_stack_pointer = resolveBoolValue(node[1][0], current_stack_pointer, stack_tracker)
        load_bool_right, current_stack_pointer = resolveBoolValue(node[1][1], current_stack_pointer, stack_tracker)
        return load_bool_left+load_bool_right+["pop B;", "pop A;", "or A;", "push A;"], current_stack_pointer
    elif node[0] == "NOT":
        load_bool, current_stack_pointer = resolveBoolValue(node[1][0], current_stack_pointer, stack_tracker)
        return load_bool+["pop A;", "not A;", "push A;"], current_stack_pointer
    elif node[0] == "LESS_THAN":
        load_int_left, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, stack_tracker)
        load_int_right, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, stack_tracker)
        jump_id = getNextFreeId()
        skip_id = getNextFreeId()
        return load_int_left+load_int_right+["pop B;", "pop A;", "sub A;", f"brp #{jump_id};", "ldim A 1;", "push A;", f"bra #{skip_id};", f"@{jump_id}", "ldim A 0;", "push A;", f"@{skip_id}"], current_stack_pointer
    elif node[0] == "MORE_THAN":
        load_int_left, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, stack_tracker)
        load_int_right, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, stack_tracker)
        jump_id = getNextFreeId()
        skip_id = getNextFreeId()
        return load_int_left+load_int_right+["pop A;", "pop B;", "sub A;", f"brp #{jump_id};", "ldim A 1;", "push A;", f"bra #{skip_id};", f"@{jump_id}", "ldim A 0;", "push A;", f"@{skip_id}"], current_stack_pointer
    elif node[0] == "LESS_THAN_OR_EQUAL_TO":
        load_int_left, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, stack_tracker)
        load_int_right, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, stack_tracker)
        jump_eq_id = getNextFreeId()
        jump_gt_id = getNextFreeId()
        skip_id = getNextFreeId()
        return load_int_left+load_int_right+["pop B;", "pop A;", "sub A;", f"brz #{jump_eq_id};", f"brp #{jump_gt_id};", f"@{jump_eq_id}", "ldim A 1;", "push A;", f"bra #{skip_id};", f"@{jump_gt_id}", "ldim A 0;", "push A;", f"@{skip_id}"], current_stack_pointer
    elif node[0] == "MORE_THAN_OR_EQUAL_TO":
        load_int_left, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, stack_tracker)
        load_int_right, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, stack_tracker)
        jump_eq_id = getNextFreeId()
        jump_lt_id = getNextFreeId()
        skip_id = getNextFreeId()
        return load_int_left+load_int_right+["pop A;", "pop B;", "sub A;", f"brz #{jump_eq_id};", f"brp #{jump_lt_id};", f"@{jump_eq_id};", "ldim A 1;", "push A;", f"bra #{skip_id};", f"@{jump_lt_id}", "ldim A 0;", "push A;", f"@{skip_id}"], current_stack_pointer
    elif node[0] == "EQUAL_TO":
        left_type = getValueTypeOfNode(node[1][0], stack_tracker)
        right_type = getValueTypeOfNode(node[1][1], stack_tracker)
        if left_type != right_type:
            raise LangError(f"Equal Comparison of mismatching types: {left_type} and {right_type}!")
        if left_type == "INT":
            load_int_left, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, stack_tracker)
            load_int_right, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, stack_tracker)
            jump_id = getNextFreeId()
            skip_id = getNextFreeId()
            return load_int_left+load_int_right+["pop B;", "pop A;", "sub A;", f"brz #{jump_id};", "ldim A 0;", "push A;", f"bra #{skip_id};", f"@{jump_id}", "ldim A 1;", "push A;", f"@{skip_id}"], current_stack_pointer
        elif left_type == "BOOL":
            load_bool_left, current_stack_pointer = resolveBoolValue(node[1][0], current_stack_pointer, stack_tracker)
            load_bool_right, current_stack_pointer = resolveBoolValue(node[1][1], current_stack_pointer, stack_tracker)
            return load_bool_left+load_bool_right+["pop B;", "pop A;", "xnor A;", "ldim B 1;", "and A;", "push A;"], current_stack_pointer
    elif node[0] == "NOT_EQUAL_TO":
        left_type = getValueTypeOfNode(node[1][0], stack_tracker)
        right_type = getValueTypeOfNode(node[1][1], stack_tracker)
        if left_type != right_type:
            raise LangError(f"Not Equal Comparison of mismatching types: {left_type} and {right_type}!")
        if left_type == "INT":
            load_int_left, current_stack_pointer = resolveIntValue(node[1][0], current_stack_pointer, stack_tracker)
            load_int_right, current_stack_pointer = resolveIntValue(node[1][1], current_stack_pointer, stack_tracker)
            jump_id = getNextFreeId()
            skip_id = getNextFreeId()
            return load_int_left+load_int_right+["pop B;", "pop A;", "sub A;", f"brz #{jump_id};", "ldim A 1;", "push A;", f"bra #{skip_id};", f"@{jump_id}", "ldim A 0;", "push A;", f"@{skip_id}"], current_stack_pointer
        elif left_type == "BOOL":
            load_bool_left, current_stack_pointer = resolveBoolValue(node[1][0], current_stack_pointer, stack_tracker)
            load_bool_right, current_stack_pointer = resolveBoolValue(node[1][1], current_stack_pointer, stack_tracker)
            return load_bool_left+load_bool_right+["pop B;", "pop A;", "xor A;", "ldim B 1;", "and A;", "push A;"], current_stack_pointer
    elif node[0] == "UNKNOWN":
        if node[1] in stack_tracker.keys():
            if stack_tracker[node[1]]["TYPE"] != "bool":
                raise LangError(f"Variable: {node[1]}: Adding integer with {stack_tracker[node[1]]["TYPE"]}!", node[2])
            return getValueFromStack(node[1], stack_tracker, current_stack_pointer)
        else:
            raise LangError(f"Variable {node[1]} not defined", node[2])
    '''
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
        else:
            raise LangError(f"Trying to bool with a non boolean node: {node[0]}", node[2])
    '''

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

def getValueTypeOfNode(node, stack_tracker):
    if node[0] == "INT":
        return "INT"
    elif node[0] == "BOOL":
        return "BOOL"
    elif node[0] == "UNKNOWN":
        return stack_tracker[node[1]]["TYPE"].upper()

def navigateStackPointer(current_pointer, wanted_pointer):
    instructions = ["cpy A R13;"]
    difference = wanted_pointer-current_pointer
    if difference > 0:
        instructions.extend([f"ldim B {difference};", "add R13;"])
    else:
        instructions.extend([f"ldim B {abs(difference)};", "sub R13;"])
    return instructions