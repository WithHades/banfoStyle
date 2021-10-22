import json
import os.path
import re
from collections.abc import Iterable

import requests

from config import BANFOMSGURL, BANFOMSGHEADERS


def getAllMsgUrl(start: int = 0) -> [Iterable, None]:
    """
    获取半佛仙人公众号文章.
    :param start: 起始索引
    :return: None
    """
    offset = start
    # 请将下面两个参数换成自己的!抓包公众号历史消息即可.
    while True:
        url = BANFOMSGURL.format(offset)
        headers = BANFOMSGHEADERS
        ret = requests.get(url, headers=headers)
        if ret.status_code != 200:
            return None
        data = json.loads(ret.text)
        if 'general_msg_list' not in data:
            return None
        can_msg_continue = data['can_msg_continue']
        data = json.loads(data['general_msg_list'])
        data = data['list']
        for msg in data:
            if 'app_msg_ext_info' not in msg:
                continue
            msgUrl = msg['app_msg_ext_info']['content_url']
            if len(msgUrl) >= 1:
                yield msgUrl
        if can_msg_continue == 1:
            offset += 10
        else:
            return None


def getText(msgUrl: str) -> str:
    """
    获取公众号单条文章的文本记录
    :param msgUrl:
    :return:
    """
    data = requests.get(msgUrl)
    if data.status_code != 200:
        return ''
    pattern = '<p style="[^<]*?">([^(<b)]+?)<|strong[^<]*?>([^<]*?)</strong>|<p>([^<]*?)</p>'
    matchs = re.findall(pattern, data.text)
    ret = ''
    for match in matchs:
        ret += match[0].strip() + match[1].strip() + match[2].strip()
    return ret.replace('半佛仙人', '').replace('看一看入口已关闭', '')


if __name__ == '__main__':
    for index, msgUrl in enumerate(getAllMsgUrl(start=0)):
        if index < 557:
            if index < 217 or index > 226:
                continue
        ret = getText(msgUrl)
        if ret == '':
            continue
        print(index, msgUrl)
        print(ret)
        with open(os.path.join('banfoText', '{}.txt'.format(index)), 'w+', encoding='utf-8') as f:
            f.write(ret)
    print('done!')
