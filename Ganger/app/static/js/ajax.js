let loading = false;
let hasMoreData = true;
let followingOffset = 0;
let recommendedOffset = 0;
const limit = 2;
let totalPost = 0;
let nowPlace = "following-contents";
let requestTo = "";

// スクロールが一番下に到達したかを判定する関数
function isBottomReached() {
    return window.innerHeight + window.scrollY >= document.body.offsetHeight;
}

// フォロー中とおすすすめ投稿の切り替え処理
function switchRecommendedArea(){
    let following_container_style = document.getElementById("following-contents");
    let recommended_container_style = document.getElementById("recommended-contents");
    nowPlace = "recommended-contents";
    following_container_style.style.display = "none";
    recommended_container_style.style.display = "block";
}

function switchFollowingArea(){
    let following_container_style = document.getElementById("following-contents");
    let recommended_container_style = document.getElementById("recommended-contents");
    nowPlace = "following-contents";
    following_container_style.style.display = "block";
    recommended_container_style.style.display = "none";
}

// 投稿データ非同期取得処理
function getPostData() {
    fetch(`/${requestTo}`)
        .then(response => response.json())
        .then((data) => {
            console.log(data)
            if (Array.isArray(data)) {
              let postListHTML = "";

              let repostUserID_unique = "";
              let repostUserID        = "";
              let repostUserName      = "";
              // リポストユーザー情報解凍(リポストされていない場合はnull)
              repostMessage ="";
              
                data[1].posts.forEach(postData => {
                    bodyText        = postData.body_text;
                    commentCount    = postData.comment_count;
                    images          = postData.images;
                    isMe            = postData.is_me;
                    likeCount       = postData.like_count;
                    postID          = postData.post_id;
                    postTime        = postData.post_time;
                    repostCount     = postData.repost_count;
                    savedCount      = postData.saved_count;


                    // ユーザー情報解凍
                    userInfo        = postData.user_info;   //id, profile_image, username　番目がそれぞれ存在
                    userID_unique        = userInfo.id;
                    profileImagePath = userInfo.profile_image;
                    userID          = userInfo.user_id;
                    userName        = userInfo.username;


                    // リポストされている場合はリポストしたユーザー名を表示
                    if (postData.repost_user) {
                      repostUserID_unique = repost_user.id;
                      repostUserID        = repost_user.user_id;
                      repostUserName      = repost_user.username
                      
                      repostMessage = `
                        <a class="reposted_massage" href="ここ聞くこと！！！">
                          ${repostUserName}さんがリポストしました
                        </a>
                      `;
                    }


                    // 画像エリア情報生成
                    images          = postData.images;  //0,1,2...番目のimg_path番目に画像のパスが格納されている
                    let imageAreaHTML = "";
                        images.forEach(imagePath => {`
                          ${imageAreaHTML += `
                          <li class="splide__slide">
                            <a href="display_post/${postID}">
                              <img src="${imagePath.img_path}"alt="投稿画像">
                            </a>
                          </li>
                          `}
                        `});
                    
                    let isMeAreaHTML = "";
                    if (isMe) {
                      isMeAreaHTML = `
                        <button id="product-button-${postID}" class="extension_button" popovertarget="product-popover-${postID}">
                            <?xml version="1.0" encoding="utf-8"?>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M9 11V6C9 4.34315 10.3431 3 12 3C13.6569 3 15 4.34315 15 6V10.9673M10.4 21H13.6C15.8402 21 16.9603 21 17.816 20.564C18.5686 20.1805 19.1805 19.5686 19.564 18.816C20 17.9603 20 16.8402 20 14.6V12.2C20 11.0799 20 10.5198 19.782 10.092C19.5903 9.71569 19.2843 9.40973 18.908 9.21799C18.4802 9 17.9201 9 16.8 9H7.2C6.0799 9 5.51984 9 5.09202 9.21799C4.71569 9.40973 4.40973 9.71569 4.21799 10.092C4 10.5198 4 11.0799 4 12.2V14.6C4 16.8402 4 17.9603 4.43597 18.816C4.81947 19.5686 5.43139 20.1805 6.18404 20.564C7.03968 21 8.15979 21 10.4 21Z" stroke="#000000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                          </button>
                      `;
                    };

                    // console.log(`text"${bodyText}", commentCount"${commentCount}", imagepath"${images}", likeCount"${likeCount}", postID"${postID}", repostCount"${repostCount}", savedCount"${savedCount}", userInfo"${userInfo}", imageAreaHTML"${imageAreaHTML}"`);

                    // 投稿データHTML生成
                    postListHTML += `
                      <div class="post_container">
                        <!-- リポストされている場合はリポストしたユーザー名を表示 -->
                        ${repostMessage}


                        <!-- 投稿主のアイコン画像とユーザー名 -->
                        <div class="account_info">
                          <a href="/my_profile/${postID}">
                            <img src="${profileImagePath}" alt="プロフィール画像">
                          </a>
                          <p>${userName}</p>
                        </div>

                        <!-- 投稿画像エリア -->
                        <div class="image_area">
                          <section id="image-carousel-${postID}" class="splide">
                            <div class="splide__track">
                              <ul class="splide__list">
                                ${imageAreaHTML}
                              </ul>
                            </div>
                          </section>
                        </div>


                        <div class="post_buttons" data-post-id="${postID}" data-user-id="${userID_unique}">
                        <!-- いいねボタン -->
                        <button id="like-button-${postID}" class="extension_button">
                          <div class="svg-container">
                            <svg viewBox="0 0 24 24" class="svg-outline" xmlns="http://www.w3.org/2000/svg">
                              <path d="M17.5,1.917a6.4,6.4,0,0,0-5.5,3.3,6.4,6.4,0,0,0-5.5-3.3A6.8,6.8,0,0,0,0,8.967c0,4.547,4.786,9.513,8.8,12.88a4.974,4.974,0,0,0,6.4,0C19.214,18.48,24,13.514,24,8.967A6.8,6.8,0,0,0,17.5,1.917Zm-3.585,18.4a2.973,2.973,0,0,1-3.83,0C4.947,16.006,2,11.87,2,8.967a4.8,4.8,0,0,1,4.5-5.05A4.8,4.8,0,0,1,11,8.967a1,1,0,0,0,2,0,4.8,4.8,0,0,1,4.5-5.05A4.8,4.8,0,0,1,22,8.967C22,11.87,19.053,16.006,13.915,20.313Z"></path>
                            </svg>
                          </div>
                        </button>
                        
                        
                        <!-- コメントボタン -->
                        <button id="comment-button-${postID}" class="extension_button" popovertarget="comment-popover-${postID}">
                          <svg width="16" height="16" viewBox="0 0 32 32" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:sketch="http://www.bohemiancoding.com/sketch/ns">
                            <g id="Page-1" stroke="none" stroke-width="1" fill="none" fill-rule="evenodd" sketch:type="MSPage">
                              <g id="Icon-Set" sketch:type="MSLayerGroup" transform="translate(-100.000000, -255.000000)" fill="black">
                                <path d="M116,281 C114.832,281 113.704,280.864 112.62,280.633 L107.912,283.463 L107.975,278.824 C104.366,276.654 102,273.066 102,269 C102,262.373 108.268,257 116,257 C123.732,257 130,262.373 130,269 C130,275.628 123.732,281 116,281 L116,281 Z M116,255 C107.164,255 100,261.269 100,269 C100,273.419 102.345,277.354 106,279.919 L106,287 L113.009,282.747 C113.979,282.907 114.977,283 116,283 C124.836,283 132,276.732 132,269 C132,261.269 124.836,255 116,255 L116,255 Z" id="comment-1" sketch:type="MSShapeGroup"></path>
                              </g>
                            </g>
                          </svg>
                        </button>
                        
                        
                        <!-- リポストボタン -->
                        <button id="repost-button-${postID}" class="extension_button">
                          <?xml version="1.0" encoding="utf-8"?>
                          <svg fill="#000000" width="20" height="20" viewBox="3 0 24 24" id="repost-round" xmlns="http://www.w3.org/2000/svg" class="icon line">
                            <path id="primary" d="M6,14V9A6,6,0,0,1,16.89,5.54" style="fill: none; stroke: rgb(0, 0, 0); stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.5;"></path>
                            <polyline id="primary-2" data-name="primary" points="8 12 6 14 4 12" style="fill: none; stroke: rgb(0, 0, 0); stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.5;"></polyline>
                            <path id="primary-3" data-name="primary" d="M18,10v5A6,6,0,0,1,7.11,18.46" style="fill: none; stroke: rgb(0, 0, 0); stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.5;"></path>
                            <polyline id="primary-4" data-name="primary" points="16 12 18 10 20 12" style="fill: none; stroke: rgb(0, 0, 0); stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.5;"></polyline>
                          </svg>
                        </button>

                        ${isMeAreaHTML}

                      <!-- 保存ボタン -->
                        <button id="save-button-${postID}" class="extension_button">
                          <?xml version="1.0" encoding="utf-8"?>
                          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="feather feather-bookmark"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>
                        </button>
                      </div>

                      <p class="body_text">${bodyText}</p>
                      <p class="post_time">${postTime}</p>
                    </div>

                      <!-- コメントモーダル -->
                      <div id="comment-modal-${postID}" class="modal">
                        <div class="modal-content">
                          <span class="close" data-modal="comment-modal-${postID}">&times;</span>
                          <p>${userName}</p>
                          <a href="/my_profile/${postID}">
                            <img src="${profileImagePath}" alt="プロフィール画像">
                          </a>
                          <img src="${images[0].img_path}" alt="test">
                          <form action="/submit_comment, post_id=${postID}" method="post">
                            <input type="text" id="comment-input-${postID}" name="comment" placeholder="コメントを入力">
                            <button id="comment-submit-${postID}">送信する</button>
                          </form>
                        </div>
                      </div>

                      <!-- プロダクトモーダル -->
                      <div id="product-modal-${postID}" class="modal">
                        <div class="modal-content">
                            <span class="close" data-modal="product-modal-${postID}">&times;</span>
                            <h2>プロダクト詳細を編集</h2>
                            <form action="/make_post_into_product, post_id=${postID}" method="post">
                                <select name="category" id="category-box-${postID}">
                                  <option value="tops">tops</option>
                                  <option value="pants">pants</option>
                                  <option value="items">items</option>
                                  <option value="other">other</option>
                                </select>
                                <input type="text" name="price" placeholder="価格を入力" id="price-box-${postID}">
                                <input type="text" name="name" placeholder=" 商品名を入力" id="name-box-${postID}">
                                <button type="submit">保存</button>
                            </form>
                        </div>
                      </div>
                    `;
                  }// end of data.forEach
            )
            // console.log(postListHTML);
            document.getElementById(`${nowPlace}`).innerHTML += postListHTML;
            console.log("offset:", recommendedOffset, followingOffset);
            document.querySelectorAll('.splide').forEach(function (carousel) {
              new Splide(carousel).mount();
              });
          }})
      }

// データを非同期に取得
async function loadMoreData() {
    if (!hasMoreData) {
        console.log("すべてのデータがロードされました");
        return
    };

    try {
      if (nowPlace == "following-contents") {
        requestTo = `fetch_posts/${limit}/${followingOffset}`;
        getPostData();
        followingOffset += limit;
      }else {
        requestTo = `fetch_trending_posts/${limit}/${recommendedOffset}`;
        getPostData();
        recommendedOffset += limit;
      }

    console.log("offset:", recommendedOffset, followingOffset);

    // すべてのデータがロードされたかチェック
    hasMoreData = result.has_more;
    } catch (error) {
        console.error("データの取得に失敗しました:", error);
    };
}

// スクロールイベントリスナー
window.addEventListener("scroll", () => {
    if (isBottomReached()) {
      loadMoreData();
    }
});


// 初回読み込み時に実行
document.addEventListener("DOMContentLoaded", () => {
    requestTo = `fetch_posts/${limit}/${followingOffset}`;
    getPostData();
    switchFollowingArea();
    followingOffset += limit;
});

// おすすめボタンクリック判定
document.getElementById('recommended-posts-button').addEventListener('click', function () {
    console.log("おすすめボタンがクリックされました");
    requestTo = `fetch_trending_posts/${limit}/${recommendedOffset}`;
    getPostData();
    switchRecommendedArea();
    recommendedOffset += limit;
});

// フォロー中ボタンクリック判定
document.getElementById('following-posts-button').addEventListener('click', function () {
    console.log("フォロー中ボタンがクリックされました");
    requestTo = `fetch_posts/${limit}/${followingOffset}`;
    getPostData();
    switchFollowingArea();
    followingOffset += limit;
});