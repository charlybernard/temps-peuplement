import os
import code.filemanagement as fm
import code.curl as curl
import urllib.parse as up
from rdflib import Graph, Namespace, Literal, BNode 
from rdflib.namespace import RDF

def get_repository_uri_from_name(graphdb_url, repository_name):
    return f"{graphdb_url}/repositories/{repository_name}"

def get_graph_uri_from_name(graphdb_url, repository_name, graph_name):
    return f"{graphdb_url}/repositories/{repository_name}/rdf-graphs/{graph_name}"

def get_repository_uri_statements_from_name(graphdb_url, repository_name):
    return f"{graphdb_url}/repositories/{repository_name}/statements"

def remove_graph(graphdb_url, project_name, graph_name):
    cmd = curl.get_curl_command("DELETE", get_graph_uri_from_name(graphdb_url, project_name, graph_name))
    os.system(cmd)

def remove_graphs(graphdb_url,project_name,graph_name_list):
    for g in graph_name_list:
        remove_graph(graphdb_url, project_name, g)

def create_config_local_repository_file(config_repository_file:str, repository_name:str):
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

def create_repository_from_config_file(graphdb_url:str, local_config_file:str):
    url = f"{graphdb_url}/rest/repositories"
    curl_cmd_local = curl.get_curl_command("POST", url, content_type="multipart/form-data", form=f"config=@{local_config_file}")
    os.system(curl_cmd_local)

def export_data_from_repository(graphdb_url, project_name, res_query_file):
    query = """CONSTRUCT {?s ?p ?o} WHERE {?s ?p ?o}"""
    query_encoded = up.quote(query)
    post_data = f"query={query_encoded}"
    cmd = curl.get_curl_command("POST", get_repository_uri_from_name(graphdb_url, project_name), content_type="application/x-www-form-urlencoded", accept="text/turtle", post_data=post_data)
    out_content = os.popen(cmd)
    fm.write_file(out_content.read(), res_query_file)

def select_query(query, graphdb_url, project_name, res_query_file):
    query_encoded = up.quote(query)
    post_data = f"query={query_encoded}"
    cmd = curl.get_curl_command("POST", get_repository_uri_from_name(graphdb_url, project_name), content_type="application/x-www-form-urlencoded", post_data=post_data)
    out_content = os.popen(cmd)
    fm.write_file(out_content.read(), res_query_file)

def update_query(query, graphdb_url, project_name):
    url = get_repository_uri_statements_from_name(graphdb_url, project_name)
    query_encoded = up.quote(query)
    cmd = curl.get_curl_command("POST", url, content_type="application/x-www-form-urlencoded", post_data=f"update={query_encoded}")
    os.system(cmd)

def get_namespaces(graphdb_url, repository_name):
    namespaces_uri = get_repository_uri_from_name(graphdb_url, repository_name) + "/namespaces"
    cmd = curl.get_curl_command("GET", namespaces_uri)
    namespaces = os.popen(cmd).read()
    return namespaces

def get_repository_prefixes(graphdb_url, repository_name):
    namespaces = get_namespaces(graphdb_url, repository_name).split("\n")
    prefixes = ""
    for namespace in namespaces[1:]:
        try:
            prefix, uri = namespace.split(",")
            prefixes += f"PREFIX {prefix}: <{uri}>\n"
        except:
            pass
    return prefixes

### Import created ttl file in GraphDB
def import_ttl_file_in_graphdb(graphdb_url, repository_id, ttl_file, graph_name=None):
    # cmd = f"curl -X POST -H \"Content-Type:application/x-turtle\" -T \"{ttl_file}\" {graphdb_url}/repositories/{repository_id}/statements"
    if graph_name is None:
        url = get_repository_uri_statements_from_name(graphdb_url, repository_id)
    else:
        url = get_graph_uri_from_name(graphdb_url, repository_id, graph_name)
    
    cmd = curl.get_curl_command("POST", url, content_type="application/x-turtle", local_file=ttl_file)

    os.system(cmd)

def upload_ttl_folder_in_graphdb_repository(ttl_folder_name, graphdb_url, repository_id, graph_name):
    for elem in os.listdir(ttl_folder_name):
        elem_path = os.path.join(ttl_folder_name, elem)
        if os.path.splitext(elem)[-1].lower() == ".ttl":
            import_ttl_file_in_graphdb(graphdb_url, repository_id, elem_path, graph_name)

def clear_repository(graphdb_url, project_name):
    url = f"{graphdb_url}/repositories/{project_name}/statements"
    cmd = curl.get_curl_command("DELETE", url, content_type="application/x-turtle")
    os.system(cmd)