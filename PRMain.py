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
            thread1Path = "car.jpg"
            thread2Path = "car2.jpg"
        else:
            thread1Path = myConfig["IPCam1URL"]
            thread2Path = myConfig["IPCam2URL"]
        thread1 = myThread(1, "Thread-1", thread1Path, myConfig)
        thread2 = myThread(2, "Thread-2", thread2Path, myConfig)
        # Start new Threads
        thread1.start()
        thread2.start()
    except BaseException as e:
        print("Error: unable to start thread_{0}".format(str(e)))
        exit()
    count = 0
    while 1:
        try:
            count += 1
            time.sleep(int(myConfig["MainSleepTime"]))
            if thread1.isException == True:
                thread1.kill()
                thread1.join()
                # print("******************* 1 Yeniden Olusuyor**************")
                thread1 = myThread(1, "Thread-1", thread1Path, myConfig)
                thread1.start()

            if thread2.isException == True:
                thread2.kill()
                thread2.join()
                # print("*******************  2 Yeniden Olusuyor**************")
                thread2 = myThread(2, "Thread-2", thread2Path, myConfig)
                thread2.start()

        except BaseException  as e:
            # Kill etmek icin var bu kod
            thread1.kill()
            thread1.join()
            thread2.kill()
            thread2.join()
            thread1 = myThread(1, "Thread-1", thread1Path, myConfig)
            thread2 = myThread(2, "Thread-2", thread2Path, myConfig)
            thread1.start()
            thread2.start()

def singleModel(myConfig):
    singlePath = None
    if int(myConfig["Debug"]) == 1:
        singlePath = "car.jpg"
    else:
        singlePath = myConfig["SingleCamURL"]
    mySingleModel = singleModelClass("Single", singlePath, myConfig)
    mySingleModel.run()

if __name__ == "__main__":
    if not os.path.exists('Logs'):
        os.makedirs('Logs')
    # Create two threads as follows
    myConfigParams = conf.GetConfigFromFile()
    setTesseractPath(myConfigParams)
    # print(myConfigParams["SingleThread"])
    if myConfigParams["SingleThread"] == 1:
        singleModel(myConfigParams)
    else:
        startThreads(myConfigParams)





