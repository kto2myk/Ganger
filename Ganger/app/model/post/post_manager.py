import os
import uuid
from PIL import Image as PILImage
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from sqlalchemy.sql import select
from sqlalchemy.orm  import joinedload
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename
from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.model_manager.model import User,Post, Image,Like,TagMaster, TagPost,CategoryMaster, ProductCategory, Shop,Repost,SavedPost,Block
from Ganger.app.model.notification.notification_manager import NotificationManager
from flask import current_app as app, session, url_for
from Ganger.app.model.validator import Validator

class PostManager(DatabaseManager):
    def __init__(self,app=None):
        super().__init__(app)
        self.__notification_manager = NotificationManager()

    def is_allowed_extension(self, filename):
        """ ファイルの拡張子が許可されているか確認 """
        allowed_extensions = {".png", ".jpg", ".jpeg", ".gif"}
        ext = os.path.splitext(filename)[1].lower()
        return ext in allowed_extensions

    def generate_filename(self, user_id, post_id, img_order, ext):
        """ 一意のファイル名を生成する """
        return f"{user_id}_{post_id}_{img_order}{ext}"

    def save_file(self, file, file_path):
        """ ファイルを正方形に加工して保存 """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with PILImage.open(file) as img:
            img = self.make_square(img)  # **ここで正方形に加工**
            img.save(file_path, quality=95, optimize=True)  # 高品質保存

    def make_square(self, img, background_color=(255, 255, 255)):
        """ 画像のアスペクト比を維持したまま、余白を追加して正方形にする """
        width, height = img.size
        new_size = max(width, height)  # 正方形のサイズ

        # 透明度を持つ画像は RGBA に変換
        if img.mode in ("P", "LA") or (img.mode == "RGBA" and "transparency" in img.info):
            img = img.convert("RGBA")
            background_color = (255, 255, 255, 0)  # 透明な背景に設定

        # 正方形の背景キャンバスを作成
        new_img = PILImage.new("RGBA" if img.mode == "RGBA" else "RGB", (new_size, new_size), background_color)

        # 画像を中央配置
        paste_position = ((new_size - width) // 2, (new_size - height) // 2)
        new_img.paste(img, paste_position, img if img.mode == "RGBA" else None)  # RGBAの場合はマスクを使用

        return new_img  # 加工後の画像を返す
    
    def delete_files(self, file_list):
        """ エラー発生時に保存したファイルを削除 """
        for file_path in file_list:
            if os.path.exists(file_path):
                os.remove(file_path)

                
    def create_post(self, content, image_files, tags, Session=None):
        """ 
        投稿データを作成し、関連する画像とタグを保存する 
        """
        upload_folder = app.config['POST_FOLDER']
        try:
            Session = self.make_session(Session)
            user_id =  Validator.decrypt(session['id'])
            # 投稿データを作成
            post_data = {
                "user_id": user_id,
                "body_text": content
            }

            # 投稿データをDBに挿入
            post_result = self.insert(model=Post, data=post_data, Session=Session)
            if not post_result:
                app.logger.error("Failed to create post.")
                self.session_rollback(Session)
                return {"success": False, "error": "Failed to create post."}

            post_id = post_result["post_id"]
            saved_images = []
            temp_file_paths = []

            # 画像処理
            
            for index, file in enumerate(Validator.ensure_list(image_files), start=1):
                original_filename = secure_filename(file.filename)
                if not self.is_allowed_extension(original_filename):
                    raise ValueError(f"File type not allowed: {original_filename}")

                ext = os.path.splitext(original_filename)[1].lower()
                filename = self.generate_filename(user_id, post_id, index, ext)
                file_path = os.path.join(upload_folder, filename)

                # ファイル名をDBに登録
                image_data = {
                    "post_id": post_id,
                    "img_path": filename,  # DBにはファイル名のみを登録
                    "img_order": index
                }
                image_result = self.insert(model=Image, data=image_data, Session=Session)
                if not image_result:
                    raise ValueError(f"Failed to register image in DB: {filename}")

                self.save_file(file, file_path)
                saved_images.append(filename)
                temp_file_paths.append(file_path)

            # タグ処理（複数タグ対応）
            if tags:
                for tag_text in Validator.ensure_list(tags):
                    self.add_tag_to_post(tag_text.strip(), post_id, Session=Session)

            self.make_commit_or_flush(Session)
            self.redis.add_score(ranking_key=self.trending[0],item_id=post_id,score=1)
            self.redis.add_score(ranking_key=self.trending[4],item_id=user_id,score=1)
            return {
                "success": True,
                "post": post_result,
                "images": saved_images,
                "tags": tags
            }

        except ValueError as e:
            self.session_rollback(Session)
            self.delete_files(temp_file_paths)
            app.logger.error(f"Validation error: {e}")
            return {"success": False, "error": str(e)}

        except SQLAlchemyError as e:
            self.session_rollback(Session)
            self.delete_files(temp_file_paths)
            app.logger.error(f"Database error: {e}")
            return {"success": False, "error": "Database error occurred"}

        except Exception as e:
            self.session_rollback(Session)
            self.delete_files(temp_file_paths)
            app.logger.error(f"Unexpected error: {e}")
            return {"success": False, "error": "An unexpected error occurred"}
    
    def get_filtered_posts_with_reposts(self, filters, current_user_id,offset = 10,limit = 5,Session=None):
        try:
            Session = self.make_session(Session)
            user_id = filters.get("user_id")
            if not user_id:
                raise ValueError("user_idフィルターが指定されていません。")

            liked_posts_subquery = Session.query(Like.post_id).filter(Like.user_id == current_user_id).subquery()
            saved_posts_subquery = Session.query(SavedPost.post_id).filter(SavedPost.user_id == current_user_id).subquery()
            blocked_users_subquery = Session.query(Block.blocked_user).filter(Block.user_id == current_user_id).subquery()
            blocked_by_subquery = Session.query(Block.user_id).filter(Block.blocked_user == current_user_id).subquery()

            # 🔥 `joinedload()` を追加して関連データを事前ロード（遅延ロードを防ぐ）
            user_posts_query = Session.query(Post).filter(
                Post.user_id == user_id,
                Post.reply_id == None,
                ~Post.post_id.in_(select(liked_posts_subquery)),
                ~Post.post_id.in_(select(saved_posts_subquery)),
                ~Post.user_id.in_(select(blocked_users_subquery)),
                ~Post.user_id.in_(select(blocked_by_subquery))
            ).options(
                joinedload(Post.images),
                joinedload(Post.author),
                joinedload(Post.likes),
                joinedload(Post.reposts),
                joinedload(Post.saved_by_users),
                joinedload(Post.replies)
            )

            reposted_posts_query = Session.query(Post).join(Repost, Repost.post_id == Post.post_id).filter(
                Repost.user_id == user_id,
                Post.reply_id == None,
                ~Post.post_id.in_(select(liked_posts_subquery)),
                ~Post.post_id.in_(select(saved_posts_subquery)),
                ~Post.user_id.in_(select(blocked_users_subquery)),
                ~Post.user_id.in_(select(blocked_by_subquery))
            ).options(
                joinedload(Post.images),
                joinedload(Post.author),
                joinedload(Post.likes),
                joinedload(Post.reposts),
                joinedload(Post.saved_by_users),
                joinedload(Post.replies),
                joinedload(Repost.user)
            )

            # 🔥 `union_all()` を適用（エラーが出る場合は `list()` に切り替え）
            all_posts = user_posts_query.union_all(reposted_posts_query).order_by(Post.post_time.desc()).offset(offset).limit(limit)

            # 🔥 投稿データをフォーマット
            formatted_posts = []
            for post in all_posts:
                formatted_post = {
                    "is_me": Validator.decrypt(session['id']) == post.author.id,
                    "id": Validator.encrypt(post.author.id),
                    "post_id": Validator.encrypt(post.post_id),
                    "user_id": post.author.user_id,
                    "username": post.author.username,
                    "profile_image": url_for("static", filename=f"images/profile_images/{post.author.profile_image}"),
                    "body_text": post.body_text,
                    "post_time": Validator.calculate_time_difference(post.post_time),
                    "images": [
                        {"img_path": url_for("static", filename=f"images/post_images/{image.img_path}")}
                        for image in post.images
                    ],
                    # 🔥 リレーションの `.count()` を使って直接カウントを取得
                    "like_count": len(post.likes or []),
                    "repost_count": len(post.reposts or []),
                    "saved_count": len(post.saved_by_users or []),
                    "comment_count": len(post.replies or []),  # 返信の数
                    "repost_user": (
                        {
                            "id": Validator.encrypt(repost.user.id),
                            "user_id": repost.user.user_id,
                            "username": repost.user.username,
                            "profile_image": url_for("static", filename=f"images/profile_images/{repost.user.profile_image}")
                        } if (repost := next((r for r in post.reposts if r.user.id == user_id), None)) else None
                    )
                }
                formatted_posts.append(formatted_post)
                self.redis.add_score(ranking_key=self.trending[0], item_id=post.post_id,score=3)
                self.redis.add_score(ranking_key=self.trending[4],item_id=post.author.id,score=3)

            self.pop_and_close(Session)
            return formatted_posts

        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"Error in get_filtered_posts_with_reposts: {e}")
            self.error_log_manager.add_error(None, str(e))
            raise


            


    def get_posts_details(self, post_ids, current_user_id=None, Session=None):
        """
        指定された複数の post_id の投稿データを取得し、フォーマットして返す。
        ブロックしている/されているユーザーの投稿を除外する。

        Args:
            post_ids (list[str]): 取得する投稿の暗号化IDリスト。
            current_user_id (int): ログイン中のユーザーのID。

        Returns:
            list[dict]: フォーマットされた投稿データのリスト。
        """
        try:
            Session = self.make_session(Session)
            if current_user_id:
                current_user_id = Validator.decrypt(current_user_id)

            post_ids = Validator.ensure_list(post_ids)
            # post_ids を動的復号化
            decrypted_ids = [Validator.decrypt(post_id) if len(post_id) > 5 else post_id for post_id in post_ids]

            # ブロック関連のサブクエリ
            blocked_users_subquery = (
                Session.query(Block.blocked_user)
                .filter(Block.user_id == current_user_id)
                .subquery()
            )

            blocked_by_subquery = (
                Session.query(Block.user_id)
                .filter(Block.blocked_user == current_user_id)
                .subquery()
            )

            # クエリ作成（リレーションも一括取得）
            posts = (
                Session.query(Post).filter(
                    Post.post_id.in_(decrypted_ids),  # 指定されたpost_idの投稿のみ取得
                    ~Post.user_id.in_(select(blocked_users_subquery)),  # 自分がブロックしたユーザーの投稿を除外
                    ~Post.user_id.in_(select(blocked_by_subquery))
                    )# 自分をブロックしているユーザーの投稿を除外
                .options(
                    joinedload(Post.images),
                    joinedload(Post.author),
                    joinedload(Post.likes),
                    joinedload(Post.reposts),
                    joinedload(Post.saved_by_users),
                    joinedload(Post.replies)
                )
                .all()
            )

            if not posts:
                app.logger.warning(f"Posts with post_ids {post_ids} not found or blocked.")
                raise ValueError("投稿が見つかりません。")

            formatted_posts = []
            for post in posts:
                # 各カウントを取得（リレーションの `.or []` で NoneType エラー回避）
                like_count = len(post.likes or [])
                repost_count = len(post.reposts or [])
                saved_count = len(post.saved_by_users or [])
                comment_count = len(post.replies or [])

                # データをフォーマット
                formatted_post = {
                    "post_id": Validator.encrypt(post.post_id),
                    "user_info": {
                        "id": Validator.encrypt(post.author.id),
                        "user_id": post.author.user_id,
                        "username": post.author.username,
                        "profile_image": url_for("static", filename=f"images/profile_images/{post.author.profile_image}")
                    },
                    "body_text": post.body_text,
                    "post_time": Validator.calculate_time_difference(post.post_time),
                    "images": [
                        {"img_path": url_for("static", filename=f"images/post_images/{image.img_path}")}
                        for image in post.images
                    ],
                    "like_count": like_count,
                    "repost_count": repost_count,
                    "saved_count": saved_count,
                    "comment_count": comment_count,
                    "is_me": current_user_id == post.author.id
                }
                # Redis スコア更新
                self.redis.add_score(ranking_key=self.trending[0], item_id=post.post_id, score=6)
                formatted_posts.append(formatted_post)

            self.pop_and_close(Session)
            return formatted_posts

        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"Error in get_posts_details: {e}")
            raise

    def search_tags(self, query,limit=10,Session=None):
        try:
            Session = self.make_session(Session)

            # タグの検索（部分一致）
            tags = Session.query(TagMaster).filter(
                TagMaster.tag_text.ilike(f"%{query}%")
            ).all()

            results = []
            if tags:
                for tag in tags:
                    # タグに紐づく投稿数をカウント
                    post_count = Session.query(Post).join(TagPost).filter(
                        TagPost.tag_id == tag.tag_id
                    ).count()

                    self.redis.add_score(ranking_key=self.trending[1],item_id=tag.tag_id,score=2)

                    # タグに紐づく投稿を最大5件取得
                    posts = (
                        Session.query(Post)
                        .join(TagPost)
                        .filter(TagPost.tag_id == tag.tag_id)
                        .limit(limit)
                        .all()
                    )

                    formatted_posts = []
                    for post in posts:
                        # 各投稿の最初の画像を取得（存在すれば）
                        first_image = (
                            Session.query(Image)
                            .filter(Image.post_id == post.post_id)
                            .order_by(Image.img_order)
                            .first()
                        )

                        formatted_posts.append({
                            "post_id": Validator.encrypt(post.post_id),
                            "body_text": post.body_text,
                            "post_time": Validator.calculate_time_difference(post.post_time),
                            "image_url": url_for('static', filename=f"images/post_images/{first_image.img_path}") if first_image else None
                        })
                        self.redis.add_score(ranking_key=self.trending[0],item_id=post.post_id,score=2)
                    results.append({
                        "tag_text": tag.tag_text,  # タグ名
                        "post_count": post_count,  # タグに紐づく投稿数
                        "posts": formatted_posts  # 投稿リスト（最大30件）
                    })

            self.pop_and_close(Session)
            return results

        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"Error in search_tags: {e}")
            return []    

    def get_tags_by_ids(self, tag_ids,Session=None):
        """
        指定されたタグIDリストに対応するタグテキストを取得する（辞書型で返す）。

        Args:
            tag_ids (list[int]): 検索対象のタグIDリスト。

        Returns:
            dict: {tag_id: tag_text} の形式の辞書。
        """
        if not tag_ids:
            return {}
        else:
            tag_ids = Validator.ensure_list(tag_ids) #単一値のリスト化

        try:
            Session = self.make_session(Session)
            # ORM クエリで TagMaster から tag_id と tag_text を取得
            tag_records = (
                Session.query(TagMaster.tag_id, TagMaster.tag_text)
                .filter(TagMaster.tag_id.in_(tag_ids))
                .all()
            )
            #辞書型で返す
            self.pop_and_close(Session)
            return {tag.tag_id: tag.tag_text for tag in tag_records}

        except Exception as e:
            print(f"❌ ERROR: get_tags_by_ids failed - {e}")
            self.session_rollback(Session)
            return {}
        
    def add_tag_to_post(self, tag_text, post_id, Session=None):
        """ 投稿にタグを追加する処理 """
        try:
            Session = self.make_session(Session)
            # タグが既存か確認、なければ作成
            tag_data = {"tag_text": tag_text}
            tag = self.insert(model=TagMaster, data=tag_data, unique_check={"tag_text": tag_text}, Session=Session)
            
            if not tag:  # タグが既存の場合、取得
                tag = self.fetch_one(model=TagMaster, filters={"tag_text": tag_text}, Session=Session)
                tag = {"tag_id": tag.tag_id,}
            # タグと投稿の関連付け
            tag_post_data = {"tag_id": tag["tag_id"], "post_id": post_id}
            self.insert(model=TagPost, data=tag_post_data, unique_check=tag_post_data, Session=Session)

            self.redis.add_score(ranking_key=self.trending[1],item_id=tag['tag_id'],score=7)
            self.make_commit_or_flush(Session)
            app.logger.info(f"タグ '{tag_text}' が投稿 {post_id} に追加されました。")
        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"エラーが発生しました: {e}")



    def toggle_like(self, post_id, sender_id,Session=None):
        """
        いいね機能を切り替えるメソッド

        :param post_id: いいね対象の投稿ID
        :param recipient_id: いいねを受け取るユーザーID
        :param sender_id: いいねを送信するユーザーID
        :return: 処理結果を表す辞書
        """
        try:
            Session = self.make_session(Session)
            # Likeテーブルを検索
            unique_check = {'post_id': post_id, 'user_id': sender_id}
            existing_like = self.fetch_one(model=Like, filters=unique_check,relationships=["post"],Session=Session)

            if existing_like:
                # いいねが存在する場合は削除
                self.delete(model=Like, filters=unique_check,Session=Session)
                self.__notification_manager.delete_notification(
                    sender_id=sender_id,
                    recipient_id=existing_like.post.user_id,
                    type_name="LIKE",
                    related_item_id=post_id,
                    related_item_type="post",
                    Session=Session
                )
                self.redis.add_score(ranking_key=self.trending[0],item_id=post_id,score=-5)
                app.logger.info(f"Like removed: post_id={post_id}, user_id={sender_id}")
                result =  {"status": "removed"}
            else:
                # いいねが存在しない場合は作成
                self.insert(model=Like, data={'post_id': post_id, 'user_id': sender_id},Session=Session)
                post = self.fetch_one(Post, filters={"post_id": post_id},Session=Session)
                self.__notification_manager.create_full_notification(
                    sender_id=sender_id,
                    recipient_ids=post.user_id,  # 受信者は単一でもリスト形式で処理可能
                    type_name="LIKE",
                    contents=f"{session['username']}さんがあなたの投稿にいいねしました",
                    related_item_id=post_id,
                    related_item_type="post",
                    Session=Session
                )
                self.redis.add_score(ranking_key=self.trending[0],item_id=post_id,score=5)
                app.logger.info(f"Like added: post_id={post_id}, user_id={sender_id}")
                result =  {"status": "added"}
            self.make_commit_or_flush(Session)
            return result
                
        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"Failed to toggle like: {e}")
            self.error_log_manager.add_error(sender_id, str(e))
            raise

    def add_comment(self, user_id, parent_post_id, comment_text, Session=None):
        """
        コメントを投稿し、通知を送信するメソッド

        :param user_id: コメントを投稿するユーザーのID
        :param parent_post_id: 親投稿のID
        :param comment_text: コメント本文
        :return: 作成されたコメントの情報
        """
        try:
            Session = self.make_session(Session)
            # 親投稿の存在確認とリレーションの事前ロード
            parent_post = self.fetch_one(Post, filters={"post_id": parent_post_id}, relationships=["author"],Session=Session)
            if not parent_post:
                raise ValueError(f"Parent post with ID {parent_post_id} does not exist.")
            # コメントデータを挿入
            comment_data = {
                "user_id": user_id,
                "reply_id": parent_post_id,
                "body_text": comment_text
            }
            new_comment = self.insert(model=Post, data=comment_data,Session=Session)

            if not new_comment:
                raise ValueError("Failed to insert the comment. Possible duplicate.")

            # 通知を送信
            self.__notification_manager.create_full_notification(
                sender_id=user_id,
                recipient_ids=parent_post.author.id,
                type_name="COMMENT",
                contents=f"{session['username']}さんがあなたの投稿にコメントしました。: {comment_text[:50]}...",
                related_item_id=new_comment["post_id"],
                related_item_type="post",
                Session=Session
            )
            self.redis.add_score(ranking_key=self.trending[0],item_id=parent_post_id,score=5)
            self.make_commit_or_flush(Session)
            return new_comment

        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"Failed to add comment: {e}")
            self.__error_log_manager.add_error(user_id, str(e))
            raise
        
    def toggle_saved_post(self, post_id, user_id,Session=None):
        """
        保存機能をトグルするメソッド。
        - 指定された投稿を保存または保存解除する。

        :param post_id: 保存対象の投稿ID
        :param user_id: 保存操作を行うユーザーID
        :return: 処理結果を表す辞書
        """
        try:
            Session = self.make_session(Session)
            # SavedPost テーブルを検索
            unique_check = {'post_id': post_id, 'user_id': user_id}
            existing_saved_post = self.fetch_one(
                model=SavedPost,
                filters=unique_check,
                Session=Session
            )

            if existing_saved_post:
                # 保存済みの場合は削除
                self.delete(model=SavedPost, filters=unique_check,Session=Session)
                app.logger.info(f"SavedPost removed: post_id={post_id}, user_id={user_id}")
                self.redis.add_score(ranking_key=self.trending[0],item_id=post_id,score=-8)
                result = {"status": "removed"}
            else:
                # 保存されていない場合は追加
                self.insert(model=SavedPost, data={'post_id': post_id, 'user_id': user_id},Session=Session)
                app.logger.info(f"SavedPost added: post_id={post_id}, user_id={user_id}")
                self.redis.add_score(ranking_key=self.trending[0],item_id=post_id,score=8)
                result = {"status": "added"}
            
            self.make_commit_or_flush(Session)
            return result

        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"Failed to toggle saved post: {e}")
            self.error_log_manager.add_error(user_id, str(e))
            raise

    def create_repost(self, user_id, post_id,Session=None):
        """
        リポストを作成し、通知を発行するメソッド。

        Args:
            user_id (int): リポストを行うユーザーのID。
            post_id (int): リポストする投稿のID。

        Returns:
            dict: 作成されたリポストの情報。
        """
        try:
            Session = self.make_session(Session)
            # リポストデータを挿入
            repost_data = {
                "user_id": user_id,
                "post_id": post_id,
            }

            # 重複チェックを含めて挿入
            unique_check = {"user_id": user_id, "post_id": post_id}
            repost = self.insert(model=Repost, data=repost_data, unique_check=unique_check,Session=Session)

            if repost:
                # 通知を発行
                post_author = self.fetch_one(model=Post, filters={"post_id": post_id}, relationships=["author"],Session=Session)
                self.__notification_manager.create_full_notification(
                    sender_id=user_id,
                    recipient_ids=[post_author.author.id],  # 投稿の作成者に通知
                    type_name="REPOST",
                    contents=f"{session['username']}さんがあなたの投稿をリポストしました。",
                    related_item_id=post_id,
                    related_item_type="post",
                    Session=Session
                )
            else:
                repost = None
                app.logger.info("リポストはすでに存在します。")

            self.make_commit_or_flush(Session)
            self.redis.add_score(ranking_key=self.trending[0],item_id=post_id,score=10)
            return repost


        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"Failed to create repost: {e}")
            self.error_log_manager.add_error(None, str(e))
            raise


    # def make_post_metadata(
    #     self,
    #     post_id: Union[int, str],
    #     body_text: str,
    #     post_time: Union[str, datetime],
    #     post_images: Optional[List[Any]],
    #     count_like: int,
    #     count_comment: int,
    #     count_repost: int,
    #     count_saved: int,
    #     author_id: Union[int, str],  # 組み込みのidとの衝突回避のため、author_idに変更
    #     username: str,
    #     user_id: Union[int, str],
    #     profile_image: str,
    # ) -> Dict[str, Any]:
    #     """
    #     投稿関連のメタデータを整形して返します。  
    #     入力値の型・値に不備がある場合は ValueError を発生させます。
        
    #     :param post_id: 投稿の一意な識別子
    #     :param body_text: 投稿本文
    #     :param post_time: 投稿日時 (datetimeオブジェクトまたはISO形式の文字列)
    #     :param post_images: 投稿に含まれる画像のリスト。Noneの場合は空リストに変換されます。
    #     :param count_like: いいねの数
    #     :param count_comment: コメントの数
    #     :param count_repost: リポストの数
    #     :param count_saved: 保存された数
    #     :param author_id: 投稿者の一意な識別子
    #     :param username: 投稿者のユーザー名
    #     :param user_id: 投稿者のユーザーID（表示用など）
    #     :param profile_image: プロフィール画像のURLまたはパス
    #     :return: 整形済みの投稿メタデータ辞書
    #     :raises ValueError: パラメータの型や値に不正があった場合
    #     """
    #     try:
    #         # post_time の型チェックと変換
    #         if isinstance(post_time, datetime):
    #             post_time_str = post_time.isoformat()
    #         elif isinstance(post_time, str):
    #             post_time_str = post_time
    #         else:
    #             raise TypeError("post_time は datetime オブジェクトまたは文字列である必要があります。")
            
    #         # post_images が None の場合は空リストに変換、リスト以外の場合はエラー
    #         if post_images is None:
    #             post_images = []
    #         elif not isinstance(post_images, list):
    #             raise TypeError("post_images はリストまたは None である必要があります。")
            
    #         # 各カウント値が整数であることをチェック
    #         if not isinstance(count_like, int):
    #             raise TypeError("count_like は整数である必要があります。")
    #         if not isinstance(count_comment, int):
    #             raise TypeError("count_comment は整数である必要があります。")
    #         if not isinstance(count_repost, int):
    #             raise TypeError("count_repost は整数である必要があります。")
    #         if not isinstance(count_saved, int):
    #             raise TypeError("count_saved は整数である必要があります。")
            
    #         # ここで他のパラメータ（post_id, author_id, user_id など）の型チェックも必要に応じて追加可能です
    #         # 例:
    #         if not isinstance(username, str):
    #             raise TypeError("username は文字列である必要があります。")
    #         if not isinstance(profile_image, str):
    #             raise TypeError("profile_image は文字列である必要があります。")
            
    #         metadata = {
    #             "post_id": post_id,
    #             "body_text": body_text,
    #             "post_time": post_time_str,
    #             "images": post_images,
    #             "like_count": count_like,
    #             "comment_count": count_comment,
    #             "repost_count": count_repost,
    #             "saved_count": count_saved,
    #             "author_id": author_id,
    #             "username": username,
    #             "user_id": user_id,
    #             "profile_image": profile_image,
    #         }
            
    #         return metadata

    #     except Exception as e:
    #         # エラー発生時はエラー内容を含めた例外を発生させる
    #         raise ValueError(f"投稿メタデータの作成中にエラーが発生しました: {e}")
