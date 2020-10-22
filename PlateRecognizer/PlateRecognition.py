import numpy as np
import cv2
import imutils
import pytesseract
import base64
import string

#TODO: temizlenecek burası.
#TODO: Configuration eklenecek.


def RecognizePlate(name, imagePath, config, showImages = 0):
    try:
        showImages = int(config["ShowImages"])
        image = imagePath
        image = imutils.resize(image, width=500)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        minValue = 100
        maxValue = 200
        cannyParams = config["Canny"]
        if cannyParams is not None:
            minValue = int(cannyParams["MinValue"])
            maxValue = int(cannyParams["MaxValue"])
        edged = cv2.Canny(gray, minValue, maxValue)
        (cnts, new) = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:30]
        NumberPlateCnt = None
        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4:
                NumberPlateCnt = approx
                break
        if NumberPlateCnt is None:
            return False, "Plaka Bulunamadi.", None
        # Masking the part other than the number plate
        mask = np.zeros(gray.shape, np.uint8)
        new_image = cv2.drawContours(mask, [NumberPlateCnt], 0, 255, -1)
        # cv2.imshow("1",new_image)
        new_image = cv2.bitwise_and(image, image, mask=mask)
        # cv2.namedWindow("Final_image", cv2.WINDOW_NORMAL)
        # cv2.imshow("Final_image", new_image)

        # Configuration for tesseract
        tesseractConfig = ('-c tessedit_char_whitelist={0} -l {1} --oem {2} --psm {3}'.format(config["Tesseract"]["WhiteList"], config["Tesseract"]["Lang"],
                                                                                config["Tesseract"]["Oem"],
                                                                                config["Tesseract"]["Psm"]))

        # Run tesseract OCR on image
        text = pytesseract.image_to_string(new_image, config=tesseractConfig)
        if showImages == 1 and int(config["SingleThread"]) == 1:
            cv2.imshow("Original Image", image)
            cv2.imshow("1 - Grayscale Conversion", gray)
            cv2.imshow("2 - Bilateral Filter", gray)
            cv2.imshow("4 - Canny Edges", edged)
            cv2.namedWindow("Final_image", cv2.WINDOW_NORMAL)
            cv2.imshow("Final_image", new_image)
            cv2.waitKey(0)

        retImage = cv2.resize(image, (config["ResultImage"]["Width"],config["ResultImage"]["Height"]))
        retval, buffer = cv2.imencode('.jpg', retImage)
        myImageBase64 = base64.b64encode(buffer).decode('utf-8')
        filteredText = text.replace('\n','').replace('\r','').replace('\t','').rstrip()
        # Print recognized text
        retVal = (filteredText is not "")
        return retVal, filteredText, myImageBase64

    except BaseException as e:
        return False, str(e), None




if __name__ == "__main__":
    RecognizePlate("Hi", "..\car2.jpg")