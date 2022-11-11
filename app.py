import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import CircleModuleDrawer
import cv2
import imutils
from PIL import Image
from flask import *
from tempfile import NamedTemporaryFile
from shutil import copyfileobj
from os import remove
import time
import numpy as np


# Create a QR code with the given data, style (dark/light) and width (height is automatically calculated) (optional)
def makeqrcode(text, style, width=0):
    qrcodesize = 1800
    version = 2
    bsize = qrcodesize // (17 + 4 * version)

    # create qr code
    qr = qrcode.QRCode(
        version=version,
        box_size=bsize,
        border=0,
    )
    qr.add_data(text)
    img = qr.make_image(fill_color="white", back_color="red", image_factory=StyledPilImage,
                        module_drawer=CircleModuleDrawer())
    img.save("./temp/qr.png", "PNG")
    image = cv2.imread("./temp/qr.png")
    # add alpha channel
    image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

    # convert all white pixels to transparent pixels
    image[image[:, :, 0] > 100] = [0, 0, 0, 0]

    # erase x=0 to x=350 and y=0 to y=350
    image[0:7 * bsize, 0:7 * bsize] = [0, 0, 0, 0]
    # erase x=0 to x=-350 and y=0 to y=350
    image[0:7 * bsize, -7 * bsize:] = [0, 0, 0, 0]
    # erase x=0 to x=350 and y=0 to y=-350
    image[-7 * bsize:, 0:7 * bsize] = [0, 0, 0, 0]

    corn = Image.open("./samples/corn.png")
    corn = corn.resize((7 * bsize, 7 * bsize))
    # concatenate the images
    image[0:corn.size[0], 0:corn.size[1]] = corn
    image[0:corn.size[0], -corn.size[1]:] = corn
    image[-corn.size[0]:, 0:corn.size[1]] = corn

    # if dark is True, make the image only white
    if style == "dark":
        image[image[:, :, 3] > 200] = [255, 255, 255, 255]
    
    image = imutils.resize(image, qrcodesize, qrcodesize)
    
    # rotate the imgage by 45 degrees
    image = imutils.rotate_bound(image, 45)

    # add 50 px border to the image
    image = cv2.copyMakeBorder(image, 0, 0, 230, 0, cv2.BORDER_CONSTANT, value=[0, 0, 0, 0])[10:]

    if style == "dark":
        final = Image.open("./samples/dark.png")
    else:
        final = Image.open("./samples/light.png")

    # paste the image on the final image
    final.paste(Image.fromarray(image), (0, 0), Image.fromarray(image))
    # resize the image to width=width and calculate the height if width is not 0
    if width != 0:
        final = final.resize((width, int(width * final.size[1] / final.size[0])))

    # save the image as a in qr+randomname.png
    name = str(time.time())
    final.save("./qrcode/qr" + name + ".png", "PNG")

    # get the image
    img = Image.open("./qrcode/qr" + name + ".png")
    img = img.convert("RGBA")
    datas = img.getdata()

    newData = []
    if style != "dark":
        for item in datas:
            thr = 175
            if item[0] > thr and item[1] > thr and item[2] > thr:
                newData.append((255, 255, 255, 0))
            else:
                newData.append(item)
    else:
        for item in datas:
            if item[0] < 50 and item[1] < 50 and item[2] < 50:
                newData.append((255,255,255, 0))
            else:
                newData.append(item)

    img.putdata(newData)


    # save the image
    img.save("./qrcode/qr" + name + ".png", "PNG")

    return "./qrcode/qr" + name + ".png"



# create a simple api endpoint to get the QR code
app = Flask(__name__)


@app.route("/makeqr/")
def request_page():
    # get user query for text, style and width
    text = str(request.args.get("text"))
    style = str(request.args.get("style"))
    width = int(request.args.get("width"))
    # example request: http://localhost:5000/makeqr/?text=HelloWorld&style=dark&width=500
    # create the QR code
    name = makeqrcode(text, style, width)


    # make a temporary file to send the image
    tempfileobj = NamedTemporaryFile(mode='w+b', suffix='.png')
    pilImage = open(name, "rb")
    copyfileobj(pilImage, tempfileobj)
    pilImage.close()
    remove(name)
    tempfileobj.seek(0, 0)

    # return the image
    return send_file(tempfileobj, mimetype='image/png')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=443, ssl_context=("/etc/letsencrypt/live/qrcode.directions.app/fullchain.pem", "/etc/letsencrypt/live/qrcode.directions.app/privkey.pem"))