import serial
import serial.tools.list_ports
import os
import threading

clear = lambda: os.system("cls" if os.name == "nt" else "clear")

def list_ports():
    com_ports = list(serial.tools.list_ports.comports())
    for i, com_port in enumerate(com_ports, start=1):
        print(f"[{i}] - {com_port.name}")

    print("\n[r] - Refrescar puertos")
    return com_ports

def select_port(com_ports):
    while True:
        option = input()
        if option.lower() == 'r':
            clear()
            com_ports = list_ports()
        elif option.isdigit() and 1 <= int(option) <= len(com_ports):
            return com_ports[int(option) - 1].device
        else:
            print("Opción inválida.")

def read_baudrate():
    while True:
        baudrate = input("\nIntroduce el baudrate: ")
        if baudrate.isdigit():
            return int(baudrate)
        else:
            print("Baudrate inválido. Debe ser un número.")

def connect_port(com_port, baud_rate):
    try:
        connection = serial.Serial(com_port, baud_rate, timeout=3)
        return connection
    except serial.SerialException:
        print(f"No se pudo conectar al puerto {com_port} a {baud_rate} bauds/s.")
        return None

def send_message(connection, message):
    if not connection:
        return
    try:
        if message.lower() == "exit":
            close_port(connection)
            return
        connection.write(message.encode())
    except serial.SerialException:
        print(f"No se pudo enviar el mensaje \"{message}\".")

def read_message(connection, com_port):
    while True:
        try:
            if connection.in_waiting > 0:
                print(f"{connection.readline().decode()}{com_port}> ", end="")
        except serial.SerialException:
            print("No se pudo leer el mensaje.")

def close_port(connection):
    try:
        connection.close()
        print("Puerto cerrado.")
    except serial.SerialException:
        print("No se pudo cerrar el puerto.")


if __name__ == "__main__":
    clear()
    com_ports = list_ports()
    com_port = select_port(com_ports)
    baudrate = read_baudrate()
    connection = connect_port(com_port, baudrate)

    if connection:
        clear()
        threading.Thread(target=read_message, args=(connection, com_port), daemon=True).start()

        while connection.is_open:
            message = input(f"{com_port}> ")
            send_message(connection, message)