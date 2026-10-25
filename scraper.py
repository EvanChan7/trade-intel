import feedparser
import json
import re
from datetime import datetime, timezone
import urllib.parse
import urllib.request
import time

# 聚焦中美欧经贸的订阅源
RSS_FEEDS = [
    ("美国BIS (Federal Register)", "https://www.federalregister.gov/api/v1/documents.rss?conditions%5Bagencies%5D%5B%5D=industry-and-security-bureau"),
    ("欧盟委员会", "https://commission.europa.eu/node/33506/rss_en"),
    ("Google News-中国商务部", "https://news.google.com/rss/search?q=site:mofcom.gov.cn+(贸易+OR+关税+OR+管制)&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"),
    ("Reuters-全球贸易", "https://news.google.com/rss/search?q=(US+China+trade+OR+tariff+OR+export+control)+when:7d&hl=en-US&gl=US&ceid=US:en"),
]

# 必须包含以下至少一个关键字，否则丢弃该新闻
KEYWORDS = ['贸易', '关税', '制裁', '出口', '芯片', '半导体', '补贴', '反倾销', '反补贴', '商务部', 'BIS', 'tariff', 'trade', 'sanction', 'export', 'semiconductor', 'chip', 'subsidy', 'commerce', 'EU', 'USTR']

def strip_html(text):
    if not text: return ""
    return re.sub(r"<[^>]+>", "", text).strip()

# 免费翻译函数
def translate_text(text):
    if not text: return ""
    # 简单判断是否已经是中文，如果是就跳过
    if not re.search(r'[a-zA-Z]{4,}', text) or re.search(r'[\u4e00-\u9fa5]', text):
        return text
    try:
        q = urllib.parse.quote(text[:450]) # 限制长度防报错
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=zh-CN&dt=t&q={q}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            translated = "".join([item[0] for item in data[0]])
            time.sleep(1) # 防止请求过快被封
            return translated
    except Exception as e:
        print(f"翻译失败: {e}")
        return text # 失败则返回原文

def main():
    events = []
    seen_titles = set()

    for source_name, url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
        except Exception as e:
            print(f"抓取失败 {source_name}: {e}")
            continue
            
        for entry in feed.entries[:20]:
            title_en = getattr(entry, "title", "").strip()
            summary_en = strip_html(getattr(entry, "summary", ""))[:500]
            link = getattr(entry, "link", "")
            published = getattr(entry, "published", "")
            
            if not title_en or not link or title_en in seen_titles:
                continue

            # 关键字过滤（中英文同时匹配）
            combined_text = (title_en + summary_en).lower()
            if not any(kw.lower() in combined_text for kw in KEYWORDS):
                continue
                
            seen_titles.add(title_en)

            # 在后台进行翻译（固化中文）
            title_zh = translate_text(title_en)
            summary_zh = translate_text(summary_en)

            # 尝试格式化时间
            try:
                dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                date_str = dt.isoformat()
            except:
                date_str = datetime.now(timezone.utc).isoformat()

            events.append({
                "id": link,
                "source": source_name,
                "title": title_zh,       # 前端直接读中文标题
                "summary": summary_zh,   # 前端直接读中文摘要
                "url": link,
                "date": date_str,
            })

    # 按照时间降序排列（最新的在最前面）
    events.sort(key=lambda x: x.get("date", ""), reverse=True)

    result = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(events),
        "events": events,
    }

    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"写入 news.json，共 {len(events)} 条合法新闻")

if __name__ == "__main__":
    main()
