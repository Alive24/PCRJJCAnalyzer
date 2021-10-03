from requests import post
from ctypes import CDLL, CFUNCTYPE, c_int, c_char_p
from random import choices
from time import time
from platform import architecture
from json import dumps
from os.path import join, dirname

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36 Edg/87.0.664.66",
    "Referer": "https://pcrdfans.com/",
    "Origin": "https://pcrdfans.com",
    "Accept": "*/*",
    "Content-Type": "application/json; charset=utf-8",
    "Authorization": "",
    "Host": "api.pcrdfans.com",
}

def _getNonce():
    return ''.join(choices("0123456789abcdefghijklmnopqrstuvwxyz", k=16))

def _getTs():
    return int(time())

def _dumps(x):
    return dumps(x, ensure_ascii=False).replace(' ', '')

gsign = None

def _callback(sign):
    global gsign
    gsign = sign.decode('gbk')
    return 0

_c_callback = CFUNCTYPE(c_int, c_char_p)(_callback)

_getsign = CDLL(join(dirname(__file__), f'PCRDwasm_{architecture()[0]}.dll')).getSign

def sign(data):
    data["nonce"] = _getNonce()
    _getsign(_dumps(data).encode('utf8'), data["nonce"].encode('utf8'), _c_callback)
    data["_sign"] = gsign

async def callPcrd(_def, page, region, sort, proxies=None):
    data = {
        "def": _def,
        "nonce": _getNonce(),
        "page": page,
        "region": region,
        "sort": sort,
        "ts": _getTs()
    }

    _getsign(_dumps(data).encode('utf8'), data["nonce"].encode('utf8'), _c_callback)
    data["_sign"] = gsign

    resp = await post("https://api.pcrdfans.com/x/v1/search", headers=headers, data=_dumps(data).encode('utf8'), proxies=proxies)
    return await resp.json()

'''‘
from nonebot import on_startup
@on_startup
async def startup():
    print(await callPcrd([170101,107801,100701,104501,102901], 1, 1, 1, {
    "https": "localhost:1080"}))

'''