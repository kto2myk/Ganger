from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.model_manager.model import TagMaster, TagPost, Post
from sqlalchemy.sql import select
from Ganger.app.view.app import app
from sqlalchemy.exc import IntegrityError
import logging

# ログの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

with app.test_request_context():
    try:
        db = DatabaseManager(app)
        Session = db.make_session(None)

        logger.info("=== [START] TagPostの補完処理 ===")

        # 1. すべてのPost.body_textを取得
        posts = Session.execute(select(Post.post_id, Post.body_text)).fetchall()
        logger.info(f"取得したPost数: {len(posts)} 件")

        # 2. すべてのTagMaster.tag_textを取得
        tags = Session.execute(select(TagMaster.tag_id, TagMaster.tag_text)).fetchall()
        tag_dict = {tag_text: tag_id for tag_id, tag_text in tags}  # {tag_text: tag_id} の辞書化
        logger.info(f"取得したTag数: {len(tag_dict)} 件")

        tagpost_records = []  # 新規追加するTagPostのリスト

        # 3. 各Postのbody_textに既存タグが含まれているかチェック
        for post_id, body_text in posts:
            if not body_text:
                logger.warning(f"Post ID {post_id}: body_textが空です")
                continue

            matched_tags = {tag_dict[tag] for tag in tag_dict if f"#{tag}" in body_text}  # `#タグ` を検索

            if not matched_tags:
                logger.info(f"Post ID {post_id}: 一致するタグなし")
                continue

            logger.info(f"Post ID {post_id}: {len(matched_tags)} 件のタグが一致 {matched_tags}")

            # すでにTagPostに登録されているタグを取得
            existing_tags = Session.execute(
                select(TagPost.tag_id).where(TagPost.post_id == post_id)
            ).scalars().all()

            # 4. 未登録のタグのみ追加
            new_tags = matched_tags - set(existing_tags)
            if not new_tags:
                logger.info(f"Post ID {post_id}: すでに全タグ登録済み")
                continue

            logger.info(f"Post ID {post_id}: 新規追加 {new_tags}")

            for tag_id in new_tags:
                tagpost_records.append(TagPost(post_id=post_id, tag_id=tag_id))

        # 5. まとめてINSERT（重複回避済み）
        if tagpost_records:
            logger.info(f"TagPostに追加する新規レコード数: {len(tagpost_records)} 件")
            Session.add_all(tagpost_records)
            db.make_commit_or_flush(Session)
        else:
            logger.info("追加するTagPostレコードなし")

        logger.info("=== [END] TagPostの補完処理 ===")

    except IntegrityError as e:
        Session.rollback()
        logger.error(f"IntegrityError: 重複するデータがありました - {e}")
    except Exception as e:
        db.session_rollback(Session)
        logger.error(f"予期しないエラー: {e}")
