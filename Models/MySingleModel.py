import PlateRecognizer.PlateRecognition as pr
import time
from datetime import datetime
import cv2
import SocketModule.MySocketClass as msc
import json

class singleModelClass():
    def __init__(self, name, _imagePath, _config):
        self.name = name
        self.imagePath = _imagePath
        self.Config = _config
        self.debug = self.Config["Debug"]
        self.isException = False
        self.resultVal = None
        self.result = None
        epoch_time = int(time.time())
        self.logFilePath = self.Config["LogFilePath"] + "\Thread_{0}_{1}.txt".format(name, epoch_time)
        self.logFile = open(self.logFilePath, 'w+')
        self.base64Image = None
        self.mySocketModel = msc.SocketSender(self.Config )


    def run(self):
        while 1:
            if int(self.Config["Debug"] == 1):
                image = cv2.imread(self.imagePath)
            else:
                cap = cv2.VideoCapture(self.imagePath)
                ret, image = cap.read()
                # while 1:
                #     cap = cv2.VideoCapture(self.imagePath)
                #     ret, image = cap.read()
                #     cv2.imshow("Kamera",image)
                #     cv2.waitKey(1)

            self.resultVal, self.result, self.base64Image = pr.RecognizePlate(self.name, image, self.Config)
            # print("{0}-{1}".format(self.name, self.result))
            self.appendLog(self.result+"-"+ datetime.now().strftime("%m/%d/%Y, %H:%M:%S") +"\n")

            object = {
                       'Source': "'" + str(self.name) + "'",
                       'Result': "'"+str(self.result)+"'",
                        'ResultVal': "'"+str(self.resultVal)+"'",
                        'Image': "'"+self.base64Image+"'"}

            res = "{" + ",".join(("{}:{}".format(*i) for i in object.items())) + "}" # a=Apple,c=cat,b=ball
            self.mySocketModel.send(res)
            time.sleep(int(self.Config["ThreadSleepTime"]))

    def appendLog(self, text):
        # hatayi ezeyim burada
        try:
            with open(self.logFilePath, "a+") as self.logFile:
                self.logFile.write(text)
        except BaseException as e:
            pass
