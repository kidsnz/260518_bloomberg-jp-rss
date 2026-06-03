# Bloomberg JP RSS Feed

Bloomberg.com/jp の日本語ニュース記事を30分ごとに取得し、RSSフィードとして配信する非公式ツールです。

## 仕組み

1. `fetch_and_build.py` が Google News RSS（`site:bloomberg.com/jp` 検索）を取得
2. タイトル末尾の ` - Bloomberg.com` を除去し、最大50件を抽出
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

- Bloomberg の利用規約上、個人利用の範囲でご使用ください
- 各記事の `<link>` は Google News のリダイレクトURLになります（Bloomberg への直リンクではありません）
- Google News RSS の仕様変更によりフィードが停止する場合があります
