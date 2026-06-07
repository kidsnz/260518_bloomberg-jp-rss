# Bloomberg JP RSS Feed

Yahoo!ニュースで配信中のブルームバーグ日本語版記事を30分ごとに取得し、RSSフィードとして配信する非公式ツールです。

各記事の `<link>` は **Yahoo!ニュースの記事ページ** を指します。Bloomberg.com/jp 本体は有料化されましたが、Yahoo!ニュース版は無料で読めるためです。

## 仕組み

1. `fetch_and_build.py` が Yahoo!ニュースのブルームバーグ媒体ページ（`news.yahoo.co.jp/media/bloom_st`）を取得
2. ページに埋め込まれた `__PRELOADED_STATE__` から記事一覧（見出し・Yahoo記事リンク・配信日時）を抽出（最大50件、有料記事は除外）
3. `feed.xml` としてRSS 2.0形式で出力
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

- Bloomberg / Yahoo!ニュース の利用規約上、個人利用の範囲でご使用ください
- 各記事の `<link>` は Yahoo!ニュースの記事ページへの直リンクです
- Yahoo!ニュースの記事は一定期間で削除されるため、古いリンクはリンク切れになる場合があります
- ブルームバーグ本体の特集・コラム系記事は Yahoo!ニュース(bloom_st)に配信されないことがあり、フィードに含まれない場合があります
- Yahoo!ニュースのページ構造変更によりフィードが停止する場合があります

## 過去バージョン

- `archive/fetch_and_build_googlenews.py` — Google News RSS（`site:bloomberg.com/jp`）経由で取得し、Bloomberg本体へリンクしていた旧実装（参考用）
