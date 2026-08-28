# 1万円PJ

## 目的

1万円のGoogle検索広告で、英語圏の「東京で大人数・連泊できる宿」を探す需要を検証する。検索語句ごとの集客効率とTrip.com送客効率を明らかにする。

## 収益前提

- ADR想定: 80,000円
- 成果報酬率: 5%
- 想定売上: 1泊4,000円（宿泊日数に比例）
- 広告予算上限: 10,000円

## 主要KPI（検索語句ごと）

1. CPC = 広告費 ÷ 広告クリック数
2. Trip.com送客率 = affiliate_click ÷ 広告流入セッション数
3. Trip.com送客単価 = 広告費 ÷ affiliate_click

補助KPI: 広告CTR、施設詳細閲覧率、平均宿泊日数、予約件数、予約CPA、売上、ROAS。

## Google広告URL設定

自動タグ設定（gclid）を有効にし、「最終ページURLのサフィックス」に以下を設定する。

`utm_source=google&utm_medium=cpc&utm_campaign=1man_pj&utm_term={keyword}&utm_content={adgroupid}-{creative}&campaignid={campaignid}&adgroupid={adgroupid}&creative={creative}&keyword={keyword}&matchtype={matchtype}&device={device}&network={network}`

サイトは広告情報を30日間保存し、ad_landing、view_item、affiliate_clickへ付与する。

## 実施後PDF

検索語句別の表示・クリック・CTR・CPC、施設詳細閲覧、Trip.com送客率・送客単価、泊数・人数・端末別傾向、予約売上・CPA・ROAS、次の改善案を数枚にまとめる。予約成立はTrip.com側の成果データで確認し、affiliate_clickを予約成立と混同しない。
