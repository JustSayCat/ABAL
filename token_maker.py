SYNTAX_TOKENS = {
    "+": "PLUS",
    "-": "MINUS",
    "*": "MULTIPLY",
    "/": "DIVIDE",
    "(": "OPEN_PAREN",
    ")": "CLOSE_PAREN",
    ";": "END_COMMAND",
    "[": "OPEN_SQUARE",
    "]": "CLOSE_SQUARE",
    "{": "OPEN_BRACE",
    "}": "CLOSE_BRACE",
    ",": "SEPARATOR"
}
KEYWORDS = {
    "if": "CONTROL",
    "else": "INVERTED_CONTROL",
    "elif": "CONTROL",
    "while": "CONTROL",
    "int": "DEFINITION",
    "char": "DEFINITION",
    "bool": "DEFINITION",
    "func": "FUNCTION",
    "return": "STATEMENT",
    "true": "BOOL",
    "false": "BOOL",
    "&&": "SYNTAX",
    "||": "SYNTAX"
}

def tokeniser(contents):
    tokens = []
    token_type = ""
    current_token = ""
    i = 0
    contents += " "
    line = 1
    column = 0
    while i < len(contents):
        l = contents[i]
        if l == "\n":
            column = 0
            line = line+1
        else:
            column = column+1
        if l != "=" and token_type in ("SET_TO", "LESS_THAN", "MORE_THAN", "NOT"):
            tokens.append(("SYNTAX", token_type, (line, column)))
            token_type = ""
        elif l in SYNTAX_TOKENS.keys() and token_type == "":
            tokens, token_type, current_token = cleanUpCurrentToken(tokens, token_type, current_token, line, column)
            tokens.append(("SYNTAX", SYNTAX_TOKENS[l], (line, column)))
            i += 1
        elif l == "\"" and token_type == "":
            token_type = "CHAR"
            i += 1
        elif l == "\"" and token_type == "CHAR":
            if len(current_token) > 1:
                char_array = []
                for l in current_token:
                    char_array.append(l)
                tokens.append(("ARRAY_CHAR", char_array, (line, column)))
            else:
                tokens.append(("CHAR", current_token, (line, column)))
            current_token = ""
            token_type = ""
            i += 1
        elif l.isdigit() and token_type == "" and current_token == "":
            token_type = "INT"
            current_token += l
            i += 1
        elif not l.isdigit() and token_type == "INT":
            tokens.append((token_type, int(current_token), (line, column)))
            current_token = ""
            token_type = ""
        elif l == "<" and token_type == "":
            tokens, token_type, current_token = cleanUpCurrentToken(tokens, token_type, current_token, line, column)
            token_type = "LESS_THAN"
            i += 1
        elif l == ">" and token_type == "":
            tokens, token_type, current_token = cleanUpCurrentToken(tokens, token_type, current_token, line, column)
            token_type = "MORE_THAN"
            i += 1
        elif l == "!" and token_type == "":
            tokens, token_type, current_token = cleanUpCurrentToken(tokens, token_type, current_token, line, column)
            token_type = "NOT"
            i += 1
        elif l == "=" and token_type == "":
            tokens, token_type, current_token = cleanUpCurrentToken(tokens, token_type, current_token, line, column)
            token_type = "SET_TO"
            i += 1
        elif l == "=" and token_type == "SET_TO":
            tokens.append(("SYNTAX", "EQUAL_TO", (line, column)))
            token_type = ""
            i += 1
        elif l == "=" and token_type == "LESS_THAN":
            tokens.append(("SYNTAX", "LESS_THAN_OR_EQUAL_TO", (line, column)))
            token_type = ""
            i += 1
        elif l == "=" and token_type == "NOT":
            tokens.append(("SYNTAX", "NOT_EQUAL_TO", (line, column)))
            token_type = ""
            i += 1
        elif l == "=" and token_type == "SET_TO":
            tokens.append(("SYNTAX", "MORE_THAN_OR_EQUAL_TO", (line, column)))
            token_type = ""
            i += 1
        elif current_token in KEYWORDS.keys() and not l.isalnum() and l not in "_-":
            tokens.append((KEYWORDS[current_token], current_token,  (line, column)))
            current_token = ""
        elif l not in " \t\r\n" or (l == " " and token_type == "CHAR"): 
            current_token += l
            i += 1
        else:
            tokens, token_type, current_token = cleanUpCurrentToken(tokens, token_type, current_token, line, column)
            i += 1
    tokens, token_type, current_token = cleanUpCurrentToken(tokens, token_type, current_token, line, column)
    if tokens[-1][1] not in ("END_COMMAND", "CLOSE_BRACE"):
        tokens.append(("SYNTAX", "END_COMMAND", (line, column)))
    tokens.append(("", ""))
    return tokens

def cleanUpCurrentToken(tokens, token_type, current_token, line, column):
    if current_token != "":
        if token_type != "":
            if token_type == "INT":
                tokens.append((token_type, int(current_token), (line, column)))
            else:
                tokens.append((token_type, current_token, (line, column)))
            token_type = ""
        else:
            if current_token in KEYWORDS.keys():
                tokens.append((KEYWORDS[current_token], current_token, (line, column)))
            else:
                tokens.append(("UNKNOWN", current_token, (line, column)))
        current_token = ""
    return tokens, token_type, current_token