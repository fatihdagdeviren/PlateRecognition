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
      #preserve_interword_spaces=1
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
      self.divideEnabled = (int(self.Config["DividePlateIntoParts"]) == 1)
      self.dividedParts = []
      self.cap = cm.VideoCapture(self.imagePath)
      self.myPlateRecognizer = pr.PlateRecognizer(self.Config)
      self.daemonThread = threading.Thread(target=self.print_work, name=self.name, daemon=True)
      self.daemonThread.start()

   def checkPlate(self, plateText):
      returnText = plateText
      try:
         arr = plateText.split(' ')
         returnVal = False
         if len(arr) == 3:
            basBolum = arr[0].replace('O', '0').replace("Z", "2").replace('G', '6').replace('B', '8').replace('S', '5').replace('D', '0').replace('A', '4').replace('U', '4').replace('E','6')
            ortaBolum = arr[1].replace('0', 'O').replace('2', 'Z').replace('6', 'G').replace('8', 'B').replace('5', 'S').replace('4', 'A')
            sonBolum = arr[2].replace('O', '0').replace("Z", "2").replace('G', '6').replace('B', '8').replace('S', '5').replace('D', '0').replace('A', '4').replace('U', '4').replace('E','6')
            returnText = "{0}{1}{2}".format(basBolum, ortaBolum, sonBolum)
            returnValBas, boolValBas = self.intTryParse(basBolum)
            returnValSon, boolValSon = self.intTryParse(sonBolum)
            returnVal = (boolValBas and boolValSon) and (len(basBolum) == 2)
         else:
            returnVal = (len(returnText) == 7 or len(returnText == 8))
         return returnText, returnVal
      except BaseException as e:
         return returnText, False

   def intTryParse(self, value):
      try:
         return int(value), True
      except ValueError:
         return value, False
   """
      Bu classtaki thread için porta data gonderen daemon thread
   """
   def print_work(self):
      while 1:
         if self.resultVal:
            if not self.divideEnabled:
               try:
                  if self.roiImage is not None:
                     text = pytesseract.image_to_string(self.roiImage.copy(), config=self.tesseractConfig)
                     filteredText = text.replace('\n', '').replace('\r', '').replace('\t', '').replace('\f', '').rstrip()
                     self.result, returnValCheckPlate = self.checkPlate(filteredText)
                     # print(self.result + "-" + datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
                     self.appendLog(self.result + "-" + str(returnValCheckPlate) + "-" + datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + "\n")
                     if bool(returnValCheckPlate):
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
            else:
               try:
                  if len(self.dividedParts) == 3:
                     textBaslangic = pytesseract.image_to_string(self.dividedParts[0], config=self.tesseractConfigNumeric).replace('\n', '').replace('\r', '').replace('\t', '').replace('\f',
                                                                                                                                                                                         '').rstrip()
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
               image = self.cap.read()
               self.appendLog("Görüntü Okundu -" + datetime.now().strftime("%m/%d/%Y, %H:%M:%S") + "\n")
            self.resultVal, self.result, self.base64Image, self.roiImage , self.dividedParts = self.myPlateRecognizer.RecognizePlate(self.name, image)
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


