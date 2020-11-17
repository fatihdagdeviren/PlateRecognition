import numpy as np
import cv2
import imutils
import os
import joblib
import json
from skimage.feature import hog
from skimage import data, exposure

datas=[]
labels = []

thisdict = {
    "a": 1,    "b": 2,    "c": 3,    "d": 4,    "e": 5,    "f": 6,    "g": 7,    "h": 8,    "i": 9,    "j": 10,
    "k": 11,    "l": 12,    "m": 13,    "n": 14,    "o": 15,    "p": 16,    "q": 17,    "r": 18,    "s": 19,
    "t": 20,    "u": 21,    "v": 22,    "w": 23,    "x": 24,    "y": 25,    "z": 26,
    "A":27,    "B":28,    "C":29,    "D":30,    "E":31,    "F":32,    "G":33,    "H":34,    "I":35,    "J":36,
    "K":37,    "L":38,    "M":39,    "N":40,    "O":41,    "P":42,    "Q":43,    "R":44,    "S":45,    "T":46,
    "U":47,    "V":48,    "W":49,    "X":50,    "Y":51,    "Z":52,
    "1":53,    "2":54,    "3":55,    "4":56,    "5":57,    "6":58,    "7":59,    "8":60,    "9":61,    "0":62}

def pickleOlustur(fileName,object,method=None):
    try:
        if method is None:
            with open(fileName, 'w') as fp:
                json.dump(object, fp)
        elif method == 1:
                joblib.dump(object, fileName)
        return '0'
    except BaseException as e:
        print(str(e))
        return '-1'

def pickleYukle(fileName,method=None):
    #data =joblib.load(fileName)
    if method is None:
        with open(fileName, 'r') as fp:
            data = json.loads(fp.read())
    elif method == 1:
        data =joblib.load(fileName)
    return data


def CalculateHOG(gray, method = None):
    gray = cv2.bilateralFilter(gray, 13, 15, 15)
    edged = cv2.Canny(gray, 100, 200)
    kernel = np.ones((3, 3), np.uint8)
    # opening = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)
    # cv2.imshow("edged", edged)
    # cv2.imshow("opening", opening)
    # cv2.waitKey(0)
    fd, roi_hog_fd = hog(edged, orientations=8, pixels_per_cell=(2, 2),
                         cells_per_block=(1, 1), visualize=True, block_norm='L2-Hys')
    hog_image_rescaled = exposure.rescale_intensity(roi_hog_fd, in_range=(0, 10))
    resultImage = hog_image_rescaled

    # cv2.imshow("edged", edged)
    # cv2.imshow("roi_hog_fd", roi_hog_fd)
    # cv2.imshow("resultImage", resultImage)
    # cv2.waitKey(0)

    return resultImage

def intTryParse(value):
    try:
        return int(value), True
    except ValueError:
        return value, False

def modelOlustur(method=None):
    dosyaYolu = "D:\OutSource\PlateRecognition\Dataset\English.Alphabet.Dataset\English Alphabet Dataset"
    dirList = os.listdir(dosyaYolu)
    dictValues = list(thisdict.values())
    for dir in dirList:
        imagePathInt, res = intTryParse(dir)
        if res and imagePathInt in dictValues:
            resPath = dosyaYolu + "\\"+ dir
            imageList = os.listdir(resPath)
            for image in imageList:
                imagePath = resPath + "\\" + image
                myImage = cv2.imread(imagePath)
                myImageResized = cv2.resize(myImage, (30,30))
                myHogImage = CalculateHOG(myImageResized)
                datas.append(np.ravel(myHogImage))
                labels.append(imagePathInt)
            # Burada model olusturacagim simdi
    x = 2
        # image = CalculateHOG(path, method)
        # if image is None:
        #     continue
        # datas.append(np.ravel(np.array(image)))
    #     if imagePath.__contains__("butterfly"):
    #         labels.append(0)
    #     else:
    #         labels.append(1)
    # print("SVM fit basliyor")
    # clf = svm.SVC()
    # clf.fit(datas, labels)
    # # cv2.imshow("image", image)
    # #  cv2.waitKey(0)
    #  # dosyaya kaydederiz
    # return clf

if __name__ =="__main__":
    modelOlustur()