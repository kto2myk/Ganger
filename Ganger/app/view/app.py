from flask import Flask, request, session, render_template, redirect, url_for,flash,jsonify,abort # Flaskの各種機能をインポート
from flask_wtf.csrf import CSRFProtect  # CSRF保護用
from datetime import timedelta  # セッションの有効期限設定用
from werkzeug.security import generate_password_hash, check_password_hash   # パスワードハッシュ化用
import os  # ファイルパス操作用
from Ganger.app.model.validator.validate import Validator  # バリデーション用
from Ganger.app.model.database_manager.database_manager import DatabaseManager # データベースマネージャー

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
# csrf = CSRFProtect(app) # CSRF保護を有効化 
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=300) 
app.config["DEBUG"] = True
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['POST_FOLDER'] = POST_IMAGE_FOLDER
app.config['TEMP_FOLDER'] = TEMP_IMAGE_FOLDER
app.config['PROFILE_FOLDER'] = PROFILE_IMAGE_FOLDER



# @app.before_request
# def check_session():
#     if id in session:
#         return redirect(url_for("home"))
#     elif request.endpoint not in ["login", "signup", "password_reset"]:
#             return redirect(url_for("login"))
#     return None
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

        # ユーザーログイン処理
        user, error = user_manager.login(identifier=identifier, password=password)
        if user:
            return redirect(url_for("home"))
        else:
            flash(error)
            app.logger.error(f"Login failed for identifier: {identifier} - {error}")
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

        # ユーザー作成処理
        success, error = user_manager.create_user(
            username=username,
            email=email,
            password=password
        )

        if success:
            # 成功時、セッション登録はcreate_user内で完了
            return redirect(url_for("home"))
        else:
            # エラーメッセージをフラッシュ
            flash(error)
            app.logger.error(f"Signup failed: {error}")
            return redirect(url_for("signup"))
        
@app.route("/home")
def home():
    from Ganger.app.model.post.post_manager import PostManager
    from Ganger.app.model.notification.notification_manager import NotificationManager
    post_manager = PostManager()
    notification_manager = NotificationManager()
    try:
        # フィルターを設定して投稿データを取得
        filters = {"user_id": 3}  # テスト用フィルタ
        user_id = Validator.decrypt(session.get("id"))
        formatted_posts = post_manager.get_filtered_posts_with_reposts(filters=filters,current_user_id=user_id)
        # 未読通知の数を取得
        count_notifications = notification_manager.get_notification_count(Validator.decrypt(session.get("id")),is_read=False)
        return render_template("temp_layout.html", posts=formatted_posts,notification_count = count_notifications)
    except Exception as e:
        abort(404,description="投稿データの取得に失敗しました。")
        app.logger.error(f"Failed to fetch posts: {e}")
        return redirect(url_for("login"))
    

@app.route('/password-reset', methods=['GET', 'POST'])
def password_reset():
    if request.method == 'POST':
        
        from Ganger.app.model.model_manager.model import User
        email = request.form['email']
        password = request.form['password']
        password_confirm = request.form['password_confirm']
        
        # パスワード一致確認
        if password != password_confirm:
            error = 'パスワードが一致しません。再度入力してください。'
            flash(error)
            app.logger.error(f"Password reset failed: {error}")
            return render_template('password_reset.html')
        
        # ユーザーの検索とパスワード更新
        database_manager = DatabaseManager()
        user = database_manager.fetch_one(User, filters={"email": email})
        if not user:
            error = '該当するメールアドレスが見つかりません。'
            flash(error)
            app.logger.error(f"Password reset failed: {error}")
            return redirect(url_for('password_reset'))     
        
        # パスワードの更新
        hashed_password = generate_password_hash(password)
        success = database_manager.update(User, {"email": email}, {"password": hashed_password})
        if success:
            flash('パスワードをリセットしました。ログインしてください。', 'success')
            return redirect(url_for('login'))
        else:
            error = 'パスワードリセット中にエラーが発生しました。'
            flash(error)
            app.logger.error(f"Password reset failed: {error}")
            return redirect(url_for('password_reset'))    
        
    return render_template('password_reset.html')

@app.route('/like/<string:post_id>', methods=['POST'])
def toggle_like(post_id,):
    from Ganger.app.model.post.post_manager import PostManager
    try:
        sender_id = Validator.decrypt(session.get("id"))
        post_id = Validator.decrypt(post_id)

        if not sender_id or not post_id:
            app.logger.error("Missing required IDs for authentication.")
            return jsonify({'error': 'Unauthorized'}), 401

        post_manager = PostManager()
        result = post_manager.toggle_like(post_id=post_id, sender_id=sender_id)

        return jsonify(result), 200

    except Exception as e:
        app.logger.error(f"Error toggling like: {e}")
        return jsonify({'error': 'Server error'}), 500

@app.route("/my_profile/<id>", methods=["GET"])
def my_profile(id):
    from Ganger.app.model.user.user_table import UserManager
    user_manager = UserManager()

    try:
        # プロフィール情報を取得
        profile_data = user_manager.get_user_profile_with_posts(id)

        # テンプレートにデータを渡す
        return render_template("my_profile.html", profile=profile_data)
    except ValueError as e:
        return (str(e))
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        return ("ユーザーデータの取得に失敗しました。")

@app.route('/create_post', methods=['POST'])
def create_post():
    """
    新しい投稿を作成するエンドポイント
    """
    # セッションからユーザーIDを取得
    user_id = session['id']
    title = request.form.get('title')
    description = request.form.get('description', "")  # 任意のフィールド

    if not title:
        error = "タイトルは必須です。"
        flash(error, "error")
        app.logger.error(f"Post creation failed: {error}")
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
        error = "画像は最大6枚までアップロード可能です。"
        flash(error,"error")
        app.logger.error(f"Post creation failed: {error}")
        return redirect(url_for('post_page'))

    # PostManagerを使用して投稿作成
    from Ganger.app.model.post.post_manager import PostManager
    post_manager = PostManager()
    result = post_manager.create_post(post_data, image_files)

    if "error" in result:
        error = result["error"]
        flash(error, "error")
        app.logger.error(f"Post creation failed: {error}")
        return redirect(url_for('post_page'))

    flash("投稿が作成されました！", "success")
    return redirect(url_for('home'))

@app.route('/create_design')
def create_design():
    return render_template("create_design.html")

@app.route('/submit_comment/<string:post_id>', methods=['POST'])
def submit_comment(post_id):
    from Ganger.app.model.post.post_manager import PostManager
    post_manager = PostManager()

    try:
        sender_id = Validator.decrypt(session.get("id"))
        post_id = Validator.decrypt(post_id)
        comment = request.form.get("comment")

        if not sender_id or not post_id or not comment:
            app.logger.error("Missing required IDs for authentication.")
            return render_template("error.html", message="Unauthorized")

        result = post_manager.add_comment(user_id=sender_id, parent_post_id=post_id, comment_text=comment)
        if result:
            app.logger.info("Comment submitted successfully")
            return redirect(url_for("display_post", post_id=Validator.encrypt(post_id)))
        else:
            app.logger.error("Failed to submit comment")
            return render_template("error.html", message="Failed to submit comment")
        
    except Exception as e:
        app.logger.error(f"Error submitting comment: {e}")
        return render_template("error.html", message="Server error")
    
@app.route('/save_design', methods=['POST'])
def save_design():
    image_data = request.form.get("image")  # Base64形式の画像データ
    if not image_data:
        return "画像データが見つかりません。", 400

    try:
        import uuid
        import base64
        # 一意なファイル名を生成
        unique_name = f"{uuid.uuid4()}.png"  # 一意なファイル名
        image_path = os.path.join(app.config['TEMP_FOLDER'], unique_name)

        # Base64データをデコードして保存
        image_data = image_data.split(",")[1]  # "data:image/png;base64,"を取り除く
        with open(image_path, "wb") as f:
            f.write(base64.b64decode(image_data))

        # セッションに画像名を保存
        session['image_name'] = unique_name
        return redirect(url_for('display'))
    except Exception as e:
        app.logger.error(f"Error: {e}")
        return f"エラーが発生しました: {str(e)}", 500

@app.route('/display', methods=['GET'])
def display():
    # セッションから画像名を取得
    image_name = session.get('image_name')
    if not image_name:
        error = "画像が見つかりません。"
        app.logger.error(f"Image not found: {error}")
        return error, 404

    # URLを生成してHTMLに渡す
    image_url = url_for('static', filename=f"images/temp_images/{image_name}")
    return render_template("image_display.html", image_url=image_url)

@app.route('/delete_temp')
def delete_temp():
    # セッションから画像名を取得
    image_name = session.get('image_name')
    if not image_name:
        return "削除する画像が見つかりません。", 404

    try:
        # 画像のパスを構築
        image_path = os.path.join(app.config['TEMP_FOLDER'], image_name)

        # ファイルの存在確認
        if os.path.exists(image_path):
            os.remove(image_path)  # ファイルを削除
            session.pop('image_name', None)  # セッションから削除
            return redirect('home')
        else:
            return "画像ファイルが存在しません。", 404
    except Exception as e:
        return f"エラーが発生しました: {str(e)}", 500
    
@app.route('/search', methods=['GET'])
def search():
    try:
        # クエリパラメータから値を取得
        query = request.args.get('query', '').strip().lower()
        tab = request.args.get('tab', 'USER').upper()  # デフォルトは "USER"

        # 結果の初期化
        results = {"users": [], "tags": [], "categories": []}

        if query:
            from Ganger.app.model.post.post_manager import PostManager
            from Ganger.app.model.user.user_table import UserManager

            post_manager = PostManager()
            user_manager = UserManager()

            # タブに基づいた処理
            if tab == "USER":
                results['users'] = user_manager.search_users(query)
            elif tab == "TAG":
                results['tags'] = post_manager.search_tags(query)
            elif tab == "CATEGORY":
                results['categories'] = post_manager.search_categories(query)

        # ログ出力
        app.logger.info(f"Search completed: query={query}, tab={tab}, results={results}")

        # クライアントのリクエスト形式に応じたレスポンス
        if request.headers.get('Accept') == 'application/json':
            return jsonify(results), 200
        else:
            return render_template('search_page.html', query=query, tab=tab, results=results)

    except Exception as e:
        app.logger.error(f"Error occurred: {e}", exc_info=True)
        if request.headers.get('Accept') == 'application/json':
            return jsonify({"error": "An error occurred"}), 500
        else:
            return f"An error occurred: {str(e)}", 500
        
@app.route('/display_post/<post_id>', methods=['GET'])
def display_post(post_id):
    from Ganger.app.model.post.post_manager import PostManager
    post_manager = PostManager()

    try:
        # デバッグ用ログ
        app.logger.info(f"Fetching post with post_id: {post_id}")

        # 投稿データを取得
        post_details = post_manager.get_post_details(post_id)
        app.logger.info(f"Post details: {post_details}")
        # テンプレートにデータを渡す
        return render_template("display_post.html", post=post_details)
    except ValueError as e:
        app.logger.error(f"ValueError: {e}")
        return "指定された投稿が見つかりませんでした。", 404
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        return "投稿データの取得中にエラーが発生しました。", 500

@app.route("/notifications", methods=["GET"])
def notifications():
    """
    通知一覧を表示するエンドポイント
    """
    from Ganger.app.model.notification.notification_manager import NotificationManager
    # セッションからユーザーIDを取得

    # NotificationManager を使って通知データを取得
    notification_manager = NotificationManager()
    try:
        notifications = notification_manager.get_notifications_for_user(session["id"])
        app.logger.info(f"Notifications: {notifications}")
    except Exception as e:
        app.logger.error(f"Failed to fetch notifications: {e}")
        flash("通知の取得中にエラーが発生しました。")
        return redirect(url_for("home"))

    # HTML テンプレートに通知データを渡す
    return render_template("display_notification.html", notifications=notifications)

@app.route("/repost/<post_id>", methods=["POST"])
def repost(post_id):
    from Ganger.app.model.post.post_manager import PostManager
    post_manager = PostManager()

    try:
        sender_id = Validator.decrypt(session.get("id"))
        post_id = Validator.decrypt(post_id)

        if not sender_id or not post_id:
            app.logger.error("Missing required IDs for authentication.")
            return jsonify({'error': 'Unauthorized'}), 401

        result = post_manager.create_repost(post_id=post_id, user_id=sender_id)
        # 成功時の応答
        if result:
            return jsonify({'success': True, 'message': 'リポストが完了しました！'}), 200
        else:
            return jsonify({'success': False, 'message': 'リポストに失敗しました。'}), 400
        
    except Exception as e:
        app.logger.error(f"Error reposting: {e}")
        return jsonify({'error': 'Server error'}), 500
    
@app.route("/save_post/<post_id>", methods=["POST"])
def save_post(post_id):
    from Ganger.app.model.post.post_manager import PostManager
    post_manager = PostManager()

    try:
        post_id = Validator.decrypt(post_id)
        sender_id = Validator.decrypt(session.get("id"))

        # 必須IDの確認
        if not sender_id or not post_id:
            app.logger.error("Missing required IDs for authentication.")
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        # 保存状態のトグル
        result = post_manager.toggle_saved_post(post_id=post_id, user_id=sender_id)

        if result.get("status") == "added":
            return jsonify({'success': True, 'message': 'SAVE_POSTが完了しました！', 'status': 'added'}), 200
        elif result.get("status") == "removed":
            return jsonify({'success': True, 'message': 'SAVE_POSTが解除されました！', 'status': 'removed'}), 200
        else:
            app.logger.error(f"Unexpected result from toggle_saved_post: {result}")
            return jsonify({'success': False, 'message': 'SAVE_POSTに失敗しました。'}), 400

    except ValueError as e:
        app.logger.error(f"Decryption error: {e}")
        return jsonify({'success': False, 'message': 'Invalid data provided.'}), 400
    except Exception as e:
        app.logger.error(f"An error occurred in save_post: {e}")
        return jsonify({'success': False, 'message': 'An internal error occurred.'}), 500
    
@app.route("/make_post_into_product/<post_id>", methods=["POST"])
def make_post_into_product(post_id):
    from Ganger.app.model.shop.shop_manager import ShopManager
    try:
        # フォームデータの取得
        post_id = Validator.decrypt(post_id)
        selected_category = request.form.get('category')
        price = request.form.get('price')
        product_name = request.form.get('name')

        # バリデーション
        if not selected_category:
            return jsonify({"status": False, "message": "カテゴリを選択してください。"}), 400
        if not price or not price.isdigit() or int(price) <= 0:
            return jsonify({"status": False, "message": "価格を正しく入力してください（正の整数）。"}), 400
        if not product_name or len(product_name) < 3:
            return jsonify({"status": False, "message": "商品名は3文字以上で入力してください。"}), 400

        # 商品化処理
        shop_manager = ShopManager()
        result = shop_manager.create_product(
            post_id=post_id,
            price=int(price),
            name=product_name,
            category_name=selected_category
        )

        # 結果に基づいてレスポンスを生成
        if result["status"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        app.logger.error(f"Error in make_post_into_product: {e}")
        return jsonify({"status": False, "message": "内部エラーが発生しました。"}), 500


@app.route("/shop_page")
def shop_page():
    from Ganger.app.model.shop.shop_manager import ShopManager
    shop_manager = ShopManager()
    shop_data = shop_manager.get_shop_with_images(limit=10)

    if shop_data is None:
        abort(404, description="ショップページが見つかりません")

    return render_template("shop_page.html", products=shop_data)      

@app.route("/display_product/<product_id>")
def display_product(product_id):
    from Ganger.app.model.shop.shop_manager import ShopManager
    shop_manager = ShopManager()
    product = shop_manager.fetch_one_product_images(product_id=product_id)

    if product_id is None:
        abort(404,description="商品が見つかりません")
    
    return render_template("display_product.html",product=product)
            

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=80, debug=True)
    except KeyboardInterrupt:
        print("\n[INFO] Server 停止")