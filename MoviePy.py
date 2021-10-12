import hashlib
import json
import re

import numpy as np
import requests
from moviepy.editor import *
from moviepy.video.tools.segmenting import findObjects
import sys

from conf import backgroundMusic

import re


def decodeBaiduImg(objUrl):
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


url = 'https://image.baidu.com/search/acjson?tn=resultjson_com&logid=8763701186511659178&ipn=rj&ct=201326592&is=' \
      '&fp=result&queryWord={0}&cl=2&lm=-1&ie=utf-8&oe=utf-8&adpicid=&st=-1&z=&ic=0&hd=&latest=&copyright=&word={0}' \
      '&s=&se=&tab=&width=&height=&face=0&istype=2&qc=&nc=1&fr=&expermode=&nojc=&acjsonfr=click&pn=0&rn=30&itg=1' \
      '&gsm=3c&1634043752626='
url = url.format('山西人gif')
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'}
res = requests.get(url, headers=headers, verify=False)
if res.status_code != 200:
    exit(0)
jsonData = json.loads(res.text)
if 'data' in jsonData:
    data = jsonData['data']
    for img in data:
        imgUrl = ''
        if 'middleURL' in img:
            imgUrl = img['middleURL']
        if imgUrl == '' and 'thumbURL' in img:
            imgUrl = img['thumbURL']
        if 'replaceUrl' not in img:
            if 'objURL' in img:
                imgUrl = decodeBaiduImg(img['objURL'])
            else:
                print(img)
        if 'replaceUrl' in img and len(img['replaceUrl']) > 0:
            imgUrl = img['replaceUrl'][0]['ObjUrl']

        res = requests.get(imgUrl)
        if res.status_code != 200:
            continue
        md5 = hashlib.md5()
        md5.update(res.content)
        print(md5.hexdigest())
        if 'is_gif' in img and img['is_gif'] == 1:
            is_gif = 1
        else:
            is_gif = 0
        filename = md5.hexdigest() + '.gif' if is_gif else '.png'
        path = os.path.join('tmp', filename)
        print(path)
        with open(path, 'wb') as f:
            f.write(res.content)


xxx
screensize = (800, 600)
clip = ImageClip("test.jpg")
clip.set_memoize
final_clip = VideoFileClip('coolTextEffects.avi')
audioClip = AudioFileClip(backgroundMusic)
if audioClip.duration > final_clip.duration:
    audioClip = audioClip.subclip(0, final_clip.duration)
elif audioClip.duration < final_clip.duration:
    audioClip = afx.audio_loop(audioClip, duration=final_clip.duration)
final_clip = final_clip.set_audio(audioClip)
final_clip.write_videofile('coolTextEffects1.avi', fps=25, codec='mpeg4')

xxx
txtClip_1 = TextClip('一个小小的验证码', color='white', font="STKaiti", kerning=5, fontsize=60, align='South')
txtClip_2 = TextClip('居然也可以有上亿产业链?', color='white', font="STKaiti", kerning=5, fontsize=60, align='South')
cvc_1 = CompositeVideoClip([clip.subclip(0, 2).set_position(("center", "center")),
                            txtClip_1.set_position(("center", 0.85), relative=True)],
                           size=screensize)
cvc_2 = CompositeVideoClip([clip.set_position(("center", "center")),
                            txtClip_2.set_position(("center", 0.85), relative=True)],
                           size=screensize)

cvc_1 = cvc_1.subclip(0, 2)
cvc_2 = cvc_2.subclip(0, 2)
final_clip = concatenate_videoclips([cvc_1, cvc_2])
final_clip.write_videofile('coolTextEffects.avi', fps=25, codec='mpeg4')
