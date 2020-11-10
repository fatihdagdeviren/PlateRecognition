import PlateRecognizer.PlateRecognition as pr
import time
from datetime import datetime
import cv2
import SocketModule.MySocketClass as msc
import Camera.CameraModule as cm
import json

class singleModelClass():
    def __init__(self, name, _imagePath, _masterConfig, _configKey):
        self.name = name
        self.imagePath = _imagePath
        self.Config = _masterConfig[_configKey]
        self.tesseractConfig = _masterConfig["Tesseract"]
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
        # self.cap = cv2.VideoCapture(self.imagePath)
        # self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        # self.cap.set(cv2.CAP_PROP_FPS, 2)
        # self.cap.set(cv2.CAP_PROP_POS_FRAMES, 1)
        self.myPlateRecognizer = pr.PlateRecognizer(self.Config, self.tesseractConfig)
        self.cam = cm.camera(self.imagePath)

    def run(self):
        while 1:
            if self.debug  == 1:
                image = cv2.imread(self.imagePath)
            else:

                # ret, image = self.cap.read()
                image = self.cam.get_frame()
                self.appendLog("Görüntü Okundu -" + datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + "\n")

                # cv2.imshow("image",image)
                # cv2.waitKey(1)

            self.resultVal, self.result, self.base64Image = self.myPlateRecognizer.RecognizePlate(self.name, image)
            print(self.result+"-"+ datetime.now().strftime("%m/%d/%Y, %H:%M:%S") )
            self.appendLog(self.result+"-"+ datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +"\n")
            # if self.Config["SendImageFromUDP"] == 0:
            #    self.base64Image = ""
            # object = {
            #            'Source': "'" + str(self.name) + "'",
            #            'Result': "'"+str(self.result)+"'",
            #             'ResultVal': "'"+str(self.resultVal)+"'",
            #             'Image': "'"+self.base64Image+"'"}
            #
            # res = "{" + ",".join(("{}:{}".format(*i) for i in object.items())) + "}" # a=Apple,c=cat,b=ball
            # # self.mySocketModel.send(res)
            # sleepTime = int(self.Config["ThreadSleepTime"])
            # if sleepTime > 0:
            #     time.sleep(int(self.Config["ThreadSleepTime"]))



    def appendLog(self, text):
        # hatayi ezeyim burada
        if self.Config["EnableLog"] == 1:
            try:
                with open(self.logFilePath, "a+") as self.logFile:
                    self.logFile.write(text)
            except BaseException as e:
                pass
