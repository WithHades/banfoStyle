import base64
import hashlib
import json
import os
import random
import time
from collections.abc import Iterable
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup


def getUuid() -> str:
    """
    生成一个uuid
    :return: uuid
    """
    return str(random.randint(1, 999999)).zfill(6)


def getBaiDuAudio(text: str, filePath: str) -> [str, None]:
    """
    利用百度语音合成将文字合成语音
    :param text: 合成语音的文字
    :param filePath: 文件保存路径
    :return: 文件路径或者None
    """
    # 生成文件名
    md5 = hashlib.md5()
    md5.update(text.encode('utf-8'))
    fileName = md5.hexdigest() + '.mp3'
    fileName = os.path.join(filePath, fileName)
    # 文件已经存在的话直接返回
    if os.path.exists(fileName):
        return fileName

    url = 'https://cloud.baidu.com/aidemo'
    data = 'type=tns&per=4105&spd=8&pit=7&vol=5&aue=6&tex=' + quote(text)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    res = requests.post(url, data=data, headers=headers, verify=False)
    if res.status_code != 200:
        return None
    res = json.loads(res.text)
    if res['msg'] != 'success':
        return None
    data = res['data'].replace('data:audio/x-mpeg;base64,', '')
    if ',' in data:
        data = data[:data.find(',')]
    data = base64.b64decode(data)
    with open(fileName, 'wb') as f:
        f.write(data)
    return fileName


def decodeBaiduImg(objUrl: str) -> str:
    """
    百度图片地址解码函数
    :param objUrl: 编码的url
    :return: 解码的url
    """
    res = ''
    c = ['_z2C$q', '_z&e3B', 'AzdH3F']
    d = {'w': 'a',
         'k': 'b',
         'v': 'c',
         '1': 'd',
         'j': 'e',
         'u': 'f',
         '2': 'g',
         'i': 'h',
         't': 'i',
         '3': 'j',
         'h': 'k',
         's': 'l',
         '4': 'm',
         'g': 'n',
         '5': 'o',
         'r': 'p',
         'q': 'q',
         '6': 'r',
         'f': 's',
         'p': 't',
         '7': 'u',
         'e': 'v',
         'o': 'w',
         '8': '1',
         'd': '2',
         'n': '3',
         '9': '4',
         'c': '5',
         'm': '6',
         '0': '7',
         'b': '8',
         'l': '9',
         'a': '0',
         '_z2C$q': ':',
         '_z&e3B': '.',
         'AzdH3F': '/'}
    for m in c:
        objUrl = objUrl.replace(m, d[m])
    for char in objUrl:
        char = d[char] if char in d else char
        res = res + char
    return res


def getBaiduImgPath(text: str) -> [Iterable, None]:
    """
    从百度图片接口拉取图片
    :param text: 搜索关键字
    :return: 图片路径迭代器或者None
    """
    url = 'https://image.baidu.com/search/acjson?tn=resultjson_com&logid=8763701186511659178&ipn=rj&ct=201326592&is=' \
          '&fp=result&queryWord={0}&cl=2&lm=-1&ie=utf-8&oe=utf-8&adpicid=&st=-1&z=&ic=0&hd=&latest=&copyright=&word={0}' \
          '&s=&se=&tab=&width=&height=&face=0&istype=2&qc=&nc=1&fr=&expermode=&nojc=&acjsonfr=click&pn=0&rn=30&itg=1' \
          '&gsm=3c&1634043752626='
    url = url.format(text)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'}
    res = requests.get(url, headers=headers, verify=False)
    if res.status_code != 200:
        return None
    jsonData = json.loads(res.text)
    if 'data' not in jsonData:
        return None
    data = jsonData['data']
    for img in data:
        imgUrl = ''
        if 'objURL' in img:
            imgUrl = decodeBaiduImg(img['objURL'])
        elif 'middleURL' in img:
            imgUrl = img['middleURL']
        elif 'thumbURL' in img:
            imgUrl = img['thumbURL']
        elif imgUrl == '':
            return None
        if 'is_gif' in img and img['is_gif'] == 1:
            is_gif = 1
        else:
            is_gif = 0
        res = requests.get(imgUrl)
        if res.status_code != 200:
            continue
        md5 = hashlib.md5()
        md5.update(res.content)
        fileName = md5.hexdigest() + '.gif' if is_gif else md5.hexdigest() + '.png'
        path = os.path.join('tmp', fileName)
        with open(path, 'wb') as f:
            f.write(res.content)
        yield path


def getDoutulaImgPath(text: str) -> [Iterable, None]:
    """
    从斗图啦表情包接口拉取图片
    :param text: 搜索关键字
    :return: 图片路径迭代器或者None
    """
    url = 'https://www.doutula.com/search?keyword=' + text
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'}
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        return None
    soup = BeautifulSoup(res.text, 'html.parser')
    randomPics = soup.find_all('a', attrs={'class': 'col-xs-6 col-md-2'})
    for pic in randomPics:
        imgUrl = pic.find('img', attrs={'referrerpolicy': 'no-referrer'})['data-original']
        res = requests.get(imgUrl)
        if res.status_code != 200:
            continue
        path = os.path.join('tmp', imgUrl[imgUrl.rfind('/') + 1:])
        with open(path, 'wb') as f:
            f.write(res.content)
        yield path

