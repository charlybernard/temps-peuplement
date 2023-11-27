import os
import code.filemanagement as fm
import sys
from SPARQLWrapper import SPARQLWrapper, TURTLE, JSON
import ssl
import requests

ssl._create_default_https_context = ssl._create_unverified_context

## Export query result
def get_construct_query_wikidata(query:str, format=TURTLE):
    endpoint_url = "https://query.wikidata.org/sparql"
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(format)
    return sparql.query().convert()

## Export query result
def get_select_query_wikidata(query:str):
    endpoint_url = "https://query.wikidata.org/sparql"
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()

### Get ttl files of Wikidata entities
def get_url_content(url:str, session:requests.sessions.Session):
    r = session.get(url=url)
    return r

def get_ttl_file_from_wikidata_id(wikidata_id:str, out_wikidata_folder:str, session:requests.sessions.Session, flavor:str="full"):
    """
    flavor can get three values : `full`, `simple` and `dump` (see https://www.wikidata.org/wiki/Wikidata:Data_access for more information)
    """

    url = f"https://www.wikidata.org/entity/{wikidata_id}.ttl?flavor={flavor}"
    c = get_url_content(url, session)
    out_file = os.path.join(out_wikidata_folder, f"{wikidata_id}.ttl")
    fm.write_file(c.text, out_file)

def get_ttl_files_from_wikidata_ids(wikidata_id_list:list[str], out_wikidata_folder:str, flavor="full"):
    session = requests.Session()
    for wd_id in wikidata_id_list:
        get_ttl_file_from_wikidata_id(wd_id, out_wikidata_folder, session, flavor)

def get_wikidata_ids_list_from_query(query, qid_variable):
    query_res = get_select_query_wikidata(query)
    wd_ids = []
    for val in query_res['results']['bindings']:
        wd_id = val.get(qid_variable).get('value').replace("http://www.wikidata.org/entity/", "")
        wd_ids.append(wd_id)

    return wd_ids

def get_ttl_files_from_wikidata_query(query:str, qid_variable:str, out_wikidata_folder:str, flavor:str="full"):
    """
    For each Wikidata entity (whose URI has `http://www.wikidata.org/entity/Qxxxxxx`),
    get a ttl file describing the element thanks to `http://www.wikidata.org/entity/Qxxxxxx.ttlflavor={flavor}` URI.

    Query is SPARQL select query and must return a variable whose value is `qid_variable`, it must describe a Wikidata entity

    If `qid_variable=street`, `?street` is in `SELECT` part of the query : `SELECT ?street WHERE {...}`

    Files are saved in `out_wikidata_folder` folder.
    """

    wd_ids = get_wikidata_ids_list_from_query(query, qid_variable)
    get_ttl_files_from_wikidata_ids(wd_ids, out_wikidata_folder, flavor)