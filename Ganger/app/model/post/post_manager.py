import os
import uuid
from PIL import Image as PILImage
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from sqlalchemy.sql import select,exists,func
from sqlalchemy.orm  import joinedload,aliased
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename
from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.model_manager.model import User,Post, Image,Like,TagMaster, TagPost,CategoryMaster, ProductCategory, Shop,Repost,SavedPost,Block,Follow
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

    def make_square(self, img, background_color=(0, 0, 0)):
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
        # **JPEG で保存する場合は RGB に変換**
        if new_img.mode == "RGBA":
            new_img = new_img.convert("RGB")
        return new_img  # 加工後の画像を返す
    
    def delete_files(self, file_list):
        """ エラー発生時に保存したファイルを削除 """
        for file_path in file_list:
            if os.path.exists(file_path):
                os.remove(file_path)

    def delete_temp(self):
        """ 一時フォルダ内の画像を削除 """

        # セッションから画像名を取得
        # 画像のパスを構築

        image_path = os.path.join(app.config['TEMP_FOLDER'], session.get('image_name', ''))
        if not image_path:
            return{"success":False,"message":"削除する画像が見つかりません。"}

        try:
            # ファイルの存在確認
            if os.path.exists(image_path):
                os.remove(image_path)  # ファイルを削除
                session.pop('image_name', None)  # セッションから削除
                return {"success": True, "message": "画像を削除しました。"}
            else:
                return {"success":False, "message":"画像ファイルが存在しません。"}
        except Exception as e:
            app.logger.error(f"Failed to delete image: {e}")
            return {"success":False,"message":str(e)}

                
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
                    raise ValueError(f"ファイル形式が許容されていません: {original_filename}")

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
    
    def get_filtered_posts_with_reposts(self, offset = 0,limit = 2,Session=None):
        try:
            Session = self.make_session(Session)
            current_user_id = Validator.decrypt(session['id'])

            # # フォローしているユーザーの投稿を取得
            # following_users_subquery = (
            #     Session.query(Follow.followed_user)
            #     .filter(Follow.user_id == current_user_id)
            #     .subquery()
            #     ) or self.redis.get_ranking_ids(self.trending[4],offset=0,limit=20)
            
            # フォローしているユーザーIDを取得（リスト化）
            following_users = Session.query(Follow.followed_user).filter(Follow.user_id == current_user_id).all() or []
            following_users_id = [user[0] for user in following_users]  # `.all()` の結果をリスト化

            # フォローがゼロならキャッシュを使う
            if not following_users_id:
                recommended_users = self.redis.get_ranking_ids(self.trending[4], offset=0, top_n=20)
                if recommended_users:
                    following_users_id = recommended_users
            
            liked_posts_subquery = Session.query(Like.post_id).filter(Like.user_id == current_user_id).subquery()
            saved_posts_subquery = Session.query(SavedPost.post_id).filter(SavedPost.user_id == current_user_id).subquery()
            reposted_posts_subquery = Session.query(Repost.post_id).filter(Repost.user_id == current_user_id).subquery()
            blocked_users_subquery = Session.query(Block.blocked_user).filter(Block.user_id == current_user_id).subquery()
            blocked_by_subquery = Session.query(Block.user_id).filter(Block.blocked_user == current_user_id).subquery()

            # 🔥 `joinedload()` を追加して関連データを事前ロード（遅延ロードを防ぐ）
            user_posts_query = Session.query(Post,
                exists().where(Shop.post_id == Post.post_id).label("productized")).filter(
                Post.user_id.in_(following_users_id),
                Post.reply_id == None,
                ~Post.post_id.in_(select(liked_posts_subquery)),
                ~Post.post_id.in_(select(saved_posts_subquery)),
                ~Post.post_id.in_(select(reposted_posts_subquery)),
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

            reposted_posts_query = Session.query(Post,
                exists().where(Shop.post_id == Post.post_id).label("productized")).join(
                Repost, Repost.post_id == Post.post_id).filter(
                Repost.user_id.in_(following_users_id),
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
            all_posts = (user_posts_query.union_all(
                reposted_posts_query)
            .order_by(Post.post_time.desc())
            .offset(offset)
            .limit(limit)
            .all()
            )
            if not all_posts:
                self.pop_and_close(Session)
                return None

            # 🔥 投稿データをフォーマット
            formatted_posts = []
            for post,productized in all_posts:
                formatted_post = {
                    "is_me": Validator.decrypt(session['id']) == post.author.id,
                    "user_info":{
                        "id": Validator.encrypt(post.author.id),
                        "user_id": post.author.user_id,
                        "username": post.author.username,
                        "profile_image": url_for("static", filename=f"images/profile_images/{post.author.profile_image}")
                    },
                    "productized":productized,
                    "post_id": Validator.encrypt(post.post_id),
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
                        } if (repost := next((r for r in post.reposts if r.user.id == current_user_id), None)) else None
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


            


    def get_posts_details(self, post_ids, Session=None):
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
            user_id = Validator.decrypt(session['id'])
            post_ids = Validator.ensure_list(post_ids)
            # post_ids を動的復号化（整数っぽい値はそのまま int に変換）
            decrypted_ids = [
                Validator.decrypt(post_id) if isinstance(post_id, str) and not post_id.isdigit() else int(post_id)
                for post_id in post_ids
            ]
            # ブロック関連のサブクエリ
            blocked_users_subquery = (
                Session.query(Block.blocked_user)
                .filter(Block.user_id == user_id)
                .subquery()
            )

            blocked_by_subquery = (
                Session.query(Block.user_id)
                .filter(Block.blocked_user == user_id)
                .subquery()
            )

            # クエリ作成（リレーションも一括取得）
            posts = (
                Session.query(
                    Post,
                    exists().where((Like.post_id == Post.post_id) & (Like.user_id == user_id)).label("liked"),
                    exists().where((SavedPost.post_id == Post.post_id) & (SavedPost.user_id == user_id)).label("saved"),
                    exists().where((Repost.post_id == Post.post_id) & (Repost.user_id == user_id)).label("reposted"),
                    exists().where(Shop.post_id == Post.post_id).label("productized")
                ).filter(
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
            app.logger.info(f"posts: {posts}")
            if not posts:
                app.logger.warning(f"Posts with post_ids {post_ids} not found or blocked.")
                raise ValueError("投稿が見つかりません。")

            formatted_posts = []
        
            for post, liked, saved, reposted, productized in posts:
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
                    "is_me": user_id == post.author.id,
                    "liked": liked,
                    "saved": saved,
                    "reposted": reposted,
                    "productized": productized
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
            return [tag.tag_text for tag in tag_records]

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
                    contents=f"{session['username']}さんがあなたの投稿にいいねしました。",
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
                related_item_id=parent_post_id,
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
            repost = Session.query(Repost).filter(Repost.user_id == user_id,Repost.post_id == post_id).first()
            if repost:
                self.__notification_manager.delete_notification(related_item_id=post_id,related_item_type="post",sender_id=user_id,Session=Session)
                Session.delete(repost)
                status = "removed"
            else:
            # 重複チェックを含めて挿入
                repost = self.insert(model=Repost, data=repost_data, unique_check=repost_data,Session=Session)

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
                    status = "added"
                else:
                    raise Exception("何かのエラーが発生しました。")

            self.make_commit_or_flush(Session)
            self.redis.add_score(ranking_key=self.trending[0],item_id=post_id,score=10)
            return {"success":True,"status": status}


        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"Failed to create repost: {e}")
            self.error_log_manager.add_error(None, str(e))
            raise



    def get_post_comments(self, post_id, Session=None):
        """
        指定された投稿IDに紐づくコメント情報（コメント、コメントしたユーザーの情報、コメント数）を取得する
        :param session: SQLAlchemyのセッション
        :param post_id: 取得対象の投稿ID
        :return: コメントリスト、コメント数
        """
        try:
            Session = self.make_session(Session)
            # Userテーブルのエイリアスを作成（コメント投稿者用）
            if isinstance(post_id,str):
                post_id = Validator.decrypt(post_id)
            commenter = aliased(User)

            # クエリ実行
            comments_data = (
                Session.query(
                    Post.post_id.label("comment_id"),  # コメントのID
                    Post.body_text.label("comment_text"),  # コメント本文
                    Post.post_time.label("comment_time"),  # コメント投稿時間
                    commenter.id.label("id"),
                    commenter.username.label("username"),  # コメントしたユーザー名
                    commenter.profile_image.label("profile_image")  # コメントしたユーザーのプロフィール画像
                )
                .join(commenter, Post.user_id == commenter.id)  # コメント投稿者の情報を取得
                .filter(Post.reply_id == post_id)  # 指定の投稿IDに紐づくコメントを取得
                .order_by(Post.post_time.asc())  # 投稿の古い順に並べる
                .all()
            )

            # コメント数を取得
            comment_count = Session.query(func.count(Post.post_id)).filter(Post.reply_id == post_id).scalar()

            # データを辞書のリストとして返す
            comments_list = [
                {
                    "comment_id": comment.comment_id,
                    "comment_text": comment.comment_text,
                    "comment_time": Validator.calculate_time_difference(comment.comment_time),
                    "id":Validator.encrypt(comment.id),
                    "username": comment.username,
                    "profile_image":url_for("static", filename=f"images/profile_images/{comment.profile_image}"),
                }
                for comment in comments_data
            ]
            self.pop_and_close(Session)
            return comments_list, comment_count
        
        except Exception as e:
            app.logger.error(str(e))
            self.session_rollback(Session)
            return None
        

    def delete_post(self, post_ids, Session=None):
        try:
            app.logger.info("Starting delete_post method...")

            # セッション作成
            Session = self.make_session(Session)
            post_ids = Validator.ensure_list(post_ids)

            # post_id の復号処理（内包表記を使用）
            valid_post_ids = [
                Validator.decrypt(post_id) if isinstance(post_id, str) else post_id
                for post_id in post_ids
            ]

            if not valid_post_ids:
                raise Exception("Valid post IDs not found")

            # 投稿を取得
            posts = Session.query(Post).filter(Post.post_id.in_(valid_post_ids)).all()
            if not posts:
                raise Exception(f"Posts not found for IDs: {valid_post_ids}")

            app.logger.info(f"Found {len(posts)} posts for deletion.")

            # 画像の削除
            post_folder = app.config["POST_FOLDER"]
            for post in posts:
                images = Session.query(Image).filter_by(post_id=post.post_id).all()
                for image in images:
                    image_path = os.path.join(post_folder, image.img_path)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                        app.logger.info(f"Successfully deleted image: {image_path}")
                    else:
                        app.logger.warning(f"Image file not found: {image_path}")

            # DBから投稿を削除
            for post in posts:
                Session.delete(post)

            # コミット
            self.make_commit_or_flush(Session)
            app.logger.info(f"Successfully deleted {len(posts)} posts.")
            self.redis.remove_score(ranking_key=self.trending[0],item_id=post_ids)

            return {"success": True, "message": f"Deleted {len(posts)} posts successfully"}

        except Exception as e:
            app.logger.error(f"Error occurred in delete_post: {str(e)}", exc_info=True)
            self.session_rollback(Session)
            return {"success": False, "message": f"Failed to delete posts: {str(e)}"}
        
    def fetch_liked_posts(self, Session=None):
        """
        自分がいいねしている投稿の情報を取得し、成形するメソッド（投稿情報 + 最初の画像のみ）
        :param session: SQLAlchemyのSessionインスタンス
        :return: いいねした投稿のリスト（辞書形式）
        """
        try:
            Session = self.make_session(Session)
            user_id = session.get('id')
            if isinstance(user_id,str):
                user_id = Validator.decrypt(user_id)

            liked_posts = (
                Session.query(Post)
                .join(Like, Post.post_id == Like.post_id)
                .filter(Like.user_id == user_id)
                .options(joinedload(Post.images))  # 画像情報を事前にロード
                .all()
            )
            formatted_posts = []
            if liked_posts:
                for post in liked_posts:
                    # 最初の1枚目の画像を取得（img_orderの昇順でソート）
                    first_image = next((img for img in sorted(post.images, key=lambda x: x.img_order)), None)
                    image_url = f"/static/images/post_images/{first_image.img_path}" if first_image else None

                    formatted_posts.append({
                        "post_id": Validator.encrypt(post.post_id),
                        "body_text": post.body_text,
                        "image_url": image_url,
                        "post_time": Validator.calculate_time_difference(post.post_time),
                    })
            self.pop_and_close(Session)
            return {"success":True, "posts":formatted_posts}
        
        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(str(e))
            return {"success":False,"message":str(e)}
