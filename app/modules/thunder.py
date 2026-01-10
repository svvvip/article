import re

import requests

from app.core import settings
from app.utils.log import logger


class Thunder:
    url: str = None
    file_id: str = None
    device_id: str = None
    authorization: str = None

    def __init__(self):
        self.url = settings.THUNDER_URL
        self.file_id = settings.THUNDER_FILE_ID
        self.authorization = settings.THUNDER_AUTHORIZATION
        self.device_id = self.get_device_id()

    def get_pan_auth(self):
        try:
            index_url = f"{self.url}/webman/3rdparty/pan-xunlei-com/index.cgi/"
            headers = {
                "Authorization": self.authorization
            }
            response = requests.get(index_url, headers=headers)
            if response.status_code == 200:
                pattern = r'uiauth\(.*?\)\s*{\s*return\s*"([^"]+)"'
                match = re.search(pattern, response.text)
                return match.group(1)
            else:
                logger.error(f"获取迅雷授权code失败:{response.status_code}")
        except Exception as e:
            logger.error(f"获取迅雷授权code失败:{e}")

    def get_device_id(self):
        if self.url:
            try:
                headers = {
                    'pan-auth': self.get_pan_auth(),
                    "Authorization": self.authorization
                }
                response = requests.get(
                    f'{self.url}/webman/3rdparty/pan-xunlei-com/index.cgi/drive/v1/tasks?type=user%23runner&device_space=',
                    headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('error'):
                        logger.error(f"获取迅雷设备ID失败:{data['error']}")
                    else:
                        device_id = data['tasks'][0]['params']['target']
                        return device_id
                else:
                    logger.error(f"获取迅雷设备ID失败:{response.status_code}")
            except Exception as e:
                logger.error(f"获取迅雷设备ID失败:{e}")
        return None

    def analyze_size(self, magnet):
        if self.url:
            try:
                list_url = f"{self.url}/webman/3rdparty/pan-xunlei-com/index.cgi/drive/v1/resource/list"
                data = {
                    "page_size": 1000,
                    "urls": magnet
                }
                headers = {
                    'pan-auth': self.get_pan_auth(),
                    "Authorization": self.authorization
                }
                logger.info(f"开始解析磁力链接:{magnet}")
                response = requests.post(list_url, json=data, headers=headers)
                if response.status_code == 200:
                    files = response.json()
                    print(files)
                    file_size = files['list']['resources'][0]['file_size']
                    return int(file_size / 1024 / 1024)
                else:
                    logger.error(f"解析磁力链接失败:{response.status_code}")
            except Exception as e:
                logger.error(f"解析磁力链接失败:{e}")
        return 0


thunder = Thunder()
if __name__ == '__main__':
    analyzer = Thunder()
    analyzer.analyze_size("magnet:?xt=urn:btih:045E695734CD5C55B74B657626FE855A477F6293")
