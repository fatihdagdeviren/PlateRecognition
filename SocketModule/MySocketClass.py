# -*- coding: utf-8 -*-

import socket  # aynı şekilde burada da içeri dahil ediyoruz

class SocketSender():
    def __init__(self, conf):
        try:
            self.configuration = conf
            self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # bir socket nesnesi oluşturuyoruz
            self.host = self.configuration["Host"]  # bağlanacağımız adres
            self.port = self.configuration["Port"]  # bağlanacağımız kapı
            # self.host = socket.gethostname()  # Get the local machine name
            self.configuration = conf
            self.client.bind((self.host, 0))
            # print("Bağlantı yapıldı")
        except BaseException as e:
            print(str(e))
            pass

    def close(self):
        try:
            self.client.close()
        except BaseException as e:
            pass

    def send(self, data):
        try:
            self.client.sendto(bytes(data, encoding="utf-8"), (self.host, self.port))
        except BaseException as e:
            print(str(e))
            pass

    def receive(self):
        try:
            mesaj = self.client.recv(1024)
            print(mesaj)
        except BaseException as e:
            pass