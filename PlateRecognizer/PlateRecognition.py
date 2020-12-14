import numpy as np
import cv2
import imutils
import base64
import math

from operator import itemgetter
import pytesseract
from datetime import datetime
from skimage.segmentation import clear_border
SCALAR_RED = (0.0, 0.0, 255.0)
#TODO: temizlenecek burası.
#TODO: Configuration eklenecek.


class PlateRecognizer():
    def __init__(self, _configuration):
        self.configuration = _configuration

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
            divideEnabled = (int(self.configuration["DividePlateIntoParts"]) == 1)
            dividedParts = []

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
            kernelForDilationRoiImage = np.ones((3, 3), np.uint8)

            minValue = 100
            maxValue = 200
            cannyParams = self.configuration["Canny"]
            if cannyParams is not None:
                minValue = int(cannyParams["MinValue"])
                maxValue = int(cannyParams["MaxValue"])

            # Canny
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            edged = cv2.Canny(gray, minValue, maxValue)

            # Morph Dilation
            dilation = cv2.dilate(edged, kernel=kernelForDilation, iterations=1)

            (cnts, new) = cv2.findContours(dilation.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:30]

            NumberPlateCnts = []
            for c in cnts:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.018 * peri, True)
                if len(approx) == 4:
                    # NumberPlateCnt = approx
                    NumberPlateCnts.append(approx)

            if len(NumberPlateCnts) == 0:
                return False, "Plaka Bulunamadi.", "", None, []


            # Masking the part other than the number plate
            mask = np.zeros(gray.shape, np.uint8)
            roiImage = None
            for NumberPlateCnt in NumberPlateCnts:
                new_image = cv2.drawContours(mask, [NumberPlateCnt], 0, 255, -1)
                new_image = cv2.bitwise_and(image, image, mask=mask)

                # cv2.imshow("Gercek Resim111", new_image)
                # cv2.imwrite("new_image.jpg",new_image)

                x, y, w, h = cv2.boundingRect(NumberPlateCnt)
                rect = cv2.minAreaRect(NumberPlateCnt)
                box = cv2.boxPoints(rect)
                roi = gray[y:y + h, x:x + w]
                roiCntsList = self.getRoisFromImage(roi, minValue, maxValue)
                if len(roiCntsList) > 15:
                    angle = self.get_angle(box[0], box[1])
                    roiImage = new_image[y:y + h, x:x + w]
                    if angle > 45:
                        angle = -1 * (90 - angle)
                    (h, w) = roiImage.shape[:2]
                    center = (w // 2, h // 2)
                    M = cv2.getRotationMatrix2D(center, angle, 1.0)
                    roiImage = cv2.warpAffine(roiImage, M, (w, h),
                                             flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                        # roiImage = imutils.rotate(roiImage, angle=math.ceil(angle))
                        # cv2.imshow("roiImageAffine", roiImageAffine)

                    roiImage = cv2.cvtColor(roiImage, cv2.COLOR_BGR2GRAY)
                    roiImage = cv2.bilateralFilter(roiImage, 11, 21, 21)

                    (cntsRoi, newRoi) = cv2.findContours(roiImage.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                    cntsRoi = sorted(cntsRoi, key=cv2.contourArea, reverse=True)[0]
                    xPlate, yPlate, wPlate, hPlate = cv2.boundingRect(cntsRoi)
                    roiImage = roiImage[yPlate:yPlate + hPlate, xPlate:xPlate + wPlate]
                    # cv2.imshow("roiPlate",roiPlate)

                    # roiImage = cv2.morphologyEx(roiImage, cv2.MORPH_OPEN, kernelForDilationRoiImage)
                    roiImage = cv2.dilate(roiImage, kernel=kernelForDilation, iterations=1)
                    roiImage = cv2.erode(roiImage, kernel=kernelForDilationRoiImage, iterations=1)
                    roiImage = cv2.threshold(roiImage, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
                    # # Invert and perform text extraction
                    # roiImage = 255 - roiImage

                    # roiImage = cv2.dilate(roiImage, kernel=kernelForDilation, iterations=3)

                    # roiImage = cv2.erode(roiImage, kernel=kernelForDilation, iterations=1)

                    roiImage = clear_border(roiImage)

                    # roiImage = 255 - roiImage
                    # roiImage = cv2.resize(roiImage, None ,fx=3, fy=2)
                    # roiImage = cv2.bilateralFilter(roiImage, 11, 21, 21)

                    # roiImage = cv2.dilate(roiImage, kernel=kernelForDilation, iterations=1)

                    # roiImage = cv2.bilateralFilter(roiImage, 11, 21, 21)
                    # roiImage = cv2.morphologyEx(roiImage, cv2.MORPH_OPEN, kernelForDilationRoiImage)
                    # roiImage = 255 - roiImage

                    break



                # box = cv2.boxPoints(rect)
                # box = np.int0(box)
                # im = cv2.drawContours(image, [box], 0, (0, 0, 255), 2)
                # cv2.imshow("im", im)
                # cv2.waitKey(1000)


            # roiImage = cv2.dilate(roiImage, kernel=kernelForDilation, iterations=3)
            # dimResize = 300, 200
            # roiImage = cv2.resize(roiImage, (dimResize))
            # kernelForDilationRoiImage2 = np.ones((2, 2), np.uint8)
            # roiImage = cv2.dilate(roiImage, kernel=kernelForDilationRoiImage2, iterations=1)

            if showImages == 1:
                if roiImage is not None:
                    cv2.imshow("roiImage", roiImage)
                cv2.imshow("Original Image", image)
                cv2.imshow("Final_image", new_image)
                # cv2.imwrite("roiImage.jpg", roiImage)
                # cv2.imwrite("Original.jpg", image)
                # cv2.imwrite("Final_image.jpg", new_image)
                cv2.waitKey(1)


            # text = pytesseract.image_to_string(roiImage, config=tesseractConfig).replace('\n','').replace('\r','').replace('\t','').replace('\f','').rstrip()
            # print(text)
            retImage = cv2.resize(image, (self.configuration["ResultImage"]["Width"], self.configuration["ResultImage"]["Height"]))
            retval, buffer = cv2.imencode('.jpg', retImage)
            myImageBase64 = base64.b64encode(buffer).decode('utf-8')
            resultVal = (roiImage is not None)
            # cv2.imwrite("thresh1.jpg",roiImage)
            return resultVal, "", myImageBase64, roiImage, []

        except BaseException as e:
            return False, str(e), "", None, []





# if __name__ == "__main__":
#     RecognizePlate("Hi", "..\car2.jpg")
