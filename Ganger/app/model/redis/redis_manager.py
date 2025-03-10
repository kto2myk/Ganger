import redis
from redis.exceptions import ConnectionError
from flask import current_app, jsonify


class RedisCache:
    def __init__(self, app=None, default_ttl=604800):
        self.app = app or current_app
        self.default_ttl = default_ttl
        redis_url = self.app.config.get("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis_client = redis.StrictRedis.from_url(redis_url, decode_responses=True)  # ✅ 修正
            self.redis_client.ping()
        except ConnectionError:
            print("⚠️ Redisサーバーに接続できません！（処理は継続）")
            self.redis_client = None  # 代替処理のために None をセット

    def add_score(self, ranking_key, item_id, score):
        """
        メタデータなしで `item_id` または `item_id` のリストをスコア付きでランキングに追加
        - ranking_key: ランキングのキー（例: "post_ranking", "tag_ranking"）
        - item_ids: ランキングに追加する ID（`str` または `list[str]`）
        - score: 追加するスコア（`int`）
        """
        if not self.redis_client:
            return
        try:
            if isinstance(item_id, list):  # 🔥 リストならループ
                for item_id in item_id:
                    self.redis_client.zincrby(ranking_key, score, item_id)
            else:  # 🔹 単体ならそのまま
                self.redis_client.zincrby(ranking_key, score, item_id)

            # 🔹 TTL（有効期限）を設定（ランキング全体と同期）
            ttl = self.redis_client.ttl(ranking_key)
            self.redis_client.expire(ranking_key, ttl if ttl > 0 else self.default_ttl)
        except redis.RedisError:
            pass

    def remove_score(self, ranking_key, item_id):
        """
        指定された `ranking_key` の中から `item_id` または `item_id` のリストを削除
        - ranking_key: 削除対象のランキングキー（例: "post_ranking"）
        - item_ids: 削除する ID（`str` または `list[str]`）
        """
        if not self.redis_client:
            return
        try:
            if isinstance(item_id, list):  # 🔥 リストなら複数削除
                self.redis_client.zrem(ranking_key, *item_id)
            else:  # 🔹 単体ならそのまま削除
                self.redis_client.zrem(ranking_key, item_id)
        except redis.RedisError:
            pass


import redis
import random

    def get_ranking_ids(self, ranking_key, offset=0, top_n=10):
        """
        `top_n` 位までの ID 群を取得（スコア順）
        - ranking_key: 取得するランキングのキー
        - top_n: 取得する上位N件の ID のみを返す
        - 返り値: `["123", "456", "789"]` のような `post_id` のリスト
        """
        if not self.redis_client:
            return random.sample(range(1, 31), top_n)  # キャッシュなしなら 1〜30 のランダムサンプルを返す
        
        try:
            # `top_n` 件の ID を取得（スコア順・降順）
            ranking = self.redis_client.zrevrange(ranking_key, offset, offset + top_n - 1)

            # `bytes` → `str` に変換
            return [item_id.decode() if isinstance(item_id, bytes) else item_id for item_id in ranking] if ranking else random.sample(range(1, 31), top_n)

        except redis.RedisError:
            return random.sample(range(1, 31), top_n)  # Redis エラー時もランダムサンプルを返す

    def remove_data(self, key):
        """キャッシュデータを削除（エラー発生時はスキップ）"""
        if not self.redis_client:
            return
        try:
            self.redis_client.delete(key)
        except redis.RedisError:
            pass

    def get_ttl(self, key):
        """キャッシュのTTL（有効期限）を取得（キーなし・エラー時は `None` を返す）"""
        if not self.redis_client:
            return None
        try:
            ttl = self.redis_client.ttl(key)
            return ttl if ttl > 0 else None
        except redis.RedisError:
            return None

    def clear_cache(self):
        """Redisの全データを削除（エラー発生時はスキップ）"""
        if not self.redis_client:
            return
        try:
            self.redis_client.flushdb()
        except redis.RedisError:
            pass

    def get_all_ranking_items(self, ranking_key):
        """
        指定されたランキングキー (`ranking_key`) に登録されている全アイテムを取得する。

        Args:
            ranking_key (str): 取得するランキングのキー（例: "post_ranking"）

        Returns:
            list: [(item_id, score), (item_id, score), ...] のリスト
        """
        if not self.redis_client:
            return []

        try:
            # 🔹 ZSET から全アイテムをスコア付きで取得
            ranking = self.redis_client.zrevrange(ranking_key, 0, -1, withscores=True)

            # 🔹 Redis はバイナリデータを返すのでデコード
            return [(item_id.decode(), score) for item_id, score in ranking]

        except redis.RedisError:
            return []
