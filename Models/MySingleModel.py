import PlateRecognizer.PlateRecognition as pr
import time
from datetime import datetime
import cv2
import SocketModule.MySocketClass as msc
import Camera.CameraModule as cm
import threading
import pytesseract

class singleModelClass():
    def __init__(self, name, _imagePath, _masterConfig, _configKey):
        self.name = name
        self.imagePath = _imagePath
        self.Config = _masterConfig[_configKey]
        # Configuration for tesseract
        # preserve_interword_spaces=1
        self.tesseractConfig = ('-c tessedit_char_whitelist={0} -l {1} --oem {2} --psm {3}'.format(_masterConfig["Tesseract"]["WhiteList"],
                                                                                              _masterConfig["Tesseract"]["Lang"],
                                                                                              _masterConfig["Tesseract"]["Oem"],
                                                                                              _masterConfig["Tesseract"]["Psm"]))

        self.tesseractConfigChar = ('-c tessedit_char_whitelist={0} -l {1} --oem {2} --psm {3}'.format(_masterConfig["Tesseract"]["WhiteListChar"],
                                                                                                   _masterConfig["Tesseract"]["Lang"],
                                                                                                   _masterConfig["Tesseract"]["Oem"],
                                                                                                   _masterConfig["Tesseract"]["Psm"]))

        self.tesseractConfigNumeric = ('-c tessedit_char_whitelist={0} -l {1} --oem {2} --psm {3}'.format(_masterConfig["Tesseract"]["WhiteListNumeric"],
                                                                                                   _masterConfig["Tesseract"]["Lang"],
                                                                                                   _masterConfig["Tesseract"]["Oem"],
                                                                                                   _masterConfig["Tesseract"]["Psm"]))
        self.debug = _masterConfig["Debug"]
        self.isException = False
        self.resultVal = None
        self.result = None
        epoch_time = int(time.time())
        self.logFilePath = _masterConfig["LogFilePath"] + "\Thread_{0}_{1}.txt".format(name, epoch_time)
        if self.Config["EnableLog"] == 1:
            self.logFile = open(self.logFilePath, 'w+')
        self.base64Image = None
        self.mySocketModel = msc.SocketSender(self.Config)
        self.divideEnabled = (int(self.Config["DividePlateIntoParts"]) == 1)
        self.dividedParts = []
        self.myPlateRecognizer = pr.PlateRecognizer(self.Config)
        self.cam = cm.camera(self.imagePath)
        self.daemonThread = threading.Thread(target=self.print_work, name=self.name, daemon=True)
        self.daemonThread.start()

    def checkPlate(self, plateText):
        returnText = plateText
        try:
            arr = plateText.split(' ')
            if len(arr) == 3:
                ortaBolum = arr[1].replace('0', 'O').replace('2', 'Z')
                sonBolum = arr[2].replace('O', '0').replace("Z","2")
                returnText = "{0}{1}{2}".format(arr[0], ortaBolum, sonBolum )
            return returnText
        except BaseException as e:
            return returnText
    """
       Bu classtaki thread için porta data gonderen daemon thread
    """
    def print_work(self):
        while 1:
            if self.result is not None:
                if not self.divideEnabled:
                    try:
                        if self.roiImage is not None:
                            text = pytesseract.image_to_string(self.roiImage.copy(), config=self.tesseractConfig)
                            filteredText = text.replace('\n', '').replace('\r', '').replace('\t', '').replace('\f', '').rstrip()
                            # cv2.imwrite("{0}.jpg".format(filteredText),image)
                            self.result = filteredText
                        print(self.result + "-" + datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
                        self.appendLog(self.result + "-" + datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + "\n")
                        if self.Config["SendImageFromUDP"] == 0:
                           self.base64Image = ""
                        object = {
                                   'Source': "'" + str(self.name) + "'",
                                   'Result': "'"+str(self.result)+"'",
                                    'ResultVal': "'"+str(self.resultVal)+"'",
                                    'Image': "'"+self.base64Image+"'"}

                        res = "{" + ",".join(("{}:{}".format(*i) for i in object.items())) + "}"
                        self.mySocketModel.send(res)
                    except BaseException as e:
                        self.appendLog("print_work Error:" + str(e) + "-" + datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + "\n")
                        pass
                else:
                    try:
                        if len(self.dividedParts) == 3:
                            textBaslangic = pytesseract.image_to_string(self.dividedParts[0], config=self.tesseractConfigNumeric).replace('\n', '').replace('\r', '').replace('\t', '').replace('\f', '').rstrip()
                            filteredTextBaslangic = textBaslangic.replace('\n', '').replace('\r', '').replace('\t', '').replace('\f', '').rstrip()
                            # print(filteredTextBaslangic)
                            textOrta = pytesseract.image_to_string(self.dividedParts[1], config=self.tesseractConfigChar).replace('\n', '').replace('\r', '').replace('\t', '').replace('\f', '').rstrip()
                            filteredTextOrta = textOrta.replace('\n', '').replace('\r', '').replace('\t', '').replace('\f', '').rstrip()
                            textSon = pytesseract.image_to_string(self.dividedParts[2], config=self.tesseractConfigNumeric).replace('\n', '').replace('\r', '').replace('\t', '').replace('\f', '').rstrip()
                            filteredTextSon = textSon.replace('\n', '').replace('\r', '').replace('\t', '').replace('\f', '').rstrip()
                            filteredTextResult = "{0}{1}{2}".format(filteredTextBaslangic, filteredTextOrta, filteredTextSon)
                            self.result = filteredTextResult
                            print(self.result + "-" + datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
                            if self.Config["SendImageFromUDP"] == 0:
                                self.base64Image = ""
                            object = {
                                'Source': "'" + str(self.name) + "'",
                                'Result': "'" + str(self.result) + "'",
                                'ResultVal': "'" + str(self.resultVal) + "'",
                                'Image': "'" + self.base64Image + "'"}

                            res = "{" + ",".join(("{}:{}".format(*i) for i in object.items())) + "}"
                            self.mySocketModel.send(res)
                    except BaseException as e:
                        self.appendLog("print_work Error:" + str(e) + "-" + datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + "\n")
                        pass

            sleepTime = int(self.Config["OCRSleepTime"])
            if sleepTime > 0:
                time.sleep(sleepTime)
    """
          iş yapan thread
    """
    def run(self):
        while 1:
            if self.debug == 1:
                image = cv2.imread(self.imagePath)
            else:

                # ret, image = self.cap.read()
                image = self.cam.get_frame()
                self.appendLog("Görüntü Okundu -" + datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + "\n")
                # cv2.imshow("image",image)
                # cv2.waitKey(1)
            self.resultVal, self.result, self.base64Image, self.roiImage, self.dividedParts = self.myPlateRecognizer.RecognizePlate(self.name, image)
            # self.roiImage = cv2.imread("D:\\OutSource\PlateRecognition\\Temp\\deneme2.png")

    def appendLog(self, text):
        # hatayi ezeyim burada
        if self.Config["EnableLog"] == 1:
            try:
                with open(self.logFilePath, "a+") as self.logFile:
                    self.logFile.write(text)
            except BaseException as e:
                pass
