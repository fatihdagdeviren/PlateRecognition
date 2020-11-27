import numpy as np
import cv2
import imutils
import base64
import math
from operator import itemgetter
import pytesseract
from datetime import datetime

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

                x, y, w, h = cv2.boundingRect(NumberPlateCnt)

                rect = cv2.minAreaRect(NumberPlateCnt)
                box = cv2.boxPoints(rect)

                roi = gray[y:y + h, x:x + w]
                roiCntsList = self.getRoisFromImage(roi, minValue, maxValue)
                if len(roiCntsList) > 15:
                    angle = self.get_angle(box[0], box[1])
                    roiImage = new_image[y:y + h, x:x + w]
                    if 25 > angle > 3:
                        # box = cv2.boxPoints(rect)
                        # box = np.int0(box)
                        # cv2.imshow("DondurmedenOnce", roiImage)
                        # (h, w) = roiImage.shape[:2]
                        # center = (w // 2, h // 2)
                        # M = cv2.getRotationMatrix2D(center, angle, 1.0)
                        # roiImage = cv2.warpAffine(roiImage, M, (w, h),
                        #                          flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                        roiImage = imutils.rotate(roiImage, angle=math.ceil(angle))
                        # cv2.imshow("rotated", roiImage)

                    roiImage = cv2.cvtColor(roiImage, cv2.COLOR_BGR2GRAY)
                    roiImage = cv2.bilateralFilter(roiImage, 13, 15, 15)
                    # roiImage = cv2.resize(roiImage, None, fx=2, fy=2)
                    # roiImage = cv2.erode(roiImage, kernel=kernelForDilationRoiImage, iterations=1)
                    # roiImage = cv2.morphologyEx(roiImage, cv2.MORPH_OPEN, kernelForDilationRoiImage)
                    roiImage = cv2.dilate(roiImage, kernel=kernelForDilation, iterations=2)
                    roiImage = cv2.erode(roiImage, kernel=kernelForDilationRoiImage, iterations=3)
                    # cv2.imshow("MorphSonrasi", roiImage)
                    roiImage = cv2.threshold(roiImage, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
                    # Invert and perform text extraction

                    roiImage = 255 - roiImage
                    # roiImage = cv2.resize(roiImage, None, fx=2, fy=2)

                    # cv2.imshow("thresh", roiImage)

                    #region deneme
                    if divideEnabled:
                        (cntsRoi, new1) = cv2.findContours(roiImage, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                        parentiPlakaOlanlar = []
                        index = 0
                        for x in new1[0]:
                            if x[3] == 0:
                                parentiPlakaOlanlar.append((cntsRoi[index], cv2.boundingRect(cntsRoi[index])))
                            index += 1

                        # boundingBoxes = [cv2.boundingRect(c) for c in parentiPlakaOlanlar]
                        # Buraya bakilacak
                        cntsSorted = [x[0] for x in sorted(parentiPlakaOlanlar, key= lambda x: x[1][0])]
                        # ilkodu Cikarim islemi yapiliyor
                        ilkKoduIlkRakam = cntsSorted[0]
                        ilkKoduIkinciRakamCntr = cntsSorted[1]
                        xilKodu1, yilKodu1, wilKodu1, hilKodu1 = cv2.boundingRect(ilkKoduIlkRakam)
                        xilKodu2, yilKodu2, wilKodu2, hilKodu2 = cv2.boundingRect(ilkKoduIkinciRakamCntr)
                        ilKoduImage = roiImage[yilKodu1:yilKodu2 + hilKodu2, xilKodu1:xilKodu2 + wilKodu2]

                        # ortadaki harf bolumu icin
                        ucuncu_deger = cntsSorted[2]
                        dorduncu_deger = cntsSorted[3]
                        besinci_deger  = cntsSorted[4]
                        x_ucuncu_deger, y_ucuncu_deger, w_ucuncu_deger, h_ucuncu_deger = cv2.boundingRect(ucuncu_deger)
                        x_dorduncu_deger, y_dorduncu_deger, w_dorduncu_deger, h_dorduncu_deger = cv2.boundingRect(dorduncu_deger)
                        x_besinci_deger, y_besinci_deger, w_besinci_deger, h_besinci_deger = cv2.boundingRect(besinci_deger)

                        uzaklik_uc_dort = ((x_ucuncu_deger - x_dorduncu_deger)**2 + (y_ucuncu_deger - y_dorduncu_deger)**2)**0.5
                        uzaklik_dort_bes = ((x_dorduncu_deger - x_besinci_deger) ** 2 + (y_dorduncu_deger - y_besinci_deger) ** 2) ** 0.5
                        distance = 80
                        roiOrtaAlan = None
                        xOrtaBitis, yOrtaBitis = 0,0
                        if uzaklik_uc_dort < distance and uzaklik_dort_bes < distance:
                            #3 harfli plaka burada
                            roiOrtaAlan = roiImage[y_ucuncu_deger:y_besinci_deger + h_besinci_deger, x_ucuncu_deger:x_besinci_deger + w_besinci_deger]
                            xOrtaBitis = x_besinci_deger + w_besinci_deger
                            yOrtaBitis = y_besinci_deger
                        elif uzaklik_uc_dort < distance and uzaklik_dort_bes > distance:
                            #2 harfli plaka
                            roiOrtaAlan = roiImage[y_ucuncu_deger:y_dorduncu_deger + h_dorduncu_deger, x_ucuncu_deger:x_dorduncu_deger + w_dorduncu_deger]
                            xOrtaBitis = x_dorduncu_deger + w_dorduncu_deger
                            yOrtaBitis = y_dorduncu_deger
                        else:
                            #tek harfli plaka
                            roiOrtaAlan = roiImage[y_ucuncu_deger:y_ucuncu_deger + h_ucuncu_deger, x_ucuncu_deger:x_ucuncu_deger + w_ucuncu_deger]
                            xOrtaBitis = x_ucuncu_deger + w_ucuncu_deger
                            yOrtaBitis = y_ucuncu_deger

                        son_deger = cntsSorted[-1]
                        x_son_deger, y_son_deger, w_son_deger, h_son_deger= cv2.boundingRect(son_deger)
                        endRoi = (x_son_deger + w_son_deger)
                        sonAlan = roiImage[yOrtaBitis: yOrtaBitis + h_besinci_deger, xOrtaBitis: endRoi]
                        dividedParts.append(ilKoduImage)
                        dividedParts.append(roiOrtaAlan)
                        dividedParts.append(sonAlan)
                        # cv2.imshow("ilKoduImage", ilKoduImage)
                        # cv2.imshow("roiOrtaAlan", roiOrtaAlan)
                        # cv2.imshow("sonAlan", sonAlan)
                    #endregion

                    # for (x, y, w, h, roiCntAreaT) in roiCntsListTresh:
                    #     cv2.imshow("roiCntArea", roiCntAreaT)
                    #     cv2.waitKey(1000)

                    break



                # box = cv2.boxPoints(rect)
                # box = np.int0(box)
                # im = cv2.drawContours(image, [box], 0, (0, 0, 255), 2)
                # cv2.imshow("im", im)
                # cv2.waitKey(1000)


            # roiImage = cv2.dilate(roiImage, kernel=kernelForDilation, iterations=3)
            # dimResize = 300, 200
            # roiImage = cv2.resize(roiImage, (dimResize))
            # kernelForDilationRoiImage2 = np.ones((4, 4), np.uint8)
            # roiImage = cv2.dilate(roiImage, kernel=kernelForDilationRoiImage2, iterations=1)

            if showImages == 1:
                cv2.imshow("roiImage", roiImage)
                cv2.imshow("Original Image", image)
                cv2.imshow("Final_image", new_image)
                cv2.imwrite("roiImage.jpg", roiImage)
                cv2.imwrite("Original.jpg", image)
                cv2.imwrite("Final_image.jpg", new_image)
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
