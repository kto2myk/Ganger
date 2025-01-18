from Ganger.app.model.user.user_table import UserManager
from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.model_manager.model import User
from Ganger.app.view.app import app
# UserManagerのインスタンスを作成
user_manager = UserManager()
db_manager = DatabaseManager()
# テスト用サインアップ情報
username = "ppp"
email = "p@p.p"
password = "ppp"

# サインアップ試行
print("[TEST] サインアップ処理をテスト中...")
with app.test_request_context():
    try:
        success, user_or_error = user_manager.create_user(username, email, password)
        user = db_manager.fetch_one(User,filters={"username":"ppp"})
    except Exception as e:
        app.logger.error(e)
# 結果を確認
if success:
    print(f"[TEST PASSED] サインアップ成功: {user_or_error}")
    print(user)
else:
    print(f"[TEST FAILED] サインアップ失敗: {user_or_error}")

# # 再度サインアップを試み、重複エラーを確認
# print("[TEST] 同一メールアドレスでのサインアップをテスト中...")
# success, user_or_error = user_manager.create_user(username, email, password, year, month, day)

# # 結果を確認
# if not success and "このメールアドレスは既に使用されています。" in user_or_error:
#     print(f"[TEST PASSED] 重複エラーメッセージ確認成功: {user_or_error}")
# else:
#     print(f"[TEST FAILED] 重複エラー確認失敗: {user_or_error}")
