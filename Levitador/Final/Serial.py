import serial
import serial.tools.list_ports
import time

class SerialController:

    def __init__(self):
        self.output = None

    def listPorts(self):
        comPorts = list(serial.tools.list_ports.comports())
        devices = [port.device for port in comPorts]
        return devices

    def selectPort(self, comPorts):
        while True:
            option = input()
            if option.lower() == 'r':
                comPorts = self.listPorts()
            elif option.isdigit() and 1 <= int(option) <= len(comPorts):
                return comPorts[int(option) - 1].device
            else:
                print("Opción inválida.")

    def readBaudRate(self):
        while True:
            baudrate = input("\nIntroduce el baud rate: ")
            if baudrate.isdigit():
                return int(baudrate)
            else:
                print("Baudrate inválido. Debe ser un número.")

    def connectPort(self, comPort, baudRate):
        try:
            connection = serial.Serial(comPort, baudRate, timeout=3)
            time.sleep(2)
            return connection
        except serial.SerialException:
            print(f"No se pudo conectar al puerto {comPort} a {baudRate} bauds/s.")
            return None

    def sendMessage(self, connection, message):
        try:
            if message.lower() == "exit":
                self.closePort(connection)
                return
            connection.write(message.encode())
        except serial.SerialException:
            print(f"No se pudo enviar el mensaje \"{message}\".")

    def readMessage(self, connection):
        """Lee mensajes del puerto serial y los pasa directamente a la gráfica."""
        while True:
            if connection.in_waiting > 0:
                message = connection.readline().decode(errors='ignore').strip()
                if message:
                    self.output = message

    def closePort(self, connection):
        try:
            connection.close()
        except serial.SerialException:
            print("No se pudo cerrar el puerto.") 
    
    def get_output(self):
        output = self.output
        self.output = None
        return output