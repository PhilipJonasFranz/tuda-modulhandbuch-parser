import pypdfium2 as pdfium
import json

import random
import string
import time
import hashlib
import re

enc = "utf-8"

IDs = []

def generateID(n):
    while True:
        id = ''.join(random.choices(string.ascii_lowercase, k=n))
        if not id in IDs:
            IDs.append(id)
            return id


def generateHashFromURI(uri):
    hash = hashlib.md5(uri.encode("latin-1"))

    bytes = hash.digest()

    out_bytes = []
    for i in range(0, len(bytes)):
        if bytes [i] == 0x22:
            out_bytes.append(0x5c)
            out_bytes.append(bytes [i])
        elif bytes [i] == 0x09:
            out_bytes.append(0x5c)
            out_bytes.append(0x74)
        elif bytes [i] == 0x0c:
            out_bytes.append(0x5c)
            out_bytes.append(0x66)
        elif bytes [i] >= 0xc0 and bytes [i] <= 0xc5:
            out_bytes.append(bytes [i])
        elif bytes [i] <= 0x20 or (bytes [i] >= 0x80 and bytes [i] <= 0xa0):
            out_bytes.append(0x5c)
            out_bytes.append(0x75)
            out_bytes.append(0x30)
            out_bytes.append(0x30)
            left = bytes [i] >> 4
            if left < 10:
                out_bytes.append(0x30 + left)
            else:
                out_bytes.append(0x61 + left - 10)
            right = bytes [i] & 0xf
            if right < 10:
                out_bytes.append(0x30 + right)
            else:
                out_bytes.append(0x61 + right - 10)
        else:
            converted_bytes = bytearray(chr(bytes [i]).encode('utf-8'))
            out_bytes += converted_bytes

    return out_bytes


def extract_section_list(lines, i, seperator, newline_split):
    i += 1
    contents = ""
    while i < len(lines) and not lines [i].startswith(seperator):
        line = lines [i]
        contents += line + newline_split
        i += 1

    return contents, i


def extract_section(lines, i, seperator):
    return extract_section_list(lines, i, seperator, "")


def initializeDB():
    with open("./data/db/pages.db", "w+", encoding=enc) as f:
        f.write("")
    with open("./data/db/pagesOrder.db", "w+", encoding=enc) as f:
        f.write("")
    with open("./data/db/aliases.db", "w+", encoding=enc) as f:
        f.write("")
    with open("./data/db/files.db", "w+", encoding=enc) as f:
        f.write("")


def emitHeader(name):
    data = {}
    data["text"] = name
    data["level"] = 2

    header = {}
    header["id"] = generateID(10)
    header["type"] = "header"
    header["data"] = data

    return header


def emitParagraph(text):
    data = {}
    data["text"] = text

    header = {}
    header["id"] = generateID(10)
    header["type"] = "paragraph"
    header["data"] = data

    return header


def parseList(lines, i, list_delimeter):
    items = []
    line = lines [i]

    while line.startswith(list_delimeter) and i < len(lines):
        items.append(line[len(list_delimeter):])
        i = i + 1
        if i >= len(lines):
            break
        line = lines [i]

    return items, i


def parseNumberedList(lines, i):
    items = []
    line = lines [i]

    last_index = None

    while re.match(r'^[0-9]+\.', line) and i < len(lines):
        m = re.search(r'^[0-9]+\.', line)
        start, end = m.span()

        index = int(line[:(end - 1)])
        if last_index is None:
            last_index = index
        elif index <= last_index:
            break

        items.append(line[end:])
        i = i + 1
        if i >= len(lines):
            break
        line = lines [i]

    return items, i


def emitFormattedText(text, spliterator):
    split = text.split(spliterator)

    headers = []
    buffer = ""

    i = 0
    while i < len(split):
        line = split [i]
        if (line.startswith("-") or line.startswith("●") or line.startswith("•") or line.startswith("*") or line.startswith("○")):
            if len(buffer) > 0:
                headers.append(emitParagraph(buffer))
                buffer = ""
            items, i = parseList(split, i, line[0])
            headers.append(emitList("unordered", items))
        elif (re.match(r'^[0-9]+\.', line)):
            if len(buffer) > 0:
                headers.append(emitParagraph(buffer))
                buffer = ""

            items, i = parseNumberedList(split, i)
            headers.append(emitList("ordered", items))
        else:
            buffer += line
            i += 1

    if len(buffer) > 0:
        headers.append(emitParagraph(buffer))

    return headers


def emitList(style, items):
    data = {}
    data["style"] = style # unordered, ordered
    data["items"] = items

    header = {}
    header["id"] = generateID(10)
    header["type"] = "list"
    header["data"] = data

    return header


def emitPage(title, blocks):
    page = None

    with open("./data/db/pages.db", "a", encoding=enc) as f:
        id = generateID(16)
        uri = title.lower().replace(" ", "-").replace("—", "-").replace("–", "-").replace(":", "").replace(";", "").replace("ä", "-").replace("ö", "-").replace("ü", "-").replace(",", "")

        body = {}
        body["time"] = int(time.time())
        body["blocks"] = blocks

        page = {}
        page["_id"] = id
        page["title"] = title
        page["uri"] = uri
        page["body"] = body

        f.write(json.dumps(page) + "\n")

    return page


def emitSubPages(parent, children):
    with open("./data/db/pagesOrder.db", "a", encoding=enc) as f:
        subpage = {}
        subpage["_id"] = generateID(16)
        subpage["page"] = "0" if parent is None else parent["_id"]
        subpage["order"] = [page["_id"] for page in children]
        
        f.write(json.dumps(subpage) + "\n")


def emitAlias(page):
    alias = {}
    alias["_id"] = generateID(16)
    alias["id"] = page["_id"]
    alias["type"] = "page"
    alias["hash"] = "$"
    alias["deprecated"] = False

    dump = json.dumps(alias)
    split = dump.split("$")
    
    with open("./data/db/aliases.db", "a", encoding=enc) as f:
        f.write(split [0])

    with open("./data/db/aliases.db", "ab") as f:
        out_bytes = generateHashFromURI(page["uri"])
        f.write(bytearray(out_bytes))

    with open("./data/db/aliases.db", "a", encoding=enc) as f:
        f.write(split [1] + "\n")


def formatURL(url, text):
    return "<a href=\"" + url + "\">" + text + "</a>"


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
    split = text_all.splitlines()

    # Remove strings of the form 'Modulhandbuch B. Sc./M. Sc. Informatik 8', since they are mixed randomly into the strings
    for a in range(0, len(split)):
        line = re.sub(r"Modulhandbuch B\. Sc\.\/M\. Sc\. Informatik [0-9]+", '', split[a])
        if len(line) > 0:
            lines.append(line)


print("Extracted", len(lines), "lines of text")

# List of all parsed pages
pages = []

# Current modules that is being parsed
module = {}
page = None

# Create initial empty files for the DB
initializeDB()

# Generate Home Page
blocks = []
blocks.append(emitHeader("Module"))
blocks.append(emitParagraph("Dieses Projekt bezieht seine Informationen aus dem Modulhandbuch B.Sc./M.Sc. Informatik. Das Skript mit dem die Informationen extrahiert wurden kann hier gefunden werden: " + formatURL("https://github.com/PhilipJonasFranz/tuda-modulhandbuch-parser", "tuda-modulhandbuch-parser")))
blocks.append(emitParagraph("Es wird keine Garantie übernommen das die gezeigten Informationen korrekt sind."))
home = emitPage("Module", blocks)
emitAlias(home)

# Emit Home Page at Root
emitSubPages(None, [home])

# Traverse the list and attempt to extract module data by keywords
for i in range(0, len(lines)):
    line = lines [i]

    # Start of new Modul Definition
    if line.startswith("Modulbeschreibung"):
        if len(module) > 0 and not page is None:
            pages.append(page)
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
        lerninhalt, i = extract_section_list(lines, i, "3 Qualifikationsziele / Lernergebnisse", "$")
        ziele, i = extract_section_list(lines, i, "4 Voraussetzung für die Teilnahme", "$")
        voraussetzungen, i = extract_section_list(lines, i, "5 Prüfungsform", "$")
        exam, i = extract_section(lines, i, "6 Voraussetzung für die Vergabe von Kreditpunkten")
        pass_requirement, i = extract_section(lines, i, "7 Benotung")
        grading, i = extract_section(lines, i, "8 Verwendbarkeit des Moduls")
        verwendbarkeit, i = extract_section(lines, i, "9 Literatur")
        literatur, i = extract_section_list(lines, i, "10 Kommentar", "$")
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

        # Translate into Codex DB Format
        blocks = []
        blocks.append(emitHeader(module["Modulname"]))
        
        blocks.append(emitHeader("Fakten"))
        blocks.append(emitList("unordered", [
            "Modul CP: " + module["Kreditpunkte"], 
            "TuCan Kennung: " + module["Modul Nr."],
            #"Turnus: " + module["Angebotsturnus"],
            "Fachbereich: FB-20",
            "Lehrende: " + module["Modulverantwortliche Person"],
            "Benotung: " + kurs["Benotung"]
        ]))

        blocks.append(emitHeader("Inhalt"))
        blocks.extend(emitFormattedText(kurs["Lerninhalt"], "$"))

        blocks.append(emitHeader("Qualifikationsziele & Lernergebnisse"))
        blocks.extend(emitFormattedText(kurs["Qualifikationsziele_Lernergebnisse"], "$"))
        
        blocks.append(emitHeader("Literatur"))
        blocks.extend(emitFormattedText(kurs["Literatur"], "$"))

        page = emitPage(module["Modulname"], blocks)
        emitAlias(page)

# Create entry for all modules as sub pages of Home page
emitSubPages(home, pages)

print("Parsed", len(pages), "modules")