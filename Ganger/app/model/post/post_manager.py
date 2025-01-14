import os
from sqlalchemy.sql import select
from sqlalchemy.orm  import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename
from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.model_manager.model import User,Post, Image,Like,TagMaster, TagPost,CategoryMaster, ProductCategory, Shop,Repost,SavedPost
from Ganger.app.model.notification.notification_manager import NotificationManager
from flask import current_app as app, session, url_for
from Ganger.app.model.validator import Validator

class PostManager(DatabaseManager):
    def __init__(self):
        super().__init__()
        self.__notification_manager = NotificationManager()

    def is_allowed_extension(self, filename):
        """
        ファイルの拡張子が許可されているか確認
        """
        allowed_extensions = {".png", ".jpg", ".jpeg", ".gif"}
        ext = os.path.splitext(filename)[1].lower()
        return ext in allowed_extensions

    def generate_filename(self, user_id, post_id, img_order, ext):
        """
        ファイル名を生成する
        :param user_id: ユーザーID
        :param post_id: 投稿ID
        :param img_order: 画像順序
        :param ext: ファイル拡張子
        :return: 生成されたファイル名
        """
        return f"{user_id}_{post_id}_{img_order}{ext}"

    def save_file(self, file, file_path):
        """
        ファイルを指定のパスに保存する
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)

    def create_post(self, post_data, image_files):
        """
        投稿データを作成し、関連する画像を保存する
        """
        upload_folder = "Ganger/app/static/images/post_images"

        try:
            # 投稿データをDBに挿入
            post_result = self.insert(model=Post, data=post_data)
            if not post_result:
                app.logger.error("Failed to create post.")
                return {"error": "Failed to create post."}

            post_id = post_result["post_id"]
            user_id = post_data["user_id"]
            saved_images = []

            for index, file in enumerate(image_files, start=1):
                # ファイル名を安全化し、拡張子を確認
                original_filename = secure_filename(file.filename)
                if not self.is_allowed_extension(original_filename):
                    app.logger.error(f"File type not allowed: {original_filename}")
                    return {"error": f"File type not allowed: {original_filename}"}

                ext = os.path.splitext(original_filename)[1].lower()
                filename = self.generate_filename(user_id, post_id, index, ext)
                file_path = os.path.join(upload_folder, filename)

                # ファイル名をDBに登録
                image_data = {
                    "post_id": post_id,
                    "img_path": filename,  # DBにはファイル名のみを登録
                    "img_order": index
                }
                image_result = self.insert(model=Image, data=image_data)
                if not image_result:
                    app.logger.error(f"Failed to register image in DB: {filename}")
                    return {"error": f"Failed to register image in DB: {filename}"}

                # ファイルを保存
                self.save_file(file, file_path)
                saved_images.append(filename)

            return {
                "post": post_result,
                "images": saved_images
            }
        except SQLAlchemyError as e:
            self.error_log_manager.add_error(None, str(e))
            app.logger.error(f"Failed to create post: {e}")
            return {"error": str(e)}


    def get_filtered_posts_with_reposts(self, filters, current_user_id):
        """
        指定されたユーザーIDを基に投稿とリポスト元の投稿を取得し、いいねと保存に登録されていない投稿のみを返す。

        Args:
            filters (dict): 投稿データの取得条件。
            current_user_id (int): ログインしているユーザーのID。

        Returns:
            list: フォーマットされた投稿データのリスト。
        """
        try:
            with Session(self.engine) as session:
                # フィルターで渡されたUSERIDを取得
                user_id = filters.get("user_id")
                if not user_id:
                    raise ValueError("user_idフィルターが指定されていません。")

                # サブクエリでログインユーザーの「いいね」と「保存」を取得
                liked_posts_subquery = session.query(Like.post_id).filter(Like.user_id == current_user_id).subquery()
                saved_posts_subquery = session.query(SavedPost.post_id).filter(SavedPost.user_id == current_user_id).subquery()

                # 指定されたユーザーのオリジナル投稿を取得
                user_posts_query = session.query(Post).filter(
                    Post.user_id == user_id,
                    Post.reply_id == None,  # リプライでない
                    Post.post_id.notin_(select(liked_posts_subquery)),
                    Post.post_id.notin_(select(saved_posts_subquery))
                ).options(
                    joinedload(Post.images),
                    joinedload(Post.author)
                )

                # 指定されたユーザーがリポストした元の投稿を取得
                reposted_posts_query = session.query(Post).join(Repost, Repost.post_id == Post.post_id).filter(
                    Repost.user_id == user_id,
                    Post.reply_id == None,  # リプライでない
                    Post.post_id.notin_(select(liked_posts_subquery)),
                    Post.post_id.notin_(select(saved_posts_subquery))
                ).options(
                    joinedload(Post.images),
                    joinedload(Post.author),
                    joinedload(Repost.user)
                )

                # オリジナル投稿とリポストを結合し、投稿時間で降順に並べ替え
                all_posts = user_posts_query.union_all(reposted_posts_query).order_by(Post.post_time.desc()).all()

                # 投稿データをフォーマット
                formatted_posts = []
                for post in all_posts:
                    # 投稿データをフォーマット
                    formatted_post = {
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
                                } if (repost := next((r for r in post.reposts if r.user.id == user_id), None)) else None
                            )
                    }

                    formatted_posts.append(formatted_post)

                return formatted_posts

        except Exception as e:
            app.logger.error(f"Error in get_filtered_posts_with_reposts: {e}")
            self.error_log_manager.add_error(None, str(e))
            raise


            

    def get_post_details(self, post_id):
        """
        指定されたpost_idの投稿データを取得し、フォーマットして返す。

        Args:
            post_id (int): 取得する投稿のID。

        Returns:
            dict: フォーマットされた投稿データ。
        """

        try:
            # デバッグ用ログ
            app.logger.info(f"Querying post with post_id: {post_id}")

            # 投稿データを取得
            post = self.fetch_one(
                model=Post,
                relationships=["images", "author"],
                filters={"post_id": Validator.decrypt(post_id)}
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

            app.logger.info(f"Formatted post: {formatted_post}")
            return formatted_post
        except Exception as e:
            app.logger.error(f"Error in get_post_details: {e}")
            raise

    def search_tags(self, query):

        with Session(self.engine) as session:
            # タグの検索
            tags = session.query(TagMaster).filter(
                TagMaster.tag_text.ilike(f"%{query}%")
            ).all()

            print(f"Query: {query}, Tags Found: {[tag.tag_text for tag in tags]}")  # デバッグログ

            if tags:
                tag_ids = [tag.tag_id for tag in tags]
                # タグに紐づくPOSTを取得
                posts = session.query(Post).join(TagPost).filter(
                    TagPost.tag_id.in_(tag_ids)
                ).all()

                # 結果をフォーマット
                results = []
                for post in posts:
                    # POSTに関連する最初の画像を取得
                    first_image = session.query(Image).filter(
                        Image.post_id == post.post_id
                    ).order_by(Image.img_order).first()  # 画像の順序を考慮

                    results.append({
                        "post_id": Validator.encrypt(post.post_id),
                        "body_text": post.body_text,
                        "post_time": post.post_time,
                        "tag_texts": [tag.tag_text for tag in tags if tag.tag_id in [tp.tag_id for tp in post.tags]],  # POSTのタグ名
                        "image_url": url_for('static', filename=f"images/post_images/{first_image.img_path}") if first_image else None
                    })
                
                return results
            return []

    def search_categories(self, query):
        with Session(self.engine) as session:
            # カテゴリーの検索
            categories = session.query(CategoryMaster).filter(
                CategoryMaster.category_name.ilike(f"%{query}%")
            ).all()

            if categories:
                category_ids = [category.category_id for category in categories]
                
                # カテゴリーに紐づく商品を取得
                products = session.query(Shop).join(ProductCategory).filter(
                    ProductCategory.category_id.in_(category_ids)
                ).all()

                # 商品に紐づくPOSTを取得
                post_ids = [product.post_id for product in products if product.post_id]
                posts = session.query(Post).filter(Post.post_id.in_(post_ids)).all()

                # 結果をフォーマット
                results = []
                for post in posts:
                    # POSTに関連する最初の画像を取得
                    first_image = session.query(Image).filter(
                        Image.post_id == post.post_id
                    ).order_by(Image.img_order).first()  # 画像の順序を考慮

                    results.append({
                        "post_id": Validator.encrypt(post.post_id),
                        "body_text": post.body_text,
                        "post_time": post.post_time,
                        "category_names": [category.category_name for category in categories if category.category_id in [pc.category_id for pc in post.categories]],  # POSTのカテゴリ名
                        "image": first_image.img_path if first_image else None  # 最初の画像
                    })
                
                return results
            return []
        
    def add_tag_to_post(self, tag_text, post_id):
        try:
            # タグが既存か確認
            tag_data = {"tag_text": tag_text}
            tag = self.insert(model=TagMaster, data=tag_data, unique_check={"tag_text": tag_text})
            
            if not tag:  # タグが既存の場合、取得
                tag = self.fetch_one(model=TagMaster, filters={"tag_text": tag_text})
            
            # タグポスト関係を作成
            tag_post_data = {"tag_id": tag["tag_id"], "post_id": post_id}
            self.insert(model=TagPost, data=tag_post_data, unique_check=tag_post_data)
            app.logger.info(f"タグ '{tag_text}' が投稿 {post_id} に追加されました。")
        except Exception as e:
            app.logger.error(f"エラーが発生しました: {e}")



    def toggle_like(self, post_id, sender_id):
        """
        いいね機能を切り替えるメソッド

        :param post_id: いいね対象の投稿ID
        :param recipient_id: いいねを受け取るユーザーID
        :param sender_id: いいねを送信するユーザーID
        :return: 処理結果を表す辞書
        """
        try:
            # Likeテーブルを検索
            unique_check = {'post_id': post_id, 'user_id': sender_id}
            existing_like = self.fetch_one(model=Like, filters=unique_check,relationships=["post"])

            if existing_like:
                # いいねが存在する場合は削除
                self.delete(model=Like, filters=unique_check)
                self.__notification_manager.delete_notification(
                    sender_id=sender_id,
                    recipient_id=existing_like.post.user_id,
                    type_name="LIKE",
                    related_item_id=post_id,
                    related_item_type="post"
                )
                app.logger.info(f"Like removed: post_id={post_id}, user_id={sender_id}")
                return {"status": "removed"}
            else:
                # いいねが存在しない場合は作成
                self.insert(model=Like, data={'post_id': post_id, 'user_id': sender_id})
                post = self.fetch_one(Post, filters={"post_id": post_id})
                self.__notification_manager.create_full_notification(
                    sender_id=sender_id,
                    recipient_ids=post.user_id,  # 受信者は単一でもリスト形式で処理可能
                    type_name="LIKE",
                    contents=f"{session["username"]}さんがあなたの投稿にいいねしました",
                    related_item_id=post_id,
                    related_item_type="post"
                )
                app.logger.info(f"Like added: post_id={post_id}, user_id={sender_id}")
                return {"status": "added"}
        except Exception as e:
            app.logger.error(f"Failed to toggle like: {e}")
            self.error_log_manager.add_error(sender_id, str(e))
            raise

    def add_comment(self, user_id, parent_post_id, comment_text):
        """
        コメントを投稿し、通知を送信するメソッド

        :param user_id: コメントを投稿するユーザーのID
        :param parent_post_id: 親投稿のID
        :param comment_text: コメント本文
        :return: 作成されたコメントの情報
        """
        try:
            # 親投稿の存在確認とリレーションの事前ロード
            parent_post = self.fetch_one(Post, filters={"post_id": parent_post_id}, relationships=["author"])
            if not parent_post:
                raise ValueError(f"Parent post with ID {parent_post_id} does not exist.")
            # コメントデータを挿入
            comment_data = {
                "user_id": user_id,
                "reply_id": parent_post_id,
                "body_text": comment_text
            }
            new_comment = self.insert(model=Post, data=comment_data)

            if not new_comment:
                raise ValueError("Failed to insert the comment. Possible duplicate.")

            # 通知を送信
            self.__notification_manager.create_full_notification(
                sender_id=user_id,
                recipient_ids=parent_post.author.id,
                type_name="COMMENT",
                contents=f"{session["username"]}さんがあなたの投稿にコメントしました。: {comment_text[:50]}...",
                related_item_id=new_comment["post_id"],
                related_item_type="post"
            )

            return new_comment

        except Exception as e:
            app.logger.error(f"Failed to add comment: {e}")
            self.__error_log_manager.add_error(user_id, str(e))
            raise


    def create_repost(self, user_id, post_id):
        """
        リポストを作成し、通知を発行するメソッド。

        Args:
            user_id (int): リポストを行うユーザーのID。
            post_id (int): リポストする投稿のID。

        Returns:
            dict: 作成されたリポストの情報。
        """
        try:
            # リポストデータを挿入
            repost_data = {
                "user_id": user_id,
                "post_id": post_id,
            }

            # 重複チェックを含めて挿入
            unique_check = {"user_id": user_id, "post_id": post_id}
            repost = self.insert(model=Repost, data=repost_data, unique_check=unique_check)

            if repost:
                # 通知を発行
                post_author = self.fetch_one(model=Post, filters={"post_id": post_id}, relationships=["author"])
                self.__notification_manager.create_full_notification(
                    sender_id=user_id,
                    recipient_ids=[post_author.author.id],  # 投稿の作成者に通知
                    type_name="REPOST",
                    contents=f"{session["username"]}さんがあなたの投稿をリポストしました。",
                    related_item_id=post_id,
                    related_item_type="post"
                )

                return repost
            else:
                app.logger.info("リポストはすでに存在します。")
                return None

        except Exception as e:
            app.logger.error(f"Failed to create repost: {e}")
            self.error_log_manager.add_error(None, str(e))
            raise

