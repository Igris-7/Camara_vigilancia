import cv2
import utiles
from flask import Flask, render_template, Response, jsonify
import time
from pygame import mixer

faceClassif = cv2.CascadeClassifier("cascade.xml")
mensaje = "No se detectó el objeto"
alarma = "Alerta!!!"

app = Flask(__name__) #instancia el flask , crear rutas web de manera sencilla

camara = cv2.VideoCapture(1)

"""
    Configuraciones de vídeo
"""
FRAMES_VIDEO = 20.0
RESOLUCION_VIDEO = (640, 480)
# Marca de agua

UBICACION_FECHA_HORA = (0, 15)
FUENTE_FECHA_Y_HORA = cv2.FONT_HERSHEY_PLAIN
ESCALA_FUENTE = 1
COLOR_FECHA_HORA = (255, 255, 255)
GROSOR_TEXTO = 1
TIPO_LINEA_TEXTO = cv2.LINE_AA

fourcc = cv2.VideoWriter_fourcc(*'XVID')
archivo_video = None
grabando = False
#cantidadDetectada = 0

def alarma():
    print (mensaje)
    print (alarma)
    mixer.init()
    mixer.music.load('alarma.mp3')
    mixer.music.play()
    time.sleep(3)
    mixer.music.stop()

def agregar_fecha_hora_frame(frame):
    cv2.putText(frame, utiles.fecha_y_hora(), UBICACION_FECHA_HORA, FUENTE_FECHA_Y_HORA,
                ESCALA_FUENTE, COLOR_FECHA_HORA, GROSOR_TEXTO, TIPO_LINEA_TEXTO)

def deteccion_facial(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = faceClassif.detectMultiScale(gray,
        scaleFactor = 7,
        minNeighbors = 120,
        minSize = (60, 70))
    
    cantidadDetectada = len(faces)

    if(cantidadDetectada == 0) :
        alarma()

    return frame
# Una función generadora para stremear la cámara

def deteccion_facialSA(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = faceClassif.detectMultiScale(gray, 
        scaleFactor = 7,
        minNeighbors = 120,
        minSize = (60, 70))

    for (x,y, w ,h) in faces:
        frame = cv2.rectangle(frame, (x,y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, "Cámara", (x,y-10), 2, 0.7,(0, 255, 0), 2, cv2.LINE_AA)
    return frame


def generador_frames():
    while True:
        ok, imagen = obtener_frame_camara()
        if not ok:
            break
        else:
            # Regresar la imagen en modo de respuesta HTTP
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + imagen + b"\r\n"
            #Con el fin de tener una secuencia donde cada parte reemplaza a la parte anterior, 
            #se debe usar el tipo de contenido


def obtener_frame_camara():
    global frame
    ok, frame = camara.read()
    if not ok:
        return False, None
    agregar_fecha_hora_frame(frame)
    frame = deteccion_facialSA(frame)
    # Escribir en el vídeo en caso de que se esté grabando
    if grabando and archivo_video is not None:
        archivo_video.write(frame)
        frame = deteccion_facial(frame)
    # Codificar la imagen como JPG
    _, bufer = cv2.imencode(".jpg", frame)
    imagen = bufer.tobytes()

    return True, imagen


# Cuando visiten la ruta
@app.route("/streaming_camara")
def streaming_camara():
    return Response(generador_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Cuando visiten /, servimos el index.html
@app.route('/')
def index():
    return render_template("index.html")


@app.route("/comenzar_grabacion")
def comenzar_grabacion():
    global grabando
    global archivo_video
    if grabando and archivo_video:
        return jsonify(False) 
    nombre = utiles.fecha_y_hora_para_nombre_archivo() + ".avi"
    archivo_video = cv2.VideoWriter(
        nombre, fourcc, FRAMES_VIDEO, RESOLUCION_VIDEO)
    grabando = True
    return jsonify(True)


@app.route("/detener_grabacion")
def detener_grabacion():
    global grabando
    global archivo_video
    if not grabando or not archivo_video:
        return jsonify(False)
    grabando = False
    archivo_video.release()
    archivo_video = None
    return jsonify(True) #enviar respuesta JSON al navegador


@app.route("/estado_grabacion")
def estado_grabacion():
    return jsonify(grabando)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0") #excepciones no controladas se muestran, host por defecto puerto 5000
