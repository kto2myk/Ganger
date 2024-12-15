import os
import mimetypes
from werkzeug.datastructures import FileStorage
from Ganger.app.model.post.post_manager import PostManager

def test_with_existing_images():
    # PostManagerインスタンスの作成
    post_manager = PostManager()

    # テストデータ
    post_data = {
        "user_id": 1,
        "body_text": "これは用意された画像を使ったテスト投稿です。",
        "reply_id": None
    }

    # 用意された画像ファイルのパス
    image_paths = [
        os.path.abspath(r"C:\HAL\IH\IH22\Ganger\app\static\images\post_images\fuwa.png"),
        os.path.abspath(r"C:\HAL\IH\IH22\Ganger\app\static\images\post_images\gl.png"),
        os.path.abspath(r"C:\HAL\IH\IH22\Ganger\app\static\images\post_images\hi.png")
    ]

    # FileStorageオブジェクトを作成
    image_files = []
    for path in image_paths:
        absolute_path = os.path.abspath(path)
        print(f"Generated path: {absolute_path}")
        if not os.path.exists(absolute_path):
            print(f"File not found: {absolute_path}")
            continue

        # ファイルを開いたまま保持する
        file = open(absolute_path, "rb")
        mime_type, _ = mimetypes.guess_type(absolute_path)
        file_storage = FileStorage(
            stream=file,
            filename=os.path.basename(absolute_path),
            content_type=mime_type
        )
        image_files.append(file_storage)

    # 投稿作成メソッドの呼び出し
    result = post_manager.create_post(post_data, image_files)

    # ファイルを明示的に閉じる
    for file_storage in image_files:
        file_storage.stream.close()

    # テスト結果の確認
    print("Test Result:")
    print(result)

# テスト実行
if __name__ == "__main__":
    test_with_existing_images()
