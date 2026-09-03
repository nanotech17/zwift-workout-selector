# Zwift Workout Selector (ZWS)

A self-hosted, single-user web app that catalogs a local library of Zwift
`.zwo` workout files, computes training metrics (TSS/IF/zone distribution/
structure) for each one, lets you search and pick workouts by those metrics,
and schedules the chosen ones onto your Zwift calendar via the intervals.icu
API.

This README is in English, followed by a Japanese translation.
このREADMEは英語の後に日本語訳を掲載しています。

---

## English

### Requirements

- Python 3.11+
- An [intervals.icu](https://intervals.icu) account and API key, if you want
  to schedule workouts onto your calendar (optional — search/browse works
  without it)

### Setup

```bash
git clone <this repo>
cd workout-selector
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Quick start (try it with sample data)

This repo bundles `sample_workouts/` — 150 synthetically generated `.zwo`
files (see `tools/generate_sample_workouts.py`) covering the full range of
searchable metrics, tagged `sample` so you can filter them out later. They
exist so you can try every feature immediately after cloning, without first
tracking down real workout files.

1. Start the server:
   ```bash
   .venv/bin/uvicorn workout_selector.web:app --host 0.0.0.0 --port 8000
   ```
2. Open `http://localhost:8000` in a browser.
3. Open **⚙ Settings**, set the `.zwo` directory to `<repo>/sample_workouts`,
   and click **Rescan (Full)**.
4. Search and browse — every filter (duration/TSS/IF/primary type/structure/
   sub-types) has matching sample data to try it against.

### Moving to production

Once you have your own `.zwo` files:

1. In **⚙ Settings**, either point the `.zwo` directory at your own workout
   folder, or copy `sample_workouts/` into a subfolder of it so both are
   scanned together, then **Rescan (Full)**.
2. Check **"Exclude sample workouts from search"** in Settings — this hides
   everything tagged `sample` from search results without deleting anything,
   so you can turn it back off later if you want to see the samples again.

   Note: switching the `.zwo` directory to somewhere that no longer contains
   the sample files does *not* remove their rows from the catalog by itself
   (the scanner only prunes files missing from whatever directory you're
   currently pointed at) — the "exclude" setting is what actually keeps them
   out of your results.

### intervals.icu integration (optional)

In **⚙ Settings**, enter your intervals.icu Athlete ID and API key to enable
scheduling workouts onto your Zwift calendar and testing the connection.

### License

MIT — see `LICENSE`.

---

## 日本語

### 動作要件

- Python 3.11以上
- [intervals.icu](https://intervals.icu)のアカウントとAPIキー（Zwiftカレンダーへの登録機能を使う場合のみ必要。検索・閲覧のみなら不要）

### セットアップ

```bash
git clone <このリポジトリ>
cd workout-selector
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### クイックスタート（サンプルデータで試す）

このリポジトリには`sample_workouts/`（150件の自動生成`.zwo`ファイル。生成方法は`tools/generate_sample_workouts.py`参照）を同梱しています。検索可能な各指標を幅広くカバーしており、`sample`タグが付いているため後から除外できます。クローン直後に、実際のワークアウトファイルを用意しなくても全機能を試せます。

1. サーバーを起動:
   ```bash
   .venv/bin/uvicorn workout_selector.web:app --host 0.0.0.0 --port 8000
   ```
2. ブラウザで`http://localhost:8000`を開く。
3. **⚙ 設定**を開き、.zwoディレクトリを`<リポジトリ>/sample_workouts`に設定し、**再スキャン(全件)**を実行。
4. 検索・閲覧してみてください。時間/TSS/IF/主タイプ/構造/副タイプ、いずれの条件にも対応するサンプルデータがあります。

### 本番運用への移行

自分の`.zwo`ファイルを用意できたら：

1. **⚙ 設定**で.zwoディレクトリを自分のワークアウトフォルダに変更するか、`sample_workouts/`をそのフォルダのサブフォルダとしてコピーして両方が同時にスキャンされるようにし、**再スキャン(全件)**を実行。
2. 設定画面の「**サンプルワークアウトを検索対象から除外する**」をON。これは`sample`タグの付いたワークアウトを検索結果から隠すだけで削除はしないため、後で再度OFFにすれば見えるようになります。

   注意: .zwoディレクトリをサンプルファイルが存在しない場所に切り替えるだけでは、カタログ上のレコードは自動削除されません（スキャナは現在指定中のディレクトリ配下に存在しないファイルのみを削除対象とするため）。実際に検索結果から除外するには、上記の「除外する」設定が必要です。

### intervals.icu連携（任意）

**⚙ 設定**でintervals.icuのAthlete IDとAPIキーを入力すると、Zwiftカレンダーへのワークアウト登録・接続テストが可能になります。

### ライセンス

MIT — `LICENSE`を参照してください。
