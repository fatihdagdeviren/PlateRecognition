import numpy as np
import cv2
import imutils
import base64
import math
import pytesseract
#TODO: temizlenecek burası.
#TODO: Configuration eklenecek.


class PlateRecognizer():
    def __init__(self, _configuration, _tesseractConf):
        self.configuration = _configuration
        self.tesseractConfiguration = _tesseractConf

    def get_center(self, contour):
        M = cv2.moments(contour)
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])

        return cX, cY

    def get_angle(self, p1, p2):
        return math.atan2(p1[1] - p2[1], p1[0] - p2[0]) * 180 / math.pi

    def getRoisFromImage(self,roi, cannyMin, cannyMax):
        try:
            roiCany = cv2.Canny(roi, cannyMin, cannyMax)
            (roiCnts, roiNew) = cv2.findContours(roiCany, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            # print(len(roiCnts))
            roiCntsAreas =[]
            if len(roiCnts) > 10:
                for roiCnt in roiCnts:
                    x, y, w, h = cv2.boundingRect(roiCnt)
                    roiCntArea = roi[y:y + h, x:x + w]
                    roiCntsAreas.append([x, y, w, h, roiCntArea])
                    # cv2.imshow("roiCntArea", roiCntArea)
                    # cv2.waitKey(1000)
            return roiCntsAreas
        except BaseException as e:
            return None

    def RecognizePlate(self, name, imagePath):
        try:
            showImages = int(self.configuration["ShowImages"])
            image = imagePath
            cropImageEnabled = int(self.configuration["CropEnabled"])
            dim = (int(self.configuration["ResizeDimension"]["Width"]), int(self.configuration["ResizeDimension"]["Height"]))

            # resize image
            if int(self.configuration["ResizeEnabled"]) == 1:
                image = cv2.resize(image, dim)
            h, w, d = image.shape

            # image = image[150:h, int(w/3)-50:int(w*2/3)+50]

            if cropImageEnabled == 1:
                image = image[self.configuration["CropCoordinates"]["HStart"]:self.configuration["CropCoordinates"]["HEnd"]
                , self.configuration["CropCoordinates"]["WStart"]:self.configuration["CropCoordinates"]["WEnd"]]
                image = cv2.resize(image, None, fx=2, fy=2)
                # cv2.imshow("image",image)
                # cv2.waitKey(1)

            # cv2.imshow("image", image)
            # cv2.waitKey(0)

            # gri seviye
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # biliteral filtre
            gray = cv2.bilateralFilter(gray, 13, 15, 15)

            gray = cv2.equalizeHist(gray)
            kernelForDilation = np.ones((2, 2), np.uint8)

            minValue = 100
            maxValue = 200
            cannyParams = self.configuration["Canny"]
            if cannyParams is not None:
                minValue = int(cannyParams["MinValue"])
                maxValue = int(cannyParams["MaxValue"])

            # Canny
            gray = cv2.GaussianBlur(gray, (7, 7), 0)
            edged = cv2.Canny(gray, minValue, maxValue)

            # Morph Dilation
            dilation = cv2.dilate(edged, kernel=kernelForDilation, iterations=1)

            # cv2.imshow("otsuImage", otsuImage)
            # cv2.imshow("edged",edged)
            # cv2.imshow("gray", gray)
            # cv2.imshow("grayCop", grayCop)
            # cv2.imshow("dilation", dilation)
            # cv2.waitKey(1)

            (cnts, new) = cv2.findContours(dilation.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:30]

            NumberPlateCnts = []
            for c in cnts:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.018 * peri, True)
                if len(approx) == 4:
                    # NumberPlateCnt = approx
                    NumberPlateCnts.append(approx)

            found = False
            # Configuration for tesseract
            tesseractConfig = ('-c tessedit_char_whitelist={0} -l {1} --oem {2} --psm {3}'.format(self.tesseractConfiguration["WhiteList"],
                                                                                                  self.tesseractConfiguration["Lang"],
                                                                                                  self.tesseractConfiguration["Oem"],
                                                                                                  self.tesseractConfiguration["Psm"]))
            if len(NumberPlateCnts) == 0:
                return False, "Plaka Bulunamadi.", ""

            text = "Empty"

            # Masking the part other than the number plate
            mask = np.zeros(gray.shape, np.uint8)
            roiImage = None
            for NumberPlateCnt in NumberPlateCnts:
                new_image = cv2.drawContours(mask, [NumberPlateCnt], 0, 255, -1)
                new_image = cv2.bitwise_and(image, image, mask=mask)

                x, y, w, h = cv2.boundingRect(NumberPlateCnt)

                rect = cv2.minAreaRect(NumberPlateCnt)
                box = cv2.boxPoints(rect)

                roi = gray[y:y + h, x:x + w]
                roiCntsList = self.getRoisFromImage(roi, minValue, maxValue)
                if len(roiCntsList) > 15:
                    roiImage = new_image[y:y + h, x:x + w]
                    break

                # angle = self.get_angle(box[0], box[1])

                # new_image = imutils.rotate(new_image, angle=93)
                # if 25 > angle > 3:
                #     # box = cv2.boxPoints(rect)
                #     # box = np.int0(box)
                #     new_image = imutils.rotate(new_image, angle=int(angle))

                # box = cv2.boxPoints(rect)
                # box = np.int0(box)
                # im = cv2.drawContours(image, [box], 0, (0, 0, 255), 2)
                # cv2.imshow("im", im)
                # cv2.waitKey(1000)


                #TODO: buraya farklı bir yontem, contor sayma yapilacak.
                # Run tesseract OCR on image
                # text = pytesseract.image_to_string(new_image, config=tesseractConfig).replace('\n','').replace('\r','').replace('\t','').replace('\f','').rstrip()
                # print(text)
                # if len(text) >= 5:
                #     break

            if showImages == 1:
                cv2.imshow("Original Image", image)
                # cv2.imshow("1 - Grayscale Conversion", gray)
                # cv2.imshow("2 - Bilateral Filter", gray)
                # cv2.imshow("4 - Canny Edges", edged)
                # cv2.imshow("4 - thresh1", thresh1)
                cv2.imshow("roiImage", roiImage)
                # cv2.imshow("Final_image", new_image)
                cv2.waitKey(1)

            # text = pytesseract.image_to_string(roiImage, config=tesseractConfig).replace('\n','').replace('\r','').replace('\t','').replace('\f','').rstrip()
            # print(text)
            retImage = cv2.resize(image, (self.configuration["ResultImage"]["Width"], self.configuration["ResultImage"]["Height"]))
            retval, buffer = cv2.imencode('.jpg', retImage)
            myImageBase64 = base64.b64encode(buffer).decode('utf-8')
            filteredText = text.replace('\n', '').replace('\r', '').replace('\t', '').replace('\f', '').rstrip()
            # Print recognized text
            retVal = (filteredText is not "")
            return retVal, filteredText, myImageBase64

        except BaseException as e:
            return False, str(e), ""





# if __name__ == "__main__":
#     RecognizePlate("Hi", "..\car2.jpg")