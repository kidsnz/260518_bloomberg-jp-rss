# Bloomberg JP RSS Feed

TBS NEWS DIG「TBS CROSS DIG with Bloomberg」で配信中のブルームバーグ日本語版記事の**見出し**を30分ごとに取得し、RSSフィードとして配信する非公式ツールです。

各記事の `<link>` は **TBS NEWS DIG の記事ページ**（全文が無料で読めます）を指します。Bloomberg.com/jp 本体は有料ですが、TBS との公式提携記事は無料で読めるためです。フィードに入れるのは見出しとリンクだけで、本文は含めません。

## 仕組み

1. `fetch_and_build.py` が TBS NEWS DIG のブルームバーグ記事一覧（`newsdig.tbs.co.jp/list/withbloomberg/news/bloomberg`、最大3ページ）を取得
2. 一覧から見出し・記事リンク・配信日時を抽出（Bloomberg 配信分のみ。TBS 自社取材の記事は除外。最大50件、新しい順）
3. `feed.xml` としてRSS 2.0形式で出力（取得に失敗、または0件のときは既存の `feed.xml` を上書きせず異常終了）
4. GitHub Actions が30分ごとに実行し、変更があればコミット・プッシュ
5. GitHub Pages でフィードを公開

## セットアップ

### 1. このリポジトリをfork

### 2. GitHub Pages を有効化

`Settings` → `Pages` → `Branch: main` / `/ (root)` → Save

### 3. 手動で一度実行（初回フィード生成）

`Actions` タブ → `Update Bloomberg JP RSS Feed` → `Run workflow`

### 4. FeedlyにRSSを登録

```
https://<your-username>.github.io/<repo-name>/feed.xml
```

## ローカルで動かす場合

```bash
python fetch_and_build.py
```

## 注意

- Bloomberg / TBS NEWS DIG の利用規約上、個人利用の範囲でご使用ください（利用規約の本文は未確認です）
- 各記事の `<link>` は TBS NEWS DIG の記事ページへの直リンクです
- **ブルームバーグの全記事ではありません。** 2026年10月5〜8日の調査では、本家の約49%（270件中133件）でした。日本国内の企業・金融・政策、オピニオン（コラム）、定型の市況記事、海外の資産運用・社債・IPO、フランス・欧州の債券関連は載りにくい傾向があります
- TBS 側の更新は平日の日中が中心で、日本時間の夕方から翌朝は止まることがあります
- TBS NEWS DIG のページ構造変更によりフィードが停止する場合があります
- v2.0.0 で `guid`（記事リンク）が変わったため、リーダーによっては既存の記事が新着として再表示されます

## 過去バージョン

- **v1.x（Yahoo!ニュース版）** — Yahoo!ニュース `media/bloom_st` から取得。2026-10-01 12:38 JST を最後に配信が止まったため終了。
  - コード・最終フィード: `archive/fetch_and_build_yahoo.py` / `archive/feed_yahoo_final.xml`
  - 最終状態のブランチ: `legacy/yahoo-v1`、タグ: `v1.0.2`
- `archive/fetch_and_build_googlenews.py` — Google News RSS（`site:bloomberg.com/jp`）経由で取得し、Bloomberg本体へリンクしていた旧実装（参考用）
