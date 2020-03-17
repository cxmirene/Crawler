import requests
import os
import time
import pandas
import argparse
from bs4 import BeautifulSoup

class Crawler():
    def __init__(self,args):

        self.headers = {'User-Agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Mobile Safari/537.36'}

        self.start_page = args.start_page
        self.end_page = args.end_page
        self.url = 'https://bing.ioliu.cn/ranking'
        
        self.page_num = 1

        self.if_write = args.write
        self.if_download = args.download
        self.download_num = 0

        self.pic_result_list = []
        if self.if_write:
            pic_list = []
            pic_list.append('name')
            pic_list.append('description')
            pic_list.append('calendar')
            pic_list.append('location')
            pic_list.append('view')
            self.pic_result_list.append(pic_list)
        if self.if_download:
            self.datatype = 'images'
            if not os.path.exists(self.datatype):
                os.makedirs(self.datatype)

    def get_page(self, url):
        if not url:
            url=self.url+'?p='+str(self.start_page)
        self.req = requests.get(url, headers=self.headers)
        if self.req.status_code == 200:
            self.decode(self.req.content)

    def decode(self, html):

        soup = BeautifulSoup(html, "html.parser")
        mask = soup.find('body').find('div', attrs={'class':'mask'})
        container = mask.next_sibling

        start_time = time.time()

        for picture in container.find_all('div', attrs={'class':'item'}):
            card = picture.find('div', attrs={'class':'card progressive'})
            pic = card.find('img')
            pic_url = pic['src'].split('?')[0]

            description = card.find('div', attrs={'class':'description'})
            description_text = description.find('h3').getText()
            if description.find('p', attrs={'class':'calendar'}):
                calendar = description.find('p', attrs={'class':'calendar'}).find('em', attrs={'class':'t'}).getText()
            else:
                calendar = "0000-00-00"
            if description.find('p', attrs={'class':'location'}):
                location = description.find('p', attrs={'class':'location'}).find('em', attrs={'class':'t'}).getText()
            else:
                location = "未知"
            if description.find('p', attrs={'class':'view'}):
                view = description.find('p', attrs={'class':'view'}).find('em', attrs={'class':'t'}).getText()
            else:
                view = 0

            pic_list = []
            pic_list.append(pic_url.split('/')[-1])
            pic_list.append(description_text)
            pic_list.append(calendar)
            pic_list.append(location)
            pic_list.append(view)
            self.pic_result_list.append(pic_list)
            
            if self.if_download:
                self.download(pic_url, self.datatype)
        
        if self.if_download:
            print('\n'+"第"+str(self.page_num)+"页下载完毕，该页耗时："+str(round(time.time()-start_time,2))+"s")
        if self.page_num == self.end_page:
            if self.if_download:
                print("共下载 "+str(self.download_num)+" 张图片")
            return 
        else:
            self.page_num += 1


        next_page = soup.find('div', attrs={'class','page'})
        for page in next_page.find_all('a'):
            if page.getText()=='下一页':
                next = self.url + '?' + page['href'].split('?')[-1]
                self.get_page(next)
            else:
                if self.if_download:
                    print("共下载 "+str(self.download_num)+" 幅图片")

    def download(self, pic_url, datatype):
        img = requests.get(pic_url)
            
        if img.status_code == 200:
            img_path = datatype+'/'+pic_url.split('/')[-1]
            data_count = 0
            content_size = int(img.headers['content-length'])
            with open(img_path, "wb") as file:
                print('\n'+pic_url.split('/')[-1])
                for data in img.iter_content(chunk_size=1024): # 一块一块以下载
                    file.write(data)
                    data_count = data_count + len(data)
                    now = (data_count / content_size) * 50 # 计算下载的进度
                    print('\r'+"已经下载："+int(now)*"="+" 【"+str(round(data_count/1024/1024,2))+"MB】"+"【"+str(round(float(data_count/content_size)*100,2))+"%"+"】", end='')
            self.download_num += 1
            
    def result(self):
        print(self.pic_result_list)

    def write(self):
        summaryDataFrame = pandas.DataFrame(self.pic_result_list)
        summaryDataFrame.to_excel("summary_pictures_biying.xlsx", encoding='utf-8', index=False, header=False)


parser = argparse.ArgumentParser()
parser.add_argument("-s","--start_page",type=int,default=1,help="起始页")
parser.add_argument("-e","--end_page",type=int,default=1,help="终止页")
parser.add_argument("-d","--download",default=False,help="是否下载图片")
parser.add_argument("-w","--write",default=True,help="是否写入excel")
args = parser.parse_args()

crawler = Crawler(args)
crawler.get_page('')
# crawler.result()
crawler.write()
