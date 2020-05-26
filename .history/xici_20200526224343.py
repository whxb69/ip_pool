# encoding:utf-8
from bs4 import BeautifulSoup
import traceback
import requests
import base64
import cgitb
from fake_useragent import UserAgent
from retrying import retry
from threading import Thread, Lock
import time
import pymysql 
import pymysql.cursors 
from pymysql import IntegrityError

class pool():
    def __init__(self):
        self.ths = []
        self.ua = UserAgent()
        self.db = pymysql.connect(host='localhost', user='root', password='11010312', db='ip_pool', port=3306, charset='utf8')
        self.cursor = self.db.cursor()
        self.lock = Lock()
        self.tmp_ips = [] #暂存ip
        
    def run(self):
        th1 = Thread(target=self.get_ip, args=('http',))
        th1.start()
        self.ths.append(th1)
        th2 = Thread(target=self.get_ip, args=('https',))
        th2.start()
        self.ths.append(th2)
        
        time.sleep(5)
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
        sql = 'SELECT ip FROM %s' %(tar)
        self.cursor.execute(sql)
        ips = self.cursor.fetchall()
        headers = {'User-Agent': self.ua.random}  
        [self.tmp_ips.append(ip[0]) for ip in ips] 
        n = 0
        while n < len(self.tmp_ips):
            ip = self.tmp_ips[n]
            proxies = {
                'http':ip,
                'https':ip.replace('http://','https://')
            }
            try:
                res = requests.get('http://httpbin.org/ip', headers = headers, proxies = proxies, timeout = 20).status_code
                if res == 200:
                    n+=1
                    print(ip+'\验证')
                else:
                    self.del_ip(tar, ip)
                    print(ip+'\t丢弃')
            except:
                self.del_ip(tar, ip)
                print(ip+'\t丢弃')
    def del_ip(self, tar, ip):
        sql = 'DELETE * FROM %s WHERE ip = %s' % (tar,ip)
        self.lock.acquire()
        try:
            self.tmp_ips.remove(ip)
            self.cursor.execute(sql)
            self.db.commit()
        except:
            self.del_ip(tar, ip)
        finally:
            self.lock.release()
        
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
            self.lock.acquire()
            sql = "INSERT INTO %s (ip) VALUES('%s')" % (cate, ip)
            self.cursor.execute(sql)
            self.db.commit()
            self.lock.release()          
        except IntegrityError:
            self.lock.release()          
        
if __name__ == "__main__":
    pool().run()
    # pool().check_ip()