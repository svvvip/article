import re
from html import unescape
from urllib.parse import parse_qs, urlparse

from curl_cffi import requests

from app.core.config import config_manager
from pyquery import PyQuery as pq


class X1080X:
    domain = 'https://agaghhh.cc'

    def bypass_cf(self, url):
        payload = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 60000,
            "proxy": {"url": config_manager.get().PROXY},
        }
        res = requests.post(config_manager.get().FLARE_SOLVERR_URL, headers={"Content-Type": "application/json"},
                            json=payload)
        result = res.json()
        if result['solution']['status'] != 200:
            return None
        html = result['solution']['response']
        return html

    def get_tid_from_list(self, fid, typeid, page):

        url = f"{self.domain}/forum.php?mod=forumdisplay&fid={fid}&archiver=1&page={page}&filter=typeid&typeid={typeid}"
        html = self.bypass_cf(url)
        if html:
            doc = pq(html)
            content = doc('#content')
            tids = [
                parse_qs(urlparse(a.attr('href')).query)['tid'][0]
                for a in content('a[href*="viewthread"]').items()
            ]
            return [int(tid) for tid in tids]
        return []

    def get_detail_by_tid(self, tid):
        url = f"{self.domain}/forum.php?mod=viewthread&tid={tid}&archiver=1"
        html = self.bypass_cf(url)
        if html:
            doc = pq(html)
            nav = doc('#nav').text()
            title = nav.split('›')[-1].strip()
            text = doc('p.author').text()
            publish_date = text.split('发表于')[-1].strip().split(' ')[0]
            content_html = doc('#content').html()
            img_urls = re.findall(r'\[img\](.*?)\[/img\]', content_html)
            code_blocks = re.findall(r'\[code\](.*?)\[/code\]', content_html, re.S)
            magnet_links = []
            for block in code_blocks:
                block = unescape(block).strip()
                if block.startswith('magnet:?'):
                    magnet_links.append(block)
            return {
                "title": title,
                "category": '',
                "publish_date": publish_date,
                "magnet": ','.join(magnet_links),
                "preview_images": ",".join(img_urls),
                "size": 0,
                "detail_url": url,
                "website": "x1080x"
            }


x1080x = X1080X()

if __name__ == '__main__':
    x1080x = X1080X()
    tids = x1080x.get_tid_from_list('244', '5212', 1)
    for tid in tids:
        article = x1080x.get_detail_by_tid(tid)
        print(article)
