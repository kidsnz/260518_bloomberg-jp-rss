# Changelog

このプロジェクトの主な変更点を記録します。
形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に従い、
バージョニングは [Semantic Versioning](https://semver.org/lang/ja/) に従います。

## [2.0.0] - 2026-10-09

### Changed
- 取得元を Yahoo!ニュース（`media/bloom_st`）から TBS NEWS DIG「TBS CROSS DIG with Bloomberg」の一覧
  （`newsdig.tbs.co.jp/list/withbloomberg/news/bloomberg`）に変更。Yahoo 側のブルームバーグ配信が
  2026-10-01 12:38 JST を最後に止まったため。
- `<link>` / `<guid>` は TBS の記事ページ（`?display=1`）になる。リーダーによっては既存記事が新着として再表示される。
- フィードには見出しとリンクのみを入れる（本文は含めない）。
- 配信日時は TBS の記事の日時から取得（旧版の「サムネURLの日付由来で未来日付になる」問題を解消）。
- 取得失敗・0件のときは既存の `feed.xml` を上書きせず異常終了するように（従来は空のフィードを書き出していた）。
- 取得は最大3回リトライ。

### Removed
- Yahoo!ニュース用の取得処理。コードと最終フィードは `archive/` に保存
  （`fetch_and_build_yahoo.py` / `feed_yahoo_final.xml`）。最終状態は `legacy/yahoo-v1` ブランチと `v1.0.2` タグ。

### Notes
- 調査（2026-10-05〜08）では本家の約49%（270件中133件）のみが載る。日本国内の企業・金融・政策、
  オピニオン、定型の市況記事などは載りにくい。

## [1.0.2] - 2026-07-20

### Fixed
- 1.0.1 のリトライ処理が `git pull --rebase` で `feed.xml` のコンフリクトを起こし、
  ワークフローが exit code 1 で失敗する問題を解消（run #1186）。
- `feed.xml` は生成物のためマージせず、`git fetch` + `git reset --hard origin/main` の上に
  生成済みファイルを置き直して commit/push する方式に変更。
- 3回試行しても push できない場合は明示的にエラー終了するように（従来はループ内の
  最終コマンドの終了状態に依存していた）。

## [1.0.1] - 2026-06-18

### Fixed
- GitHub Actions のスケジュール実行がごく稀に二重起動した際、`git push` が
  fast-forward 拒否（`! [rejected] main -> main (fetch first)`）されてワークフローが
  失敗する競合を解消。
  - `concurrency` グループ（`cancel-in-progress: false`）を追加し、同一ワークフローの
    同時実行を直列化。
  - push を `git pull --rebase --autostash` 付きの最大3回リトライに変更（保険）。

## [1.0.0] - 2026-06-07

### Added
- 現行の安定状態を基準版として確定。
- Yahoo!ニュースのブルームバーグ日本語版メディアページ
  （`news.yahoo.co.jp/media/bloom_st`）から記事を取得し `feed.xml` を生成。
  `<link>` は無料で閲覧できる Yahoo!ニュースの記事ページを指す。
- 30分ごとに `feed.xml` を更新する GitHub Actions ワークフロー（`update.yml`）。
- Google News RSS 経由（Bloomberg.com リンク）の旧実装を
  `archive/fetch_and_build_googlenews.py` に参考として保存。

[1.0.2]: https://github.com/kidsnz/260518_bloomberg-jp-rss/releases/tag/v1.0.2
[1.0.1]: https://github.com/kidsnz/260518_bloomberg-jp-rss/releases/tag/v1.0.1
[1.0.0]: https://github.com/kidsnz/260518_bloomberg-jp-rss/releases/tag/v1.0.0
