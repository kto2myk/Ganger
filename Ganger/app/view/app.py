from flask import Flask, request, session, render_template, redirect, url_for,flash
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import os


app = Flask(__name__,
    template_folder=os.path.abspath("Ganger/app/templates"),
    static_folder=os.path.abspath("Ganger/app/static"),
)

# Flask の基本設定
app.secret_key = "your_secret_key"  # セッション用の秘密鍵（安全な値に変更してください）
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=5) 
app.config["DEBUG"] = True
app.config["TEMPLATES_AUTO_RELOAD"] = True
# @app.before_request
# def make_session_permanent(): #sessionの一括永続化
#     session.permanent = True


@app.route("/", methods=["GET", "POST"])
def login():
    from Ganger.app.model.user.user_table import UserManager
    user_manager = UserManager()

    if request.method == "GET":
        if "id" in session:
            return redirect(url_for("home"))
        return render_template("login.html")

    elif request.method == "POST":
        identifier = request.form.get("identifier")
        password = request.form.get("password")

        user,error= user_manager.login(identifier=identifier, password=password)
        if user:
            session["id"] = user.id
            session["user_id"] = user.user_id
            session["username"] = user.username
            session["profile_image"] = url_for("static",
                filename=f"profile_images/{user.profile_image}")
            return redirect(url_for("home"))
        else:
            flash(error) 
            return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    from Ganger.app.model.user.user_table import UserManager
    user_manager = UserManager()

    if request.method == "GET":
        if "id" in session:
            return redirect(url_for("home"))
        return render_template("signup.html")

    elif request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        success, result = user_manager.create_user( #successにbool resultに結果
            username=username,
            email=email, 
            password=password
            )
        
        if success:
            try:
                session["id"] = result["id"]
                session["user_id"] = result["user_id"]
                session["username"] = result["username"]
                session["profile_image"] = url_for("static", filename=f"profile_images/{result['profile_image']}")
                return redirect(url_for("home"))
            
            except Exception as e:
                print(f"[ERROR] Failed to save session data: {e}")
                flash("内部エラーが発生しました。")
                return redirect(url_for("signup"))
        else: 
            flash(result)
            return redirect(url_for("signup"))

@app.route("/home", methods=["GET", "POST"])
def home():
    if not "id" in session:
        return redirect(url_for("login"))
    return render_template("temp_layout.html")

@app.route('/password-reset', methods=['GET', 'POST'])
def password_reset():
    if request.method == 'POST':
        from Ganger.app.model.database_manager.database_manager import DatabaseManager
        from Ganger.app.model.model_manager.model import User
        email = request.form['email']
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        
        # パスワード一致確認
        if password != password_confirm:
            flash('パスワードが一致しません。再度入力してください。')
            return render_template('password_reset.html')
        
        # ユーザーの検索とパスワード更新
        database_manager = DatabaseManager()
        user = database_manager.fetch_one(User, filters={"email": email})
        if not user:
            flash('該当するメールアドレスが見つかりません。')
            return redirect(url_for('password_reset'))     
        # パスワードの更新
        hashed_password = generate_password_hash(password)
        success = database_manager.update(User, {"email": email}, {"password": hashed_password})
        if success:
            flash('パスワードをリセットしました。ログインしてください。', 'success')
            return redirect(url_for('login'))
        else:
            flash('パスワードリセット中にエラーが発生しました。')
            return redirect(url_for('password_reset'))    
        
    return render_template('password_reset.html')


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=80, debug=True)
    except KeyboardInterrupt:
        print("\n[INFO] Server 停止")