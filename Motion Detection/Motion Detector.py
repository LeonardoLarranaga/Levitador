from imutils.video import VideoStream
import argparse
import datetime
import imutils
import time
import cv2

# Construye el parser de argumentos y analiza los argumentos
argumentParser = argparse.ArgumentParser()
argumentParser.add_argument("-v", "--video", help="Ruta al archivo de video")
argumentParser.add_argument("-a", "--min-area", type=int, default=500, help="Tamaño mínimo del área")
arguments = vars(argumentParser.parse_args())

# Si el argumento de video es None, estamos leyendo desde la cámara web
if arguments.get("video", None) is None:
    videoStream = VideoStream(src=0).start()
    time.sleep(2.0)

# De lo contrario, estamos leyendo desde un archivo de video
else:
    videoStream = cv2.VideoCapture(arguments["video"])

# Inicializa el primer frame en el stream de video
# Este será el frame con el que compararemos los otros frames para determinar si hay movimiento
firstFrame = None

# Variables para el cálculo de FPS
previousTime = 0

# Bucle sobre los frames del video
while True:
    # Obtén el frame actual e inicializa el texto de ocupado/no ocupado
    frame = videoStream.read()
    frame = frame if arguments.get("video", None) is None else frame[1]
    text = "No ocupado"

    # Si no se pudo obtener el frame, significa que hemos llegado al final del video
    if frame is None:
        break

    # Redimensiona el frame y conviértelo a escala de grises
    frame = imutils.resize(frame, width=500)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Los frames consecutivos no son exactamente iguales, por lo que necesitamos aplicar un desenfoque para eliminar el ruido
    gray = cv2.GaussianBlur(gray, (21, 21), 0)

    # Si el primer frame es None, inicialízalo
    if firstFrame is None:
        firstFrame = gray
        continue

    # Calcula la diferencia absoluta entre el frame actual y el primer frame
    frameDelta = cv2.absdiff(firstFrame, gray)

    # Aplica un umbral para revelar las regiones de la imagen con cambios significativos en los valores de intensidad de los píxeles
    threshold = cv2.threshold(frameDelta, 10, 255, cv2.THRESH_BINARY)[1]

    # Diluye la imagen con umbral para llenar huecos, luego encuentra los contornos en la imagen umbralizada
    threshold = cv2.dilate(threshold, None, iterations=2)
    contours = cv2.findContours(threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)

    # Bucle sobre los contornos
    for contour in contours:
        # Si el contorno es muy pequeño, ignóralo
        if cv2.contourArea(contour) < arguments["min_area"]:
            continue

        # Calcula el cuadro delimitador del contorno, dibújalo en el frame y actualiza el texto
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = "Ocupado"

    # Dibuja el texto y la marca de tiempo en el frame
    cv2.putText(frame, "Estado de la sala: {}".format(text), (10, 20), cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 0, 0), 1)
    cv2.putText(frame, datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_TRIPLEX, 0.35, (255, 0, 0), 1)

    # Calcula los FPS https://www.geeksforgeeks.org/python-displaying-real-time-fps-at-which-webcam-video-file-is-processed-using-opencv/
    currentTime = time.time()
    fps = 1 / (currentTime - previousTime)
    previousTime = currentTime

    # Dibuja los FPS
    fpsText = "FPS: {:.2f}".format(fps)
    cv2.putText(frame, fpsText, (400, 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (0, 0, 0), 1)

    # Muestra el frame y registra si el usuario presiona una tecla
    cv2.imshow("Feed de seguridad", frame)
    cv2.imshow("Threshold", threshold)
    cv2.imshow("Delta frame", frameDelta)
    cv2.moveWindow("Feed de seguridad", 10, 10)
    cv2.moveWindow("Threshold", 10, 400)
    cv2.moveWindow("Delta frame", 550, 10)
    key = cv2.waitKey(1) & 0xFF

    # Si se presiona la tecla 'q', sal del bucle
    if key == ord("q"):
        break
    elif key == ord("r"):
        firstFrame = gray

# Limpia la cámara y cierra las ventanas abiertas
videoStream.stop() if arguments.get("video", None) is None else videoStream.release()
cv2.destroyAllWindows()
