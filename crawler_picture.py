import argparse
import os
import time

import pandas
import requests
from bs4 import BeautifulSoup


from proxy_available import proxy_available


class Crawler():
    def __init__(self,args):

        self.headers = {'User-Agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Mobile Safari/537.36'}

        self.start_page = args.start_page                       # 起始页
        self.end_page = args.end_page                           # 截止页
        self.url = 'https://bing.ioliu.cn/ranking'              # url
        
        self.page_num = self.start_page

        self.if_write = args.write
        self.if_download = args.download
        self.download_num = 0
        self.if_analysis = args.analysis

        self.proxy_available = proxy_available

        self.pic_result_list = []                               # 图片信息汇总
        if self.if_write:
            pic_list = []
            pic_list.append('name/图片名')
            pic_list.append('description/描述')
            pic_list.append('calendar/日期')
            pic_list.append('location/地点')
            pic_list.append('view/查看次数')
            pic_list.append('like/点赞')
            pic_list.append('download_times/下载次数')
            self.pic_result_list.append(pic_list)
        if self.if_download:
            self.datatype = 'images'                            # 下载的图片保存至images文件夹下
            if not os.path.exists(self.datatype):
                os.makedirs(self.datatype)
            else:
                for i in os.listdir(self.datatype):
                    path_file = os.path.join(self.datatype,i)
                    if os.path.isfile(path_file):
                        os.remove(path_file)
        if self.if_analysis: 
            self.location_name = ['亚洲','欧洲','非洲','美洲','大洋洲']
            self.location_times = [0,0,0,0,0]

    def get_page(self, url): 
        if not url:
            url=self.url+'?p='+str(self.start_page)
        try:
            self.req = requests.get(url, headers=self.headers)
            if self.req.status_code == 200:                     # 状态码为200时进行解析
                self.decode(self.req.content)
            else:                                               # 状态码不为200时选择使用代理ip
                for i in range(0, len(self.proxy_available)):
                    proxy = self.proxy_available[i]
                    try:
                        self.req = requests.get(url, headers=self.headers, proxies=proxy)
                        if self.req.status_code == 200:
                            self.decode(self.req.content)
                            break
                    except:
                        print("该代理ip无效")
        except Exception as e:
            print("出现错误")
            print(e)

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
            if description.find('p', attrs={'class':'calendar'}):               # 获取日期
                calendar = description.find('p', attrs={'class':'calendar'}).find('em', attrs={'class':'t'}).getText()
            else:
                calendar = "0000-00-00"
            if description.find('p', attrs={'class':'location'}):               # 获取拍摄地址
                location = description.find('p', attrs={'class':'location'}).find('em', attrs={'class':'t'}).getText()
            else:
                location = "未知"
            if description.find('p', attrs={'class':'view'}):                   # 获取观看量
                view = description.find('p', attrs={'class':'view'}).find('em', attrs={'class':'t'}).getText()
            else:
                view = 0

            options = card.find('div', attrs={'class':'options'})
            if options.find('span', attrs={'class':'ctrl heart'}):              # 获取点赞量
                like = options.find('span', attrs={'class':'ctrl heart'}).find('em', attrs={'class':'t'}).getText()
            else:
                like = 0
            if options.find('a', attrs={'class':'ctrl download'}):              # 获取下载量
                download_times = options.find('a', attrs={'class':'ctrl download'}).find('em', attrs={'class':'t'}).getText()
            else:
                download_times = 0


            pic_list = []
            pic_list.append(pic_url.split('/')[-1])
            pic_list.append(description_text)
            pic_list.append(calendar)
            pic_list.append(location)
            pic_list.append(view)
            pic_list.append(like)
            pic_list.append(download_times)
            self.pic_result_list.append(pic_list)                               # 将图片信息保存至列表中
            
            if self.if_download:
                self.download(pic_url, self.datatype)                           # 下载图片

            if self.if_analysis:
                self.analysis(location)                                         # 分析拍摄地址
        
        if self.if_download:
            print('\n'+"第"+str(self.page_num)+"页下载完毕，该页耗时："+str(round(time.time()-start_time,2))+"s")
        if self.page_num == self.end_page:                                      # 此页为设定的最后一页
            if self.if_download:
                print("共下载 "+str(self.download_num)+" 张图片")
            if self.if_analysis:
                self.data_analysis()                                            # 进行拍摄地址的数据分析
            self.write()                                                        # 将所有图片信息写入表格中
            return 
        else:
            self.page_num += 1


        next_page = soup.find('div', attrs={'class','page'})                    # 寻找下一页
        for page in next_page.find_all('a'):
            if page.getText()=='下一页':
                if self.page_num == page['href'].split('?')[-1]:                # 下一页与当前页相等，表示已经到了最后一页
                    self.write()
                    if self.if_download:
                        print("共下载 "+str(self.download_num)+" 幅图片")
                    if self.if_analysis:
                        self.data_analysis()
                else:    
                    next = self.url + '?' + page['href'].split('?')[-1]
                    self.get_page(next)
            else:
                continue

    def download(self, pic_url, datatype):
        img = requests.get(pic_url)                                             # 获取图片数据
            
        if img.status_code == 200:
            img_path = datatype+'/'+pic_url.split('/')[-1]
            data_count = 0
            content_size = int(img.headers['content-length'])
            with open(img_path, "wb") as file:
                print('\n'+pic_url.split('/')[-1])
                for data in img.iter_content(chunk_size=1024):                  # 一块一块以下载，一块的大小为1MB
                    file.write(data)
                    data_count = data_count + len(data)
                    now = (data_count / content_size) * 50                      # 计算下载的进度
                    print('\r'+"已经下载："+int(now)*"="+" 【"+str(round(data_count/1024/1024,2))+"MB】"+"【"+str(round(float(data_count/content_size)*100,2))+"%"+"】", end='')
            self.download_num += 1
            
    def result(self):
        print(self.pic_result_list)

    def write(self):
        summaryDataFrame = pandas.DataFrame(self.pic_result_list)               # 将二位列表转化成DataFrame数据类型
        summaryDataFrame.to_excel("summary_pictures_biying.xlsx", encoding='utf-8', index=False, header=False)

    def analysis(self, location):
        for i in range(0, 5):
            if self.location_name[i] in location:
                self.location_times[i] += 1
                break

    def data_analysis(self):
        from pyecharts import options as opts                                           # 导入包
        from pyecharts.charts import Pie
        from pyecharts.render import make_snapshot
        c = Pie()                                                                       # 绘制饼状图
        c.add(
                "",
                [list(z) for z in zip(self.location_name, self.location_times)],
                radius=["40%", "75%"],		                                            # 内半径和外半径占比
            )
        c.set_global_opts(title_opts=opts.TitleOpts(title="壁纸拍摄地址分布图"),)
        c.set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}"))
        c.render('壁纸拍摄地址分布图.html')
        # make_snapshot(driver, c.render(), "图片地理位置分布图.png")                     # 需下载chromedriver


parser = argparse.ArgumentParser()
parser.add_argument("-s","--start_page",type=int,default=1,help="起始页")
parser.add_argument("-e","--end_page",type=int,default=1,help="终止页")
parser.add_argument("-d","--download",default=False,help="是否下载图片")
parser.add_argument("-w","--write",default=True,help="是否写入excel")
parser.add_argument("-a","--analysis",default=False,help="是否进行数据分析")
args = parser.parse_args()

crawler = Crawler(args)
crawler.get_page('')
# crawler.result()
# crawler.write()
# crawler.data_analysis()
