document.addEventListener('DOMContentLoaded', function () {

    document.querySelectorAll('.splide').forEach(function (carousel) {
    new Splide(carousel).mount();
    });

    let currentUrl = location.pathname;

    console.log(`現在のURL: ${currentUrl}`);
            
    // URLに応じた対象IDと新しいIDをマッピング
    const idMapping = {
        "/home": { oldId: "home", newId: "nav-active" },
        "/search": { oldId: "search", newId: "nav-active" },
        "/notification": { oldId: "notification", newId: "nav-active" },
        "/settings": { oldId: "settings", newId: "nav-active" },
        "/message": { oldId: "message", newId: "nav-active" },
        "/cart": { oldId: "cart", newId: "nav-active" },
        "/my_profile": { oldId: "profile", newId: "nav-active" },
        "/design": { oldId: "design", newId: "nav-active" }
    };

    // 対応するページが存在すれば、IDを変更
    for (let key in idMapping) {
        if (currentUrl.startsWith(key)) {
            console.log(`URL: ${currentUrl}`);
            let element = document.getElementById(idMapping[key].oldId);

            if (element) {
                element.id = idMapping[key].newId;
            };
        };
    };
});


// 検索ボックスの非表示に関するコメントアウト
// const commentModal = document.getElementById('search-results-container');

// window.addEventListener('click', (event) => {
//     if (event.target === commentModal) {
//         commentModal.style.display = 'none';
//     }
// });

// ボタンのサイズを固定する関数
function setFixedSize() {
    let button = document.getElementById("post_button");

    // 画面の幅と高さ（物理的なモニターサイズに基づく）
    let screenWidth = screen.width;

    // ボタンサイズをモニターサイズの固定割合で設定（例: 画面幅の5%）
    button.style.width = (screenWidth * 0.05) + "px";
    button.style.height = (screenWidth * 0.05) + "px";
}

// 初回読み込み時に設定
    
window.onload = function() {
    // ボタンのサイズを設定
    setFixedSize();
};

    // ロード完了時の処理
    // window.addEventListener("load", function() {
    //     const loadingScreen = document.getElementById("loading");
    //     loadingScreen.style.opacity = "0";  // フェードアウト
    //     setTimeout(() => {
    //       loadingScreen.style.display = "none";  // 完全に非表示
    //       document.body.style.overflow = "auto";  // スクロール再開
    //     }, 500);
    // });
