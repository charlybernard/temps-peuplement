import os
import sys
import urllib.parse as up
from rdflib import Graph, Namespace, Literal, BNode 
from rdflib.namespace import RDF
import xml.etree.ElementTree as ET
from SPARQLWrapper import SPARQLWrapper, TURTLE
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

## Functions to manage files and folders

def read_file(filename, split_lines=False):
    file = open(filename, "r")
    file_content = file.read()
    if split_lines:
        file_content = file_content.split("\n")
    file.close()
    return file_content

def write_file(content,filename):
    file = open(filename, "w")
    file.write(content)
    file.close()

def create_folder_if_not_exists(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)

def remove_folder_if_exists(folder):
    if os.path.exists(folder):
        remove_folder(folder)

def remove_folder(folder):
    for e in os.listdir(folder):
        abspath_e = os.path.join(folder, e)
        print(abspath_e)
        if os.path.isfile(abspath_e):
            remove_file_if_exists(abspath_e)
        elif os.path.isdir(abspath_e):
            remove_folder(e)
        else:
            print(e)

    os.rmdir(folder)
        
def remove_file_if_exists(filename):
    if os.path.exists(filename):
        os.remove(filename)

## Functions in relations with RDF4J API 

def get_repository_uri_from_name(graphdb_url, repository_name):
    return f"{graphdb_url}/repositories/{repository_name}"

def get_graph_uri_from_name(graphdb_url, repository_name, graph_name):
    return f"{graphdb_url}/repositories/{repository_name}/rdf-graphs/{graph_name}"

def remove_graph(graphdb_url, project_name, graph_name):
    cmd = f"curl -X DELETE {get_graph_uri_from_name(graphdb_url, project_name, graph_name)}"
    os.system(cmd)

def remove_graphs(graphdb_url,project_name,graph_name_list):
    for g in graph_name_list:
        remove_graph(graphdb_url, project_name, g)

def create_config_local_repository_file(config_repository_file, repository_name):
    rep = Namespace("http://www.openrdf.org/config/repository#")
    sr = Namespace("http://www.openrdf.org/config/repository/sail#")
    sail = Namespace("http://www.openrdf.org/config/sail#")
    graph_db = Namespace("http://www.ontotext.com/config/graphdb#")
    g = Graph()

    elem = BNode()
    repository_impl = BNode()
    sail_impl = BNode()
    
    g.add((elem, RDF.type, rep.Repository))
    g.add((elem, rep.repositoryID, Literal(repository_name)))
    g.add((elem, rep.repositoryImpl, repository_impl))
    g.add((repository_impl, rep.repositoryType, Literal("graphdb:SailRepository")))
    g.add((repository_impl, sr.sailImpl, sail_impl))
    g.add((sail_impl, sail.sailType, Literal("graphdb:Sail")))
    g.add((sail_impl, graph_db["base-URL"], Literal("http://example.org/owlim#")))
    g.add((sail_impl, graph_db["defaultNS"], Literal("")))
    g.add((sail_impl, graph_db["entity-index-size"], Literal("10000000")))
    g.add((sail_impl, graph_db["entity-id-size"], Literal("32")))
    g.add((sail_impl, graph_db["imports"], Literal("")))
    g.add((sail_impl, graph_db["repository-type"], Literal("file-repository")))
    g.add((sail_impl, graph_db["ruleset"], Literal("rdfsplus-optimized")))
    g.add((sail_impl, graph_db["storage-folder"], Literal("storage")))
    g.add((sail_impl, graph_db["enable-context-index"], Literal("false")))
    g.add((sail_impl, graph_db["enablePredicateList"], Literal("true")))
    g.add((sail_impl, graph_db["in-memory-literal-properties"], Literal("true")))
    g.add((sail_impl, graph_db["enable-literal-index"], Literal("true")))
    g.add((sail_impl, graph_db["check-for-inconsistencies"], Literal("false")))
    g.add((sail_impl, graph_db["disable-sameAs"], Literal("true")))
    g.add((sail_impl, graph_db["query-timeout"], Literal("0")))
    g.add((sail_impl, graph_db["query-limit-results"], Literal("0")))
    g.add((sail_impl, graph_db["throw-QueryEvaluationException-on-timeout"], Literal("false")))
    g.add((sail_impl, graph_db["read-only"], Literal("false")))
    
    g.serialize(destination=config_repository_file)

def export_data_from_repository(graphdb_url, project_name, res_query_file):
    query = """CONSTRUCT {?s ?p ?o} WHERE {?s ?p ?o}"""
    query_encoded = up.quote(query)
    post_data = f"query={query_encoded}"
    cmd = get_curl_command("POST", get_repository_uri_from_name(graphdb_url, project_name), content_type="application/x-www-form-urlencoded", accept="text/turtle", post_data=post_data)
    out_content = os.popen(cmd)
    write_file(out_content.read(), res_query_file)

def select_query(query, graphdb_url, project_name, res_query_file):
    query_encoded = up.quote(query)
    post_data = f"query={query_encoded}"
    cmd = get_curl_command("POST", get_repository_uri_from_name(graphdb_url, project_name), content_type="application/x-www-form-urlencoded", post_data=post_data)
    out_content = os.popen(cmd)
    write_file(out_content.read(), res_query_file)

def get_curl_command(method, url, content_type=None, accept=None, post_data=None, local_file=None, form=None):
    curl_cmd = f"curl -X {method}" 
    if content_type is not None:
        curl_cmd += f" -H \"Content-Type:{content_type}\""
    if accept is not None:
        curl_cmd += f" -H \"Accept:{accept}\""
    if post_data is not None:
        curl_cmd += f" -d \"{post_data}\""
    if local_file is not None:
        curl_cmd += f" -T \"{local_file}\""
    if form is not None:
        curl_cmd += f" -F \"{form}\""
    curl_cmd += f" {url}"

    return curl_cmd

## Functions to manage graph with SPARQL queries

def remove_circular_same_as_links(graphdb_url, project_name):
    query = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>

    DELETE {
        ?s owl:sameAs ?s
    }
    WHERE {
       ?s owl:sameAs ?s
    }
    """

    query_encoded = up.quote(query)
    url = f"{get_repository_uri_from_name(graphdb_url,project_name)}/statements"
    post_data = f"update={query_encoded}"
    cmd = get_curl_command("POST", url, content_type="application/x-www-form-urlencoded", post_data=post_data)
    os.system(cmd)

def get_entries_without_same_as_links(graphdb_url, project_name, res_query_file):
    query = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX e: <http://rdf.geohistoricaldata.org/def/directory#>
    PREFIX rda: <http://rdaregistry.info/Elements/a/>
    PREFIX locn: <http://www.w3.org/ns/locn#>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    select ?id ?personne ?activite ?adresse ?source where { 
        ?id a e:Entry; rdfs:label ?personne; rda:P50104 ?activite; locn:fullAddress ?adresse; prov:wasDerivedFrom ?source.
        MINUS {?id owl:sameAs [a e:Entry]}
    }
    """

    select_query(query, graphdb_url, project_name, res_query_file)

def get_stats_per_source(graphdb_url, project_name, res_query_file):
    query = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX e: <http://rdf.geohistoricaldata.org/def/directory#>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    select ?source ?countSourceWithoutLinks (COUNT(?source) AS ?countTotal) (CEIL(?countSourceWithoutLinks/COUNT(?source)*10000)/100 AS ?ratio) where {
    ?s1 a e:Entry; prov:wasDerivedFrom ?source.
    {
    select ?source (COUNT(?source) AS ?countSourceWithoutLinks) where { 
        ?s1 a e:Entry; prov:wasDerivedFrom ?source.
        MINUS {?s1 owl:sameAs [a e:Entry]}
    }
        GROUP BY (?source)}
    }
    GROUP BY ?source ?countSourceWithoutLinks
    """

    select_query(query, graphdb_url, project_name, res_query_file)

def get_same_as_links_from_graph(graph_url, graphdb_url, project_name, res_query_file):
    query_template = """
    PREFIX locn: <http://www.w3.org/ns/locn#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rda: <http://rdaregistry.info/Elements/a/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    SELECT ?id1 ?id2 ?source1 ?source2 ?adresse1 ?adresse2 ?activite1 ?activite2 ?personne1 ?personne2 WHERE {{
        ?id1 locn:fullAddress ?adresse1; rda:P50104 ?activite1; rdfs:label ?personne1; prov:wasDerivedFrom ?source1.
        ?id2 locn:fullAddress ?adresse2; rda:P50104 ?activite2; rdfs:label ?personne2; prov:wasDerivedFrom ?source2.
        GRAPH {graph_url} {{?s1 owl:sameAs ?s2}}
    }}
    """

    query_template = """
    PREFIX locn: <http://www.w3.org/ns/locn#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rda: <http://rdaregistry.info/Elements/a/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    SELECT ?s1 ?s2  WHERE {{
        GRAPH {graph_url} {{?s1 owl:sameAs ?s2}}
    }}
    """
    
    query = query_template.format(graph_url=graph_url)
    select_query(query, graphdb_url, project_name, res_query_file)

def get_same_as_links_from_all_graph(settings, graphdb_url, project_name):
    for setting in settings:
        graph_name = setting.get("name")
        out_file = setting.get("csv_file_name")
        graph_uri = f"<{get_graph_uri_from_name(graphdb_url, project_name, graph_name)}>"
        get_same_as_links_from_graph(graph_uri, graphdb_url, project_name, out_file)

### Create a ttl file in ontorefine from csv file
def get_export_file_from_ontorefine(ontorefine_cmd, ontorefine_url, project_name, data_file, mapping_file, export_file):
    # Launch Ontorefine before launching this command
    cmd = f"{ontorefine_cmd} create \"{data_file}\" -u \"{ontorefine_url}\" -n \"{project_name}\""
    msg = os.popen(cmd)

    # Get project_id from message given by CLI
    project_id = msg.read().split(": ")[1].replace("\n", "")

    # Launch Ontorefine before launching this command
    cmd = f"{ontorefine_cmd} rdf \"{project_id}\" -u {ontorefine_url} -m \"{mapping_file}\""
    out_content = os.popen(cmd)
    out_file = open(export_file, "w")
    out_file.write(out_content.read())
    out_file.close()

    # Launch Ontorefine before launching this command
    cmd = f"{ontorefine_cmd} delete \"{project_id}\" -u {ontorefine_url}"
    os.system(cmd)

### Import created ttl file in GraphDB
def import_ttl_file_in_graphdb(graphdb_url, repository_id, ttl_file, graph_name):
    # cmd = f"curl -X POST -H \"Content-Type:application/x-turtle\" -T \"{ttl_file}\" {graphdb_url}/repositories/{repository_id}/statements"
    url = get_graph_uri_from_name(graphdb_url, repository_id, graph_name)
    cmd = get_curl_command("POST", url, content_type="application/x-turtle", local_file=ttl_file)

    os.system(cmd)

## Export query result
def get_construct_query_wikidata(query):
    endpoint_url = "https://query.wikidata.org/sparql"
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(TURTLE)
    return sparql.query().convert()