import imutils
import time
import cv2
from imutils.video import VideoStream
from scipy.spatial import distance
from connection import *

# Inicializa el video stream
video_stream = VideoStream(src=0).start()
time.sleep(2.0)

reference_pixel = (0, 0)
ball_size = 40  # mm

pixels_per_metric = None
reference_object = None

first_frame = None
max_distance = None
previous_time = 0

blue_color = (180, 130, 70)

# Definir la región de interés (ROI)
# Puedes ajustar estos valores para la zona que te interese
roi_start_x, roi_start_y, roi_width, roi_height = 0, 0, 0, 0

def mid_point(point_a, point_b):
    return (point_a[0] + point_b[0]) / 2.0, (point_a[1] + point_b[1]) / 2.0

# Bucle sobre los frames del video
while True:
    original_frame = video_stream.read()
    if original_frame is None:
        continue

    if roi_width == 0:
        frame_height, frame_width = original_frame.shape[:2]
        roi_start_x = int((frame_width - roi_width) / 4)
        roi_start_y = 0
        roi_width = int(frame_width / 2)
        roi_height = frame_height

    # Recorta el frame original según la región de interés (ROI)
    cropped_frame = original_frame[roi_start_y:roi_start_y + roi_height, roi_start_x:roi_start_x + roi_width]

    # Crea una copia redimensionada del frame para el procesamiento
    resized_frame = imutils.resize(cropped_frame, width=500)
    clean_frame = cropped_frame.copy()

    # Convierte la copia redimensionada a escala de grises
    gray = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)

    # Aplica desenfoque para reducir el ruido
    gray = cv2.GaussianBlur(gray, (23, 23), 0)

    # Inicializa el primer frame si no se ha hecho
    if first_frame is None:
        first_frame = gray
        # Pixel de referencia en el centro superior del frame recortado
        reference_pixel = (int(cropped_frame.shape[1] / 2), 0)
        continue

    # Calcula la diferencia entre el frame redimensionado actual y el primero
    frame_delta = cv2.absdiff(first_frame, gray)

    # Aplica umbral
    threshold = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
    threshold = cv2.dilate(threshold, None, iterations=2)

    # Encuentra contornos en la imagen con umbral
    contours = cv2.findContours(threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(contours)

    # Bucle sobre los contornos
    for contour in contours:
        if cv2.contourArea(contour) < 230:
            continue

        # Calcula el cuadro delimitador del contorno sobre el frame redimensionado
        (x, y, width, height) = cv2.boundingRect(contour)

        # Escala las coordenadas y el tamaño del cuadro al tamaño original
        scale_factor = cropped_frame.shape[1] / resized_frame.shape[1]
        (x, y, width, height) = int(x * scale_factor), int(y * scale_factor), int(width * scale_factor), int(height * scale_factor)

        # Dibuja el cuadro delimitador en el frame recortado
        cv2.rectangle(clean_frame, (x, y), (x + width, y + height), (0, 255, 0), 2)

        # Calcula el punto medio del cuadro delimitador
        ((center_x, center_y), radius) = cv2.minEnclosingCircle(contour)
        center_x, center_y = int(center_x * scale_factor), int(center_y * scale_factor)

        if pixels_per_metric is None:
            pixels_per_metric = radius * 2 / ball_size
            # Altura total
            # send_message(connection, f"M{max_distance:.2f}\n")

        # Calcular la distancia euclidiana entre el punto medio y el punto de referencia
        distance_to_reference = distance.euclidean((center_x, center_y), reference_pixel)
        distance_to_reference /= pixels_per_metric * scale_factor
        # send_message(connection, f"{distance_to_reference:.2f}\n")

        if max_distance is None and distance_to_reference is not None:
            max_distance = distance_to_reference
            send_message(connection, f"M{distance_to_reference:.2f}\n")

        # Dibuja el punto medio y la distancia
        cv2.circle(clean_frame, (center_x, center_y), 5, blue_color, -1)
        cv2.line(clean_frame, (center_x, center_y), reference_pixel, blue_color, 2)

        mid_x, mid_y = mid_point((center_x, center_y), reference_pixel)
        cv2.putText(clean_frame, f"{distance_to_reference:.2f}mm", (int(mid_x), int(mid_y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.0, blue_color, 2)

    # Calcula los FPS
    current_time = time.time()
    fps = 1 / (current_time - previous_time)
    previous_time = current_time

    # Dibuja los FPS en el frame recortado
    fpsText = "FPS: {:.2f}".format(fps)
    cv2.putText(clean_frame, fpsText, (cropped_frame.shape[1] - 200, 50), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 0, 0), 2)

    # Muestra el stream de video
    cv2.imshow("Levitador de Pelota - Recortado", clean_frame)

    # Si se presiona la tecla 'q', sal del bucle, si se presiona la tecla 'r', reinicia el primer frame
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
    elif key == ord("r"):
        first_frame = None
        pixels_per_metric = None
        distance_to_reference = None
        max_distance = None

# Limpia la cámara y cierra las ventanas abiertas
video_stream.stop()
cv2.destroyAllWindows()