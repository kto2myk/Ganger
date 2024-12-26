import os
from sqlalchemy.orm  import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename
from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.model_manager.model import Post, Image
from flask import current_app as app, url_for
class PostManager(DatabaseManager):
    def __init__(self):
        super().__init__()

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


    def search_tags(self, query):
        from Ganger.app.model.model_manager.model import TagMaster, TagPost, Post, Image
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
                        "post_id": post.post_id,
                        "body_text": post.body_text,
                        "post_time": post.post_time,
                        "tag_texts": [tag.tag_text for tag in tags if tag.tag_id in [tp.tag_id for tp in post.tags]],  # POSTのタグ名
                        "image_url": url_for('static', filename=f"images/post_images/{first_image.img_path}") if first_image else None
                    })
                
                return results
            return []
            
    def search_categories(self, query):
        from Ganger.app.model.model_manager.model import CategoryMaster, ProductCategory, Shop, Post, Image
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
                        "post_id": post.post_id,
                        "body_text": post.body_text,
                        "post_time": post.post_time,
                        "category_names": [category.category_name for category in categories if category.category_id in [pc.category_id for pc in post.categories]],  # POSTのカテゴリ名
                        "image": first_image.img_path if first_image else None  # 最初の画像
                    })
                
                return results
            return []
        
    def add_tag_to_post(self, tag_text, post_id):
        from Ganger.app.model.model_manager.model import TagMaster, TagPost
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