import cv2
import glob
import time
from tracker import Tracker
import numpy as np


def getCoord(blb):
    """
    Funktion zur Berechnung der Koordinaten eines BLOBs als Liste mit [xmin, ymin, xmax, ymax]
    :param blb: BLOB (Rückgabe von cv2.findContours)
    :return: [xmin, ymin, xmax, ymax]
    """
    x_min, y_min, w, h = cv2.boundingRect(blb)
    return [x_min, y_min, x_min + w, y_min + h]


def getVolume(flaeche, druck, rundheit):
    """
    Funktion zur Berechnung des Volumens aus der Fläche, dem Druck und der Rundheit
    :param flaeche: Fläche des segmentieren BLOBs in Pixeln
    :param druck: nicht umgerechneter Relativdruck (d.h. Wert zw. 0 und 1024)
    :param rundheit: Rundheit
    :return: Volumen in µl
    """
    offset = -18.633
    coeffFlaeche = 0.011229
    coeffDruck = -0.066281
    coeffKompr = 0.014264
    coeffFlaeche2 = 1.9009e-08
    coeffFlaecheDruck = 0.00026487
    vol = offset + coeffFlaeche * flaeche + coeffDruck * druck + coeffKompr * rundheit + coeffFlaeche2 * flaeche * flaeche + coeffFlaecheDruck * flaeche * druck

    return vol


def tracke(folder, anzahlInsgesamt):
    """
    Funktion zum Tracken und zur Volumenberechnung von Bildsequenzen
    :param folder: Pfad des Ordners mit den zu verarbeitenden Bildern
    :param anzahlInsgesamt: Anzahl der zu verarbeitenden Bilder
    """
    anzahlVerarbeiteterBilder = 0
    gesamtvolumen = 0
    bg = cv2.createBackgroundSubtractorMOG2(detectShadows=False, varThreshold=40, history=0)
    tracker = Tracker(150, 1)  # Tracker-Objekt initialisieren
    print("Zeit_in_s;Volumen_in_ul;Relativdruck_in_bar")
    while anzahlVerarbeiteterBilder < anzahlInsgesamt:

        fnames = sorted(glob.glob(f'{folder}/*.bmp'))
        if len(fnames) == 0:
            fnames = sorted(glob.glob(f'{folder}/*.tiff'))

        if len(fnames) > anzahlVerarbeiteterBilder:
            try:
                fname = fnames[anzahlVerarbeiteterBilder]
            except IndexError:
                time.sleep(0.01)
                return False

            frame = cv2.imread(fname)
            anzahlVerarbeiteterBilder += 1
            # Vorverarbeitung:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame = cv2.bilateralFilter(frame, 5, 75, 75)

            # Anwenden der Hintergrundsubtraktion:
            fgmask = bg.apply(frame)

            centers = np.empty((0, 2), float)  # Mittelpunkte der BLOBs im aktuellen Frame; zu Beginn leere Matrix

            # Druck und Zeit aus Bildernamen extrahieren
            try:
                zeit = int(fname[-15:].split('-')[0])
                druck = int(fname.split('-')[-1].split('.')[0])
            except ValueError:
                print("Format des Bildnamens stimmt nicht")
                return False

            blobs, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)  # Konturen extrahieren aus Maske

            for i in range(len(blobs)):
                area = cv2.contourArea(blobs[i])
                if area > 200:  # kleine BLOBs herausfiltern
                    coords = getCoord(blobs[i])  # Form: [x_min, y_min, x_max, y_max]
                    mid_y = int((coords[1] + coords[3]) / 2)  # Ungefährer Mittelpunkt (Schneller als durch Momente)
                    mid_x = int((coords[0] + coords[2]) / 2)
                    # BLOBs am Rand herausfilten
                    if (coords[0] > 150) & (coords[2] < 1600) & (mid_y in range(10, 75)):

                        # Wenn alle Voraussetzungen erfüllt sind, das Volumen berechnen
                        perimeter = cv2.arcLength(blobs[i], True)
                        rundh = int(1000 * (4 * 3.14 * area) / (perimeter ** 2))
                        vol = getVolume(area, druck, rundh)
                        # y-Koordinate bleibt ohnehin gleich: Dem Tracker die x-Koordinate und das Volumen übergeben
                        centers = np.append(centers, np.array([[mid_x, vol]]), axis=0)

            if len(centers) > 0:
                tracker.update(centers)  # Tracker updaten mit den extrahierten Mittelpunkten

                for j in range(len(tracker.tracks)):
                    if not len(tracker.tracks[j].trace) == 0:
                        x = int(tracker.tracks[j].trace[-1][0, 0])
                        # Wenn ein BLOB weit genug links ist, wird er als "Draußen" gekennzeichnet
                        if x < 800 and not tracker.tracks[j].isOut:
                            tracker.tracks[j].isOut = True  # Kennzeichnen, dass bereits draußen
                            v = tracker.tracks[j].trace[-1][0][1]  # Volumen der Blase zu aktuellem Zeitpunkt
                            gesamtvolumen += v

                        # Falls Blase weit rechts ist, sicherstellen, dass sie noch nicht als draußen gekennzeichnet wurde
                        elif x > 1200 and tracker.tracks[j].isOut:
                            tracker.tracks[j].isOut = False

            print(f"{zeit};{gesamtvolumen:.2f};{druck / 41:.2f}")

    print(f"Fertig! Gesamtvolumen: {gesamtvolumen:.2f} µl")


if __name__ == '__main__':
    ordn = glob.glob(f"JetsonTest/0-1ml_1mls_18G_kol_Test/2021-*")[-1]
    names = sorted(glob.glob(f'{ordn}/*.bmp'))
    if len(names) == 0:
        names = sorted(glob.glob(f'{ordn}/*.tiff'))

    anz = tracke(ordn, len(names))
