from flask import Flask, request, session, render_template, redirect, url_for,flash,jsonify,abort # Flaskの各種機能をインポート
from flask_session import Session
from flask_wtf.csrf import CSRFProtect  # CSRF保護用
from flask_redis import FlaskRedis
from datetime import timedelta  # セッションの有効期限設定用
from werkzeug.security import generate_password_hash, check_password_hash   # パスワードハッシュ化用
import os  # ファイルパス操作用
import subprocess
import requests
from Ganger.app.model.model_manager.model import User
from Ganger.app.model.validator.validate import Validator  # バリデーション用
from Ganger.app.model.database_manager.database_manager import DatabaseManager # データベースマネージャー
from Ganger.app.model.user.user_table import UserManager
from Ganger.app.model.post.post_manager import PostManager
from Ganger.app.model.shop.shop_manager import ShopManager
from Ganger.app.model.notification.notification_manager import NotificationManager
from Ganger.app.model.dm.message_manager import MessageManager

app = Flask(__name__,
    template_folder=os.path.abspath("Ganger/app/templates"),
    static_folder=os.path.abspath("Ganger/app/static"),
)
#docker start redis-server

# 🔹 Flaskの基本設定
app.secret_key = "your_secret_key"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=300)
app.config["DEBUG"] = True
app.config["TEMPLATES_AUTO_RELOAD"] = True

# 🔹 画像保存先の設定
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
POST_IMAGE_FOLDER = os.path.join("Ganger","app", "static", "images", "post_images")
TEMP_IMAGE_FOLDER = os.path.join(BASE_DIR, "static", "images", "temp_images")
PROFILE_IMAGE_FOLDER = os.path.join("Ganger","app", "static", "images", "profile_images")

app.config["POST_FOLDER"] = POST_IMAGE_FOLDER
app.config["TEMP_FOLDER"] = TEMP_IMAGE_FOLDER
app.config["PROFILE_FOLDER"] = PROFILE_IMAGE_FOLDER

# 🔹 Redisの設定（キャッシュ用）
app.config["REDIS_URL"] = "redis://localhost:6379/0"

# 🔹 Flask-Redisの設定
redis_client = FlaskRedis()  # `StrictRedis` ではなく `FlaskRedis` を使用
redis_client.init_app(app)
app.redis_client = redis_client
# 🔹 Flask-Sessionの設定（Redisを使用）
app.config["SESSION_TYPE"] = "redis"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_KEY_PREFIX"] = "session:"
app.config["SESSION_REFRESH_EACH_REQUEST"] = True
app.config["SESSION_REDIS"] = redis_client._redis_client
# 🔹 キャッシュの有効期限設定（12時間）
app.config["CACHE_DEFAULT_TIMEOUT"] = 3600 * 12
# Flask-Sessionを適用（Flask-Redisの初期化後に適用）
Session(app)

@app.before_request
def check_session():
    if request.endpoint and request.endpoint.startswith("static"):
        return  # `static` ディレクトリのリクエストはスルー

    if request.endpoint and request.endpoint not in ["login", "signup", "password_reset"]:
        if not session.get("id"):  # セッションがなければログインページへ
            return redirect(url_for("login"))
def make_session_permanent(): #sessionの一括永続化
    session.permanent = True

with app.app_context():
    db_manager = DatabaseManager(app)
    user_manager = UserManager()
    post_manager = PostManager()
    shop_manager = ShopManager()
    notification_manager = NotificationManager()
    dm_manager = MessageManager()

@app.route("/", methods=["GET", "POST"])
def login():

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
    try:
        return render_template("home.html")
    except Exception as e:
        abort(404,description="投稿データの取得に失敗しました。")
        app.logger.error(f"Failed to fetch posts: {e}")
    
@app.route("/fetch_posts/<int:limit>/<int:offset>", methods=["GET"])
def fetch_post(limit,offset):
    try:
            # フィルターを設定して投稿データを取得
        has_more = True
        formatted_posts = post_manager.get_filtered_posts_with_reposts(offset=offset,limit=limit)

        #AJAX取得終了時
        if formatted_posts is None:
            has_more = False
            return jsonify(has_more,{ "message": "投稿がありません", "posts": []}), 200
        else:
            return jsonify(has_more,{ "message": "投稿を取得しました", "posts": formatted_posts}), 200
    except Exception as e:
        return jsonify({"error":str(e)}), 500

@app.route('/password-reset', methods=['GET', 'POST'])
def password_reset():
    if request.method == 'POST':
        
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
        user = db_manager.fetch_one(User, filters={"email": email})
        if not user:
            error = '該当するメールアドレスが見つかりません。'
            flash(error)
            app.logger.error(f"Password reset failed: {error}")
            return redirect(url_for('password_reset'))     
        
        # パスワードの更新
        hashed_password = generate_password_hash(password)
        success = db_manager.update(User, {"email": email}, {"password": hashed_password})
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

@app.route('/follow/<string:follow_user_id>', methods=['POST'])
def toggle_follow(follow_user_id):
    try:

        if not follow_user_id:
            app.logger.error("Missing required IDs for authentication.")
            return jsonify({'error': 'Unauthorized'}), 401

        result = user_manager.toggle_follow(followed_user_id=follow_user_id)

        return jsonify(result), 200

    except Exception as e:
        app.logger.error(f"Error toggling follow: {e}")
        return jsonify({'error': 'Server error'}), 500
    
@app.route("/my_profile/<id>", methods=["GET"])
def my_profile(id):

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
    

@app.route("/my_profile/update_info",methods = ["GET","POST"])
def update_info():
    if request.method == "GET":
        user = db_manager.fetch_one(model=User,filters={"id":Validator.decrypt(session['id'])})
        return render_template("my_info.html",user=user)
    else:
        
            result = user_manager.updata_user_info(
                user_id = request.form.get('user_id',None),
                username = request.form.get('username',None),
                real_name=request.form.get('real_name',None),
                address = request.form.get('address',None),
                bio=request.form.get('bio',None),
                profile_image=request.files.get('profile_image',None)
            )
            return jsonify(result)

@app.route("/toggle_block/<string:user_id>")
def toggle_block(user_id):
    try:
        result  =user_manager.toggle_block(blocked_user_id=user_id)

        if result.get('error'):
            return abort(400,description=result.get('error'))

        return redirect(url_for("my_profile",id=user_id))
    except Exception as e:
        app.logger.error(f"Error toggling block: {e}")
        return abort(500,description='Server error')

@app.route("/api/user/followed",methods=["GET"])
def fetch_followed_users():
    try:
        result = user_manager.get_followed_users(user_id=session['id'])
        if result['result']:
            return jsonify(result),200
        else:
            raise
    except Exception as e:
        app.logger.error(e)
        return jsonify(result),500

@app.route('/create_post', methods=['POST', 'GET'])
def create_post():
    if request.method == 'GET':
        if session.get('image_name'):
            image_path = url_for('static', filename=f'images/temp_images/{session["image_name"]}')
            return render_template('create_post.html', initial_image=image_path)
        return render_template('create_post.html')
    else:
        try:
            # フォームデータの取得
            content = request.form.get('content')
            tags = request.form.get('tags', "")  # タグが無い場合は空文字
            
            # タグの整形（カンマ区切りのタグをリスト化）
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()] if tags else []

            # 画像ファイルの取得（空の場合は空リスト）
            images = request.files.getlist('images') if 'images' in request.files else []
            if len(images) > 6:
                return jsonify({"success": False, "error": "You can upload a maximum of 6 images"}), 400
            
            # 投稿処理を呼び出し
            result = post_manager.create_post(
                content=content,
                image_files=images, 
                tags=tag_list)

            if result["success"]:
                if session.get('image_name'):
                    delete_result = post_manager.delete_temp()
                    if delete_result['success']:
                        return jsonify(result), 200
                    else:
                        return jsonify(delete_result), 400
                else:#画像がない場合 通常の処理
                    return jsonify({"success": True, "message": "Post created successfully"}), 200            
            else:
                return jsonify(result), 400

        except Exception as e:
            app.logger.error(f"Unexpected error in endpoint: {e}")
            return jsonify({"success": False, "error": "Internal Server Error"}), 500

@app.route('/create_design')
def create_design():
    return render_template("create_design.html")

@app.route('/submit_comment/<string:post_id>', methods=['POST'])
def submit_comment(post_id):

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
        return redirect(url_for('create_post'))
    except Exception as e:
        app.logger.error(f"Error: {e}")
        return f"エラーが発生しました: {str(e)}", 500

    
@app.route('/message',methods=['GET'])
def display_message_room():
    message_data = dm_manager.fetch_message_rooms(user_id=session['id'])
    if message_data['success']:
        return render_template("display_message_rooms.html",room_data = message_data["result"])
    else:
        abort(400,description="不正なアクセス")
    
    

@app.route("/message/user/<user_id>", methods=["GET"])
def display_message_by_user(user_id):
    try:
        # メッセージルームのデータを取得
        message_data = dm_manager.fetch_messages_by_user(user_id=session['id'],other_user_id=user_id)
        app.logger.info(f"Message data: {message_data}")
        if message_data['success']:
            return render_template("message_room.html",message = message_data)
        else:
            abort(400,description="不正なアクセス")
    except Exception as e:
        app.logger.error(f"Error in display_message: {e}")
        return abort(500,description="エラーが発生しました")

@app.route("/message/room/<room_id>", methods=["GET"])
def display_message_by_room(room_id):
    try:
        # メッセージルームのデータを取得
        message_data = dm_manager.fetch_messages_by_room(room_id=room_id,
                                                        user_id=session['id'])
        app.logger.info(f"Message data: {message_data}")
        if message_data['success']:
            return render_template("message_room.html",message = message_data)
        else:
            abort(400,description="不正なアクセス")
    except Exception as e:
        app.logger.error(f"Error in display_message: {e}")
        return abort(500,description="エラーが発生しました")

@app.route('/message/send/<user_id>',methods=['GET','POST'])
def send_message(user_id):
    try:
        if request.method == "POST":
            message = request.form.get('message','').strip()
            
            if not message:
                abort(400,description="メッセージが空です")
            else:
                dm_manager.send_message(sender_id=session['id'],recipient_id=user_id,content=message)
                return redirect(url_for('send_message',user_id=user_id))
        elif request.method == "GET":
            return redirect(url_for('display_message_by_user',user_id=user_id))
    except Exception as e:
        app.logger.error(f"Error in send_message: {e}")
        return abort(500,description="エラーが発生しました")

@app.route('/message/mark-as-read/<message_id>',methods=['POST'])
def mark_message_as_read(message_id):
    try:
        result = dm_manager.mark_messages_as_read_up_to(message_id=message_id,recipient_id=session['id'])
        if result['success']:
            return jsonify(result),200
        else:
            return jsonify(result),400
    except Exception as e:
        app.logger.error(f"Error in mark_message_as_read: {e}")
        return jsonify({"error":"エラーが発生しました"}),500
        


@app.route('/search', methods=['GET'])
def search():
    try:
        # クエリパラメータから値を取得
        query = request.args.get('query', '').strip().lower()
        tab = request.args.get('tab', 'USER').upper()  # デフォルトは "USER"

        # 結果の初期化
        results = {"users": [], "tags": [], "categories": []}

        if query:


            # タブに基づいた処理
            if tab == "USER":
                results['users'] = user_manager.search_users(query)
            elif tab == "TAG":
                results['tags'] = post_manager.search_tags(query)
            elif tab == "CATEGORY":
                results['categories'] = shop_manager.search_categories(query)

        # ログ出力
        app.logger.info(f"Search completed: query={query}, tab={tab}, results={results}")

        # クライアントのリクエスト形式に応じたレスポンス
        if request.headers.get('Accept') == 'application/json':
            return jsonify(results), 200
        else:
            # トレンドタグを取得
            trending_tag_ids = db_manager.redis.get_ranking_ids(ranking_key=db_manager.trending[1],top_n=10)
            if trending_tag_ids:
                trending_tags = post_manager.get_tags_by_ids(tag_ids=trending_tag_ids)
            else:
                trending_tags = []
            print(trending_tags)
            return render_template('search_page.html', query=query, tab=tab, results=results,trending_tags=trending_tags)

    except Exception as e:
        app.logger.error(f"Error occurred: {e}", exc_info=True)
        if request.headers.get('Accept') == 'application/json':
            return jsonify({"error": "An error occurred"}), 500
        else:
            return f"An error occurred: {str(e)}", 500
        
@app.route('/display_post/<post_id>', methods=['GET'])
def display_post(post_id):

    try:
        # デバッグ用ログ
        # 投稿データを取得
        post_details = post_manager.get_posts_details(post_id)
        app.logger.info(f"Post details: {post_details}")
        # テンプレートにデータを渡す
        if post_details:
            post_details = post_details[0]
        return render_template("display_post.html", post=post_details)
    except ValueError as e:
        app.logger.error(f"ValueError: {e}")
        return "指定された投稿が見つかりませんでした。", 404
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        return "投稿データの取得中にエラーが発生しました。", 500

@app.route("/fetch_trending_posts/<int:limit>/<int:offset>")
def fetch_trending_posts(limit,offset):
    try:
        # 現在のユーザーIDを取得（ログインしていない場合は None）
        has_more = True
        # Redis からトレンド投稿の ID を取得
        trending_posts_ids = db_manager.redis.get_ranking_ids(
            ranking_key=db_manager.trending[0], offset=offset,top_n=limit
        )
        if trending_posts_ids:
            # 投稿データを取得
            post_data = post_manager.get_posts_details(
                post_ids=trending_posts_ids)
        else:
            has_more = False
            post_data = []

        # データが空なら適切なレスポンスを返す
        if not post_data:
            return jsonify(False, {"message": "トレンド投稿がありません。", "posts": []}),200

        # クライアントにデータを送信
        return jsonify(has_more, {"message": "トレンド投稿を取得しました", "posts": post_data}),200

    except Exception as e:
        app.logger.error(f"⚠️ Error in fetch_trending_posts: {e}")
        return jsonify("error", {"message": "トレンド投稿の取得に失敗しました。"}),500

@app.route("/fetch_trending_tags")
def fetch_trending_tags():
    try:
        trending_tag_ids = db_manager.redis.get_ranking_ids(ranking_key=db_manager.trending[1],top_n=10)
        if trending_tag_ids:
            trending_tags = post_manager.get_tags_by_ids(tag_ids=trending_tag_ids)
            if trending_tags:
                return jsonify({"tags":trending_tags}),200
            else:
                return  jsonify({"tags":[]}),200
        else:
            raise Exception("トレンドなし")
    except Exception as e:
            app.logger.error(f"⚠️ Error in fetch_trending_tags: {e}")
            return jsonify({"message": "トレンド投稿の取得に失敗しました。"}),500

@app.route("/fetch_trending_products")
def fetch_trending_products():
    try:
        trending_ids = db_manager.redis.get_ranking_ids(ranking_key=db_manager.trending[2],top_n=10)
        if trending_ids:
            trending_products = shop_manager.fetch_multiple_products_images(product_ids=trending_ids)
            if trending_products:
                return jsonify("trending_products",{"message":"トレンド商品取得","products":trending_products}),200
            else:
                return  jsonify("trending_products",{"message":"トレンド商品なし","products":[]}),200
        else:
            raise Exception("トレンドなし")
        
    except Exception as e:
            app.logger.error(f"⚠️ Error in fetch_trending_products: {e}")
            return jsonify("error", {"message": "トレンド商品の取得に失敗しました。"}),500

                

        
@app.route("/notifications", methods=["GET"])
def notifications():
    """
    通知一覧を表示するエンドポイント
    """
    # セッションからユーザーIDを取得

    # NotificationManager を使って通知データを取得
    notification_manager = NotificationManager()
    try:
        notifications = notification_manager.get_notifications_for_user(session["id"])
    except Exception as e:
        app.logger.error(f"Failed to fetch notifications: {e}")
        flash("通知の取得中にエラーが発生しました。")
        return redirect(url_for("home"))

    # HTML テンプレートに通知データを渡す
    return render_template("display_notification.html", notifications=notifications)

@app.route("/repost/<post_id>", methods=["POST"])
def repost(post_id):

    try:
        sender_id = Validator.decrypt(session.get("id"))
        post_id = Validator.decrypt(post_id)

        if not sender_id or not post_id:
            app.logger.error("Missing required IDs for authentication.")
            return jsonify({'error': 'Unauthorized'}), 401

        result = post_manager.create_repost(post_id=post_id, user_id=sender_id)
        # 成功時の応答
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify({'success': False, 'message': 'リポストに失敗しました。'}), 400
        
    except Exception as e:
        app.logger.error(f"Error reposting: {e}")
        return jsonify({'error': 'Server error'}), 500
    
@app.route("/save_post/<post_id>", methods=["POST"])
def save_post(post_id):

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
    shop_data = shop_manager.get_shop_with_images(limit=10)

    trending_product_ids = shop_manager.redis.get_ranking_ids(ranking_key=shop_manager.trending[2])
    trending_products =  shop_manager.fetch_multiple_products_images(product_ids=trending_product_ids)
    if shop_data is None:
        abort(404, description="ショップページが見つかりません")

    return render_template("shop_page.html", products=shop_data,trending_products =trending_products)      

@app.route("/shop/fetch_products_by_category/<category_name>")
def fetch_products_by_category(category_name):
    try:
        # カテゴリ名に基づいて商品を取得
        products = shop_manager.search_categories(query=category_name)

        if not products:
            abort(404,description = "商品が見つかりません")

        return render_template("shop_categorized_page.html", products=products)
    except Exception as e:
        app.logger.error(f"Error in fetch_products_by_category: {e}")
        abort(500,description = "エラーが発生しました")
@app.route("/display_product/<product_id>")
def display_product(product_id):
    product = shop_manager.fetch_multiple_products_images(product_ids=product_id)

    if product_id is None:
        abort(404,description="商品が見つかりません")
    
    return render_template("shopping_page.html",product=product[0])

@app.route('/add_cart', methods=['POST'])
def add_to_cart():
    try:
        # リクエストのJSONデータを取得
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = int(data.get('quantity'))

        # バリデーションチェック
        if not product_id or quantity <= 0:
            return jsonify({"message": "無効な入力です"}), 400

        # 商品をカートに追加
        result = shop_manager.add_cart_item(user_id=session.get('id'),product_id=product_id,quantity=quantity)
        if result:
            app.logger.info(f"商品 が {quantity} 個カートに追加されました。")
            return jsonify({"message": "カートに追加されました"}), 200
        else:
            app.logger.error("カート追加に失敗しました")
            return jsonify({"message": "カート追加に失敗しました"}), 400

    except Exception as e:
        return jsonify({"message": "エラーが発生しました", "error": str(e)}), 500
    
@app.route("/after_add_cart")
def after_add_cart():
    return render_template("after_add_cart.html")   

@app.route("/display_cart")
def display_cart():
    user_id = session.get("id")  # セッションからユーザーIDを取得
    success, cart_items = shop_manager.fetch_cart_items(user_id)

    if not success:
        abort(500, description = "カートの取得に失敗しました。")

    return render_template("display_cart.html", cart_items=cart_items)

@app.route("/update_cart_quantity", methods=["POST"])
def update_cart_quantity():
    try:
        item_id = request.json["item_id"]
        new_quantity = int(request.json["newQuantity"])

        if not item_id:
            return jsonify({"message": "無効な商品IDです"}), 400

        user_id = session.get("id")
        if isinstance(user_id, str):
            user_id = Validator.decrypt(user_id)

        result = shop_manager.update_cart_quantity(item_id=item_id, new_quantity=new_quantity)

        if result is None:
            app.logger.error("update_cart_quantity の戻り値が None です")
            return jsonify({"message": "内部エラーが発生しました"}), 500
        
        if result.get("success"):
            
            # データベースから最新のカート情報を取得し、セッションを更新
            success, updated_cart_items = shop_manager.fetch_cart_items(user_id)
            session["cart"] = {Validator.decrypt(str(item['product_id'])): item['quantity'] for item in updated_cart_items}

            return jsonify({"message": result["message"], "cart": session["cart"]}), 200
        else:
            return jsonify({"message": "数量更新に失敗しました"}), 400

    except ValueError as e:
        app.logger.error(f"Decryption error: {e}")
        return jsonify({"message": "無効なデータが提供されました。"}), 400
    except Exception as e:
        app.logger.error(f"エラーが発生しました: {e}")
        return jsonify({"message": "エラーが発生しました", "error": str(e)}), 500

@app.route("/remove_from_cart", methods=["POST"])
def remove_from_cart():
    try:
        data = request.get_json()
        product_id = data.get('product_id')

        if product_id is None:
            return jsonify({"message": "無効な商品IDです"}), 400
    
        # データベースから削除
        result = shop_manager.delete_cart_items(product_ids=product_id)
        if not result['status']:
            raise
        else:
            return jsonify(result['message']), 200

    except Exception as e:
        app.logger.error(e)
        return jsonify(result['message']), 500




@app.route("/checkout", methods=["GET","POST"])
def check_out():
    try:
        if request.method == "POST":
            user_id = Validator.decrypt(session.get("id"))
            #payment_method = request.form.get("payment_method") credit card
            check_out_items = list(map(Validator.decrypt,request.form.getlist("selected_products")))
            app.logger.info(check_out_items)
            result = shop_manager.check_out(selected_cart_item_ids=check_out_items,user_id=user_id,payment_method="credit card")
            if result['success']:
                return redirect(url_for("complete_checkout",after_checkout=True))
            else:
                abort(400,description="チェックアウトに失敗しました")
        else:
            return redirect("home")  ### ここは後で変更する
    except Exception as e:
        app.logger.error(f"エラー: {e}")
        return abort(500,description="チェックアウトに失敗しました")
    
@app.route("/complete_checkout/<after_checkout>",methods=["GET"])
def complete_checkout(after_checkout):
    try:
        user_id = session.get("id")
        result = shop_manager.fetch_sales_history(user_id=user_id)
        if after_checkout == "True" or after_checkout == True:
            after_checkout = True

        else:
            after_checkout = False
            if not result:
                return render_template("complete_checkout.html",history = None,after_checkout=after_checkout)
        return render_template("complete_checkout.html",history = result,after_checkout=after_checkout)


    except Exception as e:
        app.logger.error(f"エラー: {e}")
        return abort(500,description="サーバーエラーが発生しました")
    
@app.route("/test")
def test():
    return render_template("test.html")

@app.route("/logout")
def logout():
    session.pop("id", None)
    return redirect(url_for('login'))
    
if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=80, debug=True)
    except KeyboardInterrupt:
        print("\n[INFO] Server 停止")