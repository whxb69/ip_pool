# encoding:utf-8
from bs4 import BeautifulSoup
import traceback
import requests
from eng2chs import readip
import sqlite3
from sqlite3 import IntegrityError
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import base64
import cgitb
from fake_useragent import UserAgent
from retrying import retry
from threading import Thread

class pool():
    def __init__(self):
        self.https = []
        self.http = []
        self.ths = []
        
    def run(self):
        th1 = Thread(self.get_ip, args=('http'))
        th1.start()
        self.ths.append(th1)
        th2 = Thread(get_ip, args=('https'))
        th2.start()
        self.ths.append(th2)
        
        for _ in range(2):
            th3 = Thread(check_ip, args=('http'))
            th3.start()
            self.ths.append(th3)
        
        for _ in range(2):
            th3 = Thread(check_ip, args=('https'))
            th3.start()
            self.ths.append(th3)

    def check_ip(self, tar='http'):
        if tar == 'http':
            tar_que = self.http
        else:
            tar_que = self.https
        
        while tar_que:
            ip = tar_que[0]
            res = requests.get('http://httpbin.org/ip').status_code
            if res!= 200:
                tar_que.remove(ip)
                print(ip+'\t丢弃')
            
    def get_ip(self, cate):
        if cate == 'http':
            url = 'https://www.xicidaili.com/wt/'
        else:
            url = 'https://www.xicidaili.com/wn/'
        html = requests.get(url)
        soup = BeautifulSoup(html.text)
        ip_table = soup.find('talbe',attrs={"id":'ip_list'})
        ips1 = ip_table.find_all('odd')
        for ip in ips1:
            host = ip.find_all('td')[1]
            port = ip.find_all('td')[2]
            if cate == 'http':
                ip = 'http://'+host+':'+port
                self.http.append(ip)
            else:
                ip = 'https://'+host+':'+port                
                self.https.append(ip)    
            print(ip+'\t加入')
            
        ips2 = ip_talbe.find_all('tr')
        for ip in ips2:
            host = ip.find_all('td')[1]
            port = ip.find_all('td')[2]
            if cate == 'http':
                ip = 'http://'+host+':'+port
                self.http.append(ip)
            else:
                ip = 'https://'+host+':'+port                
                self.https.append(ip)    
            print(ip+'\t加入')
              
    
if __name__ == "__main__":
    pool.run()