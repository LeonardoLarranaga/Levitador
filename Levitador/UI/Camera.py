import imutils
import time
import cv2
import threading

from kivy.clock import Clock

from Serial import SerialController

from imutils.video import VideoStream
from scipy.spatial import distance

def mid_point(point_a, point_b):
    return (point_a[0] + point_b[0]) / 2.0, (point_a[1] + point_b[1]) / 2.0

class VideoProcessor:
    def __init__(self, ball_size=40, reference_pixel=(0, 0), main_ui_instance=None):
        self.video_stream = VideoStream(src=1).start()
        time.sleep(2.0)  # Permitir que la cámara se caliente

        self.ball_size = ball_size  # Tamaño de la pelota en mm
        self.reference_pixel = reference_pixel
        self.pixels_per_metric = None
        self.first_frame = None
        self.previous_time = 0
        self.blue_color = (180, 130, 70)

        # Cola para enviar datos
        self.frame = None
        self.fps_imutils = None

        self.serialController = SerialController()
        self.main_ui_instance = main_ui_instance
        self.max_distance = None
        self.min_distance = None

        # Hilo para procesar video
        self.thread = threading.Thread(target=self.process_video)
        self.thread.daemon = True
        self.thread.start()
        self.connection = None

    def process_video(self):
        cropped_x, cropped_y, cropped_width, cropped_height = 0, 0, 0, 0
        distance_to_reference = 0
        while True:
            original_frame = self.video_stream.read()

            if original_frame is None:
                continue

            if cropped_width == 0:
                frame_height, frame_width = original_frame.shape[:2]
                cropped_x = int((frame_width - cropped_width) / 4)
                cropped_y = 0
                cropped_width = int(frame_width / 1.8)
                cropped_height = frame_height

            # Recorta el frame original según la región de interés
            cropped_frame = original_frame[cropped_y:cropped_y + cropped_height, cropped_x:cropped_x + cropped_width]

            # Crear una copia redimensionada del frame para el procesamiento
            resized_frame = imutils.resize(cropped_frame, width=500)

            clean_frame = cropped_frame.copy()

            gray = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (33, 33), 0)

            if self.first_frame is None:
                self.first_frame = gray
                self.reference_pixel = (int(cropped_frame.shape[1] / 2), cropped_frame.shape[0])
                continue

            # Calcula la diferencia entre frames
            frame_delta = cv2.absdiff(self.first_frame, gray)
            threshold = cv2.threshold(frame_delta, 22, 255, cv2.THRESH_BINARY)[1]
            threshold = cv2.dilate(threshold, None, iterations=2)

            contours = cv2.findContours(threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = imutils.grab_contours(contours)

            found_valid_contour = False

            for contour in contours:
                area = cv2.contourArea(contour)

                # Calcular el rectángulo delimitador del contorno
                x, y, w, h = cv2.boundingRect(contour)

                # Definir límites de área y altura
                if area < 450:
                    continue

                found_valid_contour = True

                # Procesar el contorno
                (x, y, width, height) = cv2.boundingRect(contour)
                scale_factor = cropped_frame.shape[1] / resized_frame.shape[1]
                (x, y, width, height) = (int(x * scale_factor), int(y * scale_factor), int(width * scale_factor), int(height * scale_factor))

                cv2.rectangle(clean_frame, (x, y), (x + width, y + height), (0, 255, 0), 2)

                ((center_x, center_y), radius) = cv2.minEnclosingCircle(contour)
                center_x, center_y = int(center_x * scale_factor), int(center_y * scale_factor)

                if self.pixels_per_metric is None:
                    self.pixels_per_metric = radius * 2 / self.ball_size

                # Calcular la distancia
                distance_to_reference = distance.euclidean((center_x, center_y), self.reference_pixel)
                distance_to_reference /= self.pixels_per_metric * scale_factor
                self.main_ui_instance.distance = distance_to_reference
                if self.max_distance is None and distance_to_reference is not None or distance_to_reference > self.max_distance:
                    self.max_distance = distance_to_reference
                    Clock.schedule_once(lambda dt: setattr(self.main_ui_instance, 'max_distance', float(self.max_distance)))
                elif not self.connection:
                    self.max_distance = 0
                    Clock.schedule_once(lambda dt: setattr(self.main_ui_instance, 'max_distance', float(self.max_distance)))

                if self.min_distance is None and distance_to_reference is not None or distance_to_reference < self.min_distance:
                    self.min_distance = distance_to_reference
                    Clock.schedule_once(lambda dt: setattr(self.main_ui_instance, 'min_distance', float(self.min_distance)))

                    if not self.connection:
                        self.min_distance = 0
                        Clock.schedule_once(lambda dt: setattr(self.main_ui_instance, 'min_distance', float(self.min_distance)))

                if self.connection:
                    message = f"{distance_to_reference:.2f}\n"
                    self.serialController.sendMessage(self.connection, message)

                cv2.circle(clean_frame, (center_x, center_y), 5, self.blue_color, -1)
                cv2.line(clean_frame, (center_x, center_y), self.reference_pixel, self.blue_color, 2)
                mid_x, mid_y = mid_point((center_x, center_y), self.reference_pixel)
                cv2.putText(clean_frame, f"{distance_to_reference:.2f} mm", (int(mid_x), int(mid_y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.0, self.blue_color, 2)

            # Calcula y dibuja FPS
            current_time = time.time()
            time_difference = current_time - self.previous_time
            fps = 1 / time_difference
            self.previous_time = current_time

            fpsText = f"FPS: {fps:.2f}"
            cv2.putText(clean_frame, fpsText, (cropped_frame.shape[1] - 200, 50), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 2)

            self.main_ui_instance.frame = clean_frame

            if not found_valid_contour and self.connection and distance_to_reference < self.max_distance * 0.2:
                self.serialController.sendMessage(self.connection, "0.0\n")
                self.main_ui_instance.distance = 0


    def stop(self):
        self.video_stream.stop()