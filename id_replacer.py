import json
import string
import random

enc = "utf-8"

existing_ids = []

def replaceUnicodeSequences():
    print("Replacing unicode chars")
    
    lines = []
    with open("./tutorme/modules.json", "r", encoding=enc) as f:
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

    with open("./tutorme/modules.json", "w", encoding=enc) as f:
        f.writelines(lines)

def unique_id(size):
    chars = list(set(string.ascii_uppercase + string.ascii_lowercase + string.digits))
    while True:
        uid = ''.join(random.choices(chars, k=size))
        if uid not in existing_ids:
            existing_ids.append(uid)
            return uid

json_data = None

with open("./tutorme/modules.json", "r", encoding=enc) as f:
    json_data = json.loads(f.read())

for i in range(0, len(json_data)):
    module = json_data[i]

    old_id = module["_id"]
    new_id = unique_id(28)

    module["_id"] = new_id

    for a in range(0, len(json_data)):
        mod = json_data[a]
        requirements = mod["module"]["requirements"]
        for j in range(0, len(requirements)):
            req = requirements[j]
            if req.get("id", None) != None and req["id"] == old_id:
                req["id"] = new_id
        json_data[a] = mod

    json_data[i] = module

with open("./tutorme/modules.json", "w", encoding=enc) as f:
    f.write(json.dumps(json_data))

replaceUnicodeSequences()