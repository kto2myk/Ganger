from Ganger.app.model.user.user_table import UserManager

# UserManagerのインスタンスを作成
user_manager = UserManager()

# テスト用ログイン情報
identifier = "newuser_79d4fd7c"
password = "securepassword"

# ログイン試行
print("[TEST] ログイン処理をテスト中...")
user = user_manager.login(identifier, password)

# 結果を確認
if user:
    print(f"[TEST PASSED] ログイン成功: {user}")
else:
    print(f"[TEST FAILED] ログイン失敗: Identifier={identifier}, Password={password}")
