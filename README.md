# Zwift Workout Selector (ZWS)

A self-hosted, single-user web app that catalogs a local library of Zwift
`.zwo` workout files, computes training metrics (TSS/IF/zone distribution/
structure) for each one, lets you search and pick workouts by those metrics,
and schedules the chosen ones onto your Zwift calendar via the Intervals.icu
API.

> 🔗 **Live demo**: A read-only demo (sample data, browse/search only —
> settings and delivery scheduling are disabled) is available at
> [zws-demo](https://zws-demo-48355139701.asia-northeast1.run.app).
>
> 🔗 **ライブデモ**: サンプルデータによる読み取り専用のデモ版を
> [こちら](https://zws-demo-48355139701.asia-northeast1.run.app) で公開しています
> （検索・閲覧のみ可能で、設定変更や配信登録はできません）。

> ⚠️ **Security note**: ZWS is designed for personal use on a trusted LAN
> and has no authentication built in — every API endpoint (search,
> settings, delivery scheduling, etc.) is reachable by anyone who can
> reach the server. **Do not expose it to the internet or any
> shared/untrusted network.**
>
> ⚠️ **セキュリティに関する注意**: ZWSは信頼できるLAN内での個人利用を前提として設計されており、認証機能は実装されていません。検索・設定・配信登録など、すべてのAPIエンドポイントはサーバーに到達できる誰からでもアクセス可能です。**インターネットや、信頼できない/共有のネットワークには公開しないでください。**

This README is in English, followed by a Japanese translation.
このREADMEは英語の後に日本語訳を掲載しています。

---

## English

### What you can do

- **Automatic analysis** — scans your `.zwo` library and computes TSS, IF,
  zone distribution, primary training type, and structure (steady/interval/
  mixed) for every workout, no manual tagging needed.
- **Fine-grained filtering** — narrow thousands of workouts down by
  duration, TSS, IF, primary type, structure, sub-types (cadence drills,
  FreeRide, ramps, sweet spot, etc.), and free-text tags, to find what fits
  in seconds.
- **Visual, at-a-glance workouts** — every workout gets a graphical power
  profile and a zone-distribution chart, so you can judge its shape without
  opening it in Zwift first.
- **One-touch push to Zwift** — schedule a workout onto your Zwift calendar
  via Intervals.icu directly from the search results, and cancel it just as
  easily.
- **Favorites and duplicate detection** — star workouts for quick access
  later, and let ZWS automatically collapse structurally-identical
  duplicates (e.g. the same session reused across weeks of a training plan)
  so they don't clutter your results.

### Requirements

- Python 3.9+
- An [Intervals.icu](https://intervals.icu) account and API key, if you want
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

### Intervals.icu integration (optional)

In **⚙ Settings**, enter your Intervals.icu Athlete ID and API key to enable
scheduling workouts onto your Zwift calendar and testing the connection.

### Notes on workout analysis

A few classification behaviors worth knowing about:

- **Pure rest-day files are hidden from search.** A `.zwo` file with no
  actual `<workout>` steps (a "complete rest day" placeholder) is always
  excluded from search results.
- **Cooldown direction is normalized.** Some `.zwo` files author a
  Cooldown's start/end power in ascending numeric order even though it
  should still play as a descending cooldown in Zwift. ZWS always treats a
  Cooldown as ending lower than it starts, regardless of how the file orders
  `PowerLow`/`PowerHigh`.
- **FreeRide sections are handled heuristically**, since they carry no
  %FTP target of their own:
  - A quiet FreeRide block (little else in the file above tempo intensity,
    at most one coaching message per block) is treated as easy recovery
    (~55%FTP).
  - A FreeRide block standing in for a hard effort (several short bursts,
    or alongside genuinely hard content elsewhere in the file) is assigned
    a representative %FTP based on its length (e.g. ~5 min → roughly
    VO2max intensity).
  - A long FreeRide block with several periodic on-screen coaching
    messages is treated as structured-but-unquantifiable and excluded from
    TSS/IF math entirely (only its duration counts). The message text
    itself is never interpreted — only structural signals (block length,
    message count/timing) decide which of these three cases applies.
- **"Sweet spot" has two separate definitions**, since where the threshold
  sits is genuinely a judgment call: `sweet_spot_loose` (a looser
  share-of-time-in-band check) and `sweet_spot_tight` (a stricter check on
  both the %FTP band and how much of the workout it dominates). Both are
  configurable from **⚙ Settings**.

### License

MIT — see `LICENSE`.

---

## 日本語

### ZWSでできること

- **自動解析** — `.zwo`ライブラリをスキャンし、全ワークアウトのTSS・IF・ゾーン分布・主タイプ・構造（持続/インターバル/複合）を自動算出。手動タグ付けは不要です。
- **きめ細かいフィルタリング** — 時間・TSS・IF・主タイプ・構造・副タイプ（ケイデンス指定、FreeRide、ランプ、スイートスポット等）、フリーテキストタグを組み合わせて、数千件の中から目的のワークアウトを数秒で絞り込めます。
- **視認性の高いグラフィカル表示** — 全ワークアウトにパワープロファイル図とゾーン分布グラフが表示されるため、Zwiftで開く前に内容を把握できます。
- **ワンタッチでZwiftへプッシュ** — 検索結果から直接、Intervals.icu経由でZwiftカレンダーへ登録。解除も同様に簡単です。
- **お気に入り登録・重複検出** — 気に入ったワークアウトにスターを付けて後から素早くアクセス。構造的に同一のワークアウト（トレーニングプラン内で複数週に再利用されているセッション等）は自動的にまとめて表示され、結果が重複で埋まりません。

### 動作要件

- Python 3.9以上
- [Intervals.icu](https://intervals.icu)のアカウントとAPIキー（Zwiftカレンダーへの登録機能を使う場合のみ必要。検索・閲覧のみなら不要）

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

### Intervals.icu連携（任意）

**⚙ 設定**でIntervals.icuのAthlete IDとAPIキーを入力すると、Zwiftカレンダーへのワークアウト登録・接続テストが可能になります。

### ワークアウト解析に関する注意事項

ZWSの分類ロジックについて、知っておくと役立つ挙動をいくつか挙げます。

- **完全休養ファイルは検索結果に表示されません。** `<workout>`内に実際のステップが定義されていない「完全休養」用の`.zwo`ファイルは、常に検索対象から除外されます。
- **クールダウンの方向は正規化されます。** 一部の`.zwo`ファイルでは、クールダウンの開始/終了パワーが数値の昇順（小さい→大きい）で記載されていることがありますが、実際にZwift上では通常どおり降順（大きい→小さい）のクールダウンとして再生されます。ZWSは`PowerLow`/`PowerHigh`の記載順によらず、クールダウンは常に「開始が高く終了が低い」ものとして扱います。
- **Free Rideセクションはヒューリスティックに解釈します。** Free Ride自体には%FTPの目標値がないためです。
  - 他のセクションがテンポ強度を超えず、各ブロックの画面メッセージが1件以下の「静かな」Free Rideは、リカバリー相当（約55%FTP）として計算に含めます。
  - 短いFree Rideが複数回連続する、またはファイル内の他のセクションが明確に高強度である場合は、そのブロックを高強度ドリルの代替と見做し、長さに応じた代表%FTPを割り当てます（例: 約5分ならVO2max相当）。
  - 長いFree Rideブロックに周期的な画面メッセージが複数付随する場合は、構造化されているが定量化が難しいドリルと判断し、TSS/IFの計算からは除外します（時間のみカウント）。メッセージの文面自体は解釈せず、ブロックの長さやメッセージの件数・タイミングといった構造的な特徴のみで、上記どの扱いになるかを判定します。
- **「スイートスポット」判定は2種類あります。** 判定基準（%FTPの範囲や、ワークアウト全体に占める時間比など）は考え方によって異なるため、緩やかな判定（`sweet_spot_loose`）と、より厳密な判定（`sweet_spot_tight`）の2種類を用意しています。いずれも**⚙ 設定**画面からカスタマイズ可能です。

### ライセンス

MIT — `LICENSE`を参照してください。
