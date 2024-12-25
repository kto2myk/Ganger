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
        } catch (error) {
            console.error("Error fetching search candidates:", error);
            this.searchCandidates.innerHTML = `<li style="color: red;">候補の取得に失敗しました。</li>`;
            this.searchResults.style.display = "block";
        }
    }

    displayCandidates(data) {
        const candidates = this.currentTab === "USER" ? data.users || [] : data.items || [];
        this.searchCandidates.innerHTML = candidates.length
            ? candidates.map(item => `<li data-id="${item.id}">${item.name || item.username} (${item.user_id || item.id})</li>`).join("")
            : "<li>候補がありません</li>";

        this.searchResults.style.display = "block";
        this.attachCandidateClickListeners();
    }

    attachCandidateClickListeners() {
        this.searchCandidates.querySelectorAll("li").forEach((candidate) => {
            candidate.addEventListener("click", () => {
                const id = candidate.getAttribute("data-id");
                if (id) {
                    if (this.currentTab === "USER") {
                        window.location.href = `/my_profile/${id}`;
                    } else if (this.currentTab === "TAG") {
                        window.location.href = `/tag_overview/${id}`;
                    } else if (this.currentTab === "CATEGORY") {
                        window.location.href = `/category_overview/${id}`;
                    }
                }
            });
        });
    }

    saveToSearchHistory(query) {
        if (!this.searchHistory.includes(query) && query.trim() !== "") {
            this.searchHistory.push(query);
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
