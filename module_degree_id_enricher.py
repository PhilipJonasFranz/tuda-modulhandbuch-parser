import json
import string
import random

enc = "utf-8"

def replaceUnicodeSequences():
    print("Replacing unicode chars")
    
    lines = []
    with open("./modules_enriched.json", "r", encoding=enc) as f:
        lines = f.readlines()

    special_char_map = [
        ["\\u00fc", "ü"],
        ["\\u00dc", "Ü"],
        ["\\u00e4", "ä"],
        ["\\u00c4", "Ä"],
        ["\\u00f6", "ö"],
        ["\\u00d6", "Ö"],
        ["\\u00df", "ß"],
        ["\\u00a7", "§"],
        [" \\uf0b7", ""],
        ["\\uf0b7", ""],
        ["\\ufffeund", "- und"],
        ["\\ufffe", "-"],
        ["\\u201c", "'"],
        ["\\u201d", "'"],
        ["\\u201e", "'"],
        ["\\u2019", "'"],
        ["\\u2018", "'"],
        ["\\u2010", "-"],
        ["\\u2013", "-"],
        [" \\u2014 ", " - "],
        ["\\u2014", " - "],
        ["\\u25a0 ", ", "],
        ["\\u2026", "..."],
        ["\\u02dc", "~"],
        ["data\": \", ", "data\": \""],
        ["---", "-"]
    ]

    for i in range(0, len(lines)):
        line = lines[i]

        for a in range(0, len(special_char_map)):
            line = line.replace(special_char_map[a][0], special_char_map[a][1])

        if (i == len(lines) - 2):
            line = line[:-2]

        lines[i] = line

    with open("./modules_enriched.json", "w", encoding=enc) as f:
        f.writelines(lines)

module_data = None
degree_data = None

with open("./modules.json", "r", encoding=enc) as f:
    module_data = json.loads(f.read())

with open("./degrees.json", "r", encoding=enc) as f:
    degree_data = json.loads(f.read())["degrees"]

missing_degrees = []

for i in range(0, len(module_data)):
    useable_for_degree = module_data[i]["module"]["useable_for_degree"]
    located_degrees = []
    if (useable_for_degree[0]["type"] == "list"):
        degree_list = useable_for_degree[0]["data"].copy()
        for a in range(0, len(degree_list)):
            degree = degree_list[a]
            located = False
            for j in range(0, len(degree_data)):
                if degree_data[j]["title"] == degree:
                    located_degrees.append({ "did" : degree_data[j]["_id"] })
                    useable_for_degree[0]["data"].remove(degree)
                    located = True
                    break
            if located:
                a = a - 1
            else:
                if degree not in missing_degrees:
                    missing_degrees.append(degree)

    if len(useable_for_degree[0]["data"]) == 0:
        module_data[i]["module"]["useable_for_degree"].pop(0)

    module_data[i]["module"]["useable_for_degree"] = located_degrees + module_data[i]["module"]["useable_for_degree"]

if len(missing_degrees) > 0:
    print("Missing degrees:")
    for degree in missing_degrees:
        print(degree)

with open("./modules_enriched.json", "w", encoding=enc) as f:
    f.write(json.dumps(module_data))

replaceUnicodeSequences()