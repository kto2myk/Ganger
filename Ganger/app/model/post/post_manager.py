import os
import uuid
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
    def __init__(self):
        super().__init__()
        self.__notification_manager = NotificationManager()

    def is_allowed_extension(self, filename):
        """ ファイルの拡張子が許可されているか確認 """
        allowed_extensions = {".png", ".jpg", ".jpeg", ".gif"}
        ext = os.path.splitext(filename)[1].lower()
        return ext in allowed_extensions

    def generate_filename(self, user_id, post_id, img_order, ext):
        """ 一意のファイル名を生成する """
        unique_id = uuid.uuid4().hex  # UUIDを使用して衝突を回避
        return f"{user_id}_{post_id}_{img_order}_{unique_id}{ext}"

    def save_file(self, file, file_path):
        """ ファイルを指定のパスに保存する """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)

    def delete_files(self, file_list):
        """ エラー発生時に保存したファイルを削除 """
        for file_path in file_list:
            if os.path.exists(file_path):
                os.remove(file_path)

                
    def create_post(self, content, image_files, tags, Session=None):
        """ 
        投稿データを作成し、関連する画像とタグを保存する 
        """
        upload_folder = "Ganger/app/static/images/post_images"
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
    
    def get_filtered_posts_with_reposts(self, filters, current_user_id,Session=None):
        """
        指定されたユーザーIDを基に投稿とリポスト元の投稿を取得し、いいねと保存に登録されていない投稿のみを返す。

        Args:
            filters (dict): 投稿データの取得条件。
            current_user_id (int): ログインしているユーザーのID。

        Returns:
            list: フォーマットされた投稿データのリスト。
        """
        try:
            Session = self.make_session(Session)
            # フィルターで渡されたUSERIDを取得
            user_id = filters.get("user_id")
            if not user_id:
                raise ValueError("user_idフィルターが指定されていません。")

            # サブクエリでログインユーザーの「いいね」と「保存」,[ブロックされている or しているユーザー ]を取得
            liked_posts_subquery = Session.query(Like.post_id).filter(Like.user_id == current_user_id).subquery()
            saved_posts_subquery = Session.query(SavedPost.post_id).filter(SavedPost.user_id == current_user_id).subquery()
            blocked_users_subquery = Session.query(Block.blocked_user).filter(Block.user_id == current_user_id).subquery()
            blocked_by_subquery = Session.query(Block.user_id).filter(Block.blocked_user == current_user_id).subquery()

            # 指定されたユーザーのオリジナル投稿を取得
            user_posts_query = Session.query(Post).filter(
                Post.user_id == user_id,
                Post.reply_id == None,  # リプライでない
                ~Post.post_id.in_(select(liked_posts_subquery)),
                ~Post.post_id.in_(select(saved_posts_subquery)),
                ~Post.user_id.in_(select(blocked_users_subquery)),  # ブロックしている人を除外
                ~Post.user_id.in_(select(blocked_by_subquery))  # ブロックされている人を除外
            ).options(
                joinedload(Post.images),
                joinedload(Post.author)
            )

            # 指定されたユーザーがリポストした元の投稿を取得
            reposted_posts_query = Session.query(Post).join(Repost, Repost.post_id == Post.post_id).filter(
                Repost.user_id == user_id,
                Post.reply_id == None,  # リプライでない
                ~Post.post_id.in_(select(liked_posts_subquery)),
                ~Post.post_id.in_(select(saved_posts_subquery)),
                ~Post.user_id.in_(select(blocked_users_subquery)),  # ブロックしている人を除外
                ~Post.user_id.in_(select(blocked_by_subquery))  # ブロックされている人を除外

            ).options(
                joinedload(Post.images),
                joinedload(Post.author),
                joinedload(Repost.user)
            )

            # オリジナル投稿とリポストを結合し、投稿時間で降順に並べ替え
            all_posts = user_posts_query.union_all(reposted_posts_query).order_by(Post.post_time.desc()).limit(3)

            # 投稿データをフォーマット
            formatted_posts = []
            for post in all_posts:
                # 投稿データをフォーマット
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
                    "repost_user": (
                            {
                                "id": Validator.encrypt(repost.user.id),
                                "user_id": repost.user.user_id,
                                "username": repost.user.username,
                                "profile_image": url_for("static", filename=f"images/profile_images/{repost.user.profile_image}")
                            } if (repost := next((r for r in post.reposts 
                                                if r.user.id == user_id),
                                                None)) 
                                                else None
                        )
                }
                formatted_posts.append(formatted_post)
            self.pop_and_close(Session)
            return formatted_posts

        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"Error in get_filtered_posts_with_reposts: {e}")
            self.error_log_manager.add_error(None, str(e))
            raise


            

    def get_post_details(self, post_id,Session=None):
        """
        指定されたpost_idの投稿データを取得し、フォーマットして返す。

        Args:
            post_id (int): 取得する投稿のID。

        Returns:
            dict: フォーマットされた投稿データ。
        """
        try:
            Session = self.make_session(Session)
            # 投稿データを取得
            post = self.fetch_one(
                model=Post,
                relationships=["images", "author"],
                filters={"post_id": Validator.decrypt(post_id)},
                Session=Session
            )

            if not post:
                app.logger.warning(f"Post with post_id {post_id} not found.")
                raise ValueError("投稿が見つかりません。")

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
                ]
            }
            self.pop_and_close(Session)
            return formatted_post
        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"Error in get_post_details: {e}")
            raise

    def search_tags(self, query, Session=None):
        try:
            Session = self.make_session(Session)

            # タグの検索（部分一致）
            tags = Session.query(TagMaster).filter(
                TagMaster.tag_text.ilike(f"%{query}%")
            ).all()
            print(f"Query: {query}, Tags Found: {[tag.tag_text for tag in tags]}")  # デバッグログ

            results = []
            if tags:
                for tag in tags:
                    # タグに紐づく投稿数をカウント
                    post_count = Session.query(Post).join(TagPost).filter(
                        TagPost.tag_id == tag.tag_id
                    ).count()
                    app.redis_client.zincrby("trending_tags", 5, f"{tag.tag_id}:{tag.tag_text}")

                    # タグに紐づく投稿を最大5件取得
                    posts = (
                        Session.query(Post)
                        .join(TagPost)
                        .filter(TagPost.tag_id == tag.tag_id)
                        .limit(5)
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
            app.redis_client.zincrby("trending_tags", 10, f"{tag['tag_id']}:{tag_text}")
            self.insert(model=TagPost, data=tag_post_data, unique_check=tag_post_data, Session=Session)

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
                result = {"status": "removed"}
            else:
                # 保存されていない場合は追加
                self.insert(model=SavedPost, data={'post_id': post_id, 'user_id': user_id},Session=Session)
                app.logger.info(f"SavedPost added: post_id={post_id}, user_id={user_id}")
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
            return repost


        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"Failed to create repost: {e}")
            self.error_log_manager.add_error(None, str(e))
            raise

