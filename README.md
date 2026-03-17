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

## SiS ダッシュボード再現プロンプト

以下のプロンプトを AI コーディングアシスタントに渡すと、`streamlit_app_sis.py` と同等のダッシュボードを再現できます。

````
TSHO_DB.TFT_DEMO_2026.MONTHLY_SALES テーブルを使って、
Streamlit in Snowflake (SiS) にデプロイ可能な月次売上ダッシュボードを作成してください。

### テーブル定義
- SALE_DATE (DATE)
- PRODUCT_CATEGORY (VARCHAR)
- REGION (VARCHAR)
- SALES_AMOUNT (NUMBER)
- UNITS_SOLD (NUMBER)
- CUSTOMER_COUNT (NUMBER)

### SiS制約（必ず守ること）
- 認証は `from snowflake.snowpark.context import get_active_session` を使う（st.connection は不可）
- Altair v4 互換にする（xOffset 不可、column ファセットで代替）
- 以下の Streamlit API は使わない:
  - st.metric(border=True)
  - st.container(horizontal=True)
  - :material/ アイコン（emoji で代替）
  - st.dataframe(hide_index=True)（df.set_index() で代替）
  - st.cache_data(show_spinner="...")（show_spinner 引数なしで使う）

### ダッシュボード構成（上から順に）
1. サイドバーフィルター: 地域（multiselect）、カテゴリ（multiselect）、年（range slider）
2. KPI行: 総売上(¥)、総販売数量、総顧客数、データ月数 を st.columns(4) で横並び
3. カテゴリ別 月次売上トレンド: Altair 折れ線グラフ（point付き、tooltip に月・カテゴリ・売上）
4. TOP N 売上ランキング: スライダーで件数選択(5〜30)、月×カテゴリ×地域で集計した売上上位を横棒グラフ（左3:右2で棒グラフとテーブルを並べる）
5. カテゴリ別 積み上げエリアチャート
6. 地域×カテゴリ比較: 左に地域別トレンド折れ線、右に地域ごとのカテゴリ別棒グラフ（column ファセット使用）
7. 詳細データテーブル: st.expander で折りたたみ

### コード品質
- ruff で Google Python Style Guide に準拠（docstring は "." で終わる、import はソート済み）
- UIラベルは日本語
- layout="wide"
- @st.cache_data(ttl=600) でデータキャッシュ
````
