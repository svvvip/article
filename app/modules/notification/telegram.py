import io

import requests
import telebot

from telebot import apihelper

from app.core import settings
from app.enum import PusherEnum
from app.modules.notification.base import BaseSender
from app.utils.log import logger


def get_image(image_url):
    if image_url:
        resp = requests.get(
            image_url,
            proxies={
                'https': settings.PROXY,
                'http': settings.PROXY,
            },
            stream=True,
            timeout=10,
            headers={
                'Referer': 'https://sehuatang.org/'
            }
        )
        resp.raise_for_status()

        image = io.BytesIO(resp.content)
        image.name = "image.jpg"
        return image
    return None


class TelegramNotifier(BaseSender):
    conf: dict
    name = PusherEnum.TELEGRAM.value
    bot: telebot.TeleBot

    def __init__(self, conf):
        self.conf = conf
        try:
            self.bot = telebot.TeleBot(self.conf.get('bot_token'))
            apihelper.proxy = {'https': settings.PROXY}
        except Exception as e:
            logger.error(f"TG机器人创建失败：{e}")

    def send(self, title=None, message=None, image_url=None):
        if self.bot:
            try:
                self.bot.send_photo(self.conf.get('chat_id'),
                                    photo=get_image(image_url) if self.conf.get('push_image') else None,
                                    has_spoiler=self.conf.get('spoiler', False),
                                    caption=message)
            except Exception as e:
                logger.error(f"发送telegram消息失败： {e}")
