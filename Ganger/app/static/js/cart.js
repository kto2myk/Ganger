document.getElementById('dummy-data-btn').addEventListener('click', function() {
    // ダミーデータの設定
    document.getElementById('card-number').value = '4242424242424242';
    document.getElementById('card-name').value = 'TARO YAMADA';
    document.getElementById('card-month').value = '12';
    document.getElementById('card-year').value = '25';
    document.getElementById('card-security').value = '123';
});

document.addEventListener('DOMContentLoaded', function() {
    const selectAllCheckbox = document.getElementById('select-all');
    const itemCheckboxes = document.querySelectorAll('.item-checkbox');
    const totalAmountElement = document.getElementById('total-amount');
    const selectedCountElement = document.getElementById('selected-count');
    const checkoutBtn = document.getElementById('checkout-btn');

    function updateTotal() {
        let total = 0;
        let selectedCount = 0;
        itemCheckboxes.forEach(checkbox => {
            if (checkbox.checked) {
                const price = parseFloat(checkbox.closest('.cart-item').dataset.price);
                total += price;
                selectedCount++;
            }
        });
        totalAmountElement.textContent = `￥${total.toLocaleString()}`;
        selectedCountElement.textContent = selectedCount;
        checkoutBtn.disabled = selectedCount === 0;
    }

    selectAllCheckbox.addEventListener('change', function() {
        itemCheckboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
        });
        updateTotal();
    });

    itemCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            selectAllCheckbox.checked = Array.from(itemCheckboxes)
                .every(cb => cb.checked);
            updateTotal();
        });
    });

    // 数量変更ボタンの処理
    document.querySelectorAll('.quantity-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            const cartItem = this.closest('.cart-item');
            const itemId = cartItem.querySelector('.item-checkbox').value;
            const isIncrease = this.classList.contains('increase-btn');
            const change = isIncrease ? 1 : -1;

            const quantityDisplay = cartItem.querySelector('.quantity-display');
            const currentQuantity = parseInt(quantityDisplay.textContent);

            if (currentQuantity + change < 1) {
                return; // 数量が1未満にならないようにする
            }

            try {
                const response = await fetch('/update_cart_quantity', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ item_id: itemId, newQuantity: currentQuantity + change })
                });

                if (response.ok) {
                    const data = await response.json();
                    const newQuantity = currentQuantity + change;
                    quantityDisplay.textContent = newQuantity;

                    // 合計金額の更新
                    const unitPrice = parseFloat(cartItem.querySelector('.item-unit-price').textContent.replace('￥', '').replace(',', ''));
                    const newPrice = unitPrice * newQuantity;
                    cartItem.querySelector('.item-price').textContent = `￥${newPrice.toLocaleString()}`;
                    cartItem.dataset.price = newPrice;
                    updateTotal();
                } else {
                    console.error('数量更新に失敗しました');
                }
            } catch (error) {
                console.error('数量更新エラー:', error);
            }
        });
    });

    // 削除ボタンの処理
    document.querySelectorAll('.remove-btn').forEach(btn => {
        btn.addEventListener('click', async function() {
            if (confirm('この商品をカートから削除しますか？')) {
                const cartItem = this.closest('.cart-item');
                const productId = cartItem.dataset.product_id
                const itemPrice = parseFloat(cartItem.dataset.price);
                try {
                    const response = await fetch('/remove_from_cart', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ product_id: productId })
                    });

                    if (response.ok) {
                        cartItem.remove();
                    
                        // 合計金額の更新
                        const totalAmountElement = document.getElementById('total-amount');
                        const currentTotal = parseFloat(totalAmountElement.textContent.replace('￥', '').replace(/,/g, ''));
                        const newTotal = currentTotal - itemPrice;
                        totalAmountElement.textContent = `￥${newTotal.toLocaleString()}`;

                        // 選択されている商品数の更新
                        const selectedCountElement = document.getElementById('selected-count');
                        const currentCount = parseInt(selectedCountElement.textContent);
                        selectedCountElement.textContent = currentCount - 1;

                        // カートが空になった場合
                        if (document.querySelectorAll('.cart-item').length === 0) {
                            location.reload(); // ページをリロードして空のカート表示に
                        }
                    } else {
                        console.error('削除に失敗しました');
                    }
                } catch (error) {
                    console.error('削除エラー:', error);
                }
            }
        });
    });

    // 初期表示時の合計計算
    updateTotal();
});