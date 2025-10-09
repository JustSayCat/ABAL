from token_maker import tokeniser
from ast_maker import parse
from interpretor import interpretAST

DEBUG = True

with open("main.abal", "r") as file:
    contents = file.read()
    tokens = tokeniser(contents)
    if DEBUG:
        print("-----TOKENS-------")
        for token in tokens:
            print(token)
        print()
    nodes = parse(tokens)
    if DEBUG:
        print("-----NODES-------")
        for node in nodes:
            print(node)
        print()
    interpretAST(nodes)