import cv2
import glob
import time

DELAY = 0.04 # Delay in s zwischen einzelnen Bildern


def zeige(folder):
    """
    Bilder des Formats .bmp aus Ordner anzeigen
    :param folder: Ordnername
    """
    images = sorted(glob.glob(f'{folder}/*.bmp'))
    if len(images) == 0:
        images = sorted(glob.glob(f'{folder}/*.tiff'))
    for fname in images:
        frame = cv2.imread(fname)

        cv2.imshow('tracking', frame)

        time.sleep(DELAY)

        # Auf User-Eingaben reagieren
        key = cv2.waitKey(1)
        if key == ord('q'):
            print(fname)
            exit()
        elif key == ord('n'):
            return False
        elif key == ord('p'):
            print('pause')
            cv2.waitKey(-1)
            print('weiter')


if __name__ == '__main__':
    ordner = sorted(glob.glob('202*'))
    zeige(ordner[-1])
    """for ordn in ordner:
        print(ordn)
        zeige(ordn)"""