import threading
import time
import PlateRecognizer.PlateRecognition as pr
import sys
from datetime import datetime
import cv2
import SocketModule.MySocketClass as msc

class myThread (threading.Thread):
   def __init__(self, threadID, name, _imagePath, _masterConfig, _configKey):
      threading.Thread.__init__(self)
      # print("Init Oldu _ {0}".format(threadID))
      self.threadID = threadID
      self.name = name
      self.imagePath = _imagePath
      self.Config = _masterConfig[_configKey]
      self.tesseractConfig = _masterConfig["Tesseract"]
      self.debug = _masterConfig["Debug"]
      self.killed = False
      self.isException = False
      self.resultVal = None
      self.result = None
      epoch_time = int(time.time())
      self.logFilePath = _masterConfig["LogFilePath"] +"\Thread_{0}_{1}.txt".format(name, epoch_time)
      if self.Config["EnableLog"] == 1:
         self.logFile = open(self.logFilePath, 'w+')
      self.base64Image = None
      self.mySocketModel = msc.SocketSender(self.Config)
      self.cap = cv2.VideoCapture(self.imagePath)
      self.myPlateRecognizer = pr.PlateRecognizer(self.Config, self.tesseractConfig)


   def globaltrace(self, frame, event, arg):
      # call Before a function is executed.
      if event == 'call':
         return self.localtrace
      else:
         return None

   def start(self):
      self.__run_backup = self.run
      self.run = self.__run  # Force the Thread to install our trace.
      threading.Thread.start(self)

   def __run(self):
      try:
         self.isException = False
         sys.settrace(self.globaltrace)
         self.__run_backup()
         self.run = self.__run_backup
         while not self.killed:
            if self.debug == 1:
               image = cv2.imread(self.imagePath)
            else:
               ret, image = self.cap.read()
               self.appendLog("Görüntü Okundu -" + datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + "\n")

            self.resultVal, self.result, self.base64Image = self.myPlateRecognizer.RecognizePlate(self.name, image)
            self.appendLog(self.result + "-" + datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + "\n")
            # if self.Config["SendImageFromUDP"] == 0:
            #    self.base64Image = ""
            # object = {
            #    'Source': "'"+str(self.name)+"'",
            #    'Result': "'" + str(self.result) + "'",
            #    'ResultVal': "'" + str(self.resultVal) + "'",
            #    'Image': "'" + self.base64Image + "'"}
            #
            # res = "{" + ",".join(("{}:{}".format(*i) for i in object.items())) + "}"
            # self.mySocketModel.send(res)
            # sleepTime = int(self.Config["SleepTime"])
            # if sleepTime > 0:
            #    time.sleep(int(self.Config["SleepTime"]))
      except BaseException as e:
         self.isException = True

   def localtrace(self, frame, event, arg):
      # print("Event = {0}".format(event))
      if self.killed:
         # line Before a line is executed.
         if event == 'line':
            raise SystemExit()
      return self.localtrace

   def kill(self):
      self.killed = True

   def appendLog(self, text):
      if self.Config["EnableLog"] == 1:
         # hatayi ezeyim burada
         try:
               with open(self.logFilePath, "a+") as self.logFile:
                  self.logFile.write(text)
         except BaseException as e:
            pass


