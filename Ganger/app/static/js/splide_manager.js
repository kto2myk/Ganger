export let splideInstances = {}; // Splideのインスタンスを管理する辞書

export function initializeSplide(targetSelector = ".splide") {
    document.querySelectorAll(targetSelector).forEach(function (carousel) {
        // すでに適用済みのSplideがあれば一旦破棄
        if (splideInstances[carousel.id]) {
            splideInstances[carousel.id].destroy();
        }

        let slideCount = carousel.querySelectorAll(".splide__slide").length;

        let splideOptions = {
            type: "loop",
            perPage: 1,
            pagination: slideCount > 1, // 画像1枚ならインジケーター非表示
            arrows: slideCount > 1,     // 画像1枚なら矢印も非表示
        };

        // Splideを初期化して管理
        splideInstances[carousel.id] = new Splide(carousel, splideOptions);
        splideInstances[carousel.id].mount();
    });
}
