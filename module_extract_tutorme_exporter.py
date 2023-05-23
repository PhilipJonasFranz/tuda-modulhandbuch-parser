import pypdfium2 as pdfium
import json

import random
import string
import time
import hashlib
import re
import os

enc = "utf-8"

IDs = []

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

def generateID(n):
    while True:
        id = ''.join(random.choices(string.ascii_lowercase, k=n))
        if not id in IDs:
            IDs.append(id)
            return id


def generateHashFromURI(uri):
    hash = hashlib.md5(uri.encode(enc))
    return hash.hexdigest().encode(enc)

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
    with open("./tutorme/modules.json", "w+", encoding=enc) as f:
        f.write("[")

def finalizeDB():
    with open("./tutorme/modules.json", "a", encoding=enc) as f:
        f.write("]")


def emitHeader(name):
    header = {}
    header["type"] = "header"
    header["data"] = name

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
            headers.append(emitList(items))
        elif (re.match(r'^[0-9]+\.', line)):
            if len(buffer) > 0:
                headers.append(emitParagraph(buffer))
                buffer = ""

            items, i = parseNumberedList(split, i)
            headers.append(emitList(items))
        else:
            buffer += line
            i += 1

    if len(buffer) > 0:
        headers.append(emitParagraph(buffer))

    return headers


def emitParagraph(text):
    header = {}
    header["type"] = "paragraph"
    header["data"] = text

    return header


def emitList(items):
    header = {}
    header["type"] = "list"
    header["data"] = items

    return header

def emitPage(module, blocks):
    page = None

    with open("./tutorme/modules.json", "a", encoding=enc) as f:
        id = generateID(16)
        uri = module["Modulname"].lower().replace(" ", "-").replace("—", "-").replace("–", "-").replace(":", "").replace(";", "").replace("ä", "-").replace("ö", "-").replace("ü", "-").replace(",", "")

        page = {}
        page["_id"] = id
        page["title"] = module["Modulname"]
        page["uri"] = uri
        page["course"] = module["course"]
        page["tutors"] = []
        page["module"] = blocks

        f.write(json.dumps(page) + ",\n")

    return page


def formatURL(url, text):
    return "<a href=\"" + url + "\">" + text + "</a>"


def extract_useable_in_degrees(verwendbarkeit: str):
    extract = []

    original = verwendbarkeit

    keys = [
        # B.Sc. Informatik
        {"key": "B,Sc. Informatik", "values": ["B.Sc. Informatik"]},
        {"key": "BSc. Informatik", "values": ["B.Sc. Informatik"]},
        {"key": "B. Sc. Informatik", "values": ["B.Sc. Informatik"]},
        {"key": "B.Sc. Informatik", "values": ["B.Sc. Informatik"]},
        {"key": "B. Sc. Informatjk", "values": ["B.Sc. Informatik"]},
        {"key": "BSc Informatik", "values": ["B.Sc. Informatik"]},
        
        # M.Sc. Informatik
        {"key": "M. Sc. Informatik", "values": ["M.Sc. Informatik"]},
        {"key": "M.Sc. Informatik", "values": ["M.Sc. Informatik"]},
        {"key": "M.Sc Informatik", "values": ["M.Sc. Informatik"]},
        
        # Informatik Master Studiengänge
        {"key": "M. Sc. IT Sicherheit", "values": ["M.Sc. IT Sicherheit"]},
        {"key": "M. Sc. Autonome Systeme", "values": ["M.Sc. Autonome Systeme"]},
        {"key": "M. Sc. Distributed Software Systems", "values": ["M.Sc Verteilte Systeme"]},
        {"key": "M. Sc. Internet- und Web-basierte Systeme", "values": ["M.Sc. Internet- und Web-basierte Systeme"]},
        {"key": "M. Sc. Computational Engineering", "values": ["M.Sc. Computational Engineering"]},
        {"key": "M. Sc. Visual Computing", "values": ["M.Sc. Visual Computing"]},
        
        {"key": "B. Sc. Informationssystemtechnik", "values": ["B.Sc. Informationssystemtechnik"]},
        {"key": "BSc iST", "values": ["B.Sc. Informationssystemtechnik"]},
        {"key": "BSc/MSc iST", "values": ["B.Sc. Informationssystemtechnik", "M.Sc. Informationssystemtechnik"]},
        {"key": "MSc iST", "values": ["M.Sc. Informationssystemtechnik"]},
        {"key": "M. Sc. Informationssystemtechnik", "values": ["M.Sc. Informationssystemtechnik"]},

        {"key": "B. Sc. Wirtschaftsinformatik", "values": ["B.Sc. Wirtschaftsinformatik"]},
        {"key": "B.Sc./M.Sc. Wirtschaftsinformatik", "values": ["B.Sc. Wirtschaftsinformatik", "M.Sc. Wirtschaftsinformatik"]},
        {"key": "M. Sc. Wirtschaftsinformatik", "values": ["M.Sc. Wirtschaftsinformatik"]},
        {"key": "M.Sc. Wirtschaftsinformatik", "values": ["M.Sc. Wirtschaftsinformatik"]},
        
        {"key": "BSc CS", "values": ["B.Sc. Computer Science"]},
        {"key": "BSc/MSc CS", "values": ["B.Sc. Computer Science", "M.Sc. Computer Science"]},
        {"key": "MSc CS", "values": ["M.Sc. Computer Science"]},

        {"key": "B. Sc. Computational Engineering", "values": ["B.Sc. Computational Engineering"]},
        
        {"key": "MSc iCE", "values": ["M.Sc. Information and Communication Engineering"]},
        
        {"key": "BSc ETiT", "values": ["B.Sc. Elektrotechnik und Informationstechnik"]},
        {"key": "MSc ETiT", "values": ["M.Sc. Elektrotechnik und Informationstechnik"]},
        
        {"key": "MSc MEC", "values": ["M.Sc. Mechatronik"]},

        {"key": "MSc Wi-ETiT", "values": ["M.Sc. Wirtschaftsingenieurwesen — Fachrichtung Elektrotechnik und Informationstechnik"]},
        {"key": "Wi-ETiT", "values": ["M.Sc. Wirtschaftsingenieurwesen — Fachrichtung Elektrotechnik und Informationstechnik"]},
        {"key": "MSc Wi-CS", "values": ["M.Sc. Wirtschaftsingenieurwesen — Fachrichtung Computer Science"]},
        {"key": "Wi-CS", "values": ["M.Sc. Wirtschaftsingenieurwesen — Fachrichtung Computer Science"]},
        {"key": "WiCS", "values": ["M.Sc. Wirtschaftsingenieurwesen — Fachrichtung Computer Science"]},

        {"key": "ETiT", "values": ["B.Sc. Elektrotechnik und Informationstechnik", "M.Sc. Elektrotechnik und Informationstechnik"]},
        
        {"key": "CS", "values": ["B.Sc. Computer Science", "M.Sc. Computer Science"]},
        
        {"key": "B. Sc. Sportwissenschaft und Informatik", "values": ["B.Sc. Sportwissenschaft und Informatik"]},
        {"key": "B.Sc./M.Sc. Sportwissenschaft und Informatik", "values": ["B.Sc. Sportwissenschaft und Informatik", "M.Sc. Sportwissenschaft und Informatik"]},
        {"key": "B.Sc. Sportwissenschaft und Informatik", "values": ["B.Sc. Sportwissenschaft und Informatik"]},
        {"key": "M. Sc. Sportwissenschaft und Informatik", "values": ["M.Sc. Sportwissenschaft und Informatik"]},
        
        {"key": "B. Sc. Psychologie in IT", "values": ["B.Sc. Psychologie in IT"]},
        {"key": "B.Sc. Psychologie in IT", "values": ["B.Sc. Psychologie in IT"]},
        {"key": "M. Sc. Psychologie in IT", "values": ["M.Sc. Psychologie in IT"]},
        
        {"key": "Joint B.A. Informatik", "values": ["Joint B.A. Informatik"]},
    ]

    for i in range(0, len(keys)):
        if (keys[i]["key"] in verwendbarkeit):
            for a in range(0, len(keys[i]["values"])):
                extract.append(keys[i]["values"][a])
            verwendbarkeit = verwendbarkeit.replace(keys[i]["key"], "")

    blocks = [ emitList(extract) ]

    other = [
        {"key": "Kann in anderen Studiengängen verwendet werden.", "values": ["Kann in anderen Studiengängen verwendet werden."]},
        {"key": "Kann im Rahmen fachübergreifender Angebote auch in anderen Studiengängen verwendet werden.", "values": ["Kann im Rahmen fachübergreifender Angebote auch in anderen Studiengängen verwendet werden."]},
        {"key": "Kann im Rahmen fachübergreifender Angebote auch in anderenStudiengängen verwendet werden.", "values": ["Kann im Rahmen fachübergreifender Angebote auch in anderen Studiengängen verwendet werden."]},
        {"key": "Im Rahmen fachübergreifender Angebote auch in anderen Studiengängen.", "values": ["Kann im Rahmen fachübergreifender Angebote auch in anderen Studiengängen verwendet werden."]},
        {"key": "Kann in anderen Srudiengängen verwendet werden.", "values": ["Kann in anderen Srudiengängen verwendet werden."]},
        {"key": "Pflichtveranstaltung in Informatik-StudiengängenBestandteil des BSc-Mathematikmoduls „Formale Grundlagen der Informatik“", "values": ["Pflichtveranstaltung in Informatik-Studiengängen. Bestandteil des B.Sc.-Mathematikmoduls 'Formale Grundlagen der Informatik'."]},
        {"key": "Pflichtveranstaltung in Informatikstudiengängen Bestandteil des BSc-Mathematikmoduls „Formale Grundlagen der Informatik“", "values": ["Pflichtveranstaltung in Informatik-Studiengängen. Bestandteil des B.Sc.-Mathematikmoduls 'Formale Grundlagen der Informatik'."]},
        {"key": "Pflichtveranstaltung in Informatikstudiengängen", "values": ["Pflichtveranstaltung in Informatikstudiengängen."]},
        
    ]

    for i in range(0, len(other)):
        if (other[i]["key"] in verwendbarkeit):
            for a in range(0, len(other[i]["values"])):
                blocks.append(emitParagraph(other[i]["values"][a]))
            verwendbarkeit = verwendbarkeit.replace(other[i]["key"], "")

    if "Informatik" in verwendbarkeit:
        blocks.insert(0, emitParagraph("B.Sc. Informatik"))
        blocks.insert(1, emitParagraph("M.Sc. Informatik"))
        verwendbarkeit = verwendbarkeit.replace("Informatik", "")

    verwendbarkeit = verwendbarkeit.replace(",", "")

    if len(verwendbarkeit.replace(" ", "")) > 0:
        print("Original: " + original)
        print("Remainder: " + verwendbarkeit)

    return blocks


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
        kurs["cp"] = int(str(module["Kreditpunkte"])[:-3])
        sws = str(module["Arbeitsaufwand"])[:-2]
        kurs["sws"] = int(sws if len(sws) > 0 else "0")
        self_study = str(module["Selbststudium"])[:-2]
        kurs["self_study"] = int(self_study if len(self_study) > 0 else "0")
        kurs["id"] = module["Modul Nr."]
        kurs["organizer"] = module["Modulverantwortliche Person"]
        kurs["turnus"] = module.get("Angebotsturnus", "Jedes Semster")

        languages = []
        if "Deutsch" in module["Sprache"]:
            languages.append("de")
        if "Englisch" in module["Sprache"]:
            languages.append("en")
            
        kurs["language"] = languages

        module["course"] = kurs

        # Translate into Codex DB Format
        blocks = {}

        blocks["content"] = emitFormattedText(lerninhalt, "$")
        blocks["qualifications"] = emitFormattedText(ziele, "$")
        blocks["requirements"] = emitFormattedText(voraussetzungen, "$")
        blocks["exam"] = emitFormattedText(exam, "$")
        blocks["pass_requirement"] = emitFormattedText(pass_requirement, "$")
        blocks["grading"] = emitFormattedText(grading, "$")
        blocks["useable_for_degree"] = extract_useable_in_degrees(verwendbarkeit)
        blocks["literature"] = emitFormattedText(literatur, "$")
        blocks["comment"] = emitFormattedText(kommentar, "$")

        kurs["examination_type"] = ("Fachprüfung, Studienleistung" if ("Studienleistung" in exam) else "Fachprüfung") if ("Fachprüfung" in exam) else "Studienleistung"

        page = emitPage(module, blocks)

finalizeDB()

replaceUnicodeSequences()

print("Parsed", len(pages), "modules")