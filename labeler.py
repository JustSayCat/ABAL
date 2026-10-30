def resolveLabels(instructions):
    origin_offset = 2
    current_instruction = 0
    pre_processed = []
    id_linker = {}
    for inst in instructions:
        if inst[0] == "@":
            id_linker.update({ inst[1:]: current_instruction+origin_offset})
        else:
            pre_processed.append(inst)
            current_instruction += 1
    output = []
    for inst in pre_processed:
        if "#" in inst:
            main, link = inst.split("#")
            link = link.replace(";", "")
            output.append(main+str(id_linker[link])+";")
        else:
            output.append(inst)
    return output