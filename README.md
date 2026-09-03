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

### Getting workout files

This repo doesn't bundle real Zwift workout files — redistributing files
sourced from the internet, or extracted from Zwift's own game assets, sits
in a copyright grey area, so only the synthetic `sample_workouts/` are
included. You'll need to obtain or create your own `.zwo` files. A couple of
starting points:

- **Zwift Forums archive**: the [October 2023 Workout Refresh thread](https://forums.zwift.com/t/workout-refresh-october-2023/609799)
  links to a downloadable archive containing 1,000+ `.zwo` workouts.
- **Zwift's own installation**: the Zwift client ships
  `assets/Workouts/workouts.wad`, an archive holding roughly 2,500 workouts
  as `.xml`/`.zwo` files. It uses a proprietary compression format, so it
  needs decoding first — `tools/wad_to_zwo.py` in this repo handles both
  steps (extracting the wad, then converting the results to `.zwo`); see the
  script's docstring for usage.

Once you have files, point the `.zwo` directory at wherever you keep them,
per "Moving to production" above.

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

### ワークアウトファイルの入手方法

本リポジトリには実在のZwiftワークアウトファイルは同梱していません。インターネット上から入手したファイルや、Zwift本体のゲームアセットから抽出したファイルを再配布することは著作権上グレーな面があるため、同梱しているのは合成データである`sample_workouts/`のみです。自分の`.zwo`ファイルは各自で入手または作成してください。入手先の例:

- **Zwiftフォーラムのアーカイブ**: [Workout Refresh (October 2023)スレッド](https://forums.zwift.com/t/workout-refresh-october-2023/609799)から、1,000件を超える`.zwo`ワークアウトを含むアーカイブをダウンロードできます。
- **Zwift本体のインストールから**: Zwiftクライアントには`assets/Workouts/workouts.wad`が含まれており、約2,500件のワークアウトが`.xml`（`.zwo`）形式で格納されています。独自の圧縮形式のためデコードが必要ですが、本リポジトリの`tools/wad_to_zwo.py`が抽出・変換の両方に対応しています（使い方はスクリプト冒頭のdocstringを参照）。

入手したファイルは、上記「本番運用への移行」の手順に沿って.zwoディレクトリに指定してください。

### intervals.icu連携（任意）

**⚙ 設定**でintervals.icuのAthlete IDとAPIキーを入力すると、Zwiftカレンダーへのワークアウト登録・接続テストが可能になります。

### ライセンス

MIT — `LICENSE`を参照してください。
