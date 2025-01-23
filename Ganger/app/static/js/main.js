document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.splide').forEach(function (carousel) {
    new Splide(carousel).mount();
    });

    let currentUrl = location.pathname;
            
    // URLに応じた対象IDと新しいIDをマッピング
    const idMapping = {
        "/home": { oldId: "home", newId: "nav-active" },
        "/search": { oldId: "search", newId: "nav-active" },
        "/notification": { oldId: "notification", newId: "nav-active" },
        "/settings": { oldId: "settings", newId: "nav-active" },
        "/message": { oldId: "message", newId: "nav-active" },
        "/profile": { oldId: "profile", newId: "nav-active" },
        "/design": { oldId: "design", newId: "nav-active" }
    };

    // 対応するページが存在すれば、IDを変更
    if (idMapping[currentUrl]) {
        let element = document.getElementById(idMapping[currentUrl].oldId);
        if (element) {
            element.id = idMapping[currentUrl].newId;
            console.log(`IDが "${idMapping[currentUrl].oldId}" から "${element.id}" に変更されました`);
        } else {
            console.warn(`要素 "${idMapping[currentUrl].oldId}" が見つかりません`);
        }
    } else {
        console.warn("対応するページがありません");
    }
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
};
