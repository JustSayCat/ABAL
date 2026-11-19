import argparse
from token_maker import tokeniser
from ast_maker import parse
from interpretor import interpretAST
from compiler import compileAST
from optimiser import optimiseInstructions
from labeler import resolveLabels

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("infile")
    parser.add_argument("outfile")
    parser.add_argument("-debug", "-d", action="store_true")
    parser.add_argument("-compile", "-c", action="store_true")
    parser.add_argument("-asmcomments", "-ac", action="store_true")
    args = parser.parse_args()
    DEBUG = args.debug
    COMPILE = args.compile
    OUTPUT_COMMENTS = args.asmcomments
    contents = ""
    with open(args.infile, "r") as file:
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
        if DEBUG:
            print(instructions)
        optimised = optimiseInstructions(instructions)
        labelled = []
        if OUTPUT_COMMENTS:
            labelled = resolveLabels(instructions)
        else:
            labelled = resolveLabels(optimised)
        for i in range(len(labelled)):
            if i < len(labelled)-1:
                labelled[i] += "\n"
        with open(args.outfile, "w") as file:
            file.write(''.join(labelled))
    else:
        interpretAST(nodes)