document.addEventListener('DOMContentLoaded', () => {
    // 動的にボタンを取得してイベントを登録
    document.querySelectorAll('[data-post-id]').forEach(post => {
        const postId = post.dataset.postId; // 投稿ID

        // いいねボタン
        const likeButton = document.getElementById(`like-button-${postId}`);
        if (!likeButton) {
            console.error(`Like button not found for post ID: ${postId}`);
            return;
        }
        
        likeButton.addEventListener('click', async () => {
            if (likeButton.disabled) {
                return;
            }
            likeButton.disabled = true; // ボタンを無効化
            try {
                // SVGのpath要素を取得
                const svgContainer = likeButton.querySelector('.svg-container');
                if (!svgContainer) {
                    console.error(`SVG container not found in like button for post ID: ${postId}`);
                    return;
                }

                // サーバーにリクエストを送信
                const response = await fetch(`/like/${postId}`, { method: 'POST' });
                const result = await response.json();

                // サーバーのレスポンスに応じてSVGを切り替える
                if (result.status === 'added') {
                    // いいねを追加：塗りつぶし表示
                    svgContainer.innerHTML = `
                        <svg viewBox="0 0 24 24" class="svg-filled" xmlns="http://www.w3.org/2000/svg">
                            <path d="M17.5,1.917a6.4,6.4,0,0,0-5.5,3.3,6.4,6.4,0,0,0-5.5-3.3A6.8,6.8,0,0,0,0,8.967c0,4.547,4.786,9.513,8.8,12.88a4.974,4.974,0,0,0,6.4,0C19.214,18.48,24,13.514,24,8.967A6.8,6.8,0,0,0,17.5,1.917Z"></path>
                        </svg>`;
                } else if (result.status === 'removed') {
                    // いいねを解除：アウトライン表示
                    svgContainer.innerHTML = `
                        <svg viewBox="0 0 24 24" class="svg-outline" xmlns="http://www.w3.org/2000/svg">
                            <path d="M17.5,1.917a6.4,6.4,0,0,0-5.5,3.3,6.4,6.4,0,0,0-5.5-3.3A6.8,6.8,0,0,0,0,8.967c0,4.547,4.786,9.513,8.8,12.88a4.974,4.974,0,0,0,6.4,0C19.214,18.48,24,13.514,24,8.967A6.8,6.8,0,0,0,17.5,1.917Zm-3.585,18.4a2.973,2.973,0,0,1-3.83,0C4.947,16.006,2,11.87,2,8.967a4.8,4.8,0,0,1,4.5-5.05A4.8,4.8,0,0,1,11,8.967a1,1,0,0,0,2,0,4.8,4.8,0,0,1,4.5-5.05A4.8,4.8,0,0,1,22,8.967C22,11.87,19.053,16.006,13.915,20.313Z"></path>
                        </svg>`;
                }
            } catch (error) {
                console.error('Error toggling like:', error);
            }finally {
                likeButton.disabled = false; // ボタンを有効化
            }
        });

        // コメントボタン
        // const commentButton = document.getElementById(`comment-button-${postId}`);
        // commentButton.addEventListener('click', () => {
        //     window.location.href = `/comments/${postId}`;
        // });
    
        // リポストボタン
        const repostButton = document.getElementById(`repost-button-${postId}`);
                if (repostButton) {
                    // リスナーがすでに登録されていないか確認
                    if (!repostButton.dataset.listenerAdded) {
                        repostButton.addEventListener('click', async () => {
                            try {
                                // `/repost/<postId>`にPOSTリクエストを送信
                                const response = await fetch(`/repost/${postId}`, { method: 'POST' });
                                const result = await response.json();

                                if (result.success) {
                                    alert('リポストが完了しました！');
                                    repostButton.disabled = true; // ボタンを無効化
                                } else {
                                    alert(result.message || 'リポストに失敗しました。');
                                }
                            } catch (error) {
                                console.error(`Error while reposting post ID ${postId}:`, error);
                                alert('リポスト処理中にエラーが発生しました。');
                            }
                        });
                        repostButton.dataset.listenerAdded = "true"; // リスナーが追加されたことを記録
                    }
                } else {
                    console.error(`Repost button not found for post ID: ${postId}`);
                }
            });
        // 保存ボタン
        const saveButton = document.getElementById(`save-button-${postId}`);
        saveButton.addEventListener('click', async () => {
            try {
            const response = await fetch(`/api/save/${postId}`, { method: 'POST' });
            const result = await response.json();
            if (result.status === 'saved') {
                saveButton.classList.add('saved');
            } else if (result.status === 'unsaved') {
                saveButton.classList.remove('saved');
            }
            } catch (error) {
            console.error('Error saving post:', error);
            }
        });
    });