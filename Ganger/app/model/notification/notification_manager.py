from sqlalchemy.orm import joinedload
from sqlalchemy import or_,and_
from sqlalchemy.exc import SQLAlchemyError
from Ganger.app.model.model_manager.model import Notification
from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.validator.validate import Validator
from Ganger.app.model.model_manager.model import Notification, NotificationDetail,NotificationStatus, NotificationType
from flask import current_app as app, url_for

class NotificationManager(DatabaseManager):
    def __init__(self):
        super().__init__()

    def get_notification_count(self, user_id, is_read=None, is_deleted=False, Session=None):
        """
        特定のユーザーの通知件数を取得

        :param user_id: 通知の対象ユーザーID
        :param is_read: 既読/未読を指定（Noneの場合はすべての通知を対象）
        :param is_deleted: 削除済みを含むかどうか（デフォルトはFalse）
        :return: 通知件数（int）
        """
        try:
            Session = self.make_session(Session)
            # ベースクエリ
            query = Session.query(NotificationStatus).join(Notification).filter(
                NotificationStatus.user_id == user_id,
                NotificationStatus.is_deleted == is_deleted
            )

            # 未読/既読のフィルタリング
            if is_read is not None:
                query = query.filter(NotificationStatus.is_read == is_read)

            count = query.count()  # 件数を取得
            app.logger.info(f"Notification count for user {user_id}: {count}")
            self.pop_and_close(Session)
            return count

        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"Error retrieving notification count: {e}")
            self.error_log_manager.add_error(None, str(e))
            raise
        
    def get_notifications_for_user(self, user_id,Session=None):
        """
        指定したユーザーの通知情報を降順で取得するメソッド
        :param user_id: ユーザーID
        :return: 辞書型の通知情報リスト
        """
        try:
            user_id = Validator.decrypt(user_id)  # ユーザーIDを復号化
            Session = self.make_session(Session)
            # 通知情報を降順で取得
            notifications = (
                Session.query(Notification)
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
            self.pop_and_close(Session)
            return notification_dicts

        except SQLAlchemyError as e:
            # エラーハンドリング
            self.session_rollback(Session)
            app.logger.error(f"Failed to fetch notifications: {e}")
            self.error_log_manager.add_error("NotificationManager.get_notifications_for_user", str(e))
            return []


    def get_or_create_notification_type(self, type_name,Session=None):
        """
        通知タイプを取得または新規作成するメソッド

        :param type_name: 通知タイプ名（例: "LIKE", "COMMENT"）
        :return: 該当するNotificationTypeのID
        """
        try:
            Session = self.make_session(Session)
            # 通知タイプを検索
            existing_type = self.fetch_one(model=NotificationType, filters={"type_name": type_name},Session=Session)
            
            if existing_type:
                # 既存のタイプが見つかった場合、そのIDを返す
                self.pop_and_close(Session)
                return existing_type.notification_type_id
            
            # 存在しない場合は新しいタイプを作成
            new_type = self.insert(
                model=NotificationType,
                data={"type_name": type_name},
                Session=Session
            )
            self.make_commit_or_flush(Session=Session)
            return new_type["notification_type_id"]

        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"Failed to get or create notification type '{type_name}': {e}")
            self.error_log_manager.add_error(None, str(e))
            raise


    def create_full_notification(self, sender_id, recipient_ids, type_name, contents, related_item_id=None, related_item_type=None,Session=None):
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

            Session = self.make_session(Session)
            # 通知タイプを取得または作成
            notification_type_id = self.get_or_create_notification_type(type_name,Session=Session)

            # 各受信者ごとにNotificationを作成
            for recipient_id in recipient_ids:
                # Notificationの作成（受信者IDを設定）
                new_notification = Notification(
                    notification_type_id=notification_type_id,
                    contents=contents,
                    user_id=recipient_id  # 受信者ID
                )
                Session.add(new_notification)
                Session.flush()  # `notification_id`を取得

                # NotificationDetailの作成
                detail = NotificationDetail(
                    notification_id=new_notification.notification_id,
                    sender_id=sender_id,  # 送信者ID
                    recipient_id=recipient_id,
                    notification_type_id=notification_type_id,
                    related_item_id=related_item_id,
                    related_item_type=related_item_type
                )
                Session.add(detail)

                # NotificationStatusの作成
                status = NotificationStatus(
                    notification_id=new_notification.notification_id,
                    user_id=recipient_id,  # 受信者ID
                    is_read=False,
                    is_deleted=False
                )
                Session.add(status)

            # コミットされるとすべての操作が保存される
            self.make_commit_or_flush(Session)
            return True

        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"Failed to create full notification: {e}")
            self.error_log_manager.add_error(None, str(e))
            raise

    def delete_notification(self, related_item_id, related_item_type=None, type_name=None, sender_id=None, recipient_id=None, Session=None):
        """
        指定条件に基づいて通知を削除する
        """
        try:
            Session = self.make_session(Session)
            notification_type_id = self.get_or_create_notification_type(type_name, Session) if type_name else None

            # 条件を辞書型で整理
            filters = {
                "sender_id": sender_id,
                "recipient_id": recipient_id,
                "notification_type_id": notification_type_id,
                "related_item_id": related_item_id,
                "related_item_type": related_item_type,
            }

            # build_query を使用してクエリを動的に構築
            query = self.build_query(Session, NotificationDetail, filters)

            # NotificationDetail を検索
            notification_detail = query.first()

            if not notification_detail:
                app.logger.info("No matching notification found.")
                self.make_commit_or_flush(Session)
                return 0  # 該当する通知が見つからない場合

            # 該当する Notification を削除
            notification_id = notification_detail.notification_id
            deleted_count = self.delete(model=Notification, filters={"notification_id": notification_id}, Session=Session)

            self.make_commit_or_flush(Session)  # コミットして削除を確定
            app.logger.info(f"Notification with ID {notification_id} deleted.")
            return deleted_count

        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(f"Failed to delete notification: {e}")
            raise

    def delete_notifications(self, user_id, blocked_user_id,Session=None):
        """
        (user_id, blocked_user_id) または (blocked_user_id, user_id) のペアに該当する
        NotificationDetail の notification_id を持つ Notification を削除
        """
        try:
            Session = self.make_session(Session)
            #NotificationDetail から該当する notification_id を取得
            notification_ids_subquery = Session.query(NotificationDetail.notification_id).filter(
                or_(
                    and_(NotificationDetail.sender_id == user_id, NotificationDetail.recipient_id == blocked_user_id),
                    and_(NotificationDetail.sender_id == blocked_user_id, NotificationDetail.recipient_id == user_id)
                )
            ).subquery()

            #Notification テーブルから該当する通知を削除
            Session.query(Notification).filter(
                Notification.notification_id.in_(notification_ids_subquery)
            ).delete(synchronize_session=False)

            self.make_commit_or_flush(Session)

        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(e)