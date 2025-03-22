"""这个是解析系统的具体实现模块。
没有特殊需求就不要再改来改去了，虽然看起来很屎山。
别骂了别骂了.jpg"""

import json
import os
import urllib.parse
from hashlib import md5
from random import randrange
import requests
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# 在文件开头定义全局变量 COOKIE
COOKIE = "MUSIC_U=1eb9ce22024bb666e99b6743b2222f29ef64a9e88fda0fd5754714b900a5d70d993166e004087dd3b95085f6a85b059f5e9aba41e3f2646e3cebdbec0317df58c119e5;os=pc;appver=8.9.75;"


def hex_digest(data):
    return "".join([hex(d)[2:].zfill(2) for d in data])


def hash_digest(text):
    _hash = md5(text.encode("utf-8"))
    return _hash.digest()


def hash_hex_digest(text):
    return hex_digest(hash_digest(text))


def parse_cookie(text: str):
    cookie_ = [item.strip().split('=', 1) for item in text.strip().split(';') if item]
    cookie_ = {k.strip(): v.strip() for k, v in cookie_}
    return cookie_


def ids(ids):
    if '163cn.tv' in ids:
        response = requests.get(ids, allow_redirects=False)
        ids = response.headers.get('Location')
    if 'music.163.com' in ids:
        index = ids.find('id=') + 3
        ids = ids[index:].split('&')[0]
    return ids


def size(value):
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = 1024.0
    for i in range(len(units)):
        if (value / size) < 1:
            return "%.2f%s" % (value, units[i])
        value = value / size
    return value


def music_level1(value):
    levels = {
        'standard': "标准音质",
        'exhigh': "极高音质",
        'lossless': "无损音质",
        'hires': "Hires音质",
        'sky': "沉浸环绕声",
        'jyeffect': "高清环绕声",
        'jymaster': "超清母带"
    }
    return levels.get(value, "未知音质")


def post(url, params, cookie):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36 Chrome/91.0.4472.164 NeteaseMusicDesktop/2.10.2.200154',
        'Referer': '',
    }
    cookies = {
        "os": "pc",
        "appver": "",
        "osver": "",
        "deviceId": "pyncm!"
    }
    cookies.update(cookie)
    response = requests.post(url, headers=headers, cookies=cookies, data={"params": params})
    return response.text


def get_url(id, level, cookies):
    url = "https://interface3.music.163.com/eapi/song/enhance/player/url/v1"
    AES_KEY = b"e82ckenh8dichen8"
    config = {
        "os": "pc",
        "appver": "8.9.75",  # 确保版本号正确
        "osver": "",  # 操作系统版本
        "deviceId": "pyncm!",  # 设备 ID
        "requestId": str(randrange(20000000, 30000000)),  # 随机请求 ID
    }

    payload = {
        'ids': [id],
        'level': level,
        'encodeType': 'flac',  # 或其他编码类型
        'header': json.dumps(config),
    }

    if level == 'sky':
        payload['immerseType'] = 'c51'

    url2 = urllib.parse.urlparse(url).path.replace("/eapi/", "/api/")
    digest = hash_hex_digest(f"nobody{url2}use{json.dumps(payload)}md5forencrypt")
    params = f"{url2}-36cd479b6b5-{json.dumps(payload)}-36cd479b6b5-{digest}"

    """ 调试信息
    print("DEBUG: Original payload:", payload)  # 打印原始参数
    print("DEBUG: Encrypted params:", params)  # 打印加密后的参数
    """

    padder = padding.PKCS7(algorithms.AES(AES_KEY).block_size).padder()
    padded_data = padder.update(params.encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(AES_KEY), modes.ECB())
    encryptor = cipher.encryptor()
    enc = encryptor.update(padded_data) + encryptor.finalize()
    params = hex_digest(enc)

    try:
        response = post(url, params, cookies)
        return json.loads(response)
    except json.decoder.JSONDecodeError:
        return None


def get_name(id):
    urls = "https://interface3.music.163.com/api/v3/song/detail"
    data = {'c': json.dumps([{"id": id, "v": 0}])}
    response = requests.post(url=urls, data=data)
    return response.json()


def get_lyrics(id, cookies):
    url = "https://interface3.music.163.com/api/song/lyric"
    data = {'id': id, 'cp': 'false', 'tv': '0', 'lv': '0', 'rv': '0', 'kv': '0', 'yv': '0', 'ytv': '0', 'yrv': '0'}
    response = requests.post(url=url, data=data, cookies=cookies)
    return response.json()


# 主程序
def parse(url, level):
    level_options = {
        '1': 'standard',
        '2': 'exhigh',
        '3': 'lossless',
        '4': 'hires',
        '5': 'sky',
        '6': 'jyeffect',
        '7': 'jymaster'
    }

    level = level_options.get(level, 'lossless')

    # 解析歌曲信息
    song_id = ids(url)
    cookies = parse_cookie(COOKIE)  # 使用全局变量 COOKIE
    urls = get_url(song_id, level, cookies)
    if not urls:
        print("错误：无法获取歌曲信息，请检查URL或音质设置。")
        return "错误：无法获取歌曲信息，请检查URL或音质设置。"

    names = get_name(urls['data'][0]['id'])
    lyrics_data = get_lyrics(urls['data'][0]['id'], cookies)

    # 提取歌曲详情
    song_name = names['songs'][0]['name']
    song_pic = names['songs'][0]['al']['picUrl']
    artist_names = ', '.join(artist['name'] for artist in names['songs'][0]['ar'])
    album_name = names['songs'][0]['al']['name']
    music_quality = music_level1(urls['data'][0]['level'])
    file_size = size(urls['data'][0]['size'])
    music_url = urls['data'][0]['url']
    lyrics = lyrics_data['lrc']['lyric']
    translated_lyrics = lyrics_data.get('tlyric', {}).get('lyric', None)

    # 输出结果
    output_text = f"""
    歌曲名称: {song_name}
    歌曲图片: {song_pic}
    歌手: {artist_names}
    专辑名称: {album_name}
    音质: {music_quality}
    大小: {file_size}
    音乐链接: {music_url}
    歌词: {lyrics}
    翻译歌词: {translated_lyrics if translated_lyrics else '没有翻译歌词'}
    """

    meta_dict = {"song_name": song_name,
                 "song_pic": song_pic,
                 "artist_names": artist_names,
                 "album_name": album_name,
                 "music_quality": music_quality,
                 "file_size": file_size,
                 "music_url": music_url,
                 "lyrics": lyrics,
                 "translated_lyrics": (translated_lyrics if translated_lyrics else '没有翻译歌词')}

    print(output_text)
    return output_text, meta_dict


if __name__ == '__main__':
    parse("https://music.163.com/#/song?id=1306371615", 7)
