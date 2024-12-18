from flask import Flask, request, session, render_template, redirect, url_for,flash,jsonify
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import os


app = Flask(__name__,
    template_folder=os.path.abspath("Ganger/app/templates"),
    static_folder=os.path.abspath("Ganger/app/static"),
)

# 実行ディレクトリを基準に保存先を設定  app.pyディレクトリの一階層上 app/までを取得
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))  
# 画像保存先の設定
POST_IMAGE_FOLDER = os.path.join(BASE_DIR, "static", "images", "post_images")
TEMP_IMAGE_FOLDER = os.path.join(BASE_DIR, "static", "images", "temp_images")
PROFILE_IMAGE_FOLDER = os.path.join(BASE_DIR, "static", "images", "profile_images")

# Flask の基本設定
app.secret_key = "your_secret_key"  # セッション用の秘密鍵（安全な値に変更してください）
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=300) 
app.config["DEBUG"] = True
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['POST_FOLDER'] = POST_IMAGE_FOLDER
app.config['TEMP_FOLDER'] = TEMP_IMAGE_FOLDER
app.config['PROFILE_FOLDER'] = PROFILE_IMAGE_FOLDER
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
            session["profile_image"] =url_for("static", 
            filename=f"images/profile_images/{user.profile_image}")
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
                session["profile_image"] = url_for("static", filename=f"images/profile_images/{result['profile_image']}")
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
    if "id" not in session:
        return redirect(url_for("login"))
    from Ganger.app.model.database_manager.database_manager import DatabaseManager
    from Ganger.app.model.model_manager.model import Post
    from Ganger.app.model.validator.validate import Validator
    db_manager = DatabaseManager()

    try:
        filters = {"post_id": "8"}  # テスト用フィルタ
        posts = db_manager.fetch(
            model=Post,
            relationships=["images", "author"],
            filters=filters
        )

        # テンプレートに渡すデータ構造を生成
        formatted_posts = []
        for post in posts:
            formatted_posts.append({
                "post_id": post.post_id,
                "user_id": post.author.user_id,
                "username": post.author.username,
                "profile_image": url_for("static", filename = f"images/profile_images/{post.author.profile_image}"),
                "body_text": post.body_text,
                "post_time": Validator.calculate_time_difference(post.post_time),  # 差分を計算
                "images": [
                {"img_path": url_for("static", filename=f"images/post_images/{image.img_path}")}
                for image in post.images
                ]
            })
            
        return render_template("temp_layout.html", posts=formatted_posts)
    except Exception as e:
        print(f"Error: {e}")
        flash("投稿データの取得に失敗しました。")
        return redirect(url_for("login"))
    

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

@app.route('/my_profile',methods = ['POST','GET'])
def my_profile():
    if request.method == "POST":
        redirect(url_for('my_profile'))
    return render_template("my_profile.html")

@app.route('/create_post', methods=['POST'])
def create_post():
    """
    新しい投稿を作成するエンドポイント
    """
    if 'user_id' not in session:
        flash("ログインしてください。", "error")
        return redirect(url_for('login'))

    # セッションからユーザーIDを取得
    user_id = session['user_id']
    title = request.form.get('title')
    description = request.form.get('description', "")  # 任意のフィールド

    if not title:
        flash("タイトルは必須です。", "error")
        return redirect(url_for('post_page'))

    # 投稿データ
    post_data = {
        "user_id": user_id,
        "title": title,
        "description": description
    }

    # 画像ファイルの処理
    if 'images' not in request.files:
        flash("画像ファイルを選択してください。", "error")
        return redirect(url_for('post_page'))

    image_files = request.files.getlist('images')

    if len(image_files) > 6:
        flash("画像は最大6枚までアップロード可能です。", "error")
        return redirect(url_for('post_page'))

    # PostManagerを使用して投稿作成
    from Ganger.app.model.post.post_manager import PostManager
    post_manager = PostManager()
    result = post_manager.create_post(post_data, image_files)

    if "error" in result:
        flash(result["error"], "error")
        return redirect(url_for('post_page'))

    flash("投稿が作成されました！", "success")
    return redirect(url_for('home'))

@app.route('/post_page')
def post_page():
    """
    投稿作成ページの表示
    """
    return "<h1>投稿ページにリダイレクトされました！</h1>"

@app.route('/create_design')
def create_design():
    return render_template("create_design.html")

@app.route("/display", methods=["POST","GET"])
def display():
    if request.method == "POST":
        image_data = request.form.get("image")  # Base64形式の画像データ
        if not image_data:
            return "画像データが見つかりません。", 400
        return render_template("image_display.html", image_data=image_data)
    return redirect(url_for('home'))

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=80, debug=True)
    except KeyboardInterrupt:
        print("\n[INFO] Server 停止")