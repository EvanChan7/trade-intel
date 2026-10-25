import feedparser
import json
import re
from datetime import datetime, timezone

# 把你第 2 步拿到的订阅链接填进来
RSS_FEEDS = [
    # 美国官方
    ("美国BIS (Federal Register)", "https://www.federalregister.gov/api/v1/documents.rss?conditions%5Bagencies%5D%5B%5D=industry-and-security-bureau"),
    
    # 欧盟官方
    ("欧盟委员会新闻", "https://commission.europa.eu/node/33506/rss_en"),
    
    # 中国官方（通过Google News索引，比RSSHub稳定）
    ("中国商务部 (Google News)", "https://news.google.com/rss/search?q=site:mofcom.gov.cn+%E6%94%BF%E7%AD%96%E5%8F%91%E5%B8%83&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"),
    
    # 国际组织
    ("WTO", "http://www.wto.org/library/rss/latest_news_s.xml"),
    
    # 主流媒体（可选，作为交叉验证）
    ("Reuters", "https://feeds.reuters.com/reuters/topNews"),
    ("Politico", "https://www.politico.com/rss/politicopicks.xml"),
    ("SCMP", "https://www.scmp.com/rss/318421/feed"),
    ("Nikkei Asia", "https://asia.nikkei.com/rss/feed/nar"),
]

def strip_html(text):
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", text)
    return clean.strip()

def main():
    events = []
    for source_name, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
        except Exception:
            continue
        for entry in feed.entries[:15]:  # 每个源取最近 15 条，避免数据过多
            title = getattr(entry, "title", "").strip()
            link = getattr(entry, "link", "")
            summary = strip_html(getattr(entry, "summary", ""))[:300]
            published = getattr(entry, "published", "") or getattr(entry, "updated", "")

            if not title or not link:
                continue

            events.append({
                "id": link,  # 用链接做唯一标识，方便前端去重
                "source": source_name,
                "title": title,
                "summary": summary,
                "url": link,
                "date": published,
            })

    # 按发布时间倒序（字符串比较对 RSS 日期格式基本有效；如需更严格可解析为 datetime）
    events.sort(key=lambda x: x.get("date", ""), reverse=True)

    result = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(events),
        "events": events,
    }

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"写入 news.json，共 {len(events)} 条")

if __name__ == "__main__":
    main()
