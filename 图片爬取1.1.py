import requests
import cchardet                          #用于处理网页编码
import asyncio, aiohttp                  #处理异步模块，处理异步请求模块
import os
import time                              #用于计时
from lxml import etree
from urllib.parse import urlparse        #判断图片地址合法性


def get_hub(url): #请求图片hub页，返回标题详情页url

    hub_next = url
    page_number = 0

    while 1:
        page_number += 1
        print('正在请求第%d页'%(page_number),':',hub_next)

        response = requests.get(url=hub_next, headers=headers)
        encoding = cchardet.detect(response.content)['encoding']
        hub_page = response.content.decode(encoding)

        tree = etree.HTML(hub_page)
        li_list = tree.xpath('//ul[@class="art_list"]/li/a/@href')

        #区分首尾页
        a_text = tree.xpath('//div[@class="page clearfix"]/a[@class="pagelink_a"]/text()')
        hub_next = tree.xpath('//div[@class="page clearfix"]/a[@class="pagelink_a"]/@href')[-2]
        hub_next = 'https://' + url.split('/')[2] + hub_next

        for li in li_list:
            li = 'https://' + url.split('/')[2] + li
            li_urls.append(li)
            print(li)

        if not '尾页' in a_text:
            break

    return li_urls, encoding, page_number


async def get_page(url, semaphore):   #请求图片标题详情页，返回图片地址
    async with semaphore:
        async with aiohttp.ClientSession() as session:
            async with await session.get(url=url, headers=headers) as response:
                detail_page = await response.text()

                tree = etree.HTML(detail_page)
                li_src = tree.xpath('//div[@class="content"]/li/img/@src')
                print(li_src)
                for img_url in li_src:
                    parse = urlparse(img_url)[0]
                    if not parse:
                        img_url = 'https:' + img_url
                    img_urls.append(img_url)


async def run_assist1():
    semaphore = asyncio.Semaphore(250)
    tasks1 = [get_page(url, semaphore) for url in li_urls]
    await asyncio.wait(tasks1)


def get_page_all(li_urls):    #异步运行get_page函数
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_assist1())

    return img_urls


async def download(url, semaphore):        #请求图片地址，得到数据并存入文件
    async with semaphore:
        async with aiohttp.ClientSession() as session:
            async with await session.get(url=url, headers=headers) as response:
                img_data = await response.read()
                img_name = url.split('/')[-2:]
                img_name = ''.join(img_name)
                with open(img_path+'/'+img_name, 'wb') as fp:
                    fp.write(img_data)
                print(url,'->',img_name,'下载成功 ！')


async def run_assist2():                   #用于解决select限制问题
    semaphore = asyncio.Semaphore(250)
    tasks2 = [download(url, semaphore) for url in img_urls]
    await asyncio.wait(tasks2)


def download_all(img_urls):     #异步运行download函数
    loop = asyncio.get_event_loop()
    loop.run_until_complete((run_assist2()))
    loop.close()


if __name__ == '__main__':
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0'
    }
    url = 'https://www.2221.life/tphtm/10.html'
    encoding = 'utf_8'
    img_path = './picture'
    li_urls = []           #存储所有标题页地址
    img_urls = []          #存储所有图片地址

    if not os.path.exists(img_path):
        os.mkdir(img_path)

    start_time = time.time()
    li_urls, encoding, page_number = get_hub(url)
    print('响应', ':', time.time() - start_time)
    print('页码数量', ':', page_number)
    print('标题数量', ':', len(li_urls))

    print('正在获取并生成图片地址......')
    pause_time = time.time()
    img_urls = get_page_all(li_urls)
    print(img_urls)
    print('响应', ':', time.time() - pause_time)

    print('正在下载图片......')
    pause_time = time.time()
    download_all(img_urls)
    print('响应', ':', time.time() - pause_time)

    print('页码数量', ':', page_number)
    print('标题数量', ':', len(li_urls))
    print('图片数量', ':', len(img_urls))
    print('本次下载共耗时', ':', time.time() - start_time)




