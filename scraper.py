import feedparser
import json
import re
from datetime import datetime, timezone

# 把你第 2 步拿到的订阅链接填进来
RSS_FEEDS = [
    ("中国商务部", "https://rsshub.app/gov/mofcom/"),
    ("美国BIS/Federal Register", "https://www.federalregister.gov/api/v1/documents.rss?conditions%5Bagencies%5D%5B%5D=industry-and-security-bureau"),
    ("欧盟DG TRADE", "https://rsshub.app/eu/commission/dg-trade"),
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
