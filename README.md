# GROUP STAY JAPAN

Apartment hotels for groups and longer stays in Japan

[Visit GROUP STAY JAPAN](https://groupstayjapan.synthx.jp/)

- [Home](https://groupstayjapan.synthx.jp/)
- [Tokyo apartment hotels for 4 guests](https://groupstayjapan.synthx.jp/en/tokyo/hotels-for-4-guests/)
- [Tokyo apartments for 6 guests](https://groupstayjapan.synthx.jp/en/tokyo/hotels-for-6-guests/)
- [Tokyo group accommodation for 8 guests](https://groupstayjapan.synthx.jp/en/tokyo/hotels-for-8-guests/)
- [Tokyo apartment hotels for longer stays](https://groupstayjapan.synthx.jp/en/tokyo/apartment-hotels-for-longer-stays/)

生成のあと最後に `python scripts/apply-v10.py --date YYYY-MM-DD` を実行する。

生成のあとに `python scripts/build-home-locales.py --date YYYY-MM-DD` を実行する。

scripts/build-city-pages.py — 大阪・京都・福岡の都市ページ（en/ko/zh-tw）を config/city-rooms.json と config/city-pages.json から作る。施設ページのパンくず・トップのリンク・サイトマップも直す

scripts/apply-room-cards.py — 施設ページの部屋カード（4言語）を config/room-cards.json と config/room-card-labels.json から作る。カードの中身を直すときは config/room-cards.json を直して再実行する
