from scipy.spatial import distance
from imutils import perspective
from imutils import contours as imutils_contours
import numpy
import argparse
import imutils
import cv2

# Calcular el punto medio entre dos puntos
def mid_point(point_a, point_b):
    return (point_a[0] + point_b[0]) * 0.5, (point_a[1] + point_b[1]) * 0.5

# Argumentos
argumet_parser = argparse.ArgumentParser()
argumet_parser.add_argument("-i", "--image", required=True, help="path to the input image")
argumet_parser.add_argument("-w", "--width", type=float, required=True, help="width of the left-most object in the image")
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
pixels_per_metric = None

# Iterar sobre los contornos
for contour in contours:
    # Si el contorno no es lo suficientemente grande, ignorarlo, probablemente es ruido
    if cv2.contourArea(contour) < 100:
        continue

    # Calcular el rectángulo delimitador del contorno y usarlo para calcular las dimensiones del objeto
    original_image = image.copy()
    box = cv2.minAreaRect(contour)
    box = cv2.boxPoints(box)
    box = numpy.array(box, dtype="int")

    # Ordenar los puntos del contorno para que aparezcan en sentido horario y luego dibujalo
    box = perspective.order_points(box)
    cv2.drawContours(original_image, [box.astype("int")], -1, (0, 255, 0), 2)

    # Iterar sobre los puntos del contorno y dibujarlos
    for (x, y) in box:
        cv2.circle(original_image, (int(x), int(y)), 5, (0, 0, 255), -1)

    # Extraer los puntos del contorno y calcular las dimensiones del objeto
    (top_left, top_right, bottom_right, bottom_left) = box
    # Calculamos la distancia euclidiana entre el punto superior izquierdo y el punto superior derecho
    (top_left_top_right_x, top_left_top_right_y) = mid_point(top_left, top_right)
    (bottom_left_bottom_right_x, bottom_left_bottom_right_y) = mid_point(bottom_left, bottom_right)

    # Calculamos la distancia euclidiana entre las diagonales del objeto
    (top_left_bottom_left_x, top_left_bottom_left_y) = mid_point(top_left, bottom_left)
    (top_right_bottom_right_x, top_right_bottom_right_y) = mid_point(top_right, bottom_right)

    # Dibujar los puntos
    cv2.circle(original_image, (int(top_left_top_right_x), int(top_left_top_right_y)), 5, (255, 0, 0), -1)
    cv2.circle(original_image, (int(bottom_left_bottom_right_x), int(bottom_left_bottom_right_y)), 5, (255, 0, 0), -1)
    cv2.circle(original_image, (int(top_left_bottom_left_x), int(top_left_bottom_left_y)), 5, (255, 0, 0), -1)
    cv2.circle(original_image, (int(top_right_bottom_right_x), int(top_right_bottom_right_y)), 5, (255, 0, 0), -1)

    # Dibujar las líneas
    cv2.line(original_image, (int(top_left_top_right_x), int(top_left_top_right_y)), (int(bottom_left_bottom_right_x), int(bottom_left_bottom_right_y)), (255, 0, 255), 2)
    cv2.line(original_image, (int(top_left_bottom_left_x), int(top_left_bottom_left_y)), (int(top_right_bottom_right_x), int(top_right_bottom_right_y)), (255, 0, 255), 2)

    # Calcular la distancia euclidiana entre los puntos y luego encontrar la relación de píxeles por métrica
    distance_a = distance.euclidean((top_left_top_right_x, top_left_top_right_y), (bottom_left_bottom_right_x, bottom_left_bottom_right_y))
    distance_b = distance.euclidean((top_left_bottom_left_x, top_left_bottom_left_y), (top_right_bottom_right_x, top_right_bottom_right_y))

    # Si la relación de píxeles por métrica es nula, inicializarla
    if pixels_per_metric is None:
        pixels_per_metric = distance_b / arguments["width"]

    # Calcular las dimensiones del objeto
    dimension_a = distance_a / pixels_per_metric
    dimension_b = distance_b / pixels_per_metric

    # Dibujar las dimensiones en la imagen
    cv2.putText(original_image, "{:.1f}mm".format(dimension_a), (int(top_left_top_right_x - 15), int(top_left_top_right_y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    cv2.putText(original_image, "{:.1f}mm".format(dimension_b), (int(top_right_bottom_right_x + 10), int(top_right_bottom_right_y)), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

    # Mostrar la imagen
    cv2.imshow("Image", original_image)
    cv2.waitKey(0)