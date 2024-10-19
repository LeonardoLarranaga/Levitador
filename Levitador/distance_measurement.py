import imutils
from scipy.spatial import distance
from imutils import perspective
from imutils import contours as imutils_contours
import numpy
import argparse
import cv2

# Calcular el punto medio entre dos puntos
def mid_point(point_a, point_b):
    return (point_a[0] + point_b[0]) * 0.5, (point_a[1] + point_b[1]) * 0.5

# Argumentos
argumet_parser = argparse.ArgumentParser()
argumet_parser.add_argument("-i", "--image", required=True, help="path to the input image")
argumet_parser.add_argument("-w", "--width", type=float, required=True, help="width of the left-most object in the image (in inches)")
arguments = vars(argumet_parser.parse_args())

# Leer la imagen, convertirla a escala de grises y suavizarla
image = cv2.imread(arguments["image"])
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
gray = cv2.GaussianBlur(gray, (7, 7), 0)

# Detectar bordes en la imagen en escala de grises, dilatar y erosionar los bordes para cerrar cualquier brecha entre los objetos
edged_image = cv2.Canny(gray, 50, 100)
edged_image = cv2.dilate(edged_image, None, iterations=1)
edged_image = cv2.erode(edged_image, None, iterations=1)

# Encontrar contornos en la imagen
contours = cv2.findContours(edged_image.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contours = imutils.grab_contours(contours)

# Ordenar los contornos de izquierda a derecha (donde el objeto de la izquierda es el de referencia, el objeto de tamaño conocido)
(contours, _) = imutils_contours.sort_contours(contours)
# Inicializar los colores a usar y el objeto de referencia
colors = ((0, 0, 255), (240, 0, 159), (0, 165, 255), (255, 255, 0), (255, 0, 255))
reference_object = None

# Iterar sobre los contornos
for contour in contours:
    # Si el contorno no es lo suficientemente grande, ignorarlo, probablemente es ruido
    if cv2.contourArea(contour) < 100:
        continue

    # Calcular el rectángulo delimitador del contorno
    box = cv2.minAreaRect(contour)
    box = cv2.boxPoints(box)
    box = numpy.array(box, dtype="int")

    # Ordenar los puntos del contorno para que aparezcan en sentido horario y luego dibujar las líneas del contorno
    box = perspective.order_points(box)

    # Calcular el centro de la caja
    center_x = numpy.average(box[:, 0])
    center_y = numpy.average(box[:, 1])

    # Si el objeto de referencia no ha sido inicializado, hacerlo
    if reference_object is None:
        # Extraer los puntos del contorno y calcular las dimensiones del objeto
        (top_left, top_right, bottom_right, bottom_left) = box
        # Calculamos la distancia euclidiana entre el punto superior izquierdo y el punto superior derecho
        (top_left_bottom_left_x, top_left_bottom_left_y) = mid_point(top_left, bottom_left)
        (top_right_bottom_right_x, top_right_bottom_right_y) = mid_point(top_right, bottom_right)

        # Calculamos la distancia euclidiana entre los puntos
        euclidean_distance = distance.euclidean((top_left_bottom_left_x, top_left_bottom_left_y), (top_right_bottom_right_x, top_right_bottom_right_y))
        reference_object = (box, (center_x, center_y), euclidean_distance / arguments["width"])
        continue

    # Dibujar los contornos
    original_image = image.copy()
    cv2.drawContours(original_image, [box.astype("int")], -1, (0, 255, 0), 2)
    cv2.drawContours(original_image, [reference_object[0].astype("int")], -1, (0, 255, 0), 2)

    # Apilar las coordenadas de referencia y las del objeto actual para incluir el centro del objeto
    reference_coordinates = numpy.vstack([reference_object[0], reference_object[1]])
    object_coordinates = numpy.vstack([box, (center_x, center_y)])

    # Iterar sobre los puntos originales
    for ((start_x, start_y), (end_x, end_y), color) in zip(reference_coordinates, object_coordinates, colors):
        # Dibujar los círculos de los puntos actuales y conectarlos con una línea
        cv2.circle(original_image, (int(start_x), int(start_y)), 5, color, -1)
        cv2.circle(original_image, (int(end_x), int(end_y)), 5, color, -1)
        cv2.line(original_image, (int(start_x), int(start_y)), (int(end_x), int(end_y)), color, 2)

        # Calcular la distancia euclidiana y convertirla a píxeles para obtener la distancia en la imagen
        distance_pixels = distance.euclidean((start_x, start_y), (end_x, end_y)) / reference_object[2]
        (mid_x, mid_y) = mid_point((start_x, start_y), (end_x, end_y))
        cv2.putText(original_image, f"{distance_pixels:.1f}mm", (int(mid_x), int(mid_y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

        # Mostrar la imagen
        cv2.imshow("Image", original_image)
        cv2.waitKey(0)