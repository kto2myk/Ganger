from Ganger.app.model.user.user_table import UserManager

# UserManagerのインスタンスを作成
user_manager = UserManager()

# テスト用サインアップ情報
username = "newuser"
email = "aaa@test.com"
password = "securepassword"
year, month, day = 1995, 7, 20

# サインアップ試行
print("[TEST] サインアップ処理をテスト中...")
success, user_or_error = user_manager.create_user(username, email, password, year, month, day)

# 結果を確認
if success:
    print(f"[TEST PASSED] サインアップ成功: {user_or_error}")
else:
    print(f"[TEST FAILED] サインアップ失敗: {user_or_error}")

# 再度サインアップを試み、重複エラーを確認
print("[TEST] 同一メールアドレスでのサインアップをテスト中...")
success, user_or_error = user_manager.create_user(username, email, password, year, month, day)

# 結果を確認
if not success and "このメールアドレスは既に使用されています。" in user_or_error:
    print(f"[TEST PASSED] 重複エラーメッセージ確認成功: {user_or_error}")
else:
    print(f"[TEST FAILED] 重複エラー確認失敗: {user_or_error}")
