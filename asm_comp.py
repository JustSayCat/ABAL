from optimiser import optimiseInstructions
from labeler import resolveLabels

instructions = []
with open("hand.bbcasm", "r") as file:
    instructions = file.read().split("\n")

optimised = optimiseInstructions(instructions)
labelled = resolveLabels(optimised)
for i in range(len(labelled)):
    if i < len(labelled)-1:
        labelled[i] += "\n"
with open("main.bbcasm", "w") as file:
    file.write(''.join(labelled))