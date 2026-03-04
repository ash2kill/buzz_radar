import os
import sqlite3
import datetime
import isodate
from googleapiclient.discovery import build
from dateutil import parser

# ==========================================
# ★APIキー
API_KEY = os.environ.get("YOUTUBE_API_KEY")
if not API_KEY:
    raise ValueError("⚠️ エラー: 環境変数 YOUTUBE_API_KEY が設定されていません")

# 設定
DB_FILE = "buzz_radar.db"

# ★バズイチ実戦用クエリ
KEYWORDS = [
    "昭和CM -fyp -tiktok",
    "架空CM -fyp -tiktok",
    "架空通販 -fyp -tiktok",
    "ローカルCM -fyp -tiktok",
    "昭和風 -fyp -tiktok",
    "AI CM -fyp -tiktok",
    "CMパロディ -fyp -tiktok",
    "嘘CM -fyp -tiktok"
]
# ==========================================

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # ★video_id を PRIMARY KEY に設定（重複防止の要）
    c.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            title TEXT,
            channel_title TEXT,
            published_at TEXT,
            scraped_at TEXT,
            view_count INTEGER,
            sub_count INTEGER,
            buzz_ratio REAL,
            views_per_day REAL,
            duration_sec INTEGER,
            is_short BOOLEAN,
            query TEXT
        )
    ''')
    
    c.execute('CREATE INDEX IF NOT EXISTS idx_videos_vid ON videos(video_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_videos_scraped ON videos(scraped_at)')
    
    conn.commit()
    return conn

def get_service():
    return build('youtube', 'v3', developerKey=API_KEY)

def main():
    conn = init_db()
    c = conn.cursor()
    youtube = get_service()
    
    print("🚀 効率化版 リサーチ開始 (重複排除 UPSERT 実装)...")
    total_added = 0

    for query in KEYWORDS:
        one_week_ago = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        try:
            res = youtube.search().list(
                q=query, part='id,snippet', maxResults=20, type='video', order='date', publishedAfter=one_week_ago
            ).execute()
        except Exception as e:
            print(f"検索エラー ({query}): {e}")
            continue

        video_ids = [item['id']['videoId'] for item in res.get('items', [])]
        if not video_ids: continue

        stats_res = youtube.videos().list(
            part='statistics,snippet,contentDetails', id=','.join(video_ids)
        ).execute()

        channel_ids = list(set([item['snippet']['channelId'] for item in stats_res.get('items', [])]))
        chan_res = youtube.channels().list(part='statistics', id=','.join(channel_ids)).execute()
        chan_map = {}
        for ch in chan_res.get('items', []):
            sub_val = ch['statistics'].get('subscriberCount', 0)
            chan_map[ch['id']] = int(sub_val) if not ch['statistics'].get('hiddenSubscriberCount') else 0

        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for item in stats_res.get('items', []):
            vid = item['id']
            stats = item['statistics']
            snippet = item['snippet']
            cid = snippet['channelId']
            
            # ★チャンネル名を取得
            channel_title = snippet.get('channelTitle', 'Unknown')
            
            content_details = item.get('contentDetails', {})
            duration_iso = content_details.get('duration', 'PT0S')
            
            try:
                dur_obj = isodate.parse_duration(duration_iso)
                duration_sec = int(dur_obj.total_seconds())
            except:
                duration_sec = 0
            is_short = 1 if duration_sec > 0 and duration_sec <= 60 else 0

            views = int(stats.get('viewCount', 0))
            subs = chan_map.get(cid, 0)

            try:
                pub_at = parser.isoparse(snippet['publishedAt'])
                now = datetime.datetime.now(datetime.timezone.utc)
                days = max((now - pub_at).total_seconds() / 86400.0, 0.1)
                views_per_day = int(views / days)
            except:
                views_per_day = 0

            safe_subs = max(subs, 1)
            buzz_ratio = round(views / safe_subs, 2)

            # ★ INSERT OR REPLACE を使用して、既存の video_id があれば最新データで更新
            c.execute('''
                INSERT OR REPLACE INTO videos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (vid, snippet['title'], channel_title, snippet['publishedAt'], current_time, 
                  views, subs, buzz_ratio, views_per_day, duration_sec, is_short, query))
            
            total_added += 1

    conn.commit()
    conn.close()
    print(f"✅ 完了: {total_added}件を処理 (重複排除/UPSERT実装済)")

if __name__ == '__main__':
    main()