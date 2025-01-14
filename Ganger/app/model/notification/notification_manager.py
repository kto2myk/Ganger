from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from Ganger.app.model.model_manager.model import Notification
from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.validator.validate import Validator
from Ganger.app.model.model_manager.model import Notification, NotificationDetail,NotificationStatus, NotificationType
from flask import current_app as app, url_for

class NotificationManager(DatabaseManager):
    def __init__(self):
        super().__init__()

    def get_notification_count(self, user_id, is_read=None, is_deleted=False):
        """
        特定のユーザーの通知件数を取得

        :param user_id: 通知の対象ユーザーID
        :param is_read: 既読/未読を指定（Noneの場合はすべての通知を対象）
        :param is_deleted: 削除済みを含むかどうか（デフォルトはFalse）
        :return: 通知件数（int）
        """
        try:
            with Session(self.engine) as session:
                # ベースクエリ
                query = session.query(NotificationStatus).join(Notification).filter(
                    NotificationStatus.user_id == user_id,
                    NotificationStatus.is_deleted == is_deleted
                )

                # 未読/既読のフィルタリング
                if is_read is not None:
                    query = query.filter(NotificationStatus.is_read == is_read)

                count = query.count()  # 件数を取得
                app.logger.info(f"Notification count for user {user_id}: {count}")
                return count

        except Exception as e:
            app.logger.error(f"Error retrieving notification count: {e}")
            self.error_log_manager.add_error(None, str(e))
            raise
        
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


    def get_or_create_notification_type(self, type_name):
        """
        通知タイプを取得または新規作成するメソッド

        :param type_name: 通知タイプ名（例: "LIKE", "COMMENT"）
        :return: 該当するNotificationTypeのID
        """
        try:
            # 通知タイプを検索
            existing_type = self.fetch_one(model=NotificationType, filters={"type_name": type_name})
            
            if existing_type:
                # 既存のタイプが見つかった場合、そのIDを返す
                return existing_type.notification_type_id
            
            # 存在しない場合は新しいタイプを作成
            new_type = self.insert(
                model=NotificationType,
                data={"type_name": type_name}
            )
            return new_type["notification_type_id"]

        except Exception as e:
            app.logger.error(f"Failed to get or create notification type '{type_name}': {e}")
            self.error_log_manager.add_error(None, str(e))
            raise


    def create_full_notification(self, sender_id, recipient_ids, type_name, contents, related_item_id=None, related_item_type=None):
        """
        通知および関連テーブルを一括作成するメソッド

        :param sender_id: 通知を送信するユーザーID
        :param recipient_ids: 通知を受信するユーザーIDのリスト
        :param type_name: 通知の種類名（例: "LIKE", "COMMENT"）
        :param contents: 通知内容
        :param related_item_id: 通知に関連するアイテムのID（例: post_id）
        :param related_item_type: 通知に関連するアイテムの種類（例: "post"）
        :return: 作成された通知情報のリスト
        """
        try:
            if not isinstance(recipient_ids, list):
                recipient_ids = [recipient_ids]

            with Session(self.engine) as session:
                # 通知タイプを取得または作成
                notification_type_id = self.get_or_create_notification_type(type_name)

                # 各受信者ごとにNotificationを作成
                for recipient_id in recipient_ids:
                    # Notificationの作成（受信者IDを設定）
                    new_notification = Notification(
                        notification_type_id=notification_type_id,
                        contents=contents,
                        user_id=recipient_id  # 受信者ID
                    )
                    session.add(new_notification)
                    session.flush()  # `notification_id`を取得

                    # NotificationDetailの作成
                    detail = NotificationDetail(
                        notification_id=new_notification.notification_id,
                        sender_id=sender_id,  # 送信者ID
                        recipient_id=recipient_id,
                        notification_type_id=notification_type_id,
                        related_item_id=related_item_id,
                        related_item_type=related_item_type
                    )
                    session.add(detail)

                    # NotificationStatusの作成
                    status = NotificationStatus(
                        notification_id=new_notification.notification_id,
                        user_id=recipient_id,  # 受信者ID
                        is_read=False,
                        is_deleted=False
                    )
                    session.add(status)

                # コミットされるとすべての操作が保存される
                session.commit()
                return True

        except Exception as e:
            app.logger.error(f"Failed to create full notification: {e}")
            self.error_log_manager.add_error(None, str(e))
            raise

    def delete_notification(self, sender_id, recipient_id, type_name,related_item_id, related_item_type):
        """
        指定条件に基づいて通知を削除する

        :param sender_id: 通知を送信したユーザーID
        :param recipient_id: 通知を受信したユーザーID
        :param type_name: 通知の種類名（例: "LIKE", "COMMENT"）
        :param notification_type_id: 通知の種類ID
        :param related_item_id: 通知に関連するアイテムのID（例: post_id）
        :param related_item_type: 通知に関連するアイテムの種類（例: "post"）
        :return: 削除された通知の数
        """
        try:
            notification_type_id = self.get_or_create_notification_type(type_name) # 通知タイプIDを取得

            with Session(self.engine) as session:
                # NotificationDetailを検索
                notification_detail = session.query(NotificationDetail).filter_by(
                    sender_id=sender_id,
                    recipient_id=recipient_id,
                    notification_type_id=notification_type_id,
                    related_item_id=related_item_id,
                    related_item_type=related_item_type
                ).first()

                if not notification_detail:
                    app.logger.info("No matching notification found.")
                    return 0  # 該当する通知が見つからない場合

                # 該当するNotificationを削除
                notification_id = notification_detail.notification_id
                deleted_count = self.delete(model=Notification, filters={"notification_id": notification_id})
                # コミットして削除を確定
                session.commit()

                app.logger.info(f"Notification with ID {notification_id} deleted.")
                return   deleted_count# 削除成功のフラグとして1を返す

        except Exception as e:
            app.logger.info(f"Failed to delete notification: {e}")
            self.error_log_manager.add_error(sender_id, str(e))
            raise
