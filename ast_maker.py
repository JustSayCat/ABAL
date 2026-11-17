from custom_errors import LangError

DEBUG = False

def parse(tokens):
    finished_nodes = []
    indent_stack = []
    stack = []
    i = 0
    if len(tokens) == 0:
        return []
    while i < len(tokens):
        current_token = tokens[i]

        if DEBUG:
            print(indent_stack)
            print(stack)
            print()
                
        if len(stack) >= 4:
            if stack[-2][1] in ("PLUS", "MINUS", "MULTIPLY", "DIVIDE", "LEFT_SHIFT", "RIGHT_SHIFT", "BITWISE_AND", "BITWISE_OR", "BITWISE_XOR") and current_token[1] == "CLOSE_PAREN" and stack[-4][1] == "OPEN_PAREN":
                stack = stack[:-4] + [(stack[-2][1], (stack[-3], stack[-1]), stack[-1][2])]
                i += 1
                continue

        if len(stack) >= 3:
            if stack[-2][1] in ("MULTIPLY", "DIVIDE", "LEFT_SHIFT", "RIGHT_SHIFT") and stack[-1][1] != "OPEN_PAREN":
                stack = stack[:-3] + [(stack[-2][1], (stack[-3], stack[-1]), stack[-1][2])]
                continue
            elif stack[-2][1] in ("PLUS", "MINUS", "BITWISE_AND", "BITWISE_OR", "BITWISE_XOR") and current_token[1] in ("END_COMMAND", "PLUS", "MINUS", "BITWISE_AND", "BITWISE_OR", "BITWISE_XOR"):
                stack = stack[:-3] + [(stack[-2][1], (stack[-3], stack[-1]), stack[-1][2])]
                continue
            elif stack[-3][1] == "func" and stack[-2][0] == "UNKNOWN" and stack[-1][1] == "OPEN_PAREN":
                if len(indent_stack) > 0:
                    raise LangError("A function must be defined in global scope", stack[-1][2])
                stack = stack[:-3] + [("FUNC", (stack[-2][1], [], (), []), stack[-1][2])]
                continue
            elif stack[-3][0] == "DEFINITION" and stack[-2][1] == "OPEN_SQUARE" and stack[-1][1] == "CLOSE_SQUARE":
                stack = stack[:-3] + [("DEFINITION", "ARRAY_"+stack[-3][1].upper(), stack[-1][2])]
                continue
            elif stack[-3][1] == "OPEN_SQUARE" and stack[-2][0] in ("INT", "UNKNOWN") and stack[-1][1] == "CLOSE_SQUARE":
                stack = stack[:-3] + [("ARRAY_ID", stack[-2], stack[-1][2])]
                continue

        if len(stack) >= 2:
            if stack[0][0] == "DEFINITION" and stack[1][0] == "UNKNOWN":
                stack = [("DEFINE", (stack[0][1], stack[1][1], stack[1][2]))]
                continue
            elif stack[0][0] == "DEFINE" and stack[1][1] == "SET_TO":
                stack = [("DEFINE_ASSIGNMENT", stack[0][1], stack[1][2])]
                continue
            elif stack[0][0] == "UNKNOWN" and stack[1][1] == "SET_TO":
                stack = [("ASSIGNMENT", stack[0][1], stack[1][2])]
                continue
            elif stack[-2][1] == "BITWISE_NOT" and stack[-1][0] == "INT":
                stack = stack[:-2] + [("BITWISE_NOT", stack[-1])]
                continue
            elif stack[0][0] == "ARRAY_INDEX" and stack[1][1] == "SET_TO":
                stack = [("INDEX_ASSIGNMENT", stack[0][1], stack[1][2])]
                continue
            elif stack[0][1] in ("if", "elif", "while") and stack[1][1] == "OPEN_PAREN":
                stack = [(stack[0][1].upper(), (), stack[0][2])] 
                continue
            elif stack[0][0] in ("IF", "ELIF", "WHILE") and stack[-1][1] == "OPEN_BRACE":
                if DEBUG:
                    print(f"Evalutating: {stack[0][0]}")
                    print(stack[1:-2])
                indent_stack.append((stack[0][0], (cleanUpBooleanExpressions(stack[1:-2]), []), stack[0][2]))
                if DEBUG:
                    print(f"Finished Evaluation of {stack[0][0]}")
                stack = []
                continue
            elif stack[0][1] == "else" and stack[1][1] == "OPEN_BRACE":
                indent_stack.append(("ELSE", [], stack[0][2]))
                stack = []
                continue
            elif stack[0][0] == "FUNC" and stack[-1][1] == "CLOSE_PAREN":
                stack = [("FUNC", (stack[0][1][0], getGenericArguments(stack[1:-1]), None, []), stack[0][2])]
                continue
            elif stack[0][0] == "FUNC" and stack[-1][1] == "OPEN_BRACE":
                if len(stack) == 2:
                    indent_stack.append(("FUNC", (stack[0][1][0], stack[0][1][1], None, []), stack[0][2]))
                    stack = []
                elif len(stack) == 3:
                    indent_stack.append(("FUNC", (stack[0][1][0], stack[0][1][1], stack[-2][1], []), stack[0][2]))
                    stack = []
                else:
                    raise LangError("Function declaration is wrong", stack[0][2])
                continue
            elif stack[-2][0] == "UNKNOWN" and stack[-1][1] == "OPEN_PAREN":
                stack = stack[:-2] + [("CALL", (stack[-2][1], None), stack[-1][2])]
            elif stack[-1][1] == "CLOSE_PAREN":
                found = False
                if DEBUG:
                    print("SEARCHING")
                for pre_j, element in enumerate(reversed(stack)):
                    j = len(stack)-(pre_j+1)
                    if element[0] == "CALL" and element[1][1] == None:
                        stack = stack[:j] + [("CALL", (element[1][0], getPassedArguments(stack[j+1:-1])), element[2])]
                        found = True
                        break
                if found:
                    continue
            elif stack[-2][0] == "UNKNOWN" and stack[-1][0] == "ARRAY_ID":
                stack = stack[:-2] + [("ARRAY_INDEX", (stack[-2][1], stack[-1][1]), stack[-2][2])]
            

        if len(stack) == 1:
            if stack[0][1] == "CLOSE_BRACE":
                if len(indent_stack) > 0:
                    popped_indent = indent_stack.pop()
                    if len(indent_stack) > 0 and indent_stack[-1][0] == "WHILE":
                        indent_stack[-1][1][1].append(popped_indent)
                    elif len(indent_stack) > 0 and indent_stack[-1][0] == "IF":
                        indent_stack[-1][1][1].append(popped_indent)
                    elif len(indent_stack) > 0 and indent_stack[-1][0] == "ELSE":
                        indent_stack[-1][1].append(popped_indent)
                    elif len(indent_stack) > 0 and indent_stack[-1][0] == "ELIF":
                        indent_stack[-1][1][1].append(popped_indent)
                    elif len(indent_stack) > 0 and indent_stack[0][0] == "FUNC":
                        indent_stack[0][1][3].append(popped_indent)
                    else:
                        finished_nodes.append(popped_indent)
                    stack = []
                    continue
                else:
                    raise LangError("Closing Brace with no block to close", stack[0][2])

        if current_token[1] == "END_COMMAND":
            stack = cleanUpBooleanExpressions(stack)
            if len(stack) == 0:
                i += 1
                continue
            if stack[0][0] == "DEFINE":
                added_node = stack[0]
                if len(indent_stack) > 0:
                    if indent_stack[-1][0] in ("IF", "WHILE", "ELIF"):
                        indent_stack[-1][1][1].append(added_node)
                    elif indent_stack[-1][0] == "FUNC":
                        indent_stack[-1][1][3].append(added_node)
                    else:
                        indent_stack[-1][1].append(added_node)
                else:
                    finished_nodes.append(added_node)
            elif stack[0][0] == "DEFINE_ASSIGNMENT":
                if len(stack) != 2:
                    raise LangError(f"Define Assignment Has Failed \nStack:\n{stack}", stack[0][2])
                added_node = ("DEFINE_ASSIGNMENT", (stack[0][1][0], stack[0][1][1], stack[1]))
                if len(indent_stack) > 0:
                    if indent_stack[-1][0] in ("IF", "WHILE", "ELIF"):
                        indent_stack[-1][1][1].append(added_node)
                    elif indent_stack[-1][0] == "FUNC":
                        indent_stack[-1][1][3].append(added_node)
                    else:
                        indent_stack[-1][1].append(added_node)
                else:
                    finished_nodes.append(added_node)
            elif stack[0][0] == "ASSIGNMENT":
                if len(stack) != 2:
                    raise LangError(f"Assignment Has Failed \nStack:\n{stack}", stack[0][2])
                added_node = (stack[0][0], (stack[0][1][0], stack[1]))
                if len(indent_stack) > 0:
                    if indent_stack[-1][0] in ("IF", "WHILE", "ELIF"):
                        indent_stack[-1][1][1].append(added_node)
                    elif indent_stack[-1][0] == "FUNC":
                        indent_stack[-1][1][3].append(added_node)
                    else:
                        indent_stack[-1][1].append(added_node)
                else:
                    finished_nodes.append(added_node)
            elif stack[0][0] == "INDEX_ASSIGNMENT":
                if len(stack) != 2:
                    raise LangError(f"Index Assignment Has Failed \nStack:\n{stack}", stack[0][2])
                added_node = (stack[0][0], (stack[0][1][0], stack[0][1][1], stack[1]))
                if len(indent_stack) > 0:
                    if indent_stack[-1][0] in ("IF", "WHILE", "ELIF"):
                        indent_stack[-1][1][1].append(added_node)
                    elif indent_stack[-1][0] == "FUNC":
                        indent_stack[-1][1][3].append(added_node)
                    else:
                        indent_stack[-1][1].append(added_node)
                else:
                    finished_nodes.append(added_node)
            elif stack[0][1] == "return":
                if len(indent_stack) == 0:
                    raise LangError("Cannot return when outside a function", stack[0][2])
                if indent_stack[0][0] != "FUNC":
                    raise LangError("Can only return out of a function", stack[0][2])
                if indent_stack[0][1][2] == None:
                    if len(stack) >= 2:
                        raise LangError("Cannot return an item from a void function", stack[0][2])
                    added_node = ("RETURN", None)
                    if indent_stack[-1][0] in ("IF", "WHILE", "ELIF"):
                        indent_stack[-1][1][1].append(added_node)
                    elif indent_stack[-1][0] == "FUNC":
                        indent_stack[-1][1][3].append(added_node)
                    else:
                        indent_stack[-1][1].append(added_node)
                else:
                    if len(stack) > 2 and indent_stack[0][1][2] != None:
                        raise LangError("Can only return 1 item from a function", stack[0][2])
                    added_node = ("RETURN", stack[1])
                    if indent_stack[-1][0] in ("IF", "WHILE", "ELIF"):
                        indent_stack[-1][1][1].append(added_node)
                    elif indent_stack[-1][0] == "FUNC":
                        indent_stack[-1][1][3].append(added_node)
                    else:
                        indent_stack[-1][1].append(added_node)
            else:
                for node in stack:
                    if len(indent_stack) > 0:
                        if indent_stack[-1][0] in ("IF", "WHILE", "ELIF"):
                            indent_stack[-1][1][1].append(node)
                        elif indent_stack[-1][0] == "FUNC":
                            indent_stack[-1][1][3].append(node)
                        else:
                            indent_stack[-1][1].append(node)
                    else:
                        finished_nodes.append(node)
            stack = []
            i += 1
            continue
        stack.append(current_token)
        i += 1
    return finished_nodes

def getGenericArguments(stack):
    arguments = []
    state = 0
    for element in stack:
        if state == 2 and element[1] != "SEPARATOR":
            raise LangError("Arguments must be separated by a \",\"", element[2])
        elif state == 1 and element[0] == "UNKNOWN":
            arguments.append((arguments.pop(), element[1]))
            state = 2
        elif state == 1 and element[0] != "UNKNOWN":
            raise LangError("Arguments have to be variables", element[2])
        elif state == 0 and element[0] == "DEFINITION":
            arguments.append(element[1])
            state = 1
        elif state == 0 and element[0] != "DEFINITION":
            raise LangError("Arguments have to be type annotated", element[2])
        else:
            state = 0
    return arguments

def getPassedArguments(stack):
    if DEBUG:
        print("PROCESSING ARGUMENTS")
        print(stack)
    unclean_arguments = [[]]
    for element in stack:
        if element[1] == "SEPARATOR":
            unclean_arguments.append([])
        else:
            unclean_arguments[-1].append(element)
    arguments = []
    if unclean_arguments[0] != []:
        for cluster in unclean_arguments:
            if DEBUG:
                print(cluster)
            parsed = parse(cluster+[("SYNTAX", "END_COMMAND")])
            if DEBUG:
                print(parse)
            if len(parsed) != 1:
                raise LangError("Missing arguments, or bad syntax", stack[0][2])
            arguments.append(parsed[0])
    if DEBUG:
        print("FINISHED")
        print(arguments)
        print()
    return arguments

def cleanUpBooleanExpressions(stack):
    if DEBUG:
        print(f"CLEANING: {stack}")
    collection = [[]]
    resolved_stack = []
    # Resolve brackets
    for element in stack:
        if element[1] == "OPEN_PAREN":
            collection.append([])
        elif element[1] == "CLOSE_PAREN" and len(collection)>0:
            collection[-2] += cleanUpBooleanExpressions(collection.pop())
        elif element[1] in ("&&", "||"):
            temp_resolve = cleanUpBooleanExpressions(collection.pop())
            collection.append(temp_resolve+[element])
        else:
            collection[-1].append(element)
    resolved_stack = collection[0]
    # Resolve Whole
    changed = True
    while changed:

        if len(resolved_stack) >= 5:
            if resolved_stack[-4][1] in ("MORE_THAN", "LESS_THAN", "MORE_THAN_OR_EQUAL_TO", "LESS_THAN_OR_EQUAL_TO", "EQUAL_TO", "NOT_EQUAL_TO") and resolved_stack[-3][0] and resolved_stack[-2][1] in ("&&", "||"):
                if resolved_stack[-5][0] in ("INT", "UNKNOWN", "MULTIPLY", "DIVIDE", "PLUS", "MINUS") and resolved_stack[-4][1] in ("MORE_THAN", "LESS_THAN", "MORE_THAN_OR_EQUAL_TO", "LESS_THAN_OR_EQUAL_TO", "EQUAL_TO", "NOT_EQUAL_TO") and resolved_stack[-3][0] in ("INT", "UNKNOWN", "MULTIPLY", "DIVIDE", "PLUS", "MINUS"):
                    resolved_stack = resolved_stack[:-5] + [(resolved_stack[-4][1], (resolved_stack[-5], resolved_stack[-3])), resolved_stack[-2], resolved_stack[-1]]
                    continue
                elif resolved_stack[-5][0] in ("UNKNOWN", "BOOL") and resolved_stack[-4][1] in ("EQUAL_TO", "NOT_EQUAL_TO") and resolved_stack[-3][0] in ("UNKNOWN", "BOOL"):
                    resolved_stack = resolved_stack[:-5] + [(resolved_stack[-4][1], (resolved_stack[-5], resolved_stack[-3])), resolved_stack[-2], resolved_stack[-1]]
                    continue
                elif resolved_stack[-5][0] in ("UNKNOWN", "CHAR") and resolved_stack[-4][1] in ("EQUAL_TO", "NOT_EQUAL_TO") and resolved_stack[-3][0] in ("UNKNOWN", "CHAR"):
                    resolved_stack = resolved_stack[:-5] + [(resolved_stack[-4][1], (resolved_stack[-5], resolved_stack[-3])), resolved_stack[-2], resolved_stack[-1]]
                    continue

        if len(resolved_stack) >= 4:
            if resolved_stack[-4][1] != "NOT" and resolved_stack[-3][0] in ("MORE_THAN", "LESS_THAN", "MORE_THAN_OR_EQUAL_TO", "LESS_THAN_OR_EQUAL_TO", "EQUAL_TO", "NOT_EQUAL_TO", "AND", "OR", "UNKNOWN", "BOOL", "NOT", "CALL") and resolved_stack[-2][1] in ("&&", "||") and resolved_stack[-1][0] in ("MORE_THAN", "LESS_THAN", "MORE_THAN_OR_EQUAL_TO", "LESS_THAN_OR_EQUAL_TO", "EQUAL_TO", "NOT_EQUAL_TO", "AND", "OR", "UNKNOWN", "BOOL", "NOT", "CALL"):
                if resolved_stack[-2][1] == "&&":
                    resolved_stack = resolved_stack[:-3] + [("AND", (resolved_stack[-3], resolved_stack[-1]))]
                elif resolved_stack[-2][1] == "||":
                    resolved_stack = resolved_stack[:-3] + [("OR", (resolved_stack[-3], resolved_stack[-1]))]
                continue
            elif resolved_stack[-4][1] == "NOT" and resolved_stack[-3][0] in ("MORE_THAN", "LESS_THAN", "MORE_THAN_OR_EQUAL_TO", "LESS_THAN_OR_EQUAL_TO", "EQUAL_TO", "NOT_EQUAL_TO", "AND", "OR", "UNKNOWN", "BOOL", "NOT"):
                resolved_stack = resolved_stack[:-4] + [("NOT", (resolved_stack[-3])), resolved_stack[-2], resolved_stack[-1]]
                continue

        if len(resolved_stack) >= 3:
            if resolved_stack[-3][0] in ("MORE_THAN", "LESS_THAN", "MORE_THAN_OR_EQUAL_TO", "LESS_THAN_OR_EQUAL_TO", "EQUAL_TO", "NOT_EQUAL_TO", "AND", "OR", "UNKNOWN", "BOOL", "NOT", "CALL") and resolved_stack[-2][1] in ("&&", "||") and resolved_stack[-1][0] in ("MORE_THAN", "LESS_THAN", "MORE_THAN_OR_EQUAL_TO", "LESS_THAN_OR_EQUAL_TO", "EQUAL_TO", "NOT_EQUAL_TO", "AND", "OR", "UNKNOWN", "BOOL", "NOT", "CALL"):
                if resolved_stack[-2][1] == "&&":
                    resolved_stack = resolved_stack[:-3] + [("AND", (resolved_stack[-3], resolved_stack[-1]))]
                elif resolved_stack[-2][1] == "||":
                    resolved_stack = resolved_stack[:-3] + [("OR", (resolved_stack[-3], resolved_stack[-1]))]
                continue
            elif resolved_stack[-3][0] in ("INT", "UNKNOWN", "MULTIPLY", "DIVIDE", "PLUS", "MINUS", "CALL") and resolved_stack[-2][1] in ("MORE_THAN", "LESS_THAN", "MORE_THAN_OR_EQUAL_TO", "LESS_THAN_OR_EQUAL_TO", "EQUAL_TO", "NOT_EQUAL_TO") and resolved_stack[-1][0] in ("INT", "UNKNOWN", "MULTIPLY", "DIVIDE", "PLUS", "MINUS", "CALL"):
                resolved_stack = resolved_stack[:-3] + [(resolved_stack[-2][1], (resolved_stack[-3], resolved_stack[-1]))]
                continue
            elif resolved_stack[-3][0] in ("UNKNOWN", "BOOL", "CALL", "ARRAY_CHAR") and resolved_stack[-2][1] in ("EQUAL_TO", "NOT_EQUAL_TO") and resolved_stack[-1][0] in ("UNKNOWN", "BOOL", "CALL", "ARRAY_CHAR"):
                resolved_stack = resolved_stack[:-3] + [(resolved_stack[-2][1], (resolved_stack[-3], resolved_stack[-1]))]
                continue
            elif resolved_stack[-3][0] in ("UNKNOWN", "CHAR", "CALL", "ARRAY_CHAR") and resolved_stack[-2][1] in ("EQUAL_TO", "NOT_EQUAL_TO") and resolved_stack[-1][0] in ("UNKNOWN", "CHAR", "CALL", "ARRAY_CHAR"):
                resolved_stack = resolved_stack[:-3] + [(resolved_stack[-2][1], (resolved_stack[-3], resolved_stack[-1]))]
                continue

        if len(resolved_stack) >= 2:
            if resolved_stack[-2][1] == "NOT" and resolved_stack[-1][0] in ("MORE_THAN", "LESS_THAN", "MORE_THAN_OR_EQUAL_TO", "LESS_THAN_OR_EQUAL_TO", "EQUAL_TO", "NOT_EQUAL_TO", "AND", "OR", "UNKNOWN", "BOOL"):
                resolved_stack = resolved_stack[:-2] + [("NOT", (resolved_stack[-1]))]
                continue
        changed = False
    return resolved_stack