import json
import string
import random

enc = "utf-8"

existing_ids = []

def unique_id(size):
    chars = list(set(string.ascii_uppercase + string.ascii_lowercase + string.digits))
    while True:
        uid = ''.join(random.choices(chars, k=size))
        if uid not in existing_ids:
            existing_ids.append(uid)
            return uid

json_data = None

with open("./degrees.json", "r", encoding=enc) as f:
    json_data = json.loads(f.read())["degrees"]

for i in range(0, len(json_data)):
    module = json_data[i]

    id = module["_id"]
    existing_ids.append(id)

print(unique_id(28))