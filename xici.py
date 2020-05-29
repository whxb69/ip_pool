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
import aiohttp
import asyncio

class pool():
    def __init__(self):
        self.ths = []
        self.ua = UserAgent()
        self.db = pymysql.connect(host='localhost', user='root', password='11010312', db='ip_pool', port=3306, charset='utf8')
        self.cursor = self.db.cursor()
        self.lock = Lock()
        self.tmp = []
        self.inuse = []

    '''
    建立临时ip列表
    '''
    def set_tmp(self):
        if not self.tmp:
            sql = 'SELECT ip FROM ips'
            self.lock.acquire()
            self.cursor.execute(sql)
            self.lock.release()
            ips = self.cursor.fetchall()
            self.tmp = []#暂存ip
            [self.tmp.append(ip[0]) for ip in ips] 
    
    '''
    启动爬取和验证
    '''
    def run(self):
        #爬取xici
        thx1 = Thread(target=self.get_xici, args=('http',))
        thx1.start()
        self.ths.append(thx1)
        thx2 = Thread(target=self.get_xici, args=('https',))
        thx2.start()
        self.ths.append(thx2)
        
        #爬取kuaidaili
        thk1 = Thread(target=self.get_kuai, args=('1',))
        thk1.start()
        self.ths.append(thk1)
        thk2 = Thread(target=self.get_kuai, args=('2',))
        thk2.start()
        self.ths.append(thk2)
        
        
        self.set_tmp()        
        for _ in range(2):
            th3 = Thread(target=self.check_ip)
            th3.start()
            self.ths.append(th3)
        
        for th in self.ths:
            th.join()

    '''
    验证ip
    '''
    def check_ip(self):
        print('开始检查')
            
        headers = {'User-Agent': self.ua.random}          
        while self.tmp:
            while len(self.tmp)<5:
                time.sleep(500)
            ip = self.tmp.pop(0)
            
            # conn = aiohttp.TCPConnector(verify_ssl=False)
            # async with aiohttp.ClientSession(connector=conn) as session:
            #     try:
            #         proxy = tar + '://' + ip
            #         async with session.get('http://httpbin.org/ip', proxy=proxy, timeout=15) as response:
            #             if response.status in [200]:
            #                 print(ip+'\t验证')
            #                 tar_que.append(ip)
            #             else:
            #                 self.del_ip(tar, ip)
            #                 print(ip+'\t丢弃')
            #     except Exception as e:
            #         self.del_ip(tar, ip)
            #         print(ip+'\t丢弃')
            
            try:
                proxies = {'https':'https://' + ip, 'http':'http://' + ip}
                res = requests.get('http://httpbin.org/ip', headers = headers, proxies = proxies, timeout = 20).status_code
                if res == 200:
                    print(ip+'\t验证')
                    self.set_100(ip)
                    self.tmp.append(ip)
                else:
                    self.decrease(ip)
            except Exception as e:
                self.decrease(ip)
        time.sleep(2000)
        return self.check_ip()
    
    '''
    为未通过验证ip减分
    '''
    def decrease(self, ip):
        sql = "SELECT score FROM ips WHERE ip = '%s'" % (ip)
        self.lock.acquire()            
        if self.cursor.execute(sql):
            score = self.cursor.fetchone()[0]
        self.lock.release()  
        
        if score>1:
            sql = "UPDATE ips SET score = score-1 WHERE ip = '%s'" % (ip)
            try:
                self.lock.acquire()            
                self.cursor.execute(sql)
                self.db.commit()
                self.lock.release() 
                print(ip+'\t减分')                       
            except Exception as e:
                self.lock.release()
        else:
            self.del_ip(ip)               
    
    '''
    为通过验证ip置满分
    '''     
    def set_100(self, ip):
        sql = "UPDATE ips SET score = '%d' WHERE ip = '%s'" % (100, ip)
        try:
            self.lock.acquire()            
            self.cursor.execute(sql)
            self.db.commit()
            self.lock.release()                        
        except Exception as e:
            self.lock.release()
    
    '''
    删除不可用ip
    '''
    def del_ip(self, ip):
        sql = "DELETE FROM ips WHERE ip = '%s'" % (ip)
        try:
            if ip in self.tmp:
                self.tmp.remove(ip)
            self.lock.acquire()            
            self.cursor.execute(sql)
            self.db.commit()
            self.lock.release() 
            print(ip+'\t丢弃')                     
        except Exception as e:
            self.lock.release()
    
    def get_kuai(self, page):
        headers = {'Host': 'www.kuaidaili.com',
                   'User-Agent':self.ua.random}
        url = 'https://www.kuaidaili.com/free/inha/%s' % page
        html = requests.get(url, headers=headers)
        if html.status_code==503:
            time.sleep(1)
            html = requests.get(url, headers=headers)
            
        soup = BeautifulSoup(html.text)
        trs = soup.find('tbody').find_all('tr')
        for tr in trs:
            tds = tr.find_all('td')
            ip = tds[0].text+':'+tds[1].text
            self.set_db(ip) 
        
    '''
    爬取新ip
    '''
    def get_xici(self, cate):
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
            if html.status_code != 200:
                time.sleep(10000)
                return self.get_xici(cate)
            soup = BeautifulSoup(html.text)
            ip_table = soup.find('table',attrs={"id":'ip_list'})
            ips1 = ip_table.find_all('odd')
            for ip in ips1:
                host = ip.find_all('td')[1]
                port = ip.find_all('td')[2]
                ip = host + ':' + port
                self.set_db(ip) 
            
            ips2 = ip_table.find_all('tr')[1:]
            for ip in ips2:
                host = ip.find_all('td')[1].text
                port = ip.find_all('td')[2].text
                ip = host + ':' + port
                self.set_db(ip) 
            time.sleep(1000)
    
    '''
    存储新爬取ip
    '''
    def set_db(self, ip):
        try:
            self.lock.acquire()
            sql = "INSERT INTO ips (ip) VALUES('%s')" % (ip)
            self.cursor.execute(sql)
            self.db.commit()
            self.lock.release() 
            print(ip+'\t加入')           
        except IntegrityError:
            self.lock.release()   
    
    '''
    获取ip
    '''
    def get_pro(self):
        sql = 'SELECT ip,score FROM ips ORDER BY score DESC LIMIT 20'
        try:
            self.lock.acquire()
            self.cursor.execute(sql)
            ips = self.cursor.fetchall()
            self.lock.release() 
            for ip in ips:
                if ip[0] not in self.inuse:
                    return ip[0]         
        except IntegrityError:
            self.lock.release()  
    
    '''
    释放ip的使用状态
    '''
    def freeuse(self, ip):
        if ip in self.inuse:
            self.inuse.remove(ip)    
        
if __name__ == "__main__":
    pool().run()