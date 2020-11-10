import cv2
import Configuration as conf

if __name__ == "__main__":
    myConfigParams = conf.GetConfigFromFile()
    url = "rtsp://admin:admin1234@155.223.207.86/main"
    cap = cv2.VideoCapture(url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # latest frame
    while 1:
        ret, image = cap.read()
        cv2.imshow("Cam Test", image)
        k = cv2.waitKey(1)
        if k == 27:  # wait for ESC key to exit
            cv2.destroyAllWindows()
            break



