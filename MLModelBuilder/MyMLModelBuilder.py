import numpy as np
import cv2
import imutils
import os
from sklearn.externals import joblib
import json
from skimage.feature import hog
from skimage import data, exposure

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

def modelOlustur(method=None):
    dosyaYolu = "MLModelBuilder"
    imageList = os.listdir(dosyaYolu)
    for imagePath in imageList:
        print(imagePath)
        path = "{0}\\{1}".format(dosyaYolu, imagePath)
        image = OpencvCanny(path, method)
        if image is None:
            continue
        datas.append(np.ravel(np.array(image)))
        if imagePath.__contains__("butterfly"):
            labels.append(0)
        else:
            labels.append(1)
    print("SVM fit basliyor")
    clf = svm.SVC()
    clf.fit(datas, labels)
    # cv2.imshow("image", image)
    #  cv2.waitKey(0)
     # dosyaya kaydederiz
    return clf
