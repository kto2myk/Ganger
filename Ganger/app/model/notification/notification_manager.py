from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from Ganger.app.model.model_manager.model import Notification
from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.validator.validate import Validator
from Ganger.app.model.model_manager.model import Notification, NotificationDetail
from flask import current_app as app, url_for

class NotificationManager(DatabaseManager):
    def __init__(self):
        super().__init__()

    def get_notifications_for_user(self, user_id):
        """
        指定したユーザーの通知情報を降順で取得するメソッド
        :param user_id: ユーザーID
        :return: 辞書型の通知情報リスト
        """
        try:
            user_id = Validator.decrypt(user_id)  # ユーザーIDを復号化
            with Session(self.engine) as session:
                # 通知情報を降順で取得
                notifications = (
                    session.query(Notification)
                    .join(Notification.details)  # NotificationDetail を結合
                    .filter(Notification.details.any(recipient_id=user_id))  # 被送信者が指定されたユーザー
                    .options(
                        joinedload(Notification.notification_type_relation),  # 通知タイプのリレーションをロード
                        joinedload(Notification.statuses),                   # 通知ステータスのリレーションをロード
                        joinedload(Notification.details).joinedload(NotificationDetail.sender),  # 発信者の情報をロード
                        joinedload(Notification.details).joinedload(NotificationDetail.recipient)  # 被送信者の情報をロード
                    )
                    .order_by(Notification.sent_time.desc())  # 送信日時で降順にソート
                    .all()
                )

                # 辞書型に変換
                notification_dicts = []
                for notification in notifications:
                    notification_dict = {
                        "contents": notification.contents,
                        "sent_time": notification.sent_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "notification_type": notification.notification_type_relation.type_name,
                        "statuses": [
                            {
                                "is_read": status.is_read,
                                "is_deleted": status.is_deleted,
                            }
                            for status in notification.statuses
                        ],
                        "details": [
                            {
                                "sender": {
                                    "id": Validator.encrypt(detail.sender.id),
                                    "username": detail.sender.username,
                                    "profile_image": url_for("static",filename = f"images/profile_images/{detail.sender.profile_image}"),
                                } if detail.sender else None,
                                "related_item_type": detail.related_item_type,
                                "related_item_id": Validator.encrypt(detail.related_item_id) if detail.related_item_id else None,
                            }
                            for detail in notification.details
                        ]
                    }
                    notification_dicts.append(notification_dict)

                return notification_dicts

        except SQLAlchemyError as e:
            # エラーハンドリング
            app.logger.error(f"Failed to fetch notifications: {e}")
            self.error_log_manager.add_error("NotificationManager.get_notifications_for_user", str(e))
            return []
