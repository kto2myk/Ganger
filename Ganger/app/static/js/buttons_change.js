document.addEventListener('DOMContentLoaded', () => {
    // 動的にボタンを取得してイベントを登録
    document.querySelectorAll('[data-post-id]').forEach(post => {
    const postId = post.dataset.postId;

    // いいねボタン
    const likeButton = document.getElementById(`like-button-${postId}`);
    if (!likeButton) {
    console.error(`Like button not found for post ID: ${postId}`);
    return;
    }

    likeButton.addEventListener('click', async () => {
    try {
        // SVGのpath要素を取得
        const path = likeButton.querySelector('svg path');
        if (!path) {
        console.error(`SVG path not found in like button for post ID: ${postId}`);
        return;
        }

        // サーバーにリクエストを送信
        const response = await fetch(`/like/${postId}`, { method: 'POST' });
        const result = await response.json();

        // サーバーのレスポンスに応じて塗りつぶしを変更
        if (result.status === 'added') {
        path.setAttribute('fill', 'red'); // 塗りつぶしを赤に変更
        } else if (result.status === 'removed') {
        path.setAttribute('fill', 'black'); // 塗りつぶしを黒に変更
        }
    } catch (error) {
        console.error('Error toggling like:', error);
    }
    });

        // コメントボタン
        const commentButton = document.getElementById(`comment-button-${postId}`);
        commentButton.addEventListener('click', () => {
            window.location.href = `/comments/${postId}`;
        });
    
        // リポストボタン
        const repostButton = document.getElementById(`repost-button-${postId}`);
        repostButton.addEventListener('click', async () => {
            try {
            const response = await fetch(`/api/repost/${postId}`, { method: 'POST' });
            const result = await response.json();
            if (result.success) {
                alert('リポストが完了しました！');
            }
            } catch (error) {
            console.error('Error reposting:', error);
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
    });
    