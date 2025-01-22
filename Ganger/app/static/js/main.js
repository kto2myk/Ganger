document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.splide').forEach(function (carousel) {
    new Splide(carousel).mount();
    });
});


// 検索ボックスの非表示に関するコメントアウト
// const commentModal = document.getElementById('search-results-container');

// window.addEventListener('click', (event) => {
//     if (event.target === commentModal) {
//         commentModal.style.display = 'none';
//     }
// });

function setFixedSize() {
    let button = document.getElementById("post_button");

    // 画面の幅と高さ（物理的なモニターサイズに基づく）
    let screenWidth = screen.width;
    let screenHeight = screen.height;

    // ボタンサイズをモニターサイズの固定割合で設定（例: 画面幅の5%）
    button.style.width = (screenWidth * 0.05) + "px";
    button.style.height = (screenWidth * 0.05) + "px";
}

// 初回読み込み時に設定
setFixedSize();

window.onload = function() {
    const spinner = document.getElementById('loading');
    spinner.classList.add('loaded');

    // パスと対応するIDのマッピング
    const pageToIdMap = {
        "/home": "home",
        "/search": "search",
        "/notification": "notification",
        "/settings": "settings",
        "/massage": "massage",
        "/profile": "profile",
        "/create-design": "login"
    };

    // 現在のパスを取得
    let currentUrl = location.pathname;

    // マッピングに一致する要素があれば、fill を変更
    for (let path in pageToIdMap) {
        if (currentUrl.startsWith(path)) {
            let id = document.getElementById(pageToIdMap[path]);
            if (id) id.style.fill = "#a46a9a"
                    id.style.stroke = "#a46a9a";
                    id.style.text = "#a46a9a";

            break;  // 一致が見つかったらループを終了
        }
    }
};