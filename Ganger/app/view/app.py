from flask import Flask, request, session, render_template, redirect, url_for
from datetime import timedelta
import os

app = Flask(__name__,
    template_folder=os.path.abspath("Ganger/app/templates"),
    static_folder=os.path.abspath("Ganger/app/static"),
)

# Flask の基本設定
app.secret_key = "your_secret_key"  # セッション用の秘密鍵（安全な値に変更してください）
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=5)  # 有効期限を30分に設定
app.config["DEBUG"] = True
app.config["TEMPLATES_AUTO_RELOAD"] = True


# ログインページの処理
@app.route("/", methods=["GET", "POST"])
def login():
    from Ganger.app.model.user.user_table import UserManager


    if request.method == "GET":
        if "id" in session:
        # 既にログインしている場合はホームページへリダイレクト
            return redirect(url_for("home"))
        # GETリクエスト：ログインフォームを表示
        return render_template("login.html", error=None)

    elif request.method == "POST":
        # POSTリクエスト：フォームからデータを取得
        identifier = request.form.get("identifier")
        password = request.form.get("password")

        # ユーザー認証
        user_manager = UserManager()
        user = user_manager.login(identifier=identifier, password=password)
        if user:
            session["id"] = user.id
            session["user_id"] = user.user_id  # user_idをセッションに保存
            session["username"] = user.username  # usernameをセッションに保存
            session["profile_image"] = url_for("static",
            filename= f"profile_images/{user.profile_image}")            
            return redirect(url_for("home"))  # HOMEにリダイレクト
        else:
            # 認証失敗
            error_message = "ログインに失敗しました。ユーザー名またはパスワードが間違っています。"
            return render_template("login.html", error=error_message)  # 再度ログインページを表示


# サインアップ処理（新規会員登録）
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html", error=None)

    elif request.method == "POST":
        from Ganger.app.model.user.user_table import UserManager

        user_manager = UserManager()

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        year = int(request.form.get("year"))
        month = int(request.form.get("month"))
        day = int(request.form.get("day"))

        success, result = user_manager.create_user(
            username=username, email=email, password=password, year=year, month=month, day=day
        )
        if success:
            session["id"] = result["id"]
            session["user_id"] = result["user_id"]  # セッションに保存
            session["username"] = result["username"]  # セッションに保存
            session["profile_image"] = url_for("static",
            filename= f"profile_images/{result['profile_image']}")
            
            return redirect(url_for("home"))  # HOMEにリダイレクト
        else:
            return render_template("signup.html", error=result)


# ホームページの処理
@app.route("/home", methods = ["GET","POST"])
def home():
    if request.method == "GET":
        if "id" not in session:
        # 未ログインの場合、ログインページへリダイレクト
            return redirect(url_for("login"))    
        # ログイン済みの場合、ホームページを表示
        return render_template("temp_layout.html")

if __name__ == "__main__":
    app.run("0.0.0.0", 80, True)

print(f"Template folder: {os.path.abspath(app.template_folder)}")
