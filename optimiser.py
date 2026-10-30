def optimiseInstructions(instructions):
    current_pass = []
    next_pass = optimisePass(instructions)
    while current_pass != next_pass:
        current_pass = next_pass
        next_pass = optimisePass(current_pass)
    return current_pass

def optimisePass(instructions):
    optimised = []
    i = 0
    while i < len(instructions):
        if i == len(instructions)-1:
            optimised.append(instructions[i])
            i += 1
            continue
        current_inst = instructions[i].replace(";", "").split(" ")
        next_inst = instructions[i+1].replace(";", "").split(" ")
        if current_inst[0] == "push" and next_inst[0] == "pop":
            fromReg = current_inst[1]
            toReg = next_inst[1]
            if fromReg != toReg:
                optimised.append(f"cpy {toReg} {fromReg};")
            i += 2
        elif current_inst[0] == "ldfr" and next_inst[0] == "cpy":
            if current_inst[1] == next_inst[2]:
                optimised.append(f"{current_inst[0]} {next_inst[1]} {current_inst[2]} {current_inst[3]};")
            else:
                optimised.extend([instructions[i], instructions[i+1]])
            i += 2
        else:
            optimised.append(instructions[i])
            i += 1
    return optimised