document.getElementById('payment-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const lastname = document.getElementById('lastname').value;
    const firstname = document.getElementById('firstname').value;
    const lastnameKana = document.getElementById('lastname-kana').value;
    const firstnameKana = document.getElementById('firstname-kana').value;
    const address = document.getElementById('address').value;
    
    // 既存のカード情報
    const cardNumber = document.getElementById('card-number').value;
    const expiry = document.getElementById('expiry').value;
    const cvv = document.getElementById('cvv').value;
    const name = document.getElementById('name').value;

    if (validatePersonalInfo(lastname, firstname, lastnameKana, firstnameKana, address) 
        && validateForm(cardNumber, expiry, cvv, name)) {
        // ここに実際の決済処理を実装
        alert('決済処理を実行します');
    }
});

function validatePersonalInfo(lastname, firstname, lastnameKana, firstnameKana, address) {
    if (lastname.trim() === '' || firstname.trim() === '') {
        alert('氏名を入力してください');
        return false;
    }
    
    if (!/^[\u30A0-\u30FF]+$/.test(lastnameKana) || !/^[\u30A0-\u30FF]+$/.test(firstnameKana)) {
        alert('フリガナは全角カタカナで入力してください');
        return false;
    }
    
    if (address.trim() === '') {
        alert('住所を入力してください');
        return false;
    }
    
    return true;
}

function validateForm(cardNumber, expiry, cvv, name) {
    if (!/^\d{16}$/.test(cardNumber)) {
        alert('カード番号が無効です');
        return false;
    }
    
    if (!/^\d{2}\/\d{2}$/.test(expiry)) {
        alert('有効期限の形式が不正です');
        return false;
    }
    
    if (!/^\d{3,4}$/.test(cvv)) {
        alert('セキュリティコードが無効です');
        return false;
    }
    
    if (name.trim() === '') {
        alert('カード名義人を入力してください');
        return false;
    }
    
    return true;
}
