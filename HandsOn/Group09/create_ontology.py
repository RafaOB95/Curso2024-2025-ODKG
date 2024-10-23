from rdflib import Graph
import morph_kgc, subprocess, os, requests, json, csv

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

def create_project_2_files(csv_file_path1, csv_file_path2, project_name):
    url = 'http://127.0.0.1:3333/command/core/create-project-from-upload'
    with open(csv_file_path1, 'rb') as f1, open(csv_file_path2, 'rb') as f2:
        files = {
            'file1': f1,
            'file2': f2
        }
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

def apply_changes_2_csv(path_csv1, path_csv2, project_name, changes_json_path, export_file_path):
    string = f'------------Applying changes to {path_csv1} and {path_csv2} with {changes_json_path}------------'
    print(string)
    # Crear un proyecto1
    project_id = create_project_2_files(path_csv1, path_csv2, project_name)
    
    apply_operations(project_id,changes_json_path)
    export_project_to_csv(project_id, export_file_path)
    
    delete_project(project_id)

'''
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
'''

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

def stations_csv2json(csv_file, json_file):
    print(f"------------Converting {csv_file} to json------------")
    # Leer el archivo CSV
    with open(csv_file, 'r', encoding='utf-8') as file:
        lector_csv = csv.DictReader(file)
        
        # Crear una lista para almacenar los datos
        lista_datos = []
        
        # Recorrer cada fila del archivo CSV y agregarlo a la lista
        for fila in lector_csv:
            # Convertir las columnas numéricas a enteros
            
            measures = []
            if fila['NO2'] == "true":
                measures.append('NO')
                measures.append('NOx')
                measures.append('NO2')
            if fila['SO2'] == "true":
                measures.append('SO2')
            if fila['CO'] == "true":
                measures.append('CO')
            if fila['PM10'] == "true":
                measures.append('PM10')
            if fila['PM2_5'] == "true":
                measures.append('PM2_5')
            if fila['O3'] == "true":
                measures.append('O3')
            if fila['BTX'] == "true":
                measures.append('BTX')

            station = {
              'CODIGO': fila['CODIGO'],
              'ESTACION': fila["ESTACION"],
              'ALTITUD': fila["ALTITUD"],
              'MEDIDAS': measures,
              'COD_VIA': fila['COD_VIA'],
              'LONGITUD': fila['LONGITUD'],
              'LATITUD': fila['LATITUD']
            }
            lista_datos.append(station)

    # Escribir el archivo JSON con la lista de datos
    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(lista_datos, file, ensure_ascii=False, indent=2)
    


def treatment_measures():
    source_file1 = "csv/datos_diarios_2023.csv"
    source_file2 = "csv/datos_diarios_2024.csv"
    output_path = "csv/datos_diarios-updated.csv"
    
    cambios_json_path = "openrefine/cambios_datos_diarios.json"
    
    get_csrf_token()
    # Air quality measures
    apply_changes_2_csv(source_file1, source_file2, "measures", cambios_json_path, output_path)

def treatment_stations(): 
    source_file = "csv/informacion_estaciones_red_calidad_aire.csv"
    output_path = "csv/informacion_estaciones_red_calidad_aire-updated.csv"
    json_ouput_path = "csv/informacion_estaciones_red_calidad_aire-updated.json"
    cambios_json_path = "openrefine/informacion_estaciones_red_calidad_aire 1.json"

    apply_changes_csv(source_file, "stations", cambios_json_path, output_path)
    # Generate json version
    stations_csv2json(output_path,json_ouput_path)


def main():
    treatment_measures()
    treatment_stations()
    
    g = generate_rdf()
    turtle_serialization(g)

if __name__ == "__main__":
    main()
