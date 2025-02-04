# PostManagerを使用してタグを追加
from Ganger.app.model.post.post_manager import PostManager

try:
    post_manager = PostManager()
    post_manager.add_tag_to_post("Nature", 3)
    post_manager.add_tag_to_post("Technology", 5)
    post_manager.add_tag_to_post("Science", 6)
    post_manager.add_tag_to_post("Education", 7)
except Exception as e:
    print(f"エラーが発生しました: {e}")
print("タグ付きテストデータの挿入が完了しました！")