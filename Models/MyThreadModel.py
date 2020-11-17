import threading
import time
import PlateRecognizer.PlateRecognition as pr
import sys
from datetime import datetime
import cv2
import SocketModule.MySocketClass as msc
import pytesseract
import Camera.CameraModule as cm

class myThread (threading.Thread):
   def __init__(self, threadID, name, _imagePath, _masterConfig, _configKey):
      threading.Thread.__init__(self)
      # print("Init Oldu _ {0}".format(threadID))
      self.threadID = threadID
      self.name = name
      self.imagePath = _imagePath
      self.Config = _masterConfig[_configKey]
      # Configuration for tesseract
      self.tesseractConfig = ('-c tessedit_char_whitelist={0} -l {1} --oem {2} --psm {3}'.format(_masterConfig["Tesseract"]["WhiteList"],
                                                                                                 _masterConfig["Tesseract"]["Lang"],
                                                                                                 _masterConfig["Tesseract"]["Oem"],
                                                                                                 _masterConfig["Tesseract"]["Psm"]))
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
      self.cam = cm.camera(self.imagePath)
      self.myPlateRecognizer = pr.PlateRecognizer(self.Config)
      self.daemonThread = threading.Thread(target=self.print_work, name=self.name, daemon=True)
      self.daemonThread.start()

   """
      Bu classtaki thread için porta data gonderen daemon thread
   """
   def print_work(self):
      while 1:
         if self.result is not None:
            try:
               if self.roiImage is not None:
                  text = pytesseract.image_to_string(self.roiImage, config=self.tesseractConfig).replace('\n', '').replace('\r', '').replace('\t', '').replace('\f', '').rstrip()
                  filteredText = text.replace('\n', '').replace('\r', '').replace('\t', '').replace('\f', '').rstrip()
                  self.result = filteredText
               print(self.name +"-" +self.result + "-" + datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
               self.appendLog(self.result + "-" + datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + "\n")
               if self.Config["SendImageFromUDP"] == 0:
                  self.base64Image = ""
               object = {
                  'Source': "'" + str(self.name) + "'",
                  'Result': "'" + str(self.result) + "'",
                  'ResultVal': "'" + str(self.resultVal) + "'",
                  'Image': "'" + self.base64Image + "'"}

               res = "{" + ",".join(("{}:{}".format(*i) for i in object.items())) + "}"
               self.mySocketModel.send(res)
               sleepTime = int(self.Config["OCRSleepTime"])
               if sleepTime > 0:
                  time.sleep(int(self.Config["OCRSleepTime"]))
            except BaseException as e:
               self.appendLog("print_work Error:" + self.name + "-" + str(e) + "-" + datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + "\n")
               pass


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
               image = self.cam.get_frame()
               self.appendLog("Görüntü Okundu -" + datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + "\n")
            self.resultVal, self.result, self.base64Image, self.roiImage = self.myPlateRecognizer.RecognizePlate(self.name, image)
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


