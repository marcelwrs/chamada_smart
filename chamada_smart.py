from imutils.video import VideoStream
from pyzbar import pyzbar
import argparse
from datetime import datetime
import imutils
import time
import cv2
import requests
import json

ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", type=str, default="./records.csv", help="path to output CSV file containing barcodes")
ap.add_argument("-d", "--date", type=str, default="", help="set date and time (format=\"YYYY-MM-DD HH:MM:SS\") (default=now)")

args = vars(ap.parse_args())
if args['date']:
    args['date'] = datetime.strptime(args['date'], "%Y-%m-%d %H:%M:%S")
else:
    args['date'] = False


vs = VideoStream(src=0).start()  #Uncomment this if you are using Webcam
#vs = VideoStream(usePiCamera=True).start() # For Pi Camera

csv = open(args["output"], "a")
found = set()

while True:

    # get frame and decode for qrcodes
    frame = vs.read()
    frame = imutils.resize(frame, width=400)
    barcodes = pyzbar.decode(frame, symbols=[pyzbar.ZBarSymbol.QRCODE])
    
    # foreach barcode, extract info
    for barcode in barcodes:
    
        # display barcode info in screen
        (x, y, w, h) = barcode.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type
        text = "{} ({})".format(barcodeData, barcodeType)
        cv2.putText(frame, text, (x, y - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # if the barcode text is unknown, validate it in ruralID API
        # Then, if valid user, store its information in csv file
        if (barcodeData not in found) and (barcodeType == "QRCODE"):
        
            # consulting ruralID API
            qrdata = {'qrdata': barcodeData}
            resp = requests.post('https://www.dcc.ufrrj.br/ruralid/validateqr', qrdata)
            
            if resp.status_code == 200:
                data = json.loads(resp.text)
                if int(data['register']) > 0:
                    csv.write("{},{},{},{},{}\n".format(datetime.now(), data['name'], data['register'], data['function'], data['relationship']))
                    print('Present: ' + data['name'])
                    csv.flush()
                    
            # add code to known list
            found.add(barcodeData)

    # display image and barcode info
    cv2.imshow("Barcode Reader", frame)
    
    # exit if 'q' is pressed
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

    # sleep to reduce processing load
    time.sleep(.1)

print("[INFO] cleaning up...")
csv.close()
cv2.destroyAllWindows()
vs.stop()
