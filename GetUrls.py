# coding: utf-8
import html
import os
import random
import re
import time
from pprint import pprint
import json
import pandas as pd  # 如果需要保存至excel表格的话
import requests
from wechatarticles import ArticlesInfo, ArticlesUrls
from wechatarticles.GetUrls import PCUrls
import urllib.parse


def flatten(x):
    return [y for l in x for y in flatten(l)] if type(x) is list else [x]


def transfer_url(url):
    url = html.unescape(html.unescape(url))
    return eval(repr(url).replace('\\', ''))


def verify_url(article_url):
    verify_lst = ["mp.weixin.qq.com", "__biz", "mid", "sn", "idx"]
    for string in verify_lst:
        if string not in article_url:
            return False
    return True


def get_all_urls(urls):
    # 获取所有的url
    url_lst = []
    for item in urls:
        url_lst.append(transfer_url(item['app_msg_ext_info']['content_url']))
        if 'multi_app_msg_item_list' in item['app_msg_ext_info'].keys():
            for ss in item['app_msg_ext_info']['multi_app_msg_item_list']:
                url_lst.append(transfer_url(ss['content_url']))

    return url_lst


def get_all_urls_title_date(urls):
    # 获取所有的[url, title, date]
    url_lst = []

    for item in urls:
        timestamp = item['comm_msg_info']['datetime']
        time_local = time.localtime(timestamp)
        # 转换成日期
        time_temp = time.strftime("%Y-%m-%d", time_local)

        # 文章url
        url_temp = transfer_url(item['app_msg_ext_info']['content_url'])

        # 文章标题
        title_temp = item['app_msg_ext_info']['title']
        url_lst.append([url_temp, title_temp, time_temp])

        if 'multi_app_msg_item_list' in item['app_msg_ext_info'].keys():
            for info in item['app_msg_ext_info']['multi_app_msg_item_list']:

                url_temp = transfer_url(info['content_url'])

                title_temp = info['title']
                url_lst.append([url_temp, title_temp, time_temp])

    return url_lst


def method_one(biz, uin, cookie, key):

    t = PCUrls(biz=biz, uin=uin, cookie=cookie)
    count = 0
    lst = []
    while True:
        res = t.get_urls(key, offset=count)
        if res == []:
            break
        count += 10
        lst.append(res)

    return lst


def get_info_from_url(url):
    html = requests.get(url).text
    try:
        res = re.findall(r'publish_time =.+\|\|?', html)
        date = res[0].split('=')[1].split('||')[0].strip()
    except:
        date = None

    try:
        res = re.findall(r'nickname .+;?', html)
        offical_name = res[0].split('=')[1][:-1].strip()
    except:
        offical_name = None

    try:
        res = re.findall(r'msg_title = .+;?', html)
        aritlce_name = res[0].split('=')[1][:-1].strip()
    except:
        aritlce_name = None

    return date, offical_name, aritlce_name


def save_xlsx(fj, lst):
    df = pd.DataFrame(
        lst,
        columns=['url', 'title', 'date', 'read_num', 'like_num', 'comments'])
    df.to_excel(fj + '.xlsx', encoding='utf-8')


def get_data(url):
    pass

