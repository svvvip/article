from typing import Dict, List

from sqlalchemy.orm import Session

from app.models.article import Article
from app.schemas import ArticleQuery


def get_article_list(db: Session, query: ArticleQuery) -> Dict:
    q = db.query(Article)
    if query.keyword:
        q = q.filter(Article.title.ilike(f"%{query.keyword}%"))
    if query.section:
        q = q.filter(Article.section == query.section)
    if query.sub_type:
        q = q.filter(Article.sub_type == query.sub_type)
    if query.publish_date_range and len(query.publish_date_range) == 2:
        start_date, end_date = query.publish_date_range
        q = q.filter(
            Article.publish_date.between(start_date, end_date)
        )
    total = q.count()
    page = query.page
    per_page = query.per_page
    offset = (page - 1) * per_page

    items = (
        q.order_by(Article.tid.desc())
        .offset(offset)
        .limit(per_page)
        .all()
    )
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "items": items
    }


cn_keywords: List[str] = ['中字', '中文字幕', '色花堂', '字幕']
uc_keywords: List[str] = ['UC', '无码', '步兵']
uhd_keywords: List[str] = ['4k', '8k', '2160p', '4K', '8K', '2160P']


def has_chinese(title: str):
    chinese = False
    for keyword in cn_keywords:
        if title.find(keyword) > -1:
            chinese = True
            break
    return chinese


def has_uc(title: str):
    uc = False
    for keyword in uc_keywords:
        if title.find(keyword) > -1:
            uc = True
            break
    return uc


def has_uhd(title: str):
    uhd = False
    for keyword in uhd_keywords:
        if title.find(keyword) > -1:
            uhd = True
            break
    return uhd


def get_torrents(keyword, db: Session) -> Dict:
    articles = db.query(Article).filter(Article.title.ilike(f"%{keyword}%")).all()
    torrents = []
    for article in articles:
        torrent = {
            'id': article.tid,
            'site': 'sehuatang',
            'size_mb': article.size,
            'seeders': 66,
            'title': article.title,
            'download_url': article.magnet,
            'free': True,
            'chinese': has_chinese(f"{article.title}{article.section}"),
            'uc': has_uc(f"{article.title}{article.section}"),
            'uhd': has_uhd(f"{article.title}{article.section}")
        }
        torrents.append(torrent)
    return {
        "code": 200,
        "msg": "查询成功",
        "data": torrents
    }
