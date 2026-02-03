import random
import time
from sqlalchemy import func, select
from app.core.database import session_scope
from app.models.article import Article
from app.modules.crawler.x1080x import x1080x
from app.utils.log import logger
from app.utils.wrapper import task_monitor

type_map = {
    '5212': "国产品牌",
    '5206': "有码HD",
    '5207': "无码HD",
    '5208': "FC2HD",
    '5216': "MGSHD",
    '5479': "中文字幕",
    '5213': "探花精选",
    '5217': "主播精选",
    "5218": "其他"
}


@task_monitor
def sync_x1080_by_tid():
    result = []
    for type_id in type_map:
        section = type_map[type_id]
        success_count, page, fail_list = sync_new_article(type_id, 1, 100)
        result.append(
            {
                "section": section,
                "success_count": success_count,
                "page": page - 1,
                "fail_list": fail_list,
            }
        )
    return result


@task_monitor
def sync_x1080_by_max_page(max_page):
    result = []
    for type_id in type_map:
        section = type_map[type_id]
        success_count, page, fail_list = sync_new_article_no_stop(type_id, 1, max_page)
        result.append(
            {
                "section": section,
                "success_count": success_count,
                "page": page - 1,
                "fail_list": fail_list,
            }
        )
    return result


def sync_new_article(type_id, start_page=1, max_page=100):
    type_id = str(type_id)
    section = type_map[type_id]
    fail_id_list = []
    page = start_page
    success_count = 0
    # 作为终止阈值
    with session_scope() as session:
        stop_tid = session.query(func.max(Article.tid)) \
                       .filter(Article.section == section) \
                       .filter(Article.website == 'x1080x') \
                       .scalar() or 0

    logger.info(f"[{section}] 数据库最大TID: {stop_tid}")
    while page <= max_page:
        articles = []
        time.sleep(1)
        logger.info(f"[{section}] 抓取第 {page} 页")
        tid_list = []
        # 页面级重试
        for retry in range(3):
            tid_list = x1080x.get_tid_from_list(244, type_id, page)
            if tid_list:
                break
            logger.warning(f"第{page}页抓取失败，第{retry + 1}次重试")
            time.sleep(10)

        if not tid_list:
            logger.info(f"连续抓取3次第{page}页失败,退出任务")
            break
        else:
            map_db_tid = [tid * 10000 for tid in tid_list]
            min_tid = min(map_db_tid)
            logger.info(f"当前页最小TID: {min_tid}")

            # 批量判断数据库是否已存在
            with session_scope() as session:
                existing_article_tids = (
                    session.execute(
                        select(Article.tid).filter(Article.tid.in_(map_db_tid))
                    ).scalars().all()
                )

            for tid in map_db_tid:
                if tid in existing_article_tids:
                    continue
                try:
                    data = x1080x.get_detail_by_tid(tid / 10000)
                    if not data:
                        fail_id_list.append(tid / 10000)
                        continue

                    data.update({
                        "tid": tid,
                        "section": section,
                    })
                    article = Article(data)
                    articles.append(article)
                    success_count += 1
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"TID {tid} 抓取失败: {e}")
                    fail_id_list.append(tid)
            with session_scope() as session:
                session.add_all(articles)
            # 终止条件
            if min_tid <= stop_tid:
                logger.info(f"[{section}] 已到达历史最大TID，任务结束")
                break
            page += 1

    retry_fail_id_list = retry_fail_tid(type_id, fail_id_list)
    return success_count, page, retry_fail_id_list


def sync_new_article_no_stop(type_id, start_page=1, max_page=100):
    type_id = str(type_id)
    section = type_map[type_id]
    fail_id_list = []
    page = start_page
    success_count = 0
    while page <= max_page:
        time.sleep(1)
        logger.info(f"[{section}] 抓取第 {page} 页")
        tid_list = []
        articles = []

        # 页面级重试
        for retry in range(3):
            tid_list = x1080x.get_tid_from_list(244, type_id, page)
            if tid_list:
                break
            logger.warning(f"第{page}页抓取失败，第{retry + 1}次重试")
            time.sleep(10)

        if not tid_list:
            logger.info(f"连续抓取3次第{page}页失败,退出任务")
            break
        else:
            map_db_tid = [tid * 10000 for tid in tid_list]
            # 批量判断数据库是否已存在
            with session_scope() as session:
                existing_article_tids = (
                    session.execute(
                        select(Article.tid).filter(Article.tid.in_(map_db_tid))
                    ).scalars().all()
                )

            for tid in map_db_tid:
                if tid in existing_article_tids:
                    continue
                try:
                    data = x1080x.get_detail_by_tid(tid / 10000)
                    if not data:
                        fail_id_list.append(tid / 10000)
                        continue
                    data.update({
                        "tid": tid,
                        "section": section,
                    })
                    article = Article(data)
                    articles.append(article)
                    success_count += 1
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"TID {tid} 抓取失败: {e}")
                    fail_id_list.append(tid)
            with session_scope() as session:
                session.add_all(articles)
            page += 1

    retry_fail_id_list = retry_fail_tid(type_id, fail_id_list)
    return success_count, page, retry_fail_id_list


def retry_fail_tid(type_id, fail_id_list):
    fail_id_list = list(set(fail_id_list))
    if not fail_id_list:
        return []
    section = type_id[type_id]
    logger.info(f"[{section}] 开始补抓失败ID，共 {len(fail_id_list)} 条")
    articles = []
    for tid in fail_id_list[:]:
        try:
            data = x1080x.get_detail_by_tid(tid)
            if not data:
                continue
            data.update({
                "tid": tid * 10000,
                "section": section,
            })
            article = Article(data)
            articles.append(article)
            fail_id_list.remove(tid)
            time.sleep(random.uniform(2, 3))
        except Exception as e:
            logger.exception(f"TID {tid} 二次抓取仍失败:{e}")
    with session_scope() as session:
        session.add_all(articles)
    logger.info(f"[{section}] 最终失败列表: {fail_id_list}")
    return fail_id_list
