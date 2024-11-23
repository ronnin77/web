from flask import Flask, render_template, request, redirect, url_for
import requests  # DEBEN TENER ESTA LIBRERIA INSTALADA (pip install requests)
import os
import mysql.connector
from datetime import datetime  # LIBRERIA QUE CAPTURA LA HORA Y FECHA DE LA CONSULTA

# SU API KEY (esta es de juan XD)
API_KEY = 'd02d9401cf34a72e1fe3a5e5c6b13724'

template_dir = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
template_dir = os.path.join(template_dir, 'src', 'templates')
app = Flask(__name__, template_folder=template_dir)

# Conexion con la base de datos
# RECUERDEN TENER LA BASE DE DATOS EN SU LAP (DEJARE UN ARCHIVO PARA QUE COPIEN Y PEGUEN EL MYSQL)
conexion = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="Juan20@",  # PONER SU CONTRASENA DE BASE DE DATOS
    db="ronin"
)

# ESTA FUNCION GUARDA LA CONSULTA EN LA BASE DE DATOS
def insert_song(title, artist, album, links):
    cursor = conexion.cursor()
    now = datetime.now()
    sql = "INSERT INTO api (nombreCancion, nombreArtista, nombreAlbum, links, historial) VALUES (%s, %s, %s, %s, %s)"
    values = (title, artist, album, links, now)
    cursor.execute(sql, values)
    conexion.commit()
    cursor.close()

@app.route('/')
def home():
    return render_template('index.html')

# RUTA PARA EL API
@app.route('/audd', methods=['GET', 'POST'])
def audd():
    result = None  # Inicializamos la variable para los resultados
    if request.method == 'POST':
        # Verificar si se ha subido un archivo
        if 'audio_file' not in request.files:
            return render_template('audd.html', result=None)
        
        file = request.files['audio_file']
        if file.filename == '':
            return render_template('audd.html', result=None)
        
        # Guardar el archivo temporalmente
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
        
        # Llamar a la API de Audd
        result = identificar_cancion(file_path)
        
        # Borrar el archivo después de la identificación
        os.remove(file_path)
        
        # Guardar los datos en la base de datos si la identificación fue exitosa
        if result and result['status'] == 'success':
            title = result['result']['title']
            artist = result['result']['artist']
            album = result['result']['album']
            links = result['result']['song_link']
            # Inserta los datos en la base de datos
            insert_song(title, artist, album, links)
    
    # Renderizar audd.html con los resultados (si los hay)
    return render_template('audd.html', result=result)

# Función para llamar a la API de Audd
def identificar_cancion(file_path):
    url = 'https://api.audd.io/'
    data = {
        'api_token': API_KEY,
        'return': 'timecode,lyrics',
    }
    files = {
        'file': open(file_path, 'rb')
    }
    response = requests.post(url, data=data, files=files)
    return response.json()

# Obtener el historial desde la base de datos
def get_history():
    cursor = conexion.cursor()
    cursor.execute("SELECT id,nombreCancion, nombreArtista, nombreAlbum, links, historial FROM api")
    results = cursor.fetchall()
    cursor.close()
    return results

@app.route('/historial')
def historial():
    data = get_history()
    return render_template('historial.html', canciones=data)

# RUTA PARA ELIMINAR UNA CANCION
@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar_cancion(id):
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM api WHERE id = %s", (id,))
    conexion.commit()
    cursor.close()
    return redirect(url_for('historial'))

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True, port=5501)
