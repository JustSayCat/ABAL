from token_maker import tokeniser
from ast_maker import parse
from interpretor import interpretAST
from compiler import compileAST
from optimiser import optimiseInstructions
from labeler import resolveLabels

DEBUG = True
COMPILE = True
contents = ""
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
if COMPILE:
    instructions = compileAST(nodes)
    optimised = optimiseInstructions(instructions)
    labelled = resolveLabels(optimised)
    for i in range(len(labelled)):
        if i < len(labelled)-1:
            labelled[i] += "\n"
    with open("main.bbcasm", "w") as file:
        file.write(''.join(labelled))
else:
    interpretAST(nodes)