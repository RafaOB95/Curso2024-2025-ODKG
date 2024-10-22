from rdflib import Graph
import morph_kgc, subprocess, os, requests, json

## --------------------OPENREFINE API--------------------
csrf_token = ""

def get_csrf_token():
    global csrf_token

    url = 'http://127.0.0.1:3333/command/core/get-csrf-token'
    response = requests.get(url)
    csrf_token = response.json()["token"]

# Cargar el CSV como un nuevo proyecto en OpenRefine
def create_project(csv_file_path, project_name):
    url = 'http://127.0.0.1:3333/command/core/create-project-from-upload'
    with open(csv_file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'project-name': project_name,
            'format': 'text/line-based/csv',  # Indicar que es un csv_file_path
        }
        response = requests.post(f'{url}?csrf_token={csrf_token}', files=files, data=data)
    return response.url[38:len(response.url)]

# Aplicar el archivo JSON de operaciones
def apply_operations(project_id, operations_json_file):
    url = 'http://127.0.0.1:3333/command/core/apply-operations'
    with open(operations_json_file, 'r') as f:
        operations = json.load(f)
        data = {
            'operations': json.dumps(operations),
        }
    
        response = requests.post(f'{url}?project={project_id}&csrf_token={csrf_token}', data=data)
    
        if response.json()["code"] == "error":
            raise Exception(f"Error al aplicar los cambios: {response.text}")
    return 0

def export_project_to_csv(project_id, export_file_path):
    url = 'http://127.0.0.1:3333/command/core/export-rows'
    response = requests.post(f'{url}?project={project_id}&format=csv')
    with open(export_file_path, 'wb') as f:
        f.write(response.content)

def delete_project(project_id):
    url = 'http://127.0.0.1:3333/command/core/delete-project'
    response = requests.post(f'{url}?project={project_id}&csrf_token={csrf_token}')
    if response.json()["code"] != "ok":
        raise Exception("Deleting project error")






def apply_changes_csv(path_csv, project_name, changes_json_path, export_file_path):
    string = f'------------Applying changes to {path_csv} with {changes_json_path}------------'
    print(string)
    # Crear un proyecto1
    project_id = create_project(path_csv, project_name)
    
    apply_operations(project_id,changes_json_path)
    export_project_to_csv(project_id, export_file_path)
    
    delete_project(project_id)


def join_files(path_csv1, path_csv2, output_path):
    string = f"------------Merging {path_csv1} and {path_csv2}------------"
    print(string)

    command = f"(cat {path_csv1}; tail -n +2 {path_csv2}) > {output_path}"
    resultado = subprocess.run(command, shell=True)

    if resultado.returncode == 0:
        print("------------Deleting intermediate files------------")
        os.remove(path_csv1)
        os.remove(path_csv2)
    else:
        raise Exception("Error al juntar los archivos")

def generate_rdf():
    print("------------Generating RDF data with Morph-KGC------------")

    # Generates the RDF knowledge graph
    config = """
    [CONFIGURATION]
    [DEFAULT]
    main_dir: ./

    # INPUT
    na_values=,#N/A,N/A,#N/A N/A,n/a,NA,<NA>,#NA,NULL,null,NaN,nan,None

    # MULTIPROCESSING
    number_of_processes=2

    [SOURCE]
    mappings=mappings/mapping_rules.yml
         """
    return morph_kgc.materialize(config)

def turtle_serialization(graph):
    print("------------Serializing RDF data into a file------------")
    # Turtle format printing
    graph.serialize(destination="rdf/knowledge-graph.ttl")


def main():
    source_file1 = "csv/datos_diarios_2023.csv"
    source_file2 = "csv/datos_diarios_2024.csv"
    intermediate_file1 = "csv/datos_2023-updated.csv"
    intermediate_file2 = "csv/datos_2024-updated.csv"
    joined_path = "csv/datos_dirty.csv"
    output_path = "csv/datos_diarios-updated.csv"

    cambios_json_path = "openrefine/cambios_datos_diarios.json"
    limpieza_fechas_json = "openrefine/limpieza_dias_invalidos.json"
    
    get_csrf_token()
    apply_changes_csv(source_file1, "measures_2023", cambios_json_path, intermediate_file1)
    apply_changes_csv(source_file2, "measures_2024", cambios_json_path, intermediate_file2)
    
    if(os.path.exists(intermediate_file1) and os.path.exists(intermediate_file2)):
        join_files(intermediate_file1,intermediate_file2,joined_path)

    apply_changes_csv(joined_path, "clean_strange_dates", limpieza_fechas_json, output_path)
    os.remove(joined_path)
    
    g = generate_rdf()
    turtle_serialization(g)

if __name__ == "__main__":
    main()
