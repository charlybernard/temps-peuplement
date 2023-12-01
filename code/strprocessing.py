import re
from rdflib import Graph, RDFS, Literal, URIRef

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

def simplify_french_street_name(street_name:str):
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
    normalized_name = simplify_french_street_name(normalized_name)

    return normalized_name

def get_lower_simplified_french_street_name_function(variable):
    replacements = [["([- ]de[- ]la[- ]|[- ]de[- ]|[- ]des[- ]|[- ]du[- ]|[- ]le[- ]|[- ]la[- ]|[- ]les[- ]|[- ]aux[- ]|[- ]au[- ]|[- ]à[- ]|[- ]en[- ]|/|-|\.)", " "],
                ["(l'|d')", ""],
                ["[àâ]", "a"], 
                ["[éèêë]", "e"], 
                ["[îíìï]", "i"], 
                ["[ôö]", "o"], 
                ["[ûüù]", "u"], 
                ["[ÿŷ]", "y"],
                ["[ç]", "c"], 
                ]
    
    lc_variable = f"LCASE({variable})"
    return get_remplacement_sparql_function(lc_variable, replacements)

def get_remplacement_sparql_function(string, replacements):
    # arg, pattern, replacement = string, first_repl[0], first_repl[1]
    # function_str = f"REPLACE({arg}, {pattern}, {replacement})"
    function_str = string
    for repl in replacements:
        arg, pattern, replacement = function_str, repl[0], repl[1]
        pattern = pattern.replace('\\', '\\\\')
        function_str = f"REPLACE({arg}, \"{pattern}\", \"{replacement}\")"

    return function_str

def normalize_street_rdfs_labels_in_graph_file(graph_file:str):
    # Normalisation de noms de voies
    g = Graph()
    g.parse(graph_file)
    triples_to_remove = []
    triples_to_add = []
    for s, p, o in g:
        if p == RDFS.label and isinstance(o, Literal) and o.language == "fr":
            new_o_value = normalize_french_street_name(o.value)
            new_o = Literal(new_o_value, lang="fr")
            triples_to_remove.append((s,p,o))
            triples_to_add.append((s, p, new_o))

    for triple in triples_to_remove:
        g.remove(triple)
    for triple in triples_to_add:
        g.add(triple)

    g.serialize(graph_file)

def define_time_filter_for_sparql_query(val_tRef:str, cal_tRef:str, val_t1:str, cal_t1:str, val_t2:str, cal_t2:str, time_precision:URIRef="day"):
    """
    Création d'un filtre temporel pour les requêtes afin de sélectionner des données valables à l'instant `tRef` telles que t2 <= tRef <= t1
    val_tX sont des variables de la requête liées aux timestamps (`?t1Value`, `?t2Value`...)
    cal_tX sont des variables de la requête liées aux calendriers (`?t1Calendar`, `?t2Calendar`...)

    `time_precision` peut prendre les valeurs suivantes : 
    * `URIRef("http://www.w3.org/2006/time#unitYear")` ;
    * `URIRef("http://www.w3.org/2006/time#unitMonth")` ;
    * `URIRef("http://www.w3.org/2006/time#unitDay")`.
    """
    
    t1_get_t2 = "{t1} >= {t2}"
    t1_let_t2 = "{t1} <= {t2}"
    # t1_gt_t2 = "{t1} > {t2}"
    # t1_lt_t2 = "{t1} < {t2}"
    # t1_eq_t2 = "{t1} = {t2}"
    t_not_exists = "!BOUND({t})"
    or_op = "||"
    and_op = "&&"

    t1_get_t2_year = t1_get_t2.format(t1="YEAR({t1})", t2="YEAR({t2})")
    t1_get_t2_month = t1_get_t2.format(t1="MONTH({t1})",t2="MONTH({t2})")
    t1_get_t2_year_month = f"{t1_get_t2_year} {and_op} {t1_get_t2_month}"

    t1_let_t2_year = t1_let_t2.format(t1="YEAR({t1})", t2="YEAR({t2})")
    t1_let_t2_month = t1_let_t2.format(t1="MONTH({t1})", t2="MONTH({t2})")
    t1_let_t2_year_month = f"{t1_let_t2_year} {and_op} {t1_let_t2_month}"

    if time_precision == URIRef("http://www.w3.org/2006/time#unitYear"):
        t1_get_tRef_comp = t1_get_t2_year
        t2_let_tRef_comp = t1_let_t2_year
    elif time_precision == URIRef("http://www.w3.org/2006/time#unitMonth"):
        t1_get_tRef_comp = t1_get_t2_year_month
        t2_let_tRef_comp = t1_let_t2_year_month
    else:
        t1_get_tRef_comp = t1_get_t2
        t2_let_tRef_comp = t1_let_t2

    t1_get_tRef_val = t1_get_tRef_comp.format(t1=val_t1, t2=val_tRef)
    t2_let_tRef_val = t2_let_tRef_comp.format(t1=val_t2, t2=val_tRef)
    t1_not_exists_val = t_not_exists.format(t=val_t1)
    t2_not_exists_val = t_not_exists.format(t=val_t2)
    cal_t1_not_exists_val = t_not_exists.format(t=cal_t1)
    cal_t2_not_exists_val = t_not_exists.format(t=cal_t2)

    calendar_time_filter = f"""(
        (({cal_t1} = {cal_tRef}) {and_op} ({cal_t2} = {cal_tRef})) {or_op}
        (({cal_t1} = {cal_tRef}) {and_op} ({cal_t2_not_exists_val})) {or_op}
        (({cal_t2} = {cal_tRef}) {and_op} ({cal_t1_not_exists_val})) {or_op}
        ({cal_t1_not_exists_val} {and_op} {cal_t2_not_exists_val})
        )"""

    value_time_filter = f"""(
        ({t1_get_tRef_val} {and_op} {t2_let_tRef_val}) {or_op}
        ({t1_get_tRef_val} {and_op} {t2_not_exists_val}) {or_op}
        ({t2_let_tRef_val} {and_op} {t1_not_exists_val}) {or_op}
        ({t1_not_exists_val} {and_op} {t2_not_exists_val})
        )
    """

    time_filter = f"""FILTER({value_time_filter} {and_op} {calendar_time_filter})"""
    return time_filter