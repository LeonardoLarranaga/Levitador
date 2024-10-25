import time
import os
#os.environ["KIVY_NO_CONSOLELOG"] = "1"
import cv2
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.properties import ListProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy_garden.matplotlib import FigureCanvasKivyAgg
from kivymd.app import MDApp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from Camera import VideoProcessor
from Serial import SerialController

class ImageButton(ButtonBehavior, Image):
    pass

class MyBoxLayout(BoxLayout):
    pass

class MyApp(MDApp):
    options = ListProperty([])
    data_points = [] 
    time_points = [] 
    max_time_points = 10 # Y
    max_data_points = 500 # X
    is_paused = False
    max_distance = NumericProperty(100)

    def build(self):
        self.theme_cls.primary_palette = "Blue"  
        self.theme_cls.accent_palette = "Amber"
        self.theme_cls.theme_style = "Light"
        Window.size = (900, 440) 
        self.videoProcesor = VideoProcessor(main_ui_instance=self)
        self.serial = SerialController()
        self.options = self.serial.listPorts()
        self.port_selected = self.options[0]
        self.connection = None
        self.title = "Levitador de Pelota"
        self.frame = None
        self.distance = None

        layout = MyBoxLayout()
        slider = layout.ids.slider
        self.bind(max_distance=lambda instance, value: setattr(slider, 'max', value))
        self.start_time = time.time()
        return layout

    def update_max_distance(self, new_max):
        self.max_distance = new_max

    def on_start(self):
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasKivyAgg(self.fig)
        self.root.ids.graph_container.add_widget(self.canvas)

        self.fig.patch.set_facecolor('lightgray')
        self.ax.set_facecolor('lightgray')

        # Inicializa la línea de datos
        self.line, = self.ax.plot([], [], linestyle='-')

        self.ax.set_ylim(0, 1000)
        self.ax.set_title('Posición de la pelota')
        self.ax.set_xlabel('Tiempo (s)')
        self.ax.set_ylabel('Altura (mm)')
        self.ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        # Programa la actualización de la gráfica y la cámara
        Clock.schedule_interval(self.update_frame, 1 / 500)
        Clock.schedule_interval(self.update_graph, 1 / 100)

        # Inicializar los datos con None hasta tener 100 puntos
        self.data_points = [0]
        self.time_points = [0]
        self.start_time = time.time()

    def update_graph(self, dt):
        if not self.is_paused:
            current_value = self.distance
            current_time = time.time() - self.start_time

            # Añadir el nuevo valor en el primer índice
            self.data_points.append(current_value)
            self.time_points.append(current_time)

            # Esté código hace lo siguiente:
            # if len(self.data_points) > self.max_data_points:
            #     self.data_points.pop(0)
            #     self.time_points.pop(0)
            if len(self.data_points) > self.max_data_points:
                self.data_points.pop(0)
                self.time_points.pop(0)

            self.line.set_data(self.time_points, self.data_points)

            # Ajustar límites del eje X
            self.ax.set_xlim(min(self.time_points), max(self.time_points))

            # Ajustar automáticamente el eje Y
            self.ax.relim()
            self.ax.autoscale_view()

            valid_data = list(filter(None, self.data_points))
            if valid_data:
                self.ax.set_ylim(min(valid_data), max(valid_data))
            else:
                self.ax.set_ylim(0, self.max_data_points)

            self.canvas.draw()

    def on_conect_desconect_port(self):
        if self.connection:
            self.on_desconect_port()
        else:
            self.on_conect_port()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        button = self.root.ids.pause_play_button
        if self.is_paused:
            button.text = "Play"  
        else:
            button.text = "Pausa"
    
    def clear_ploot(self):
        self.data_points.clear()
        self.time_points.clear()
        self.line.set_data(self.time_points, self.data_points)
        self.canvas.draw()

    def update_ports(self):
        self.options = self.serial.listPorts()

    def on_conect_port(self):
        self.connection = self.serial.connectPort(self.port_selected, 115200)
        self.videoProcesor.connection = self.connection
        if self.connection:
            button = self.root.ids.conect_desconect_button
            button.text = "Desconectar"

    def on_desconect_port(self):
        if self.connection and self.connection.is_open:
            self.serial.closePort(self.connection)
            self.connection = None
            button = self.root.ids.conect_desconect_button
            button.text = "Conectar"  
        else:
            print("No hay ninguna conexión activa.")

    def on_spinner_select(self, value):
        self.port_selected = value

    def update_frame(self, dt):

        if not self.frame is None:
            frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            frame = cv2.flip(frame, 0)

            # Crea un Texture a partir del frame
            texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
            texture.blit_buffer(frame.tobytes(), colorfmt='rgb', bufferfmt='ubyte')

            # Asigna el Texture al widget Image
            self.root.ids.image_display.texture = texture
       

    def on_stop(self):
        # Libera la cámara al cerrar la aplicación
        self.videoProcesor.stop()

    def update_text_input(self, value):
        self.root.ids.text_input.text = '%.2f' % value

    def update_slider(self, value):
        try:
            value = float(value)
            if 0 <= value <= 100: 
                self.root.ids.slider.value = value  
        except ValueError:
            pass  

    def on_button_press(self):
        if self.connection:
            message = f"R{self.root.ids.slider.value:.2f}\n"
            self.reference_value = self.root.ids.slider.value
            self.reference_points = [self.reference_value] * self.max_time_points
            x_line = list(range(1, self.max_time_points + 1))

            if hasattr(self, 'reference_line'):
                self.reference_line.remove()

            self.reference_line, = self.ax.plot(x_line, self.reference_points, linestyle='--', color='red', label='Referencia')
            self.canvas.draw()

            self.serial.sendMessage(self.connection, message)

    def on_refresh_videoProcesor(self):
        self.videoProcesor.first_frame = None
        self.videoProcesor.pixels_per_metric = None            

       
if __name__ == "__main__":
    MyApp().run()
