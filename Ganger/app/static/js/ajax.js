let loading = false;
let hasMoreData = true;
let offset = 0;
const limit = 10;
let totalPost = 0;


// スクロールが一番下に到達したかを判定する関数
function isBottomReached() {
    return window.innerHeight + window.scrollY >= document.body.offsetHeight;
}

// データを非同期に取得
async function loadMoreData() {
    if (!hasMoreData) {
        console.log("すべてのデータがロードされました");
    };
    if (loading) return;

    loading = true;
    document.getElementById("loading").style.display = "block";

    try {
        let response = await fetch(`/fetch_post?offset=${offset}&limit=${limit}`);
        let result = await response.json();

        if (response.ok) {
            totalPost = result.total;
            console.log(`合計投稿数: ${totalPost}`);
            result.items.forEach(item => {
                let div = document.createElement("div");
                div.classList.add("item");
                div.textContent = `Post: ${item}`;
                console.log(`Post: ${item}`);
                document.getElementById("content").appendChild(div);
            });
            offset += limit;
        }

        // すべてのデータがロードされたかチェック
        hasMoreData = result.has_more;
    } catch (error) {
        console.error("データの取得に失敗しました:", error);
    } finally {
        loading = false;
        document.getElementById("loading").style.display = "none";
    }
}

// スクロールイベントリスナー
window.addEventListener("scroll", () => {
    if (isBottomReached()) {
        loadMoreData();
    }
});