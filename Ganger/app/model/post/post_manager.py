import os
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename
from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.model_manager.model import Post, Image

class PostManager(DatabaseManager):
    def __init__(self):
        super().__init__()
        self.upload_folder = "Ganger/app/static/images/post_images"
        self.allowed_extensions = {".png", ".jpg", ".jpeg", ".gif"}

    def is_allowed_extension(self, filename):
        """
        ファイルの拡張子が許可されているか確認
        """
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.allowed_extensions

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
        try:
            # 投稿データをDBに挿入
            post_result = self.insert(model=Post, data=post_data)
            if not post_result:
                return {"error": "Failed to create post."}

            post_id = post_result["post_id"]
            user_id = post_data["user_id"]
            saved_images = []

            for index, file in enumerate(image_files, start=1):
                # ファイル名を安全化し、拡張子を確認
                original_filename = secure_filename(file.filename)
                if not self.is_allowed_extension(original_filename):
                    return {"error": f"File type not allowed: {original_filename}"}

                ext = os.path.splitext(original_filename)[1].lower()
                filename = self.generate_filename(user_id, post_id, index, ext)
                file_path = os.path.join(self.upload_folder, filename)

                # ファイル名をDBに登録
                image_data = {
                    "post_id": post_id,
                    "img_path": filename,  # DBにはファイル名のみを登録
                    "img_order": index
                }
                image_result = self.insert(model=Image, data=image_data)
                if not image_result:
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
            return {"error": str(e)}
