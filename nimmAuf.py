from pypylon import pylon
from datetime import datetime
import cv2
import os
import smbus2
import time

druckwert = 0
i = 0
beginn = 0
FAKTOR = 40.96
directoryname = ''
zeitoffset = 0


class ImageHandler(pylon.ImageEventHandler):
    """
    Event Handler: immer wenn ein Bild "ankommt", wird Funktion OnImageGrabbed ausgeführt
    """

    def __init__(self):
        super().__init__()

    def OnImageGrabbed(self, cam, grabResult):

        global i
        global beginn
        try:
            if grabResult.GrabSucceeded():
                if i == 0:  # Beim ersten Bild wird Zeit gespeichert
                    beginn = grabResult.TimeStamp
                img = grabResult.Array
                # Bild abspeichern; Zero-Padding damit Name gleich lang
                zeit = zeitoffset + int((grabResult.TimeStamp - beginn) / 1000000)
                cv2.imwrite(f"{directoryname}/{zeit:06d}-{druckwert:04d}.bmp", img)
            else:
                raise RuntimeError(
                    "Bild konnte nicht empfangen werden. Eventuell ist die Framerate zu hoch oder die Kamera überhitzt.")
        except Exception as e:
            print(f"Fehler: {e}")

        i += 1


def setCameraParameters(cam, frate):
    """
    Funktion zum Einstellen der Parameter der Basler-Kamera; Außer der Framerate sind alle Parameter fest.
    :param cam: Instanz einer geöffneten Kamera
    :param frate: Framerate in fps
    """
    cam.AcquisitionFrameRateEnable = True
    cam.AcquisitionFrameRate.SetValue(frate)

    cam.ExposureTime.SetValue(300.0)

    cam.Width.SetValue(1900)
    cam.Height.SetValue(100)
    cam.OffsetY.SetValue(670)
    cam.OffsetX.SetValue(32)


def backGroundLoop(cam, numberOfImagesToGrab, bus, startzeit):
    """
    Background-Loop zum Sammeln von Bildern
    :param cam: Instanz einer geöffneten Kamera
    :param numberOfImagesToGrab: Anzahl der aufzunehmenden Bildern
    :param bus: I2C-Bus zum Auslesen des Drucks
    """
    # Image Event Handler zuweisen
    handler = ImageHandler()
    cam.RegisterImageEventHandler(handler, pylon.RegistrationMode_ReplaceAll, pylon.Cleanup_None)

    print("los")

    cam.StartGrabbingMax(numberOfImagesToGrab, pylon.GrabStrategy_LatestImages, pylon.GrabLoop_ProvidedByInstantCamera)
    global zeitoffset
    zeitoffset = int((time.time() - startzeit) * 1000)

    while cam.IsGrabbing():
        # solange Kamera aufnimmt, wird der Druckwert vom Arduino mit I2C abgefragt und in globale Variable gespeichert
        global druckwert
        try:
            byte1, byte2 = bus.read_i2c_block_data(0x40, 0, 2)  # 2 Bytes empfangen
            druckwert = (byte1 + (byte2 << 8))  # hohes Byte shiften und Bytes addieren
        except:
            print("Fehler beim Druck auslesen.")
            cam.Close()
            exit()

    cam.StopGrabbing()
    cam.Close()  # Kamera immer schließen, sonst kann nicht mehr drauf zugegriffen werden
    cam.DeregisterImageEventHandler(handler)  # Wichtig: Event Handler wieder entfernen


def starte(namedir, anzahlBilder=10, framerate=100, start=0.0):
    """
    Funktion zum Starten der Messung
    :param namedir: Name des Ordners in dem Bilder abgespeichert werden sollen; muss schon existieren
    :param anzahlBilder: Anzahl der aufzunehmenden Bilder
    :param framerate: Framerate in fps
    """
    bus = smbus2.SMBus(0)  # Instanz eines I2C-Busses zur Kommunikation mit dem Arduino anlegen
    global directoryname
    directoryname = namedir

    cam = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())  # Instanz der Kamera anlegen
    cam.Open()
    setCameraParameters(cam, framerate)

    backGroundLoop(cam, anzahlBilder, bus, start)


if __name__ == '__main__':
    # Ordner erstellen mit aktuellem Datum
    dirname = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    bus = smbus2.SMBus(0)
    starte(dirname, 10, 100, 0.0)