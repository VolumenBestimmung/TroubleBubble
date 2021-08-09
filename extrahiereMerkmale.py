import cv2
import glob
import csv
import os


def getCoord(blb):
    """
    Funktion zur Berechnung der Koordinaten eines BLOBs als Liste mit [xmin, ymin, xmax, ymax]
    :param blb: BLOB
    :return: [xmin, ymin, xmax, ymax]
    """
    x_min, y_min, w, h = cv2.boundingRect(blb)
    return [x_min, y_min, x_min + w, y_min + h]


def writeInFile(inp):
    with open('extrahierteMerkmale.csv', 'a', newline='') as f:
        writer = csv.writer(f, delimiter=",")
        writer.writerow([inp])


def extrahiere(folder):
    ml = float(folder.split('_')[3].split('m')[0].replace('-', '.')) * 1000
    bg = cv2.createBackgroundSubtractorMOG2(detectShadows=False, varThreshold=40, history=0)
    fnames = sorted(glob.glob(f'{folder}/*.bmp'))
    if len(fnames) == 0:
        fnames = sorted(glob.glob(f'{folder}/*.tiff'))

    for fname in fnames:
        frame = cv2.imread(fname)

        # Vorverarbeitung:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.bilateralFilter(frame, 5, 75, 75)

        # Anwenden der Hintergrundsubtraktion:
        fgmask = bg.apply(frame)

        # Druck und Zeit aus Bildernamen extrahieren
        try:
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
                # BLOBs zwischen 700 und 800 Pixeln herausfiltern
                if (mid_x in range(700, 800)) & (mid_y in range(10, 75)):
                    perimeter = cv2.arcLength(blobs[i], True)
                    rundh = int(1000 * (4 * 3.14 * area) / (perimeter ** 2))
                    inp = f"{int(ml)};{int(area)};{druck};{rundh};{int(area*area)};{int(area*druck)}"
                    writeInFile(inp)
                    print(inp)


if __name__ == '__main__':
    writeInFile(f"ml;flaeche;druck;rundheit;flaecheHoch2;flaecheMalDruck")
    ordner = glob.glob('202*')

    for uo in ordner:
        extrahiere(uo)
