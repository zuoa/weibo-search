import time

import requests
import sqlite3

from requests import session


## 打开weibo
class WeiboCommentFetcher:
    def __init__(self, settings):
        self.db = sqlite3.connect('weibo_comments.db')
        self.cursor = self.db.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comment_id TEXT,
                user_id TEXT,
                text TEXT,
                created_at TEXT
            )
        ''')
        self.db.commit()

    def fetch_comments(self, url):
        # Fetch comments from the given URL
        try:
            response = self._get_response(url)
            if response.status_code == 200:
                comments_data = response.json()
                self._save_comments(comments_data)
            else:
                print(f"Failed to fetch comments: {response.status_code}")
        except Exception as e:
            print(f"Error fetching comments: {e}")

    def _save_comments(self, comments_data):
        # Save comments to the SQLite database
        for comment in comments_data.get('comments', []):
            comment_id = comment.get('id')
            user_id = comment.get('user', {}).get('id')
            text = comment.get('text')
            created_at = comment.get('created_at')

            self.cursor.execute('''
                INSERT INTO comments (comment_id, user_id, text, created_at)
                VALUES (?, ?, ?, ?)
            ''', (comment_id, user_id, text, created_at))

        self.db.commit()

    def _get_response(self, url):
        # Make a GET request to the URL with default headers
        import requests
        if not self.settings.get('DEFAULT_REQUEST_HEADERS'):
            self.settings['DEFAULT_REQUEST_HEADERS'] = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }



        response = requests.get(url, headers=self.settings.get('DEFAULT_REQUEST_HEADERS'))



from peewee import *

# 'mydatabase.db'という名前のSQLiteデータベースに接続します
db = SqliteDatabase('results/weibo.db')

class BaseModel(Model):
    class Meta:
        database = db

class Weibo(BaseModel):
    id = CharField(primary_key=True)
    bid = CharField(max_length=64)
    user_id = CharField(max_length=64)
    article_url = CharField(max_length=500)
    comments_count = IntegerField(default=0)
    created_at = DateTimeField()


class WeiboComment(BaseModel):
    id = CharField(primary_key=True)
    weibo_id = CharField(max_length=64)
    user_id = CharField(max_length=64)
    user_name = CharField(max_length=64)
    user_location = CharField(max_length=128, null=True)
    text = CharField(max_length=500)
    source = CharField(max_length=64)
    like_counts = IntegerField(default=0)
    created_at = DateTimeField()

for weibo in Weibo.select().where(Weibo.comments_count >= 50, Weibo.created_at > '2025-06-01 00:00:00').order_by(Weibo.created_at.desc()):
    print(weibo.id, weibo.bid, weibo.user_id, weibo.article_url, weibo.comments_count, weibo.created_at)

    session = requests.session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'cookie': '',
    })

    session.get(weibo.article_url)

    max_id = -1
    comment_count = 0
    failed_times = 0
    while max_id != 0 and comment_count < 100:
        last_max_id = max_id

        if max_id < 0:
            comments_url = f"https://weibo.com/ajax/statuses/buildComments?is_reload=1&id={weibo.id}&is_show_bulletin=2&is_mix=0&count=10&uid={weibo.user_id}&fetch_level=0&locale=zh-CN"
        else:
            comments_url = f"https://weibo.com/ajax/statuses/buildComments?flow=0&is_reload=1&id={weibo.id}&is_show_bulletin=2&is_mix=0&max_id={max_id}&count=20&uid={weibo.user_id}&fetch_level=0&locale=zh-CN"
        try:
            resp = session.get(comments_url)
            max_id = resp.json().get('max_id')
            comment_list = resp.json().get('data', [])
        except Exception as e:
            print(f"Error fetching comments for {weibo.id}: {e}")
            failed_times += 1
            if failed_times > 3:
                print(f"Failed to fetch comments for {weibo.id} too many times, stopping.")
                break
            time.sleep(3)
            continue

        if last_max_id == max_id:
            print(f"No new comments for {weibo.id}, stopping.")
            break

        if not comment_list:
            print(f"No comments found for {weibo.id}, stopping.")
            break

        for comment in comment_list:
            comment_model = {
                'id': comment.get('idstr'),
                'weibo_id': weibo.id,
                'user_id': comment.get('user', {}).get('idstr'),
                'user_name': comment.get('user', {}).get('screen_name'),
                'user_location': comment.get('user', {}).get('location'),
                'text': comment.get('text_raw'),
                'source': comment.get('source'),
                'like_counts': comment.get('like_counts', 0),
                'created_at': comment.get('created_at')
            }
            comment_count += 1
            try:
                WeiboComment.create(**comment_model)
            except Exception as e:
                print(f"Error saving comment {comment.get('idstr')} for weibo {weibo.id}: {e}")

        time.sleep(5)

    time.sleep(5)
