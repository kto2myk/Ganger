# # # from sqlalchemy.orm import sessionmaker
# # # from sqlalchemy import create_engine
# # # from datetime import datetime
# # # from Ganger.app.model.model_manager.model import (
# # #     Notification, NotificationStatus, NotificationType, NotificationDetail, User
# # # )

# # # # データベース接続設定
# # # db_path = r"C:\HAL\IH\IH22\Ganger\app\model\database_manager\Ganger.db"
# # # engine = create_engine(f"sqlite:///{db_path}")
# # # Session = sessionmaker(bind=engine)
# # # session = Session()
# # # データ挿入の準備
# # # try:
# #     # # NotificationType データ挿入
# #     # notification_types = [
# #     #     NotificationType(type_name="comment"),
# #     #     NotificationType(type_name="like"),
# #     #     NotificationType(type_name="follow"),
# #     # ]
# #     # session.add_all(notification_types)
# #     # session.commit()

# #     # # User データ挿入
# #     # users = [
# #     #     User(id=1, username="Alice"),
# #     #     User(id=2, username="Bob"),
# #     #     User(id=3, username="Charlie"),
# #     #     User(id=4, username="David"),
# #     #     User(id=5, username="Eve"),
# #     # ]
# #     # session.add_all(users)
# #     # session.commit()

# #     # # Notification データ挿入
# #     # notifications = [
# #     #     Notification(notification_type_id=1, user_id=1, contents="User2があなたの投稿にコメントしました。"),
# #     #     Notification(notification_type_id=2, user_id=2, contents="User3があなたの投稿にいいねしました。"),
# #     #     Notification(notification_type_id=3, user_id=3, contents="User4があなたをフォローしました。"),
# #     # ]
# #     # session.add_all(notifications)
# #     # session.commit()

# #     # NotificationDetail データ挿入
# #     # notification_details = [
# #     #     NotificationDetail(
# #     #         notification_id=1,
# #     #         sender_id=2,
# #     #         recipient_id=1,
# #     #         notification_type_id=1,
# #     #         related_item_id=3,  # 例: PostID
# #     #         related_item_type="post"
# #     #     ),
# #     #     NotificationDetail(
# #     #         notification_id=2,
# #     #         sender_id=3,
# #     #         recipient_id=2,
# #     #         notification_type_id=2,
# #     #         related_item_id=5,  # 例: PostID
# #     #         related_item_type="post"
# #     #     ),
# #     #     NotificationDetail(
# #     #         notification_id=3,
# #     #         sender_id=4,
# #     #         recipient_id=3,
# #     #         notification_type_id=3,
# #     #         related_item_id=6,
# #     #         related_item_type="post"
# #     #     ),
# #     # ]
# #     # session.add_all(notification_details)
# #     # session.commit()

# #     # # NotificationStatus データ挿入
# #     # statuses = [
# #     #     NotificationStatus(notification_id=1, user_id=1),  # デフォルト値
# #     #     NotificationStatus(notification_id=2, user_id=2, is_read=True),  # 既読
# #     #     NotificationStatus(notification_id=3, user_id=3, is_deleted=True),  # 削除済み
# #     # ]
# #     # session.add_all(statuses)
# #     # session.commit()
# # #     print("テストデータの挿入が完了しました！")

# # # except Exception as e:
# # #     print(f"エラーが発生しました: {e}")
# # #     session.rollback()
# # # finally:
# # #     session.close()

# # # with session as session:
# # #     # 削除
# # #     session.query(NotificationDetail).filter(NotificationDetail.detail_id == 3).delete()
# # #     session.commit()
# # #     print("削除完了")

# # from Ganger.app.model.notification.notification_manager import NotificationManager
# # notification_manager = NotificationManager()

# # # ユーザーIDに基づいて通知を降順で取得
# # user_notifications = notification_manager.get_notifications_for_user(user_id=1)

# # # 結果を確認
# # for notification in user_notifications:
# #     print(notification)

from Ganger.app.model.notification.notification_manager import NotificationManager
notification_manager = NotificationManager()
# try:
#     # 通知を送信
#     notification = notification_manager.create_full_notification(
#         sender_id=1,
#         recipient_ids=2,
#         type_name="comment",
#         contents="User2があなたの投稿にコメントしました。",
#         related_item_id=3,
#         related_item_type="post"
#     )
#     print("通知を送信しました！")
#     print(notification)
# except Exception as e:
#     print(f"エラーが発生しました: {e}")

# try:
#     # 通知を削除
#     deleted_count = notification_manager.delete_notification(
#         sender_id=1,
#         recipient_id=2,
#         type_name="comment",
#         related_item_id=3,
#         related_item_type="post"
#     )
#     print(f"{deleted_count} 件の通知を削除しました！")
# except Exception as e:
#     print(f"エラーが発生しました: {e}")