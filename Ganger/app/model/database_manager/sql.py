table_name= 'sqlite:///Ganger.db'

sql_statements = """
CREATE TABLE IF NOT EXISTS Users (
    ID INTEGER PRIMARY KEY,
    user_id VARCHAR(20) NOT NULL,
    username VARCHAR(16) NOT NULL,
    email VARCHAR(255) NOT NULL,
    Password VARCHAR(20) NOT NULL,
    create_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    real_name VARCHAR(45) NOT NULL,
    address VARCHAR(60) NULL,
    age INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS POST (
    post_id INTEGER PRIMARY KEY,
    user_Id INTEGER NOT NULL,
    bodyText TEXT NOT NULL,
    Post_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reply_Id INTEGER,
    FOREIGN KEY (user_Id) REFERENCES Users (ID)
);

CREATE TABLE IF NOT EXISTS Image (
    post_id INTEGER NOT NULL,
    img_path VARCHAR(100) NOT NULL,
    img_order INTEGER NOT NULL,
    PRIMARY KEY (post_id, img_path),
    FOREIGN KEY (post_id) REFERENCES POST (post_id)
);

CREATE TABLE IF NOT EXISTS Likes (
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (post_id, user_id),
    FOREIGN KEY (post_id) REFERENCES POST (post_id),
    FOREIGN KEY (user_id) REFERENCES Users (ID)
);

CREATE TABLE IF NOT EXISTS Follow (
    user_id INTEGER NOT NULL,
    follow_users_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, follow_users_id),
    FOREIGN KEY (user_id) REFERENCES Users (ID),
    FOREIGN KEY (follow_users_id) REFERENCES Users (ID)
);

CREATE TABLE IF NOT EXISTS Repost (
    post_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (post_id, user_id),
    FOREIGN KEY (post_id) REFERENCES POST (post_id),
    FOREIGN KEY (user_id) REFERENCES Users (ID)
);

CREATE TABLE IF NOT EXISTS Category_Master (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_Name VARCHAR(10) NOT NULL
);

CREATE TABLE IF NOT EXISTS Tag_Master (
    tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Tag_Post (
    tag_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    PRIMARY KEY (tag_id, post_id),
    FOREIGN KEY (post_id) REFERENCES POST (post_id),
    FOREIGN KEY (tag_id) REFERENCES Tag_Master (tag_id)
);

CREATE TABLE IF NOT EXISTS Post_Category (
    category_id INTEGER NOT NULL,
    post_id INTEGER NOT NULL,
    PRIMARY KEY (category_id, post_id),
    FOREIGN KEY (post_id) REFERENCES Category_Master (category_id),
    FOREIGN KEY (category_id) REFERENCES POST (post_id)
);

CREATE TABLE IF NOT EXISTS Massage (
    massage_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    sent_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES Users (ID),
    FOREIGN KEY (receiver_id) REFERENCES Users (ID)
);

CREATE TABLE IF NOT EXISTS Read_Status (
    status_id INTEGER NOT NULL,
    read_user INTEGER NOT NULL,
    Massage_id INTEGER NOT NULL,
    read_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (status_id),
    FOREIGN KEY (read_user) REFERENCES Massage (receiver_id),
    FOREIGN KEY (Massage_id) REFERENCES Massage (massage_id)
);

CREATE TABLE IF NOT EXISTS Credit_Card (
    User_id INTEGER NOT NULL,
    credit_number INTEGER NOT NULL,
    credit_limit DATE NOT NULL,
    credit_code INTEGER NOT NULL,
    PRIMARY KEY (User_id),
    FOREIGN KEY (User_id) REFERENCES Users (ID)
);

CREATE TABLE IF NOT EXISTS Shops (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    Category_id INTEGER NOT NULL,
    name VARCHAR(45) NOT NULL,
    Price DECIMAL(5,2) NOT NULL,
    FOREIGN KEY (post_id) REFERENCES POST (post_id),
    FOREIGN KEY (tag_id) REFERENCES Tag_Master (tag_id),
    FOREIGN KEY (Category_id) REFERENCES Category_Master (category_id)
);

CREATE TABLE IF NOT EXISTS Cart (
    cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users (ID),
    FOREIGN KEY (product_id) REFERENCES Shops (product_id)
);

CREATE TABLE IF NOT EXISTS Save_Post (
    user_id INTEGER NOT NULL,
    post_id INTEGER,
    product_id INTEGER,
    PRIMARY KEY (user_id),
    FOREIGN KEY (user_id) REFERENCES Users (ID),
    FOREIGN KEY (post_id) REFERENCES POST (post_id),
    FOREIGN KEY (product_id) REFERENCES Shops (product_id)
);

CREATE TABLE IF NOT EXISTS Notification_Type (
    notification_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_name VARCHAR(45) NOT NULL
);

CREATE TABLE IF NOT EXISTS Notification (
    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    notification_type INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    contents TEXT NOT NULL,
    sent_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users (ID),
    FOREIGN KEY (notification_type) REFERENCES Notification_Type (notification_type_id)
);

CREATE TABLE IF NOT EXISTS Notification_Status (
    status_id INTEGER PRIMARY KEY AUTOINCREMENT,
    notification_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    Read TINYINT NOT NULL DEFAULT 0,
    time_delete TINYINT NOT NULL DEFAULT 0,
    FOREIGN KEY (notification_id) REFERENCES Notification (notification_id),
    FOREIGN KEY (user_id) REFERENCES Users (ID)
);

CREATE TABLE IF NOT EXISTS Cart_Items (
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cart_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (cart_id) REFERENCES Cart (cart_id),
    FOREIGN KEY (product_id) REFERENCES Cart (product_id)
);

CREATE TABLE IF NOT EXISTS Sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    Total_Amount DECIMAL(3) NOT NULL,
    Date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users (ID)
);

CREATE TABLE IF NOT EXISTS Sales_Items (
    sale_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_Id INTEGER NOT NULL,
    product_Id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (sale_Id) REFERENCES Sales (sale_id),
    FOREIGN KEY (product_Id) REFERENCES Shops (product_id)
);

CREATE TABLE IF NOT EXISTS Block (
    user_id INTEGER NOT NULL,
    blocked_user INTEGER NOT NULL,
    PRIMARY KEY (user_id, blocked_user),
    FOREIGN KEY (user_id) REFERENCES Users (ID),
    FOREIGN KEY (blocked_user) REFERENCES Users (ID)
);
""".strip().split(";")  # 各CREATE文ごとに分割

