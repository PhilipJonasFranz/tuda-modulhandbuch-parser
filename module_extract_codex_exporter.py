import pypdfium2 as pdfium
import json

import random
import string
import time

IDs = []

def generateID(n):
    while True:
        id = ''.join(random.choices(string.ascii_lowercase, k=n))
        if not id in IDs:
            IDs.append(id)
            return id

def extract_section(lines, i, seperator):
    i += 1
    contents = ""
    while i < len(lines) and not lines [i].startswith(seperator):
        line = lines [i]
        contents += line
        i += 1

    return contents, i


def emitHeader(name):
    data = {}
    data["text"] = name
    data["level"] = 2

    header = {}
    header["id"] = generateID(11)
    header["type"] = "header"
    header["data"] = data

    return header


def emitParagraph(text):
    data = {}
    data["text"] = text

    header = {}
    header["id"] = generateID(11)
    header["type"] = "paragraph"
    header["data"] = data

    return header


def emitList(style, items):
    data = {}
    data["style"] = style # unordered, ordered
    data["items"] = items

    header = {}
    header["id"] = generateID(11)
    header["type"] = "list"
    header["data"] = data

    return header


pdf = pdfium.PdfDocument("./MHB_BSC_MSC_Informatik.pdf")

n_pages = len(pdf)  # get the number of pages in the document
print("Read", n_pages, "pages from file")

# Extract all Textlines, split them and collect them in a list
lines = []
for i in range(0, n_pages):
    page = pdf[i]

    width, height = page.get_size()

    # Load a text page helper
    textpage = page.get_textpage()

    # Extract text from the whole page
    text_all = textpage.get_text_range()
    lines += text_all.splitlines()

print("Extracted", len(lines), "lines of text")

# List of all parsed modules
modules = []

# Current modules that is being parsed
module = {}

with open("./output/pages.db", "w+", encoding="utf-8") as f:
    f.write("")

# Traverse the list and attempt to extract module data by keywords
for i in range(0, len(lines)):
    line = lines [i]

    # Start of new Modul Definition
    if line.startswith("Modulbeschreibung"):
        if len(module) > 0:
            modules.append(module)
        module = {}

    if line.startswith("Modulname"):
        module["Modulname"] = lines [i + 1]
        i += 1

    if line.startswith("Modul Nr."):
        module["Modul Nr."] = lines [i + 1]
        i += 1

    if line.startswith("Kreditpunkte"):
        module["Kreditpunkte"] = lines [i + 1]
        i += 1

    if line.startswith("Arbeitsaufwand"):
        module["Arbeitsaufwand"] = lines [i + 1]
        i += 1

    if line.startswith("Selbststudium"):
        module["Selbststudium"] = lines [i + 1]
        i += 1

    if line.startswith("Moduldauer"):
        module["Moduldauer"] = lines [i + 1]
        i += 1

    if line.startswith("Angebotsturnus"):
        module["Angebotsturnus"] = lines [i + 1]
        i += 1

    if line.startswith("Sprache"):
        module["Sprache"] = lines [i + 1]
        i += 1

    if line.startswith("Modulverantwortliche Person"):
        module["Modulverantwortliche Person"] = lines [i + 1]
        i += 1

    if line.startswith("1 Kurse des Moduls"):
        kurse, i = extract_section(lines, i, "2 Lerninhalt")
        lerninhalt, i = extract_section(lines, i, "3 Qualifikationsziele / Lernergebnisse")
        ziele, i = extract_section(lines, i, "4 Voraussetzung für die Teilnahme")
        voraussetzungen, i = extract_section(lines, i, "5 Prüfungsform")
        exam, i = extract_section(lines, i, "6 Voraussetzung für die Vergabe von Kreditpunkten")
        pass_requirement, i = extract_section(lines, i, "7 Benotung")
        grading, i = extract_section(lines, i, "8 Verwendbarkeit des Moduls")
        verwendbarkeit, i = extract_section(lines, i, "9 Literatur")
        literatur, i = extract_section(lines, i, "10 Kommentar")
        kommentar, i = extract_section(lines, i, "Modulbeschreibung")
        
        kurs = {}

        kurs["Kurse_des_Moduls"] = kurse
        kurs["Lerninhalt"] = lerninhalt
        kurs["Qualifikationsziele_Lernergebnisse"] = ziele
        kurs["Voraussetzung_fuer_die_Teilnahme"] = voraussetzungen
        kurs["Pruefungsform"] = exam
        kurs["Voraussetzung_fuer_die_Vergabe_von_Kreditpunkten"] = voraussetzungen
        kurs["Benotung"] = grading
        kurs["Verwendbarkeit_des_Moduls"] = verwendbarkeit
        kurs["Literatur"] = literatur
        kurs["Kommentar"] = kommentar

        module["kurs"] = kurs

        id = generateID(17)
        uri = module["Modulname"].lower().replace(" ", "-")

        # Translate into Codex DB Format
        blocks = []

        blocks.append(emitHeader(module["Modulname"]))
        blocks.append(emitList("unordered", ["Modul Nr.: " + module["Modul Nr."]]))

        body = {}
        body["time"] = int(time.time())
        body["blocks"] = blocks

        entry = {}
        entry["_id"] = id
        entry["title"] = module["Modulname"]
        entry["uri"] = uri
        entry["body"] = body

        with open("./output/pages.db", "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

print("Parsed", len(modules), "modules")