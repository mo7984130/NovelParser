__LAST_MODIFY__: str = "2025/05/26"

from bs4 import BeautifulSoup
import logging

import sys
sys.path.append('../')
from NovelParser import Chapter, NovelParser

__all__ = ['Parser']

class Parser(NovelParser):
    _base_host_url = "https://www.22biqu.com/"

    _headers = {
        "Host": "www.22biqu.com",
        "Referer": "https://www.22biqu.com/",
        "Pragma": "no-cache",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "sec-ch-ua": '''"Chromium";v="136", "Microsoft Edge";v="136", "Not.A/Brand";v="99"''',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
    }

    # 请求并解析主页
    def _parse_index(self, index_data):
        # 请求主页
        soup = BeautifulSoup(index_data, 'html.parser')
        # 获取书籍信息
        self._parse_book_info_div(soup.find('div', attrs={'class':'info'}))
        # 解析章节信息
        self._parse_chapter_list_div(soup.findAll('div', attrs={'class':'section-box'})[1])
        while True:
            next_page_a = soup.findAll('a', attrs={'class':'index-container-btn'})[1]
            if next_page_a.get('href') == 'javascript:void(0);': break
            next_index_data = self._get(self._base_host_url + next_page_a.get('href'))
            soup = BeautifulSoup(next_index_data, 'html.parser')
            self._parse_chapter_list_div(soup.findAll('div', attrs={'class':'section-box'})[1])

    # 解析书籍信息
    def _parse_book_info_div(self, book_info_div):
        book_info_div = book_info_div.find('div', attrs={'class':'top'})
        self._book_info.title = book_info_div.find('h1').text
        self._book_info.author = book_info_div.find('p').text

    # 解析章节信息
    def _parse_chapter_list_div(self, chapter_list_div):
        ul = chapter_list_div.find('ul')
        lis = ul.find_all('li')
        for dd in lis:
            self._last_no += 1
            a = dd.find('a')
            cpt = Chapter()
            cpt.title = a.text.replace(' ', '')
            cpt.url = self._base_host_url + a.get('href')
            cpt.no = self._last_no
            self._chapters.append(cpt)
   
    # 初始化指定章节内容
    def initChapter(self, chapter: Chapter):
        while chapter.content == None:
            soup = BeautifulSoup(self._request_chapter(chapter), 'html.parser')
            contents = soup.find('div', attrs={'id':'content'}).find_all('p')[1:]
            chapter.content = ''
            while True:
                for content in contents:
                    chapter.content += "    " + content.text.strip() + '\n'
                next_a = soup.find('a', attrs={'id':'next_url'})
                if next_a.text.strip() == '下一页':
                    next_url = self._base_host_url + next_a.get('href')
                    soup = BeautifulSoup(self._get(next_url), 'html.parser')
                    contents = soup.find('div', attrs={'id':'content'}).find_all('p')
                else: break
            
            logging.info(str(chapter) + "爬取完毕")