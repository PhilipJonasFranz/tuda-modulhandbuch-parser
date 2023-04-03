import pypdfium2 as pdfium
import json
import re

def extract_section(lines, i, seperator):
    i += 1
    contents = ""
    while i < len(lines) and not lines [i].startswith(seperator):
        line = lines [i]
        contents += line
        i += 1

    return contents, i


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

# List of all parsed modules
modules = []

# Current modules that is being parsed
module = {}

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

print("Parsed", len(modules), "modules")

with open("./output/output.json", "w+", encoding="utf-8") as f:
    f.write(json.dumps(modules))