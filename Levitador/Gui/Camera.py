import imutils
import time
import cv2
from imutils.video import VideoStream
from scipy.spatial import distance
import threading
from Serial import SerialController

class VideoProcessor:
    def __init__(self, ball_size=40, reference_pixel=(0, 0)):
        self.video_stream = VideoStream(src=0).start()
        time.sleep(2.0)  # Permitir que la cámara se caliente

        self.ball_size = ball_size  # Tamaño de la pelota en mm
        self.reference_pixel = reference_pixel
        self.pixels_per_metric = None
        self.first_frame = None
        self.previous_time = 0
        self.blue_color = (180, 130, 70)

        # Cola para enviar datos
        self.frame = None

        self.serialController = SerialController()

        # Hilo para procesar video
        self.thread = threading.Thread(target=self.process_video)
        self.thread.daemon = True
        self.thread.start()
        self.connection = None

    def mid_point(self, point_a, point_b):
        return (point_a[0] + point_b[0]) / 2.0, (point_a[1] + point_b[1]) / 2.0

    def process_video(self):
        while True:
            original_frame = self.video_stream.read()
            if original_frame is None:
                continue

            # Procesamiento de la imagen
            resized_frame = imutils.resize(original_frame, width=500)
            clean_frame = original_frame.copy()
            gray = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (23, 23), 0)

            if self.first_frame is None:
                self.first_frame = gray
                continue

            # Calcula la diferencia entre frames
            frame_delta = cv2.absdiff(self.first_frame, gray)
            threshold = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            threshold = cv2.dilate(threshold, None, iterations=2)

            contours = cv2.findContours(threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contours = imutils.grab_contours(contours)

            distances_to_reference = []

            for contour in contours:
                if cv2.contourArea(contour) < 250:
                    continue

                # Procesar el contorno
                (x, y, width, height) = cv2.boundingRect(contour)
                scale_factor = original_frame.shape[1] / resized_frame.shape[1]
                (x, y, width, height) = (int(x * scale_factor), int(y * scale_factor), int(width * scale_factor), int(height * scale_factor))

                cv2.rectangle(clean_frame, (x, y), (x + width, y + height), (0, 255, 0), 2)

                ((center_x, center_y), radius) = cv2.minEnclosingCircle(contour)
                center_x, center_y = int(center_x * scale_factor), int(center_y * scale_factor)

                if self.pixels_per_metric is None:
                    self.pixels_per_metric = radius * 2 / self.ball_size

                # Calcular la distancia
                distance_to_reference = distance.euclidean((center_x, center_y), self.reference_pixel)
                distance_to_reference /= self.pixels_per_metric * scale_factor
                distances_to_reference.append(distance_to_reference)

                cv2.circle(clean_frame, (center_x, center_y), 5, self.blue_color, -1)
                cv2.line(clean_frame, (center_x, center_y), self.reference_pixel, self.blue_color, 2)
                mid_x, mid_y = self.mid_point((center_x, center_y), self.reference_pixel)
                cv2.putText(clean_frame, f"{distance_to_reference:.2f} mm", (int(mid_x), int(mid_y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.0, self.blue_color, 2)

            # Calcula y dibuja FPS
            current_time = time.time()
            if (current_time - self.previous_time) != 0:
                fps = 1 / (current_time - self.previous_time)
                self.previous_time = current_time
                fpsText = f"FPS: {fps:.2f}"
                cv2.putText(clean_frame, fpsText, (original_frame.shape[1] - 200, 50), cv2.FONT_HERSHEY_DUPLEX, 1.0, (0, 0, 0), 2)

            # Envía los datos a la cola
            self.frame = clean_frame

            if self.connection:
                message = "C" + str(distances_to_reference[0]) + "\n"
                self.serialController.sendMessage(self.connection, message)
            
    def get_frame(self):
        output = self.frame
        self.frame = None
        return output

    def stop(self):
        self.video_stream.stop()