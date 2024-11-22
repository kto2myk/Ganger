from flask import Flask, request, session, render_template,redirect, url_for
import os
app = Flask(__name__, template_folder=os.path.join(os.getcwd(), "app/templates"))

app.config["DEBUG"] = True
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = "your_secret_key"  # セッション用の秘密鍵（安全な値に変更してください）


# ログインページの処理
@app.route("/login", methods=["GET", "POST"])
def login():
    from Ganger.app.model.user.model import User
    
    if request.method == "GET":
        # GETリクエスト：ログインフォームを表示
        return render_template("login.html", error=None)

    elif request.method == "POST":
        # POSTリクエスト：フォームからデータを取得
        username = request.form.get("identifier")
        password = request.form.get("password")

        # ユーザー認証
        if username in User and User[username] == password:
            # 認証成功
            session["user_id"] = User[id]  # セッションに保存
            return redirect(url_for("home"))  # HOMEにリダイレクト
        else:
            # 認証失敗
            error_message = "ログインに失敗しました。ユーザー名またはパスワードが間違っています。"
            return render_template("login.html", error=error_message)  # 再度ログインページを表示


# ホームページの処理
@app.route("/home")
def home():
    if "username" not in session:
        # 未ログインの場合、ログインページへリダイレクト
        return redirect(url_for("login"))

    # ログイン済みの場合、ホームページを表示
    return f"ようこそ、{session['username']}さん！"


if __name__ == "__main__":
    app.run("0.0.0.0", 80, True)
