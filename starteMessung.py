from datetime import datetime
from pypylon import pylon
import nimmAuf
import smbus2
import os
import argparse
import object_track
from threading import Thread
import time


programmstart = time.time()
# Argumente parsen (bei Aufruf im Terminal z.B. 'starteMessung.py -n 100' eingeben)
ap = argparse.ArgumentParser(description="""Skript zum Aufnehmen von Bildern der Teststrecke und der 
                                            Volumenbestimmung von Luftblasen""")
ap.add_argument("-n", "--number", default=400, type=int, help="Anzahl an Frames die aufgenommen werden sollen")
ap.add_argument("-fr", "--framerate", default=100, type=int, help="Framerate in fps")


args = vars(ap.parse_args())

# Argumente des Parsers extrahieren
numberOfImagesToGrab = args['number']
framerate = args['framerate']


if __name__ == '__main__':
    startzeit = time.time()
    #Test ob Kamera angeschlossen ist
    try:
        cam = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        cam.Open()
        cam.Close()
    except: # genaue Art der Exception kennt Python nicht, deshalb nicht genauer spezifiziert
        print("Keine Kamera angeschlossen oder Kamera woanders geöffnet.")
        exit()

    # Test ob Drucksensor angeschlossen ist
    try:
        bus = smbus2.SMBus(0)
        bus.read_i2c_block_data(0x40, 0, 2)  # 2 Bytes empfangen
    except OSError:
        print("Kein Drucksensor angeschlossen")
        exit()
    # Aus der aktuellen Zeit und den Parametern einen individuellen Ordnernamen generieren
    dirname = f'{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}'

    os.mkdir(dirname)
    beginn = time.time()-programmstart

    # Threads zum Aufnehmen und Verarbeiten starten
    t_aufnahme = Thread(target=nimmAuf.starte, args=(dirname, numberOfImagesToGrab, framerate, startzeit))
    t_tracke = Thread(target=object_track.tracke, args=(dirname, numberOfImagesToGrab))

    t_aufnahme.start()
    t_tracke.start()
    t_aufnahme.join()
    t_tracke.join()