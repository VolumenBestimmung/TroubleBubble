from datetime import datetime
from pypylon import pylon
import nimmAuf
import smbus2
import os
import argparse
import zeigeBilder


# Argumente parsen (bei Aufruf im Terminal z.B. 'starteMessung.py -n 100' eingeben)
ap = argparse.ArgumentParser(description="""Skript zum Aufnehmen von Bildern der Teststrecke und der 
                                            Volumenbestimmung von Luftblasen""")
ap.add_argument("-n", "--number", default=100, type=int, help="Anzahl an Frames die aufgenommen werden sollen")
ap.add_argument("-fr", "--framerate", default=100, type=int, help="Framerate in fps")

ap.add_argument("-inj", "--injektor", default='kol', type=str, help="kol: Kolbeninjektor, km: Kontrastmittelinj, spr: Spritze")
ap.add_argument("-vol", "--volumen", default='0.3', type=str, help="Volumen in ml")
ap.add_argument("-fl", "--flow", default=3, type=int, help="Flow in ml/s")
ap.add_argument("-kan", "--kanuele", default=20, type=int, help="Kanuele (16 = 16G, 20 = 20G)")

args = vars(ap.parse_args())

# Argumente des Parsers extrahieren
numberOfImagesToGrab = args['number']
framerate = args['framerate']
kanuele = args['kanuele']

fl = args['flow']
volu = str(args['volumen']).replace('.','-').replace(',','-')
inj = args['injektor']


if __name__ == '__main__':
    #Test ob Kamera angeschlossen
    try:
        cam = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        cam.Open()
        cam.Close()
    except:
        print("Keine Kamera angeschlossen oder Kamera woanders geöffnet.")
        exit()
    # Test ob Drucksensor angeschlossen
    try:
        bus = smbus2.SMBus(0)
        bus.read_i2c_block_data(0x40, 0, 2)  # 2 Bytes empfangen
    except OSError:
        print("Kein Drucksensor angeschlossen")
        exit()
    dirname = f'{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}_{inj}_{fl}mls_{volu}ml_{kanuele}G'

    os.mkdir(dirname)

    nimmAuf.starte(dirname, numberOfImagesToGrab, framerate)
    print("Aufnahme beendet")

    zeigeBilder.zeige(dirname)
