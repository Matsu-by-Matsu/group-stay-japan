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

scripts/build-home-v15.py — トップページ（英語・韓国語・繁体字）の新しいデザイン部分を config/home-v15.json から作る。文言や数字を直すときは config/home-v15.json を直して再実行する。build-home-locales.py や build-city-pages.py を実行したときは、最後にこれを実行する

scripts/build-real-beds-v16.py — データ記事（/en/real-beds/・/ja/real-beds/）の本文を config/real-beds-v16.json と config/home-v15.json から作る。scripts/build-real-beds.py を実行したときは、そのあとにこれを実行する

scripts/fix-official-links.py — ホテルの公式サイトへのリンクを減らす（施設ページの出典は1か所だけ小さく、東京のページの公式ページの列は消す、残りは新しいタブ）。施設ページ・東京のページ・トップを作り直すスクリプトを実行したときは、いちばん最後にこれを実行する
