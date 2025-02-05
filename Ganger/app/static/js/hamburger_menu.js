class HamburgerMenu {
    constructor() {
        this.menu = document.querySelector('.main-menu');
        this.init();
    }

    init() {
        // メニューの展開・収縮のイベントリスナー
        this.menu.addEventListener('mouseenter', () => {
            this.menu.style.width = '250px';
        });

        this.menu.addEventListener('mouseleave', () => {
            this.menu.style.width = '55px';
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new HamburgerMenu();
});