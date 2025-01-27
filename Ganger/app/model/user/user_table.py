from werkzeug.security import generate_password_hash, check_password_hash # パスワードハッシュ化用
from Ganger.app.model.database_manager.database_manager import DatabaseManager # データベース操作用
from Ganger.app.model.model_manager.model import User,Post,Follow,Block
from flask import session, url_for  # セッション管理、画像パス生成用
from Ganger.app.model.validator.validate import Validator # バリデーション用
from Ganger.app.model.model_manager.model import User # ユーザーテーブル
from sqlalchemy.orm import Session, joinedload# セッション管理、リレーション取得用
from sqlalchemy import or_ # OR検索用
from sqlalchemy.exc import SQLAlchemyError # データベースエラー用
import uuid # ランダムID生成用
from flask import current_app as app # ログ出力用


class UserManager(DatabaseManager):
    def __init__(self):
        super().__init__()


    def create_user(self, username: str, email: str, password: str,Session=None):
        """
        ユーザー作成処理を行い、成功時にセッションを登録。
        """
        randomid = str(uuid.uuid4())[:8]
        user_id = f"{username}_{randomid}"
        # Session = self.make_session(Session)
        try:
            Session = self.make_session(Session)
            # Email形式の検証
            Validator.validate_email_format(email)

            # ユーザー作成
            user_data = {
                "user_id": user_id,
                "username": username,
                "email": email,
                "password": generate_password_hash(password)
            }
            new_user = self.insert(User, user_data, unique_check={"email": email},Session=Session)

            if not new_user:
                raise ValueError("このメールアドレスは既に使用されています。")

            # セッション登録
            self.register_session(new_user)

            self.make_commit_or_flush(Session)
            return True, new_user

        except ValueError as ve:
            self.session_rollback(Session)
            app.logger.error(f"[ERROR] Validation error: {ve}")
            self.error_log_manager.add_error(None, str(ve))
            return False, str(ve)
        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"[ERROR] Unexpected error: {e}")
            self.error_log_manager.add_error(None, str(e))
            return False, str(e)

    def login(self, identifier: str, password: str,Session=None):
        """
        メールアドレスまたはユーザーIDでログイン。成功時にセッションを登録。
        """
        try:
            Session = self.make_session(Session)
            # ユーザー検索
            user = self.fetch_one(User, filters={"email": identifier},Session=Session) or self.fetch_one(User, filters={"user_id": identifier},Session=Session)
            if not user or not check_password_hash(user.password, password):
                raise Exception("ユーザー名またはパスワードが間違っています。")
            # セッション登録
            self.register_session(user)

            self.pop_and_close(Session)
            return user, None

        except Exception as e:
            self.session_rollback(Session)
            self.error_log_manager.add_error(None, str(e))
            return None, str(e)


    @staticmethod
    def register_session(data, keys=None, custom_logic=None):
        """
        セッションにデータを登録する
        :param data: 辞書型またはクラスのインスタンス
        :param keys: セッションに登録するキーのリスト（指定がない場合はすべて登録）
        :param custom_logic: 特殊処理用の辞書（key: 処理するキー, value: 関数）
        """
        # SQLAlchemyモデルの場合、辞書形式に変換
        if hasattr(data, "__dict__"):
            source = {key: value for key, value in vars(data).items() if not key.startswith("_")}
        elif isinstance(data, dict):
            source = data
        else:
            raise ValueError("渡されたデータは辞書型でもクラスのインスタンスでもありません。")

        # セッションに登録
        for key in (keys or source.keys()):
            if key in source:
                value = source[key]

                # 特殊処理: IDを暗号化
                if "id" in key.lower():  # "id" を含むキー名を検出
                    session[key] = Validator.encrypt(value)
                elif custom_logic and key in custom_logic:
                    session[key] = custom_logic[key](value)  # カスタムロジック適用
                else:
                    session[key] = value  # 通常の登録処理

        # プロフィール画像の特殊処理
        if "profile_image" in source and source["profile_image"]:
            session["profile_image"] = url_for("static", filename=f"images/profile_images/{source['profile_image']}")
        else:
            session["profile_image"] = url_for("static", filename="images/profile_images/default.png")

    def search_users(self, query,Session=None):
        """
        指定されたクエリに基づいてユーザーを検索し、結果を返す。
        """
        try:
            Session = self.make_session(Session)
            users = Session.query(User).filter(
                or_(
                    User.user_id.ilike(f"%{query}%"),
                    User.username.ilike(f"%{query}%")
                )
            ).limit(10).all()

            self.pop_and_close(Session)
            return [{"user_id": user.user_id, "username": user.username, "id": Validator.encrypt(user.id)} for user in users]
        except SQLAlchemyError as e:
            self.session_rollback(Session)
            app.logger.error(f"Failed to search users: {e}")
            raise

        
    def get_user_profile_with_posts(self, user_id,Session=None):
        """
        指定されたユーザーIDのプロフィール情報と投稿データを取得。

        Args:
            user_id (str): 暗号化されたユーザーID。

        Returns:
            dict: プロフィール情報と投稿データのリスト。
        """
        try:
            # 暗号化されたユーザーIDを復号化
            decrypted_id = Validator.decrypt(user_id)

            Session = self.make_session(Session)
            # ユーザー情報を取得
            user = Session.query(User).filter_by(id=decrypted_id).one_or_none()
            if not user:
                raise ValueError("ユーザーが見つかりません。")

            # 投稿データを取得（投稿時間降順）
            posts = (
                Session.query(Post)
                .filter(Post.user_id == decrypted_id, Post.reply_id == None)  # NULL判定を追加
                .options(joinedload(Post.images))  # 画像を一度に取得
                .order_by(Post.post_time.desc())  # 投稿時間で降順ソート
                .all()
            )

            # 投稿情報を整形
            formatted_posts = [
                {
                    "post_id": Validator.encrypt(post.post_id),
                    "first_image": (
                        url_for("static", filename=f"images/post_images/{post.images[0].img_path}")
                        if post.images else None  # 最初の画像のみ取得
                    ),
                }
                for post in posts
            ]

            # プロフィール情報を整形
            profile_data = {
                "is_me":True if session.get('id') == user_id else None,
                "id": Validator.encrypt(user.id),
                "user_id": user.user_id,
                "username": user.username,
                "profile_image": url_for("static", filename=f"images/profile_images/{user.profile_image}"),
                "posts": formatted_posts,
            }
        
            self.pop_and_close(Session)
            return profile_data
        
        except SQLAlchemyError as db_error:
            self.session_rollback(Session)
            app.logger.error(f"Database error: {db_error}")
            raise
        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"Unexpected error: {e}")
            raise

    def toggle_follow(self, followed_user_id,Session=None):
        """
        フォロー機能を切り替えるメソッド

        :param follow_user_id: フォロー対象のユーザーID
        :param sender_id: フォローを行うユーザーID
        :return: 処理結果を表す辞書
        """
        try:
            followed_user_id = Validator.decrypt(followed_user_id)
            sender_id = Validator.decrypt(session.get('id'))
            Session = self.make_session(Session)
            data = {'follow_user_id':followed_user_id , 'user_id': sender_id}
            existing_follow = self.fetch_one(model=Follow, filters=data, Session=Session)

            if existing_follow:
                # フォローが存在する場合は削除
                self.delete(model=Follow, filters=data, Session=Session)
                app.logger.info(f"Follow removed: followed_user={sender_id}, user_id={sender_id}")
                result = {"status": "unfollowed"}
            else:
                # フォローが存在しない場合は作成
                self.insert(model=Follow, data=data, Session=Session)
                app.logger.info(f"Follow added: followed_user={followed_user_id}, user_id={sender_id}")
                result = {"status": "followed"}

            self.make_commit_or_flush(Session)
            return result

        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"Failed to toggle follow: {e}")
            self.error_log_manager.add_error(sender_id, str(e))
            raise