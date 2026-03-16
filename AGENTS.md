# SiS (Streamlit in Snowflake) デプロイ時の注意点

このドキュメントは、ローカルStreamlitアプリをSiSにデプロイする際に遭遇した問題と対処法をまとめたものです。

---

## 1. 認証方法: `st.connection()` は使えない

**問題:** SiS環境（非コンテナランタイム）のStreamlitバージョンは古く、`st.connection("snowflake")` が存在しない。

**対処:**
```python
from snowflake.snowpark.context import get_active_session
session = get_active_session()
df = session.sql("SELECT ...").to_pandas()
```

SiSでは認証は自動的に行われるため、アカウント/ユーザー/パスワードの指定は不要。

---

## 2. Altair v4 制約: `xOffset` は使えない

**問題:** SiS環境のAltairはv4（Vega-Lite v4）。`xOffset`はAltair v5（Vega-Lite v5）で追加されたため、グループ化棒グラフで `xOffset="category:N"` を使うとエラーになる。

**エラー:**
```
SchemaValidationError: Additional properties are not allowed ('xOffset' was unexpected)
```

**対処:** `column` によるファセット表示で代替する。
```python
# NG (Altair v5)
alt.Chart(df).mark_bar().encode(
    x="region:N",
    y="value:Q",
    color="category:N",
    xOffset="category:N",
)

# OK (Altair v4互換)
alt.Chart(df).mark_bar().encode(
    x="category:N",
    y="value:Q",
    color="category:N",
    column="region:N",
).properties(width=120)
```

---

## 3. Streamlit API差異: 新しいウィジェットオプションが使えない

**問題:** SiSのStreamlitは最新版ではないため、以下のAPIが使えない。

| 使えないAPI | 代替方法 |
|------------|---------|
| `st.metric(border=True)` | `st.metric()` (borderなし) |
| `st.container(horizontal=True)` | `st.columns()` で横並び |
| `:material/icon_name:` アイコン | emoji (`:chart_with_upwards_trend:` など) |
| `st.column_config.NumberColumn(format=...)` | シンプルな `st.dataframe()` |
| `st.cache_data(show_spinner="...")` | `st.cache_data(ttl=600)` |
| `st.dataframe(hide_index=True)` | `st.dataframe(df.set_index("col"))` |

---

## 4. Snow CLIバージョン: `runtime_name` 非対応の場合がある

**問題:** Snow CLI v3.9.1では `snowflake.yml` の `runtime_name` フィールドが未サポート。

**エラー:**
```
Extra inputs are not permitted. You provided field 'runtime_name' with value 'SYSTEM$ST_CONTAINER_RUNTIME_PY3_11'
```

**対処:** `runtime_name` を `snowflake.yml` から削除する。コンテナランタイムを使いたい場合はSnow CLI v3.14.0以上にアップグレードするか、`uvx --from snowflake-cli snow streamlit deploy --replace` で最新版を使う。

---

## 5. Snowflake接続: PAT (Programmatic Access Token) の使い方

**問題:** PATトークンは `authenticator="oauth"` + `token=` ではなく、`password=` として渡す。

**エラー (oauth指定時):**
```
DatabaseError: 250001 (08001): Invalid OAuth access token
```

**対処:**
```python
snowflake.connector.connect(
    account=ACCOUNT,
    user=USER,
    password=PAT_TOKEN,  # PATはpasswordとして渡す
    role=ROLE,
)
```

---

## 6. Snow CLIデプロイ時: セッションにDB/Schemaが未設定

**問題:** 接続にデフォルトのdatabase/schemaが設定されていないと、ステージ作成で失敗する。

**エラー:**
```
Cannot perform CREATE STAGE. This session does not have a current database.
```

**対処:** デプロイコマンドに `--database` と `--schema` を明示する。
```bash
snow streamlit deploy --replace --database TSHO_DB --schema TFT_DEMO_2026
```

---

## 7. ファイル削除後の再デプロイ: ソースファイルの存在確認

**問題:** Snowflake側のStreamlitアプリを削除しても、`snow streamlit deploy` はローカルのソースファイル（`snowflake.yml` の `artifacts` に記載されたファイル）が存在しないとデプロイできない。ローカルのPythonファイルも削除されていた場合、デプロイ時に以下のエラーになる。

**エラー:**
```
No match was found for the specified source in the project directory: streamlit_app_sis.py
```

**対処:** デプロイ前に `snowflake.yml` の `artifacts` に列挙されたファイルがローカルに存在するか確認する。存在しなければ再作成してからデプロイする。

---

## 8. `SHOW STREAMLITS` でデプロイ状態を確認する

**問題:** `snow streamlit deploy` が成功したように見えても、実際にはSnowflake側にオブジェクトが作られていないことがある（削除済みステージへの差分アップロードのみ実行されるケース等）。

**対処:** デプロイ後に必ず確認する。
```sql
SHOW STREAMLITS IN SCHEMA TSHO_DB.TFT_DEMO_2026;
```

---

## 9. ruff lint: Google style guide の設定

**問題:** `ruff` をデフォルト設定で入れただけでは Google Python Style Guide に準拠しない。後からルールを追加すると修正箇所が増える。

**対処:** 最初から `pyproject.toml` に以下を設定しておく。
```toml
[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "D", "UP", "B", "A", "C4", "SIM"]
ignore = ["D100", "D104"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.per-file-ignores]
"streamlit_app*.py" = ["D103"]
```

**よく引っかかるポイント:**
- `D415`: docstring の1行目は `.` `?` `!` で終わる必要がある（日本語でも）
- `I001`: import の並び順（`ruff check --fix` で自動修正可能）
- `D103`: 公開関数にはdocstringが必要（Streamlitスクリプトでは per-file-ignores で除外）

---

## 10. git: コミットすべきでないファイルの管理

**問題:** 機密情報や環境固有のファイルを誤ってコミットしてしまうリスクがある。また、学習メモやローカル用スクリプトもリポジトリに入れるべきではない。

**対処:** プロジェクト開始時に `.gitignore` を整備する。
```gitignore
# Snowflake（環境固有の設定）
snowflake.yml
.streamlit/secrets.toml

# ローカルメモ・作業ファイル
output/
```

テンプレートファイル（`snowflake.yml.example`）は実際の値をプレースホルダーに置き換えてコミットする。

---

## 11. snowflake.yml.example: プレースホルダーの運用

**問題:** `snowflake.yml` にはDB名やウェアハウス名など環境固有の値が入る。そのままコミットすると他の開発者が使えない、もしくは機密情報が漏れる。

**対処:**
1. `snowflake.yml` を `.gitignore` に追加
2. `snowflake.yml.example` をプレースホルダー付きで作成してコミット
3. README.md にセットアップ手順を記載

```yaml
# snowflake.yml.example
identifier:
  name: MONTHLY_SALES_DASHBOARD
  database: <YOUR_DATABASE>
  schema: <YOUR_SCHEMA>
query_warehouse: <YOUR_WAREHOUSE>
```

---

## チェックリスト: SiSデプロイ前の確認事項

- [ ] `get_active_session()` でセッション取得しているか
- [ ] Altair v4互換のAPIのみ使っているか (`xOffset` 不可)
- [ ] Streamlit新しめのAPI (`border`, `horizontal`, `:material/`) を使っていないか
- [ ] `snowflake.yml` にSnow CLIバージョン非対応のフィールドがないか
- [ ] デプロイコマンドに `--database` / `--schema` を指定しているか
