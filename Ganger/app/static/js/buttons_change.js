// 共通のAPIリクエスト処理
async function handleRequest(url, method = 'POST') {
    const response = await fetch(url, { method });
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
}

// ボタンに対する共通のイベント設定
function setupButtonAction(buttonId, actionUrl, onSuccess) {
    const button = document.getElementById(buttonId);
    if (button) {
        button.addEventListener('click', async () => {
            if (button.disabled) return; // ボタンが無効化されていたらスキップ
            button.disabled = true;
            try {
                const result = await handleRequest(actionUrl);
                onSuccess(result, button);
            } catch (error) {
                console.error(`Error with button ${buttonId}:`, error);
                alert('操作中にエラーが発生しました。');
            }
        });
    }
}

export function initializePostButtons(postStatuses) {
    // 各投稿の処理を初期化
    document.querySelectorAll(".post_buttons button").forEach(post => {
        const postId = post.dataset.postId || post.closest('.post_buttons')?.dataset.postId;
        if (!postId) return;

        // ✅ コメントモーダルの取得 & バリデーション設定
        setupCommentValidation(postId);

        // ✅ プロダクトモーダルの取得 & バリデーション設定
        setupProductValidation(postId);

        // postStatuses 配列から対応する投稿データを探す
        const postStatus = postStatuses.find(status => status.postId === postId) || {};
        const liked = postStatus.liked || false;
        const saved = postStatus.saved || false;
        const reposted = postStatus.reposted || false;
        const productized = postStatus.productized || false;  

        // いいねボタンの処理
        setupButtonAction(
            `like-button-${postId}`,
            `/like/${postId}`,
            (result, button) => {
                const svgContainer = button.querySelector('.svg-container');
                if (!svgContainer) return;

                // いいね状態のSVG切り替え
                if (result.status === 'added') {
                    svgContainer.innerHTML = `
                        <svg viewBox="0 0 24 24" class="svg-filled" xmlns="http://www.w3.org/2000/svg">
                            <path d="M17.5,1.917a6.4,6.4,0,0,0-5.5,3.3,6.4,6.4,0,0,0-5.5-3.3A6.8,6.8,0,0,0,0,8.967c0,4.547,4.786,9.513,8.8,12.88a4.974,4.974,0,0,0,6.4,0C19.214,18.48,24,13.514,24,8.967A6.8,6.8,0,0,0,17.5,1.917Z"></path>
                        </svg>`;
                } else if (result.status === 'removed') {
                    svgContainer.innerHTML = `
                        <svg viewBox="0 0 24 24" class="svg-outline" xmlns="http://www.w3.org/2000/svg">
                            <path d="M17.5,1.917a6.4,6.4,0,0,0-5.5,3.3,6.4,6.4,0,0,0-5.5-3.3A6.8,6.8,0,0,0,0,8.967c0,4.547,4.786,9.513,8.8,12.88a4.974,4.974,0,0,0,6.4,0C19.214,18.48,24,13.514,24,8.967A6.8,6.8,0,0,0,17.5,1.917Zm-3.585,18.4a2.973,2.973,0,0,1-3.83,0C4.947,16.006,2,11.87,2,8.967a4.8,4.8,0,0,1,4.5-5.05A4.8,4.8,0,0,1,11,8.967a1,1,0,0,0,2,0,4.8,4.8,0,0,1,4.5-5.05A4.8,4.8,0,0,1,22,8.967C22,11.87,19.053,16.006,13.915,20.313Z"></path>
                        </svg>`;
                }
            button.disabled = false;
            }
        );

        // リポストボタンの処理

        // ✅ リポストボタンを無効化
        const repostButton = document.getElementById(`repost-button-${postId}`);
        if (repostButton && reposted) {
            repostButton.classList.add('reposted');
        }
        
        setupButtonAction(
            `repost-button-${postId}`,
            `/repost/${postId}`,
            (result, button) => {
                if (result.status === 'added') {
                    alert('リポストが完了しました！');
                    button.classList.add('reposted');
                } else if (result.status === 'removed') {
                    alert('リポストを解除しました！');
                    button.classList.remove('reposted');
                } else {
                    alert(result.message || 'リポストに失敗しました。');
                } button.disabled = false;
            }
        );

        // 保存ボタンの処理
        // ✅ 保存ボタンに `saved` クラスを追加
        const saveButton = document.getElementById(`save-button-${postId}`);
        if (saveButton && saved) {
            saveButton.classList.add('saved');
        }
        
        setupButtonAction(
            `save-button-${postId}`,
            `/save_post/${postId}`,
            (result, button) => {
                if (result.success) {
                    if (result.status === 'added') {
                        alert('保存が完了しました！');
                        button.classList.add('saved');
                    } else if (result.status === 'removed') {
                        alert('保存を解除しました！');
                        button.classList.remove('saved');
                    }
                } button.disabled = false;
            }
        );

        // コメントモーダルの処理
        const commentButton = document.getElementById(`comment-button-${postId}`);
        const commentModal = document.getElementById(`comment-modal-${postId}`);
        const closeCommentModal = commentModal?.querySelector('.close');

        if (commentButton && commentModal && closeCommentModal) {
            // コメントボタンでモーダルを開く
            commentButton.addEventListener('click', () => {
                commentModal.style.display = 'block';
            });

            // モーダルを閉じるボタンで閉じる
            closeCommentModal.addEventListener('click', () => {
                commentModal.style.display = 'none';
            });

            // モーダル外をクリックして閉じる
            window.addEventListener('click', (event) => {
                if (event.target === commentModal) {
                    commentModal.style.display = 'none';
                }
            });
        }
        // プロダクトボタンの処理
        const productButton = document.getElementById(`product-button-${postId}`);

        // ✅ プロダクト化ボタンを無効化
        if (productButton && productized) {
            productButton.style.display = "none";
            productButton.style.pointerEvents = "none";
        }

        const productModal = document.getElementById(`product-modal-${postId}`);
        const closeProductModal = productModal?.querySelector('.close');
    
        if (productButton && productModal && closeProductModal) {
            // プロダクトボタンをクリックしてモーダルを開く
            productButton.addEventListener('click', () => {
                productModal.style.display = 'block';
            });
    
            // モーダルを閉じるボタンで閉じる
            closeProductModal.addEventListener('click', () => {
                productModal.style.display = 'none';
            });
    
            // モーダル外をクリックして閉じる
            window.addEventListener('click', (event) => {
                if (event.target === productModal) {
                    productModal.style.display = 'none';
                }
            });
        }

    });
}

// **📝 コメントモーダルのバリデーション**
function setupCommentValidation(postId) {
    const commentInput = document.getElementById(`comment-input-${postId}`);
    const submitButton = document.getElementById(`comment-submit-${postId}`);

    if (!commentInput || !submitButton) return;

    function validateComment() {
        if (commentInput.value.trim() === "") {
            submitButton.disabled = true; // 🚫 送信不可
            submitButton.style.opacity = "0.5";
        } else {
            submitButton.disabled = false; // ✅ 送信可能
            submitButton.style.opacity = "1";
        }
    }

    // 初回適用
    validateComment();

    // 入力ごとにバリデーションを適用
    commentInput.addEventListener("input", validateComment);
}

// **📝 プロダクトモーダルのバリデーション**
function setupProductValidation(postId) {
    const priceInput = document.getElementById(`price-box-${postId}`);
    const nameInput = document.getElementById(`name-box-${postId}`);
    const submitButton = document.getElementById(`product-submit-${postId}`);

    if (!priceInput || !nameInput || !submitButton) return;

    function validateProductForm() {
        let isValid = true;

        // ✅ 価格は半角数字のみ許容（空白も禁止）
        if (!/^\d+$/.test(priceInput.value.trim())) {
            isValid = false;
            priceInput.classList.add("error");
        } else {
            priceInput.classList.remove("error");
        }

        // ✅ 商品名は空白禁止
        if (nameInput.value.trim() === "") {
            isValid = false;
            nameInput.classList.add("error");
        } else {
            nameInput.classList.remove("error");
        }

        // **バリデーション結果でボタンを有効/無効化**
        if (!isValid) {
            submitButton.disabled = true; // 🚫 送信不可
            submitButton.style.opacity = "0.5";
        } else {
            submitButton.disabled = false; // ✅ 送信可能
            submitButton.style.opacity = "1";
        }
    }

    // 初回適用
    validateProductForm();

    // 入力ごとにバリデーションを適用
    priceInput.addEventListener("input", validateProductForm);
    nameInput.addEventListener("input", validateProductForm);
}
