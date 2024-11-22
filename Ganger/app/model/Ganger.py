from flask import Flask, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "your_secret_key"  # セッション用の秘密鍵（安全な値に変更してください）


@app.route("/login", methods=["GET", "POST"])
def login_route():
    from Ganger.app.model.user.user_table import UserManager
    user_manager = UserManager()

    if request.method == "POST":
        # フォームからデータを取得
        identifier = request.form.get("identifier")  # メールアドレスまたはユーザーID
        password = request.form.get("password")  # パスワード

        # UserManager の login メソッドを呼び出し
        user = user_manager.login(identifier, password)

        if user:
            # セッションにユーザー情報を保存
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect(url_for("dashboard"))  # ダッシュボードにリダイレクト
        else:
            return "ログイン失敗", 401  # エラーメッセージを表示

    # GETリクエストの場合はログインフォームを表示
    return """
    <form method="POST">
        <label>メールアドレスまたはユーザーID: <input type="text" name="identifier"></label><br>
        <label>パスワード: <input type="password" name="password"></label><br>
        <button type="submit">ログイン</button>
    </form>
    """

@app.route("/dashboard")
def dashboard():
    # ログインしているかを確認
    if "user_id" not in session:
        return redirect(url_for("login_route"))

    return f"ようこそ、{session['username']} さん！"
