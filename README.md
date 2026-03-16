# 2026_tft_japan_demo
2026 Tech Fast Track のデモコードです

## セットアップ

### 1. Python 環境

```bash
uv sync
```

### 2. Snowflake 設定

`snowflake.yml.example` をコピーして `snowflake.yml` を作成し、プレースホルダーを自分の環境に合わせて書き換えてください。

```bash
cp snowflake.yml.example snowflake.yml
```

| プレースホルダー | 説明 | 例 |
|---|---|---|
| `<YOUR_DATABASE>` | デプロイ先データベース | `MY_DB` |
| `<YOUR_SCHEMA>` | デプロイ先スキーマ | `PUBLIC` |
| `<YOUR_WAREHOUSE>` | クエリ実行用ウェアハウス | `COMPUTE_WH` |

> **注意:** `snowflake.yml` は `.gitignore` に登録されており、リポジトリにはコミットされません。

### 3. SiS デプロイ

```bash
snow streamlit deploy --replace --database <YOUR_DATABASE> --schema <YOUR_SCHEMA>
```
