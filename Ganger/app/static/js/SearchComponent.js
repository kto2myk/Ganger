class SearchComponent {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.searchBox = this.container.querySelector("#search-box");
        this.searchResults = this.container.querySelector("#search-results");
        this.searchCandidates = this.container.querySelector("#search-candidates");
        this.searchHistoryContainer = this.container.querySelector("#search-history-container");
        this.searchHistoryEmpty = this.container.querySelector("#search-history-empty");
        this.searchHistoryList = this.container.querySelector("#search-history-list");
        this.clearHistoryBtn = this.container.querySelector("#clear-history-btn");
        this.clearSearchBtn = this.container.querySelector("#clear-search-btn");

        this.timeout = null;
        this.searchHistory = JSON.parse(localStorage.getItem("searchHistory")) || [];
        this.apiEndpoint = options.apiEndpoint || "/search"; // 統一されたエンドポイント
        this.currentTab = "USER"; // 初期タブ

        this.init();
    }

    setTab(tab) {
        this.currentTab = tab;
    }

    init() {
        this.updateSearchHistory();
        this.attachEventListeners();
        this.loadQueryFromUrl();
    }

    loadQueryFromUrl() {
        const params = new URLSearchParams(window.location.search);
        const query = params.get("query");
        if (query) {
            this.searchBox.value = query;
        }
    }

    updateSearchHistory() {
        if (this.searchHistory.length === 0) {
            this.searchHistoryEmpty.style.display = "block";
            this.searchHistoryList.style.display = "none";
            this.clearHistoryBtn.style.display = "none";
        } else {
            this.searchHistoryEmpty.style.display = "none";
            this.searchHistoryList.style.display = "block";
            this.clearHistoryBtn.style.display = "inline-block";

            this.searchHistoryList.innerHTML = this.searchHistory
                .map((item, index) => `
                    <div>
                        <span data-query="${item}" class="history-item">${item}</span>
                        <button data-index="${index}" class="delete-item-btn">×</button>
                    </div>`
                ).join("");

            this.searchHistoryList.querySelectorAll(".history-item").forEach((item) => {
                item.addEventListener("click", () => {
                    const query = item.getAttribute("data-query");
                    if (query) {
                        window.location.href = `/search?query=${encodeURIComponent(query)}&tab=${this.currentTab}`;
                    }
                });
            });

            this.searchHistoryList.querySelectorAll(".delete-item-btn").forEach((btn) => {
                btn.addEventListener("click", () => {
                    const index = parseInt(btn.getAttribute("data-index"), 10);
                    this.searchHistory.splice(index, 1);
                    localStorage.setItem("searchHistory", JSON.stringify(this.searchHistory));
                    this.updateSearchHistory();
                });
            });
        }
    }

    attachEventListeners() {
        this.searchBox.addEventListener("focus", () => {
            this.updateSearchHistory();
            this.searchHistoryContainer.style.display = "block";
            document.getElementById("search-results-container").classList.add("results-active");
        });

        this.searchBox.addEventListener("input", () => {
            clearTimeout(this.timeout);
            const query = this.searchBox.value.trim();
            if (query) {
                this.timeout = setTimeout(() => this.fetchCandidates(query), 500);
                this.searchHistoryContainer.style.display = "none";
            } else {
                this.searchResults.style.display = "none";
                this.searchHistoryContainer.style.display = "block";
                this.updateSearchHistory();
            }
        });

        this.searchBox.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                const query = this.searchBox.value.trim();
                if (query) {
                    this.saveToSearchHistory(query);
                    window.location.href = `/search?query=${encodeURIComponent(query)}&tab=${this.currentTab}`;
                }
            }
        });

        this.clearHistoryBtn.addEventListener("click", () => {
            this.searchHistory = [];
            localStorage.removeItem("searchHistory");
            this.updateSearchHistory();
        });

        this.clearSearchBtn.addEventListener("click", () => {
            this.searchBox.value = "";
            this.searchResults.style.display = "none";
        });

         // 画面外クリックで検索履歴・候補ボックスを閉じる
        document.addEventListener("click", (event) => {
            if (!this.searchBox.contains(event.target) &&
                !this.searchResults.contains(event.target) &&
                !this.searchCandidates.contains(event.target) &&
                !this.searchHistoryContainer.contains(event.target)) {
                this.searchResults.style.display = "none";
                this.searchCandidates.style.display = "none";
                this.searchHistoryContainer.style.display = "none";
            }
        });
    }

    async fetchCandidates(query) {
        try {
            const url = `${this.apiEndpoint}?query=${encodeURIComponent(query)}&tab=${this.currentTab}`;
            const response = await fetch(url, {
                headers: { Accept: "application/json" }, // ヘッダーでJSONを要求
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.displayCandidates(data);

            this.searchResults.style.display = "block";
            this.searchCandidates.style.display = "block"; 
        } catch (error) {
            console.error("Error fetching search candidates:", error);
            this.searchCandidates.innerHTML = `<li style="color: red;">候補の取得に失敗しました。</li>`;
            this.searchResults.style.display = "block";
        }
    }

    displayCandidates(data) {
        let candidates = [];
    
        // タブごとに候補を選択
        if (this.currentTab === "USER") {
            candidates = data.users || []; // USERタブの候補
        } else if (this.currentTab === "TAG") {
            candidates = data.tags || []; // TAGタブの候補
        } else if (this.currentTab === "CATEGORY") {
            candidates = data.categories || []; // CATEGORYタブの候補
        }
    
        console.log("Current Tab:", this.currentTab, "Candidates:", candidates); // デバッグログ
    
         // 件数 (post_count) の多い順にソート
        candidates.sort((a, b) => (b.post_count || 0) - (a.post_count || 0));

        // 候補リストを生成
        this.searchCandidates.innerHTML = candidates.length
            ? candidates.map(item => {
                let displayText = "不明な項目";  // 表示テキストのデフォルト値
                let dataId = "不明なID";          // data-id のデフォルト値
                let countText = item.post_count ? ` (${item.post_count}件)` : "";  // カウントテキスト
    
                if (this.currentTab === "USER") {
                    const userId = item.user_id || "不明なユーザー";
                    const userName = item.username || "";
                    dataId = item.id || "不明なID";
                    displayText = `${userId} (${userName})`;
                } else if (this.currentTab === "TAG") {
                    displayText = item.tag_text || "不明なタグ";
                    dataId = item.post_id || "不明なID";
                } else if (this.currentTab === "CATEGORY") {
                    displayText = item.category_name || "不明なカテゴリ";
                    dataId = item.category_id || "不明なID";
                }
    
                // data-query属性に件数なしのタグ名をセットし、リスト要素を作成
                return `<li data-id="${dataId}" data-query="${displayText}">${displayText}${countText}</li>`;
            }).join("")
            : "<li>候補がありません</li>";
    
        this.searchResults.style.display = "block";
        this.attachCandidateClickListeners();
    }

    attachCandidateClickListeners() {
        this.searchCandidates.querySelectorAll("li").forEach((candidate) => {
            candidate.addEventListener("click", () => {
                const id = candidate.getAttribute("data-id"); // 候補のIDを取得
                const rawQuery = candidate.getAttribute("data-query");  // 件数なしのクエリを取得
                const cleanQuery = rawQuery.trim();  // 余分な空白を削除

                if (this.currentTab === "USER") {
                    if (id) {
                        window.location.href = `/my_profile/${id}`;
                    }
                } else if (this.currentTab === "TAG" || this.currentTab === "CATEGORY") {
                    if (cleanQuery) {
                        this.saveToSearchHistory(cleanQuery);  // 履歴保存時も件数なし
                        window.location.href = `/search?query=${encodeURIComponent(cleanQuery)}&tab=${this.currentTab}`;
                    }
                }
            });
        });
    }        

    saveToSearchHistory(query) {
        const cleanQuery = query.replace(/\s\(\d+件\)$/, ""); // 件数 (X件) を削除
        if (!this.searchHistory.includes(cleanQuery) && cleanQuery.trim() !== "") {
            this.searchHistory.push(cleanQuery);
            localStorage.setItem("searchHistory", JSON.stringify(this.searchHistory));
            this.updateSearchHistory();
        }
    }
    }
document.addEventListener("DOMContentLoaded", () => {
    window.searchComponent = new SearchComponent("search-container", {
        apiEndpoint: "/search" // 統一エンドポイント
    });
});

document.addEventListener("click", (event) => {
    if (event.target.id === "search-candidates") {
        document.getElementById("search-candidates").style.display = "none";
    }
})
