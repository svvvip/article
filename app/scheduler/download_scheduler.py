import json
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import exists

from app.api.services import article_service
from app.core.database import session_scope
from app.models import Config, Article, DownloadLog
from app.utils.wrapper import task_monitor


@task_monitor
def download_by_route(route_index_list):
    results = []
    with session_scope() as session:
        config = session.query(Config).filter(Config.key == 'DownloadFolder').first()
    if config:
        route_arr = json.loads(config.content)
        for index in route_index_list:
            success_count = 0
            fail_list = []
            index = int(index) - 1
            route = route_arr[index]
            now = datetime.now(timezone.utc)  # 如果数据库存的是 UTC 时间
            start_time = now - timedelta(hours=24)
            with session_scope() as session:
                query = session.query(Article).filter(Article.create_time.between(start_time, now),
                                                      ~exists().where(DownloadLog.tid == Article.tid))
                if route.get('category'):
                    query = query.filter(Article.section == route['category'])
                if route.get('subCategory'):
                    query = query.filter(Article.category == route['subCategory'])
                articles = query.all()
                if route.get('regex'):
                    pattern = re.compile(route["regex"])
                    articles = [
                        article
                        for article in articles
                        if article.title and pattern.search(article.title)
                    ]
            for article in articles:
                is_success = article_service.download_magnet(article.tid, article.magnet, route.get('downloader'),
                                                             route.get('savePath'))
                if is_success:
                    success_count += 1
                else:
                    fail_list.append(article.tid)
            results.append({
                "success_count": success_count,
                "fail_list": fail_list,
                "index": index
            })
    return results
