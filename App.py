import logging

import requests
from NovelParser import NovelParser
from ProxyManager import ProxyManager, HttpProxy

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)

ip_url = '''http://api.shenlongip.com/ip?key=r2hld60w&protocol=1&mr=1&pattern=txt&split=%5Cn&count=1&sign=4948b1c67770e82d1ff8d40757aa235b'''

def getNewProxy():
    data = requests.get(ip_url).text.split('\n')[0]
    proxy = HttpProxy(data.split(':')[0], data.split(':')[1])
    proxy.setLifeTime(10 * 60)
    proxy.setMaxUseCount(100)
    return proxy

if __name__ == "__main__":
    # proxyManager = ProxyManager(16, getNewProxy)
    # proxyManager.init()

    parser = NovelParser.getParser("https://www.22biqu.com/biqu5811/")
    parser.set_enbale_cache(True)
    parser.init()
    # parser.setProxyManager(proxyManager)
    logging.info(parser.getBookInfo())
    parser.setThreaPoolWorkers(800)
    print(parser.check_chapters())
    parser.initChapters()
    parser.save()