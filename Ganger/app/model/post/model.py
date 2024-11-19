from Ganger.app.model.database_manager import Base, Column, Integer, String, Text, DateTime, ForeignKey, func, relationship
from sqlalchemy.schema import UniqueConstraint

class Post(Base):
    __tablename__ = 'posts'
    post_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    body_text = Column(Text, nullable=False)
    post_time = Column(DateTime, default=func.now())
    reply_id = Column(Integer)

    # リレーション
    author = relationship("Users", back_populates="posts")  # 投稿したユーザー
    images = relationship("Images", back_populates="post")  # 投稿に紐づく画像
    likes = relationship("Likes", back_populates="post")  # 投稿に付けられた「いいね」
    tags = relationship("TagPosts", back_populates="post")  # 投稿に付けられたタグ
    categories = relationship("PostCategories", back_populates="post")  # 投稿に関連付けられたカテゴリ
    saved_posts = relationship("SavePosts", back_populates="post")  # 保存された投稿

    def __repr__(self):
        return f"<Post(post_id={self.post_id}, user_id={self.user_id}, post_time={self.post_time}, reply_id={self.reply_id})>"

class Image(Base):
    __tablename__ = 'images'
    post_id = Column(Integer, ForeignKey('posts.post_id'), primary_key=True, nullable=False)
    img_path = Column(String(100), primary_key=True, nullable=False)
    img_order = Column(Integer, nullable=False)

    # ユニーク制約を追加（投稿内での順序を一意にする）
    __table_args__ = (
        UniqueConstraint('post_id', 'img_order', name='unique_post_image_order'),
    )

    # リレーション
    post = relationship("Posts", back_populates="images")  # 投稿に関連付けられた画像

    def __repr__(self):
        return f"<Image(post_id={self.post_id}, img_path={self.img_path}, img_order={self.img_order})>"

class Like(Base):
    __tablename__ = 'likes'
    post_id = Column(Integer, ForeignKey('posts.post_id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)

    # リレーション
    post = relationship("Posts", back_populates="likes")  # 「いいね」が付いた投稿
    user = relationship("Users", back_populates="likes")  # 「いいね」を付けたユーザー

    def __repr__(self):
        return f"<Like(post_id={self.post_id}, user_id={self.user_id})>"

class TagMaster(Base):
    __tablename__ = 'tag_master'
    tag_id = Column(Integer, primary_key=True, autoincrement=True)
    tag_text = Column(Text, nullable=False)

    def __repr__(self):
        return f"<TagMaster(tag_id={self.tag_id}, tag_text={self.tag_text})>"

class TagPost(Base):
    __tablename__ = 'tag_posts'
    tag_id = Column(Integer, ForeignKey('tag_master.tag_id'), primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.post_id'), primary_key=True)

    # リレーション
    post = relationship("Posts", back_populates="tags")  # タグが付けられた投稿

    def __repr__(self):
        return f"<TagPost(tag_id={self.tag_id}, post_id={self.post_id})>"

class CategoryMaster(Base):
    __tablename__ = 'category_master'
    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_name = Column(String(10), nullable=False)

    def __repr__(self):
        return f"<CategoryMaster(category_id={self.category_id}, category_name={self.category_name})>"

class PostCategory(Base):
    __tablename__ = 'post_categories'
    category_id = Column(Integer, ForeignKey('category_master.category_id'), primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.post_id'), primary_key=True)

    # リレーション
    post = relationship("Posts", back_populates="categories")  # カテゴリが関連付けられた投稿

    def __repr__(self):
        return f"<PostCategory(category_id={self.category_id}, post_id={self.post_id})>"
