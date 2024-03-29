import cv2
import time
import multiprocessing as mp

#https://stackoverflow.com/questions/60816436/open-cv-rtsp-camera-buffer-lag

class camera():
    def __init__(self,rtsp_url):
        #load pipe for data transmittion to the process
        self.parent_conn, child_conn = mp.Pipe()
        #load process
        self.p = mp.Process(target=self.update, args=(child_conn,rtsp_url))
        #start process
        self.p.daemon = True
        self.p.start()
        print("Camera İnit oldu")

    def end(self):
        #send closure request to process
        self.parent_conn.send(2)

    def update(self,conn,rtsp_url):
        try:
            #load cam into seperate process
            print("Cam Loading...")
            cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
            print("Cam Loaded...")
            run = True
            while run:
                #grab frames from the buffer
                cap.grab()
                #recieve input data
                rec_dat = conn.recv()
                if rec_dat == 1:
                    #if frame requested
                    ret,frame = cap.read()
                    conn.send(frame)
                elif rec_dat == 2:
                    #if close requested
                    cap.release()
                    run = False
            print("Camera Connection Closed")
            conn.close()
        except BaseException as e:
            print("update_frame".format(str(e)))
            return None

    def get_frame(self,resize=None):
        try:
            print("GetFrame ici")
            ###used to grab frames from the cam connection process
            ##[resize] param : % of size reduction or increase i.e 0.65 for 35% reduction  or 1.5 for a 50% increase
            #send request
            self.parent_conn.send(1)
            print("self.parent_conn.send(1")
            frame = self.parent_conn.recv()
            print("Frame Shape : {0}".format(frame.shape))
            print("self.parent_conn.recv()")
            #reset request
            self.parent_conn.send(0)
            print("self.parent_conn.send(0)")
            #resize if needed
            if resize == None:
                return frame
            else:
                return self.rescale_frame(frame,resize)
        except BaseException as e:
            print("get_frame".format(str(e)))
            return None

    def rescale_frame(self,frame, percent=65):
        return cv2.resize(frame,None,fx=percent,fy=percent)



import cv2, queue, threading, time

# bufferless VideoCapture
class VideoCapture:

  def __init__(self, name):
    self.cap = cv2.VideoCapture(name)
    self.q = queue.Queue()
    t = threading.Thread(target=self._reader)
    t.daemon = True
    t.start()

  # read frames as soon as they are available, keeping only most recent one
  def _reader(self):
    while True:
      ret, frame = self.cap.read()
      if not ret:
        break
      if not self.q.empty():
        try:
          self.q.get_nowait()   # discard previous (unprocessed) frame
        except queue.Empty:
          pass
      self.q.put(frame)

  def read(self):
    return self.q.get()