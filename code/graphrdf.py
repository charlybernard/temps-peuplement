from rdflib import Graph
from rdflib.namespace import RDF, RDFS, SKOS, NamespaceManager
from rdflib import Graph, Namespace, URIRef, Literal, BNode
from rdflib.namespace import CSVW, DC, DCAT, DCTERMS, DOAP, FOAF, ODRL2, ORG, OWL, \
                           PROF, PROV, RDF, RDFS, SDO, SH, SKOS, SOSA, SSN, TIME, \
                           VOID, XSD
from uuid import uuid4


def create_landmark(landmark_uri:URIRef, label:str, lang:str, landmark_type:str, g:Graph, namespace:Namespace):
    g.add((landmark_uri, RDF.type, namespace["Landmark"]))
    g.add((landmark_uri, namespace["isLandmarkType"], namespace[landmark_type]))
    g.add((landmark_uri, RDFS.label, Literal(label, lang=lang)))

def create_event(event_uri:URIRef, g:Graph, namespace:Namespace):
    g.add((event_uri, RDF.type, namespace["Event"]))

def create_change(change_uri:URIRef, change_type:str, g:Graph, namespace:Namespace, change_class="Change"):
    g.add((change_uri, RDF.type, namespace[change_class]))
    if change_type is not None:
        g.add((change_uri, namespace["isChangeType"], namespace[change_type]))

def create_change_event_relation(change_uri:URIRef, event_uri:URIRef, g:Graph, namespace:Namespace):
    g.add((change_uri, namespace["dependsOn"], event_uri))

def create_attribute_change(change_uri:URIRef, attribute_uri:URIRef, g:Graph, namespace:Namespace):
    create_change(change_uri, None, g, namespace, change_class="AttributeChange")
    g.add((change_uri, namespace["appliedTo"], attribute_uri))

def create_landmark_change(change_uri:URIRef, change_type:str, landmark_uri:URIRef, g:Graph, namespace:Namespace):
    create_change(change_uri, change_type, g, namespace, change_class="LandmarkChange")
    g.add((change_uri, namespace["appliedTo"], landmark_uri))

def create_landmark_with_changes(landmark_uri:URIRef, label:str, lang:str, landmark_type:str, g:Graph, namespace:Namespace):
    create_landmark(landmark_uri, label, lang, landmark_type, g, namespace)
    creation_change_uri, creation_event_uri = generate_uri(namespace, "CH"), generate_uri(namespace, "EV")
    dissolution_change_uri, dissolution_event_uri = generate_uri(namespace, "CH"), generate_uri(namespace, "EV")

    create_landmark_change(creation_change_uri, "Creation", landmark_uri, g, namespace)
    create_landmark_change(dissolution_change_uri, "Dissolution", landmark_uri, g, namespace)
    create_event(creation_event_uri, g, namespace)
    create_event(dissolution_event_uri, g, namespace)
    create_change_event_relation(creation_change_uri, creation_event_uri, g, namespace)
    create_change_event_relation(dissolution_change_uri, dissolution_event_uri, g, namespace)

def create_landmark_attribute(attribute_uri:URIRef, landmark_uri:URIRef, attribute_type:str, g:Graph, namespace:Namespace):
    g.add((attribute_uri, RDF.type, namespace["Attribute"]))
    g.add((attribute_uri, namespace["isAttributeType"], namespace[attribute_type]))
    g.add((landmark_uri, namespace["hasAttribute"], attribute_uri))

def create_attribute_version(attribute_uri:URIRef, value:str, g:Graph, namespace:Namespace, lang:str=None, datatype:URIRef=None, change_before_uri=None, change_after_uri=None):
    attr_vers_uri = generate_uri(namespace, "AV")
    attr_vers_lit = Literal(value, lang=lang, datatype=datatype)

    g.add((attr_vers_uri, RDF.type, namespace["AttributeVersion"]))
    g.add((attr_vers_uri, namespace["value"], attr_vers_lit))
    g.add((attribute_uri, namespace["version"], attr_vers_uri))

    if change_after_uri is None:
        after_change_uri, after_event_uri = generate_uri(namespace, "CH"), generate_uri(namespace, "EV")
        create_attribute_change(after_change_uri, attribute_uri, g, namespace)
        create_event(after_event_uri, g, namespace)
        create_change_event_relation(after_change_uri, after_event_uri, g, namespace)
    if change_before_uri is None:
        before_change_uri, before_event_uri = generate_uri(namespace, "CH"), generate_uri(namespace, "EV")
        create_attribute_change(before_change_uri, attribute_uri, g, namespace)
        create_event(before_event_uri, g, namespace)
        create_change_event_relation(before_change_uri, before_event_uri, g, namespace)

    g.add((before_change_uri, namespace["before"], attr_vers_uri))
    g.add((after_change_uri, namespace["after"], attr_vers_uri))
    

def convert_result_elem_to_rdflib_elem(result_elem:dict):
    """
    A partir d'un dictionnaire qui décrit un élement d'un résultat d'une requête, le convertir en un élément d'un triplet d'un graph (URIRef, Literal, Bnode)
    """
    
    res_type = result_elem.get("type")
    res_value = result_elem.get("value")
    
    if res_type == "uri":
        return URIRef(res_value)
    elif res_type == "literal":
        res_lang = result_elem.get("xml:lang")
        res_datatype = result_elem.get("datatype")
        return Literal(res_value, lang=res_lang, datatype=res_datatype)
    elif res_type == "bnode":
        return BNode(res_value)
    

def generate_uri(namespace:Namespace=None, prefix:str=None):
    if prefix:
        return namespace[f"{prefix}_{uuid4().hex}"]
    else:
        return namespace[uuid4().hex]
    
def generate_uuid():
    return uuid4().hex