import cv2
import threading
import time
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp
from kivy.clock import Clock
from Camera import VideoProcessor
from Serial import SerialController
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ListProperty
from kivy.graphics.texture import Texture
import matplotlib.pyplot as plt
from kivy_garden.matplotlib import FigureCanvasKivyAgg

class MyBoxLayout(BoxLayout):
    pass

class MyApp(MDApp):
    options = ListProperty([])
    data_points = [] 
    time_points = [] 
    max_data_points = 50
    is_paused = False
        
    def build(self):
        self.theme_cls.primary_palette = "Blue"  
        self.theme_cls.accent_palette = "Amber"
        self.theme_cls.theme_style = "Light"
        Window.size = (900, 440) 
        self.videoProcesor = VideoProcessor()
        self.serial = SerialController()
        self.options = self.serial.listPorts()
        self.port_selected = self.options[0]
        self.connection = None

        return MyBoxLayout()
    
    def on_start(self):
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasKivyAgg(self.fig)
        self.root.ids.graph_container.add_widget(self.canvas) 

        self.fig.patch.set_facecolor('lightgray')
        self.ax.set_facecolor('lightgray')

        # Inicializa la línea de datos
        self.line, = self.ax.plot([], [], linestyle='-')
        
        self.ax.set_ylim(0, 100)
        self.ax.set_title('Real-time Data Plot')
        self.ax.set_xlabel('Time (seconds)')
        self.ax.set_ylabel('Value')

        # Programa la actualización de la gráfica y la cámara
        Clock.schedule_interval(self.update_frame, 1/500)
        Clock.schedule_interval(self.update_graph, 1/100)

    def update_graph(self, dt):
        if (not self.is_paused) and (self.connection):
            value = self.serial.get_output()

            if value:
                current_value = float(value)
                current_time = time.time() - self.start_time
                
                self.data_points.append(current_value)  
                self.time_points.append(current_time)  
                
                if len(self.data_points) > self.max_data_points:
                    self.data_points.pop(0)  
                    self.time_points.pop(0)  

                self.line.set_data(self.time_points, self.data_points)
                self.ax.set_xlim(min(self.time_points), max(self.time_points))
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
        self.connection = self.serial.connectPort(self.port_selected, 9600)
        self.videoProcesor.connection = self.connection
        if self.connection:
            self.thread = threading.Thread(target=self.serial.readMessage, args=(self.connection,))
            self.thread.daemon = True 
            self.start_time = time.time()
            self.thread.start()
            button = self.root.ids.conect_desconect_button
            button.text = "Desconectar"
        else: 
            print("No se pudo")  

    def on_desconect_port(self):
        if self.connection and self.connection.is_open:
            self.serial.closePort(self.connection)
            self.thread.join()  
            self.connection = None  
            button = self.root.ids.conect_desconect_button
            button.text = "Conectar"  
        else:
            print("No hay ninguna conexión activa.")

    def on_spinner_select(self, value):
        self.port_selected = value

    def update_frame(self, dt):
        frame = self.videoProcesor.get_frame()

        if not frame is None:

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

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
            message = "R" + str(self.root.ids.slider.value) + "\n"

            self.reference_value = self.root.ids.slider.value
            self.reference_points = [self.reference_value] * self.max_data_points
            x_line = list(range(1, self.max_data_points + 1))

            if hasattr(self, 'reference_line'):
                self.reference_line.remove()

            self.reference_line, = self.ax.plot(x_line, self.reference_points, linestyle='--', color='red', label='Referencia')
            self.canvas.draw()

            print(message)
            self.serial.sendMessage(self.connection, message)

       
