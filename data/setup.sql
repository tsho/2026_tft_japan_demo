-- =============================================================================
-- setup.sql
-- MONTHLY_SALES テーブルと関連リソースのセットアップ
--
-- 使い方:
--   1. <YOUR_*> プレースホルダーを自分の環境に合わせて置換する
--   2. ACCOUNTADMIN またはリソース作成権限のあるロールで実行する
--   3. CSVデータのロードは最後のセクションを参照
-- =============================================================================

-- =====================
-- 変数（環境に合わせて変更）
-- =====================
SET db_name     = 'TFT_DEMO_DB';        -- <YOUR_DATABASE>
SET schema_name = 'TFT_DEMO_2026';      -- <YOUR_SCHEMA>
SET wh_name     = 'TFT_DEMO_WH';        -- <YOUR_WAREHOUSE>
SET role_name   = 'TFT_DEMO_ROLE';      -- <YOUR_ROLE>

-- =====================
-- ウェアハウス作成
-- =====================
USE ROLE SYSADMIN;

CREATE WAREHOUSE IF NOT EXISTS IDENTIFIER($wh_name)
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND   = 60
    AUTO_RESUME    = TRUE;

-- =====================
-- データベース・スキーマ作成
-- =====================
CREATE DATABASE IF NOT EXISTS IDENTIFIER($db_name);
CREATE SCHEMA IF NOT EXISTS IDENTIFIER($db_name || '.' || $schema_name);

-- =====================
-- ロール作成と権限付与
-- =====================
USE ROLE SECURITYADMIN;

CREATE ROLE IF NOT EXISTS IDENTIFIER($role_name);
GRANT ROLE IDENTIFIER($role_name) TO ROLE SYSADMIN;

-- DB/Schema/Warehouse の権限
GRANT USAGE ON DATABASE IDENTIFIER($db_name) TO ROLE IDENTIFIER($role_name);
GRANT USAGE ON SCHEMA IDENTIFIER($db_name || '.' || $schema_name) TO ROLE IDENTIFIER($role_name);
GRANT ALL PRIVILEGES ON SCHEMA IDENTIFIER($db_name || '.' || $schema_name) TO ROLE IDENTIFIER($role_name);
GRANT USAGE ON WAREHOUSE IDENTIFIER($wh_name) TO ROLE IDENTIFIER($role_name);

-- =====================
-- テーブル作成
-- =====================
USE ROLE IDENTIFIER($role_name);
USE WAREHOUSE IDENTIFIER($wh_name);
USE SCHEMA IDENTIFIER($db_name || '.' || $schema_name);

CREATE TABLE IF NOT EXISTS MONTHLY_SALES (
    SALE_DATE        DATE,
    PRODUCT_CATEGORY VARCHAR(50),
    REGION           VARCHAR(30),
    SALES_AMOUNT     NUMBER(12, 2),
    UNITS_SOLD       NUMBER(38, 0),
    CUSTOMER_COUNT   NUMBER(38, 0)
);

-- =====================
-- CSV データロード
-- =====================
-- 方法1: SnowSQL / Snow CLI からの PUT + COPY
--
--   PUT file://data/monthly_sales.csv @%MONTHLY_SALES AUTO_COMPRESS=TRUE;
--
--   COPY INTO MONTHLY_SALES
--       FROM @%MONTHLY_SALES
--       FILE_FORMAT = (
--           TYPE            = 'CSV'
--           SKIP_HEADER     = 1
--           FIELD_OPTIONALLY_ENCLOSED_BY = '"'
--           DATE_FORMAT     = 'YYYY-MM-DD'
--       )
--       ON_ERROR = 'ABORT_STATEMENT';

-- 方法2: Snowsight の UI から CSV をアップロード
--   1. Snowsight > Data > Databases > TFT_DEMO_DB > TFT_DEMO_2026 > MONTHLY_SALES
--   2. "Load Data" からCSVファイルを選択

-- =====================
-- データ確認
-- =====================
-- SELECT COUNT(*) FROM MONTHLY_SALES;                -- 675 rows
-- SELECT * FROM MONTHLY_SALES ORDER BY SALE_DATE LIMIT 10;
