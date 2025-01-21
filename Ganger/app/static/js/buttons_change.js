// document.addEventListener('DOMContentLoaded', () => {
//     // 動的にボタンを取得してイベントを登録
//     document.querySelectorAll('[data-post-id]').forEach(post => {
//         const postId = post.dataset.postId; // 投稿ID

//         // いいねボタン
//         const likeButton = document.getElementById(`like-button-${postId}`);
//         if (!likeButton) {
//             console.error(`Like button not found for post ID: ${postId}`);
//             return;
//         }
        
//         likeButton.addEventListener('click', async () => {
//             if (likeButton.disabled) {
//                 return;
//             }
//             likeButton.disabled = true; // ボタンを無効化
//             try {
//                 // SVGのpath要素を取得
//                 const svgContainer = likeButton.querySelector('.svg-container');
//                 if (!svgContainer) {
//                     console.error(`SVG container not found in like button for post ID: ${postId}`);
//                     return;
//                 }

//                 // サーバーにリクエストを送信
//                 const response = await fetch(`/like/${postId}`, { method: 'POST' });
//                 const result = await response.json();

//                 // サーバーのレスポンスに応じてSVGを切り替える
//                 if (result.status === 'added') {
//                     // いいねを追加：塗りつぶし表示
//                     svgContainer.innerHTML = `
//                         <svg viewBox="0 0 24 24" class="svg-filled" xmlns="http://www.w3.org/2000/svg">
//                             <path d="M17.5,1.917a6.4,6.4,0,0,0-5.5,3.3,6.4,6.4,0,0,0-5.5-3.3A6.8,6.8,0,0,0,0,8.967c0,4.547,4.786,9.513,8.8,12.88a4.974,4.974,0,0,0,6.4,0C19.214,18.48,24,13.514,24,8.967A6.8,6.8,0,0,0,17.5,1.917Z"></path>
//                         </svg>`;
//                 } else if (result.status === 'removed') {
//                     // いいねを解除：アウトライン表示
//                     svgContainer.innerHTML = `
//                         <svg viewBox="0 0 24 24" class="svg-outline" xmlns="http://www.w3.org/2000/svg">
//                             <path d="M17.5,1.917a6.4,6.4,0,0,0-5.5,3.3,6.4,6.4,0,0,0-5.5-3.3A6.8,6.8,0,0,0,0,8.967c0,4.547,4.786,9.513,8.8,12.88a4.974,4.974,0,0,0,6.4,0C19.214,18.48,24,13.514,24,8.967A6.8,6.8,0,0,0,17.5,1.917Zm-3.585,18.4a2.973,2.973,0,0,1-3.83,0C4.947,16.006,2,11.87,2,8.967a4.8,4.8,0,0,1,4.5-5.05A4.8,4.8,0,0,1,11,8.967a1,1,0,0,0,2,0,4.8,4.8,0,0,1,4.5-5.05A4.8,4.8,0,0,1,22,8.967C22,11.87,19.053,16.006,13.915,20.313Z"></path>
//                         </svg>`;
//                 }
//             } catch (error) {
//                 console.error('Error toggling like:', error);
//             }finally {
//                 likeButton.disabled = false; // ボタンを有効化
//             }
//         });

//         // コメントボタン
//         // const commentButton = document.getElementById(`comment-button-${postId}`);
//         // commentButton.addEventListener('click', () => {
//         //     window.location.href = `/comments/${postId}`;
//         // });
    
//         // リポストボタン
//         const repostButton = document.getElementById(`repost-button-${postId}`);
//                 if (repostButton) {
//                     // リスナーがすでに登録されていないか確認
//                     if (!repostButton.dataset.listenerAdded) {
//                         repostButton.addEventListener('click', async () => {
//                             try {
//                                 // `/repost/<postId>`にPOSTリクエストを送信
//                                 const response = await fetch(`/repost/${postId}`, { method: 'POST' });
//                                 const result = await response.json();

//                                 if (result.success) {
//                                     alert('リポストが完了しました！');
//                                     repostButton.disabled = true; // ボタンを無効化
//                                 } else {
//                                     alert(result.message || 'リポストに失敗しました。');
//                                 }
//                             } catch (error) {
//                                 console.error(`Error while reposting post ID ${postId}:`, error);
//                                 alert('リポスト処理中にエラーが発生しました。');
//                             }
//                         });
//                         repostButton.dataset.listenerAdded = "true"; // リスナーが追加されたことを記録
//                     }
//                 } else {
//                     console.error(`Repost button not found for post ID: ${postId}`);
//                 }
            

//         // 保存ボタン
//         const SaveButton = document.getElementById(`save-button-${postId}`);
//         if (SaveButton) {
//             // リスナーがすでに登録されていないか確認
//             if (!SaveButton.dataset.listenerAdded) {
//                 SaveButton.addEventListener('click', async () => {
//                     SaveButton.disabled = true; // ボタンを無効化
//                     try {
//                         // `/save_post/<postId>`にPOSTリクエストを送信
//                         const response = await fetch(`/save_post/${postId}`, { method: 'POST' });
//                         if (!response.ok) {
//                             throw new Error(`HTTP error! status: ${response.status}`);
//                         }
//                         const result = await response.json();

//                         // サーバーのレスポンスに基づいてUIを更新
//                         if (result.success) {
//                             if (result.status === 'added') {
//                                 alert('SAVE_POSTが完了しました！');
//                                 SaveButton.classList.add('saved'); // 保存済みを示すスタイルを適用
//                             } else if (result.status === 'removed') {
//                                 alert('SAVE_POSTが解除されました！');
//                                 SaveButton.classList.remove('saved'); // 保存済みスタイルを解除
//                             }
//                         } else {
//                             alert(result.message || 'SAVE_POSTに失敗しました。');
//                         }
//                     } catch (error) {
//                         console.error(`Error while saving post ID ${postId}:`, error);
//                         alert('SAVE_POST処理中にエラーが発生しました。');
//                     } finally {
//                         SaveButton.disabled = false; // 成功/失敗に関わらず有効化
//                     }
//                 });
//                 SaveButton.dataset.listenerAdded = "true"; // リスナーが追加されたことを記録
//             }
//         } else {
//             console.error(`Save button not found for post ID: ${postId}`);
//         }

        
//     });
// })

document.addEventListener('DOMContentLoaded', () => {
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
                } finally {
                    button.disabled = false;
                }
            });
        }
    }

    // 各投稿の処理を初期化
    document.querySelectorAll('[data-post-id]').forEach(post => {
        const postId = post.dataset.postId;

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
            }
        );

        // リポストボタンの処理
        setupButtonAction(
            `repost-button-${postId}`,
            `/repost/${postId}`,
            (result, button) => {
                if (result.success) {
                    alert('リポストが完了しました！');
                    button.disabled = true;
                } else {
                    alert(result.message || 'リポストに失敗しました。');
                }
            }
        );

        // 保存ボタンの処理
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
                }
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
});
