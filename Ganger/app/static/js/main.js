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
            if (id) id.style.fill = "#000";
            break;  // 一致が見つかったらループを終了
        }
    }
};