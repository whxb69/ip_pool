# encoding:utf-8
from bs4 import BeautifulSoup
import traceback
import requests
import base64
import cgitb
from fake_useragent import UserAgent
from retrying import retry
from threading import Thread
import time
import pymysql 
import pymysql.cursors 
from pymysql import IntegrityError

class pool():
    def __init__(self):
        self.https = []
        self.http = []
        self.ths = []
        self.ua = UserAgent()
        self.db = pymysql.connect(host='localhost', user='root', password='11010312', db='ip_pool', port=3306, charset='utf8')
        self.cursor = self.db.cursor()
        self.mutex = 0
        
    def run(self):
        th1 = Thread(target=self.get_ip, args=('http',))
        th1.start()
        self.ths.append(th1)
        th2 = Thread(target=self.get_ip, args=('https',))
        th2.start()
        self.ths.append(th2)
        
        for _ in range(2):
            th3 = Thread(target=self.check_ip, args=('http',))
            th3.start()
            self.ths.append(th3)
        
        for _ in range(2):
            th3 = Thread(target=self.check_ip, args=('https',))
            th3.start()
            self.ths.append(th3)
        
        for th in self.ths:
            th.join()

    def check_ip(self, tar='http'):
        if tar == 'http':
            tar_que = self.http
        else:
            tar_que = self.https
        
        headers = {'User-Agent': self.ua.random}        
        while tar_que:
            ip = tar_que[0]
            proxies = {
                'http':ip,
                'https':ip
            }
            try:
                res = requests.get('http://httpbin.org/ip', headers = headers, proxies = proxies).status_code
                if res!= 200:
                    tar_que.remove(ip)
                    print(ip+'\t丢弃')
            except:
                tar_que.remove(ip)
                print(ip+'\t丢弃')
                
            
    def get_ip(self, cate):
        num=1
        while 1:
            num+=1
            print(num)
            if cate == 'http':
                url = 'https://www.xicidaili.com/wt/'
            else:
                url = 'https://www.xicidaili.com/wn/'
            
            headers = {'User-Agent': self.ua.random}
            html = requests.get(url, headers = headers)
            soup = BeautifulSoup(html.text)
            ip_table = soup.find('table',attrs={"id":'ip_list'})
            ips1 = ip_table.find_all('odd')
            for ip in ips1:
                host = ip.find_all('td')[1]
                port = ip.find_all('td')[2]
                if cate == 'http':
                    ip = 'http://'+host+':'+port
                    self.set_db(ip, cate) 
                else:
                    ip = 'https://'+host+':'+port                
                    self.set_db(ip, cate)     
                print(ip+'\t加入')
            
            ips2 = ip_table.find_all('tr')[1:]
            for ip in ips2:
                host = ip.find_all('td')[1].text
                port = ip.find_all('td')[2].text
                if cate == 'http':
                    ip = 'http://'+host+':'+port
                    self.set_db(ip, cate) 
                else:
                    ip = 'https://'+host+':'+port                
                    self.set_db(ip, cate)  
                print(ip+'\t加入')
            time.sleep(10)
              
    def set_db(self, ip, cate):
        try:
            while self.mutex == 1:
                time.sleep(2)
            self.mutex = 1
            sql = "INSERT INTO %s (ip) VALUES('%s')" % (cate, ip)
            self.cursor.execute(sql)
            self.db.commit()
            self.mutex = 0            
        except IntegrityError:
            self.mutex = 0           
        
        
if __name__ == "__main__":
    pool().run()