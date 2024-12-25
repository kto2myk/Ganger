document.addEventListener("DOMContentLoaded", () => {
    const searchComponent = window.searchComponent; // 親コンポーネントのインスタンスを利用

    // URLから初期タブとクエリを取得
    const urlParams = new URLSearchParams(window.location.search);
    let currentTab = urlParams.get("tab") || "USER"; // 初期タブは "USER"
    const query = urlParams.get("query") || "";

    searchComponent.setTab(currentTab); // 親コンポーネントにタブ情報を設定

    // タブの初期状態を設定
    document.querySelectorAll(".tab-link").forEach(tab => {
        if (tab.getAttribute("data-tab") === currentTab) {
            tab.classList.add("active");
        } else {
            tab.classList.remove("active");
        }
    });

    // タブ切り替え時の処理
    document.querySelectorAll(".tab-link").forEach(tab => {
        tab.addEventListener("click", function () {
            currentTab = this.getAttribute("data-tab");
            searchComponent.setTab(currentTab); // タブ情報を親コンポーネントに設定

            const query = searchComponent.searchBox.value.trim();

            // タブの見た目を更新
            document.querySelectorAll(".tab-link").forEach(t => t.classList.remove("active"));
            this.classList.add("active");

            // タブ変更時にリロードを強制
            const newUrl = `/search?query=${encodeURIComponent(query)}&tab=${currentTab}`;
            window.location.href = newUrl; // ページリロードを強制
        });
    });

    // 検索ボックスでエンターキーを押したときの処理
    searchComponent.searchBox.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            const query = searchComponent.searchBox.value.trim();
            if (query) {
                // タブ情報を含めたURLを生成
                const newUrl = `/search?query=${encodeURIComponent(query)}&tab=${currentTab}`;
                window.location.href = newUrl; // 正しいURLにリダイレクト
            }
        }
    });

    // 検索結果を取得（ヘッダーでJSONを要求）
    function fetchResults(tab, query) {
        fetch(`/search?query=${encodeURIComponent(query)}&tab=${tab}`, {
            headers: { Accept: "application/json" }, // ヘッダーでJSONを要求
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(() => {
                // データはHTMLテンプレートで描画されるため、ここでは何も行わない
                console.log("Results fetched successfully.");
            })
            .catch(error => {
                console.error("Error fetching results:", error);
            });
    }

    // 初期ロード時に結果を取得
    if (query) {
        console.log(`Initial load: query="${query}", tab="${currentTab}"`);
        fetchResults(currentTab, query);
    }
});
