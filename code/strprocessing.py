import re

def remove_abbreviations_in_french_street_name(street_name:str):
    normalized_name = street_name.lower()
    street_abbre = {"^pl(\.|) ":"place ",
                    "^av(\.|) ":"avenue ",
                    "^(bd|blvd|boul)(\.|) ":"boulevard ",
                    "^r(\.|) ":"rue ",
                    "^rle(\.|) ":"ruelle ",
                    "^rte(\.|) ":"route ",
                    "^pas(\.|) ": "passage ",
                    "^all(\.|) ": "allée ",
                    "^imp(\.|) ": "impasse ",
                    " s(\.|) ":" saint-",
                    " s(ain|)t[- ]":" saint-",
                    " s(ain|)te[- ]":" sainte-",
                    " s(ain|)ts[- ]":" saints-",
                    " s(ain|)tes[- ]":" saintes-",
                    "' ": "'",
                    " {2,}":" ",
                    "\.": ""              
    }

    for abbre, val in street_abbre.items():
        normalized_name = re.sub(abbre, val, normalized_name)

    return normalized_name

def x(street_name:str):
    street_cmplt = ["[- ]d'", "[- ]de[- ]", "[- ]du[- ]", "[- ]des[- ]", "[- ]la[- ]", "[- ]le[- ]", "[- ]l'", "[- ]en[- ]", "[- ]à[- ]", "[- ]aux[- ]", "[- ]au[- ]"]
    normalized_name = street_name.title()
    for cmplt in street_cmplt:
        match_elems = re.findall(f"({cmplt})", normalized_name, flags=re.IGNORECASE)
        for elem in match_elems:
            normalized_name = normalized_name.replace(elem, elem.lower())
    return normalized_name

def normalize_french_street_name(street_name:str):
    normalized_name = street_name
    normalized_name = remove_abbreviations_in_french_street_name(normalized_name)
    normalized_name = x(normalized_name)

    return normalized_name