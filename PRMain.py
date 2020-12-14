from Models.MyThreadModel import myThread
from Models.MySingleModel import singleModelClass
import Configuration as conf
import time
import pytesseract
import os

def setTesseractPath(config):
    pytesseract.pytesseract.tesseract_cmd = "{0}".format(config["Tesseract"]["Path"])

def startThreads(myConfig):
    try:
        # Create new threads
        thread1Path = None
        thread2Path = None
        if int(myConfig["Debug"]) == 1:
            thread1Path = "Temp/car.jpg"
            thread2Path = "Temp/car2.jpg"
        else:
            thread1Path = myConfig["Thread1Config"]["URL"]
            thread2Path = myConfig["Thread2Config"]["URL"]
        thread1 = myThread(1, "Thread-1", thread1Path, myConfig, "Thread1Config")
        thread2 = myThread(2, "Thread-2", thread2Path, myConfig, "Thread2Config")
        # Start new Threads
        thread1.start()
        thread2.start()
    except BaseException as e:
        print("Error: unable to start thread_{0}".format(str(e)))
        exit()
    while 1:
        try:
            time.sleep(int(myConfig["MainSleepTime"]))
            if thread1.isException == True:
                thread1.kill()
                thread1.join()
                # print("******************* 1 Yeniden Olusuyor**************")
                thread1 = myThread(1, "Thread-1", thread1Path, myConfig, "Thread1Config")
                thread1.start()

            if thread2.isException == True:
                thread2.kill()
                thread2.join()
                # print("*******************  2 Yeniden Olusuyor**************")
                thread2 = myThread(2, "Thread-2", thread2Path, myConfig, "Thread2Config")
                thread2.start()

        except BaseException  as e:
            # Kill etmek icin var bu kod
            thread1.kill()
            thread1.join()
            thread2.kill()
            thread2.join()
            thread1 = myThread(1, "Thread-1", thread1Path, myConfig, "Thread1Config")
            thread2 = myThread(2, "Thread-2", thread2Path, myConfig, "Thread2Config")
            thread1.start()
            thread2.start()

def singleModel(myConfig):
    singlePath = None
    if int(myConfig["Debug"]) == 1:
        singlePath = "Temp/car.jpg"
    else:
        singlePath = myConfig["SingleThreadConfig"]["URL"]
    mySingleModel = singleModelClass("Single", singlePath, myConfig, "SingleThreadConfig")
    mySingleModel.run()

if __name__ == "__main__":
    # os.system("taskkill /f /im  PRMain.exe")



    if not os.path.exists('Logs'):
        os.makedirs('Logs')
    # Create two threads as follows
    myConfigParams = conf.GetConfigFromFile()
    setTesseractPath(myConfigParams)
    # print(myConfigParams["SingleThread"]) # myConfigParams = conf.GetConfigFromFile()
    #     # import pytesseract
    #     # import cv2
    #     # import numpy as np
    #     # from skimage.segmentation import clear_border
    #     # setTesseractPath(myConfigParams)
    #     # ima = cv2.imread("35KBG04.tiff")
    #     # ima = cv2.cvtColor(ima, cv2.COLOR_BGR2GRAY)
    #     #
    #     #
    #     #
    #     # kernelForDilation = np.ones((2, 2), np.uint8)
    #     # kernelForDilationRoiImage = np.ones((3, 3), np.uint8)
    #     #
    #     # # ima = cv2.resize(ima, None, fx=2, fy=2)
    #     # # ima = cv2.GaussianBlur(ima,(5, 5),0)
    #     #
    #     # ima = cv2.dilate(ima, kernel=kernelForDilation, iterations=1)
    #     # ima = cv2.erode(ima, kernel=kernelForDilation, iterations=1)
    #     # ima = cv2.threshold(ima, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    #     # # Invert and perform text extraction
    #     # ima = clear_border(ima)
    #     # ima = 255 - ima
    #     # h, w = ima.shape
    #     # ima = ima[5:h-8, 5:w-5]
    #     #
    #     # # im = 255-im
    #     # # kernelForDilation = np.ones((2, 2), np.uint8)
    #     # # im = cv2.bilateralFilter(im, 11, 21, 21)
    #     # # im = cv2.erode(im, kernel=kernelForDilation, iterations=2)
    #     # while 1:
    #     #     text = pytesseract.image_to_string(ima, config=('-c  tessedit_char_whitelist={0} -l {1} --oem {2} --psm {3}'.format(myConfigParams["Tesseract"]["WhiteList"],
    #     #                                                                                               myConfigParams["Tesseract"]["Lang"],
    #     #                                                                                               myConfigParams["Tesseract"]["Oem"],
    #     #                                                                                               myConfigParams["Tesseract"]["Psm"])))
    #     #
    #     #
    #     #     print(text)
    #     #     cv2.imshow("ima", ima)
    #     #     cv2.waitKey(1)
    if myConfigParams["SingleThread"] == 1:
        singleModel(myConfigParams)
    else:
        startThreads(myConfigParams)





