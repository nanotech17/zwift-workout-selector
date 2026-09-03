// --- i18n ---------------------------------------------------------------
// Two-language (ja/en) dictionary. Domain/technical vocabulary that reads
// naturally in English even on Japanese sites (TSS, IF, FTP, VO2max, tag
// names, workout titles, primary-type/structure enum values such as
// "endurance"/"interval") is intentionally left untranslated and has no
// entry here — see workout-selector.md owner note (2026-09).
const I18N = {
  ja: {
    "header.settings": "⚙ 設定",

    "settings.title": "設定",
    "settings.data_source": "データソース",
    "settings.zwo_dir_label": ".zwoディレクトリ",
    "settings.save": "保存",
    "settings.rescan_diff": "再スキャン(差分)",
    "settings.rescan_full": "再スキャン(全件)",
    "settings.hide_sample_tag": "サンプルワークアウトを検索対象から除外する",
    "settings.ingest_errors": "取り込みエラー一覧",
    "settings.intervals_integration": "Intervals.icu連携",
    "settings.api_key": "APIキー",
    "settings.api_key_placeholder": "新しいキーを入力して保存（既存の値は表示されません）",
    "settings.test_connection": "接続テスト",
    "settings.zone_classification": "ゾーン分類（境界値・配色）",
    "settings.reflect_hint": "保存しただけでは既存データには反映されません。保存後は「再スキャン(全件)」を実行してください。",
    "settings.show_defaults": "既定値(Zwift準拠)を表示",
    "settings.show_defaults_plain": "既定値を表示",
    "settings.tuning_title": "分類ロジックの詳細設定",
    "settings.sweet_spot_h4": "Sweet Spot（副タイプ <code>sweetspot_loose</code>）",
    "settings.sweet_spot_low": "下限(%FTP)",
    "settings.sweet_spot_high": "上限(%FTP)",
    "settings.sweet_spot_tag_min_pct": "タグ付与の最低滞在率(%)",
    "settings.sweetspot_h4": "Sweet Spot（副タイプ <code>sweetspot_tight</code>・厳格版、tempo/thresholdにのみ適用）",
    "settings.ss_low": "SS帯 下限(%FTP)",
    "settings.ss_high": "SS帯 上限(%FTP)",
    "settings.high_frac": "HIGH判定(%FTP超)",
    "settings.recovery_frac": "easy recovery(%FTP未満)",
    "settings.min_minutes": "SS_TIME最低(分)",
    "settings.ss_ratio_min": "SS/WORK最低(%)",
    "settings.high_ratio_max": "HIGH/WORK上限(%)",
    "settings.structure_h4": "構造分類",
    "settings.interval_structure_threshold": "インターバル判定 時間比(%)",
    "settings.vi_interval_threshold": "VI interval閾値",
    "settings.vi_mixed_threshold": "VI mixed閾値",
    "settings.cadence_h4": "ケイデンス・極端パワー",
    "settings.high_cadence_rpm": "高ケイデンス(rpm以上)",
    "settings.low_cadence_rpm": "低ケイデンス(rpm以下)",
    "settings.extreme_power_frac": "極端パワー無視(%FTP超)",

    "settings.status.dir_unset": "未設定です。パスを入力して保存してください。",
    "settings.status.dir_missing": "⚠ このパスは現在見つかりません",
    "settings.status.dir_ok": "有効なディレクトリです",
    "settings.status.key_set": "(設定済み)",
    "settings.status.key_unset": "(未設定)",
    "settings.status.no_scan_yet": "まだスキャンを実行していません。",
    "settings.status.last_scan": "最終スキャン: {at}（{mode}）— 走査{scanned}件 / 解析{analyzed}件 / スキップ{skipped}件 / 削除{removed}件 / エラー{errors}件",
    "settings.mode_full": "全件",
    "settings.mode_diff": "差分",
    "settings.status.scan_running": "スキャン中...(件数によっては数秒〜十数秒かかります)",
    "settings.status.scan_failed": "スキャン失敗: {msg}",
    "settings.status.scan_done": "完了 — 走査{scanned}件 / 解析{analyzed}件 / スキップ{skipped}件 / 削除{removed}件 / エラー{errors}件",
    "settings.status.save_failed": "保存に失敗しました: {msg}",
    "settings.status.saved_rescan_hint": "保存しました。既存データへ反映するには「再スキャン(全件)」を実行してください。",
    "settings.status.defaults_shown": "既定値を表示しました（保存ボタンを押すまで反映されません）",
    "settings.status.checking": "確認中...",
    "settings.status.conn_failed": "接続失敗: {msg}",
    "settings.status.conn_success": "接続成功 (athlete: {name})",
    "settings.errors_count": "({n}件)",
    "settings.errors_none": "エラーはありません。",
    "settings.zone_upper": "上限",
    "settings.zone_upper_none": "上限なし",

    "search.title": "検索条件",
    "search.toggle_collapse": "▲",
    "search.toggle_expand": "▼",
    "search.duration_min": "時間(分)",
    "search.primary_type": "主タイプ",
    "search.sub_type": "副タイプ",
    "search.structure": "構造",
    "search.zone_emphasis": "ゾーン強調 Z",
    "search.zone_min_pct": "滞在率 ≥",
    "search.flags": "フラグ",
    "search.cadence": "ケイデンス指定",
    "search.high_cadence": "高ケイデンス(≥100rpm)",
    "search.low_cadence": "低ケイデンス(≤70rpm)",
    "search.warmup": "ウォームアップ",
    "search.cooldown": "クールダウン",
    "search.opt_yes": "あり",
    "search.opt_no": "なし",
    "search.tags": "タグ",
    "search.name_query": "ワークアウト名",
    "search.name_query_placeholder": "部分一致で検索",
    "search.tags_placeholder": "クリックして追加、またはカンマ区切りで入力",
    "search.target_duration": "目標時間(分)",
    "search.target_tss": "目標TSS",
    "search.limit": "件数",
    "search.include_duplicates": "重複(同一内容)を含める",
    "search.favorites_only": "お気に入りのみ",
    "search.submit": "検索",
    "search.clear": "検索条件クリア",

    "results.title": "候補",
    "results.sort_by": "並べ替え:",
    "results.sort_default": "検索順(目標への近さ)",
    "results.sort_duration": "合計時間",
    "results.count": "(全{matched}件中 {start}〜{end}件目を表示)",
    "results.empty": "該当するワークアウトが見つかりませんでした。検索条件を緩めてみてください。",
    "results.asc": "昇順 ▲",
    "results.desc": "降順 ▼",
    "results.page_prev": "前へ",
    "results.page_next": "次へ",
    "results.page_indicator": "{page} / {total} ページ",
    "card.details": "詳細",
    "card.close": "閉じる",
    "card.register": "登録",
    "card.scheduled": "配信予定あり",
    "card.scheduled_dates": "配信予定: {dates}",
    "card.favorite_on": "お気に入り解除",
    "card.favorite_off": "お気に入りに追加",

    "deliveries.title": "配信状況(Intervals.icu登録済み)",
    "deliveries.refresh": "更新",
    "deliveries.empty": "登録中のワークアウトはありません。",
    "deliveries.remove": "解除",
    "deliveries.remove_confirm": "解除してよろしいですか？",
    "deliveries.remove_failed": "解除に失敗しました: {msg}",
    "deliveries.sync_failed": "Intervals.icuとの同期に失敗しました: {msg}",

    "deliver_dialog.title_prefix": "登録:",
    "deliver_dialog.date": "日付",
    "deliver_dialog.time": "時刻(任意)",
    "deliver_dialog.submit": "登録",
    "deliver_dialog.cancel": "キャンセル",
    "deliver.replace_confirm_suffix": "\n\n既存の登録を削除して置き換えますか？",
    "deliver.failed": "登録に失敗しました: {msg}",
    "deliver.success": "登録しました",

    "detail.primary_type": "主タイプ:",
    "detail.structure": "構造:",
    "detail.tags": "タグ:",
    "detail.overview": "ワークアウト概要",
    "detail.duration": "時間:",
    "detail.zone_distribution": "ゾーン分布",
    "detail.loading": "読み込み中...",

    "step.freeride_label": "FreeRide（目標なし）",
    "step.maxeffort_label": "MaxEffort（全力）",

    "unit.min": "分",
    "unit.sec": "秒",
  },
  en: {
    "header.settings": "⚙ Settings",

    "settings.title": "Settings",
    "settings.data_source": "Data Source",
    "settings.zwo_dir_label": ".zwo Directory",
    "settings.save": "Save",
    "settings.rescan_diff": "Rescan (Diff)",
    "settings.rescan_full": "Rescan (Full)",
    "settings.hide_sample_tag": "Exclude sample workouts from search",
    "settings.ingest_errors": "Ingest Errors",
    "settings.intervals_integration": "Intervals.icu Integration",
    "settings.api_key": "API Key",
    "settings.api_key_placeholder": "Enter a new key to save (existing value is hidden)",
    "settings.test_connection": "Test Connection",
    "settings.zone_classification": "Zone Classification (Boundaries & Colors)",
    "settings.reflect_hint": "Saving alone does not update existing data. Run “Rescan (Full)” afterward to apply it.",
    "settings.show_defaults": "Show Defaults (Zwift Standard)",
    "settings.show_defaults_plain": "Show Defaults",
    "settings.tuning_title": "Classification Logic — Detailed Settings",
    "settings.sweet_spot_h4": "Sweet Spot (sub-type <code>sweetspot_loose</code>)",
    "settings.sweet_spot_low": "Lower bound (%FTP)",
    "settings.sweet_spot_high": "Upper bound (%FTP)",
    "settings.sweet_spot_tag_min_pct": "Min. time-in-zone for tag (%)",
    "settings.sweetspot_h4": "Sweet Spot (sub-type <code>sweetspot_tight</code> — strict, tempo/threshold only)",
    "settings.ss_low": "SS range lower (%FTP)",
    "settings.ss_high": "SS range upper (%FTP)",
    "settings.high_frac": "HIGH threshold (above %FTP)",
    "settings.recovery_frac": "Easy recovery (below %FTP)",
    "settings.min_minutes": "Min. SS_TIME (min)",
    "settings.ss_ratio_min": "Min. SS/WORK (%)",
    "settings.high_ratio_max": "Max. HIGH/WORK (%)",
    "settings.structure_h4": "Structure Classification",
    "settings.interval_structure_threshold": "Interval-detection time ratio (%)",
    "settings.vi_interval_threshold": "VI interval threshold",
    "settings.vi_mixed_threshold": "VI mixed threshold",
    "settings.cadence_h4": "Cadence & Extreme Power",
    "settings.high_cadence_rpm": "High cadence (rpm and above)",
    "settings.low_cadence_rpm": "Low cadence (rpm and below)",
    "settings.extreme_power_frac": "Ignore extreme power (above %FTP)",

    "settings.status.dir_unset": "Not set. Enter a path and save.",
    "settings.status.dir_missing": "⚠ This path was not found",
    "settings.status.dir_ok": "Valid directory",
    "settings.status.key_set": "(set)",
    "settings.status.key_unset": "(not set)",
    "settings.status.no_scan_yet": "No scan has been run yet.",
    "settings.status.last_scan": "Last scan: {at} ({mode}) — scanned {scanned} / analyzed {analyzed} / skipped {skipped} / removed {removed} / errors {errors}",
    "settings.mode_full": "full",
    "settings.mode_diff": "diff",
    "settings.status.scan_running": "Scanning... (may take a few seconds to over a minute depending on file count)",
    "settings.status.scan_failed": "Scan failed: {msg}",
    "settings.status.scan_done": "Done — scanned {scanned} / analyzed {analyzed} / skipped {skipped} / removed {removed} / errors {errors}",
    "settings.status.save_failed": "Failed to save: {msg}",
    "settings.status.saved_rescan_hint": "Saved. Run “Rescan (Full)” to apply it to existing data.",
    "settings.status.defaults_shown": "Defaults shown (not applied until you press Save)",
    "settings.status.checking": "Checking...",
    "settings.status.conn_failed": "Connection failed: {msg}",
    "settings.status.conn_success": "Connected (athlete: {name})",
    "settings.errors_count": "({n})",
    "settings.errors_none": "No errors.",
    "settings.zone_upper": "Upper bound",
    "settings.zone_upper_none": "None",

    "search.title": "Search Criteria",
    "search.toggle_collapse": "▲",
    "search.toggle_expand": "▼",
    "search.duration_min": "Duration (min)",
    "search.primary_type": "Primary Type",
    "search.sub_type": "Sub Type",
    "search.structure": "Structure",
    "search.zone_emphasis": "Zone Emphasis Z",
    "search.zone_min_pct": "Time in zone ≥",
    "search.flags": "Flags",
    "search.cadence": "Cadence specified",
    "search.high_cadence": "High cadence (≥100rpm)",
    "search.low_cadence": "Low cadence (≤70rpm)",
    "search.warmup": "Warmup",
    "search.cooldown": "Cooldown",
    "search.opt_yes": "Yes",
    "search.opt_no": "No",
    "search.tags": "Tags",
    "search.name_query": "Workout Name",
    "search.name_query_placeholder": "Search by partial match",
    "search.tags_placeholder": "Click to add, or type comma-separated",
    "search.target_duration": "Target duration (min)",
    "search.target_tss": "Target TSS",
    "search.limit": "Limit",
    "search.include_duplicates": "Include duplicates (identical content)",
    "search.favorites_only": "Favorites only",
    "search.submit": "Search",
    "search.clear": "Clear Criteria",

    "results.title": "Candidates",
    "results.sort_by": "Sort by:",
    "results.sort_default": "Search order (closest to target)",
    "results.sort_duration": "Total duration",
    "results.count": "(showing {start}-{end} of {matched})",
    "results.empty": "No matching workouts found. Try loosening your search filters.",
    "results.asc": "Asc ▲",
    "results.desc": "Desc ▼",
    "results.page_prev": "Prev",
    "results.page_next": "Next",
    "results.page_indicator": "Page {page} of {total}",
    "card.details": "Details",
    "card.close": "Close",
    "card.register": "Register",
    "card.scheduled": "Scheduled",
    "card.scheduled_dates": "Scheduled: {dates}",
    "card.favorite_on": "Remove from favorites",
    "card.favorite_off": "Add to favorites",

    "deliveries.title": "Delivery Status (registered on Intervals.icu)",
    "deliveries.refresh": "Refresh",
    "deliveries.empty": "No workouts currently registered.",
    "deliveries.remove": "Remove",
    "deliveries.remove_confirm": "Remove this delivery?",
    "deliveries.remove_failed": "Failed to remove: {msg}",
    "deliveries.sync_failed": "Failed to sync with Intervals.icu: {msg}",

    "deliver_dialog.title_prefix": "Register:",
    "deliver_dialog.date": "Date",
    "deliver_dialog.time": "Time (optional)",
    "deliver_dialog.submit": "Register",
    "deliver_dialog.cancel": "Cancel",
    "deliver.replace_confirm_suffix": "\n\nDelete the existing registration and replace it?",
    "deliver.failed": "Failed to register: {msg}",
    "deliver.success": "Registered.",

    "detail.primary_type": "Primary type:",
    "detail.structure": "Structure:",
    "detail.tags": "Tags:",
    "detail.overview": "Workout Overview",
    "detail.duration": "Duration:",
    "detail.zone_distribution": "Zone Distribution",
    "detail.loading": "Loading...",

    "step.freeride_label": "FreeRide (no target)",
    "step.maxeffort_label": "MaxEffort (all-out)",

    "unit.min": "min",
    "unit.sec": "s",
  },
};

let LANG = localStorage.getItem("lang") === "en" ? "en" : "ja";

function t(key, vars) {
  let s = (I18N[LANG] && I18N[LANG][key]) ?? I18N.ja[key] ?? key;
  if (vars) for (const k in vars) s = s.split(`{${k}}`).join(vars[k]);
  return s;
}

function applyStaticI18n() {
  document.documentElement.lang = LANG;
  document.querySelectorAll("[data-i18n]").forEach(el => {
    el.innerHTML = t(el.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });
  document.querySelectorAll(".lang-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.lang === LANG);
  });
}

// Re-renders everything whose text was built dynamically in JS (and thus
// isn't covered by the data-i18n sweep above) after a language switch.
function refreshDynamicI18n() {
  updateResultCountLabel();
  const sortDirBtn = document.getElementById("sort-dir");
  sortDirBtn.textContent = t(sortDirBtn.dataset.dir === "desc" ? "results.desc" : "results.asc");
  setSearchFormCollapsed(document.getElementById("search-form").hidden);
  renderResults();
  renderPagination();
  loadDeliveries();
  if (!document.getElementById("settings-panel").hidden) loadSettings();
}

document.querySelectorAll(".lang-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    if (btn.dataset.lang === LANG) return;
    LANG = btn.dataset.lang;
    localStorage.setItem("lang", LANG);
    applyStaticI18n();
    refreshDynamicI18n();
  });
});

// --- zones / metrics rendering ------------------------------------------
// Defaults match settings.py's DEFAULT_ZONE_BOUNDS/DEFAULT_ZONE_COLORS —
// used only until loadConfig() below overwrites them with the settings
// screen's current values (GET /api/config), so a slow/failed fetch still
// renders something correct rather than blank.
let ZONE_BOUNDS = [[1, 0.60], [2, 0.75], [3, 0.89], [4, 1.04], [5, 1.18], [6, null]];
// Mirrors metrics.py's ZONE_BOUNDARY_TOLERANCE — a value authored a hair
// over a zone boundary (e.g. 75.45%FTP, which displays rounded as "75%")
// still reads as the lower zone. Without this, the chart's per-step color
// (zoneOf, below) could disagree with the zone-distribution bar for the
// exact same step (found via "Phase 1.2 - Strength Endurance Rotations #1"'s
// 75.45%FTP interval: distribution counted it Z2, chart painted it Z3's
// green). 2026-09.
const ZONE_BOUNDARY_TOLERANCE = 0.005;
let ZONE_COLOR = {1: "#9aa0a6", 2: "#4c8bf5", 3: "#34a853", 4: "#fbbc04", 5: "#ff9800", 6: "#ea4335"};
// Zone names are established Zwift/training vocabulary — left untranslated
// in both languages (workout-selector.md owner note, 2026-09).
const ZONE_NAME = {1: "Recovery", 2: "Endurance", 3: "Tempo", 4: "Threshold", 5: "VO2max", 6: "Anaerobic"};
// Power target readings above this are clamped for bar HEIGHT only (a few
// workouts use e.g. 300% as an "ignore the number, go all-out" placeholder
// — see metrics.py EXTREME_POWER_FRAC); the true value still shows on hover.
const MAX_DISPLAY_FRAC = 1.6;
const CHART_H = 60;
const CADENCE_Y = CHART_H + 4;
const CADENCE_H = 5;
const VIEWBOX_H = CADENCE_Y + CADENCE_H;
let svgGradientSeq = 0;

// Mirrors metrics.py's _zone_of, reading the same configurable ZONE_BOUNDS
// (owner's settings-screen values, or the Zwift-reference default above).
function zoneOf(p) {
  if (p < ZONE_BOUNDS[0][1] + ZONE_BOUNDARY_TOLERANCE) return 1;  // zone 1 is exclusive at its top
  for (let i = 1; i < ZONE_BOUNDS.length; i++) {
    const upper = ZONE_BOUNDS[i][1];
    if (upper === null || p < upper + ZONE_BOUNDARY_TOLERANCE) return ZONE_BOUNDS[i][0];
  }
  return 6;
}

async function loadConfig() {
  const cfg = await fetch("/api/config").then(r => r.json()).catch(() => null);
  if (!cfg) return;
  ZONE_BOUNDS = cfg.zone_bounds;
  ZONE_COLOR = cfg.zone_colors;
  renderZoneConfigRows(ZONE_BOUNDS, ZONE_COLOR);
  renderTuningForm(cfg.tuning);
}

// Maps each metrics.py DEFAULT_TUNING key to how the settings-screen form
// displays it: `mult` converts the stored fraction/ratio to the input's
// display units (e.g. 0.88 -> "88" %FTP) and back on save. Fields already
// in their natural display unit (minutes, rpm, a raw VI ratio) use mult: 1.
const TUNING_FIELDS = {
  sweet_spot_low: 100, sweet_spot_high: 100, sweet_spot_tag_min_pct: 1,
  sweetspot_tag_low: 100, sweetspot_tag_high: 100, sweetspot_high_frac: 100,
  sweetspot_recovery_frac: 100, sweetspot_min_minutes: 1,
  sweetspot_ss_ratio_min: 100, sweetspot_high_ratio_max: 100,
  interval_structure_threshold: 100, vi_interval_threshold: 1, vi_mixed_threshold: 1,
  high_cadence_rpm: 1, low_cadence_rpm: 1, extreme_power_frac: 100,
};

// Mirrors metrics.py's DEFAULT_TUNING — used only by the "既定値を表示"
// button as a form-fill convenience, same as DEFAULT_ZONE_BOUNDS above.
const DEFAULT_TUNING = {
  sweet_spot_low: 0.88, sweet_spot_high: 0.94, sweet_spot_tag_min_pct: 15,
  sweetspot_tag_low: 0.85, sweetspot_tag_high: 0.95, sweetspot_high_frac: 1.05,
  sweetspot_recovery_frac: 0.60, sweetspot_min_minutes: 20,
  sweetspot_ss_ratio_min: 0.50, sweetspot_high_ratio_max: 0.10,
  interval_structure_threshold: 0.60, vi_interval_threshold: 1.15, vi_mixed_threshold: 1.08,
  high_cadence_rpm: 100, low_cadence_rpm: 70, extreme_power_frac: 2.95,
};

function renderTuningForm(tuning) {
  for (const [key, mult] of Object.entries(TUNING_FIELDS)) {
    const el = document.getElementById(`tune-${key}`);
    if (el) el.value = Math.round(tuning[key] * mult * 100) / 100;
  }
}

function collectTuning() {
  const out = {};
  for (const [key, mult] of Object.entries(TUNING_FIELDS)) {
    out[key] = parseFloat(document.getElementById(`tune-${key}`).value) / mult;
  }
  return out;
}

function heightFrac(p) {
  return Math.min(p, MAX_DISPLAY_FRAC) / MAX_DISPLAY_FRAC;
}

function fmtPower(low, high) {
  const l = Math.round(low * 100), h = Math.round(high * 100);
  return l === h ? `${l}%FTP` : `${l}→${h}%FTP`;
}

function fmtDuration(sec) {
  const m = Math.floor(sec / 60), s = Math.round(sec % 60);
  if (m === 0) return `${s}${t("unit.sec")}`;
  return s === 0 ? `${m}${t("unit.min")}` : `${m}${t("unit.min")} ${s}${t("unit.sec")}`;
}

// Longer form used in the detail view's overview box (e.g. "2h0m" / "2時間0分").
function fmtDurationLong(totalMin) {
  if (totalMin >= 60) {
    const h = Math.floor(totalMin / 60), m = Math.round(totalMin % 60);
    return LANG === "ja" ? `${h}時間${m}分` : `${h}h${m}m`;
  }
  return `${totalMin}${t("unit.min")}`;
}

/** §9 profile plot, built from /api/workouts/{id}/steps. Same shape is used
 * for both the card-sized ("mini") and detail-sized ("large") renderings —
 * only the CSS box size differs, per the "small version for cards, large
 * for the detail view" requirement. `opts.reference` draws a faint 100%FTP
 * dashed guideline (large view only — a mini card is too small to benefit). */
function stepProfileSvg(steps, opts) {
  opts = opts || {};
  const cssClass = opts.cssClass || "profile-mini";
  const total = steps.reduce((s, st) => s + (st.duration_sec || 0), 0);
  if (!total) {
    return `<svg class="${cssClass}" viewBox="0 0 100 ${VIEWBOX_H}"></svg>`;
  }

  const defs = [];
  const shapes = [];
  let cumX = 0;

  if (opts.reference) {
    const refY = CHART_H - heightFrac(1.0) * CHART_H;
    shapes.push(`<line x1="0" y1="${refY}" x2="100" y2="${refY}" stroke="#b0b6bd" stroke-width="0.5" stroke-dasharray="1.4,1.4"/>`);
  }

  for (const s of steps) {
    const dur = s.duration_sec || 0;
    if (dur <= 0) continue;
    const x = (cumX / total) * 100;
    const w = (dur / total) * 100;
    cumX += dur;
    const rx = Math.min(w * 0.25, 1.2);

    if (s.kind === "freeride" || s.kind === "maxeffort") {
      const h = CHART_H * (s.kind === "maxeffort" ? 0.85 : 0.5);
      const label = s.kind === "maxeffort" ? t("step.maxeffort_label") : t("step.freeride_label");
      const patId = `hatch${svgGradientSeq++}`;
      defs.push(`<pattern id="${patId}" width="4" height="4" patternTransform="rotate(45)" patternUnits="userSpaceOnUse"><rect width="4" height="4" fill="#ccc"/><line x1="0" y1="0" x2="0" y2="4" stroke="#999" stroke-width="2"/></pattern>`);
      shapes.push(`<rect x="${x}" y="${CHART_H - h}" width="${w}" height="${h}" rx="${rx}" fill="url(#${patId})"><title>${label} - ${fmtDuration(dur)}</title></rect>`);
      continue;
    }

    if (s.power_low == null) continue; // unresolvable target, nothing sane to draw

    const yLow = CHART_H - heightFrac(s.power_low) * CHART_H;
    const yHigh = CHART_H - heightFrac(s.power_high) * CHART_H;

    if (s.power_low === s.power_high) {
      const color = ZONE_COLOR[zoneOf(s.power_low)];
      shapes.push(`<rect x="${x}" y="${yLow}" width="${w}" height="${CHART_H - yLow}" rx="${rx}" fill="${color}"><title>${s.kind} - ${fmtDuration(dur)} @ ${fmtPower(s.power_low, s.power_high)}</title></rect>`);
    } else {
      // Warmup/Cooldown/Ramp: sloped top edge, gradient between the
      // zone colors at each end (§9: "傾斜（グラデーション）で表現").
      const gradId = `grad${svgGradientSeq++}`;
      defs.push(`<linearGradient id="${gradId}" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stop-color="${ZONE_COLOR[zoneOf(s.power_low)]}"/><stop offset="100%" stop-color="${ZONE_COLOR[zoneOf(s.power_high)]}"/></linearGradient>`);
      const points = `${x},${CHART_H} ${x},${yLow} ${x + w},${yHigh} ${x + w},${CHART_H}`;
      shapes.push(`<polygon points="${points}" fill="url(#${gradId})"><title>${s.kind} - ${fmtDuration(dur)} @ ${fmtPower(s.power_low, s.power_high)}</title></polygon>`);
    }
  }

  cumX = 0;
  for (const s of steps) {
    const dur = s.duration_sec || 0;
    if (dur <= 0) continue;
    const x = (cumX / total) * 100;
    const w = (dur / total) * 100;
    cumX += dur;
    if (s.cadence_low == null && s.cadence_high == null) continue;
    const lo = s.cadence_low ?? s.cadence_high;
    const hi = s.cadence_high ?? s.cadence_low;
    const color = hi >= 100 ? "#1a73e8" : lo <= 70 ? "#e37400" : "#aaa";
    const label = lo === hi ? `${lo}rpm` : `${lo}–${hi}rpm`;
    shapes.push(`<rect x="${x}" y="${CADENCE_Y}" width="${w}" height="${CADENCE_H}" fill="${color}"><title>${label}</title></rect>`);
  }

  return `<svg class="${cssClass}" viewBox="0 0 100 ${VIEWBOX_H}" preserveAspectRatio="none"><defs>${defs.join("")}</defs>${shapes.join("")}</svg>`;
}

function zoneDistributionHtml(zonePcts, poweredDurationSec) {
  const cols = [];
  for (let z = 1; z <= 6; z++) {
    const pct = zonePcts[String(z)] || 0;
    const mins = Math.round((poweredDurationSec || 0) * (pct / 100) / 60);
    const h = Math.max(pct, pct > 0 ? 4 : 0); // keep a sliver visible for small nonzero pcts
    cols.push(`
      <div class="bar-col">
        <span class="bar-pct">${pct > 0 ? Math.round(pct) + "%" : ""}</span>
        <div class="bar-track">
          <div class="bar" style="height:${h}%; background:${ZONE_COLOR[z]}"></div>
        </div>
        <span class="bar-label">Z${z}<br>${mins}${t("unit.min")}</span>
      </div>`);
  }
  return `<div class="zone-bars">${cols.join("")}</div>`;
}

/** Run-length-encodes consecutive identical steps, and consecutive repeats
 * of an (on, off) pair — the shape IntervalsT expands into — into a single
 * summary line, so e.g. 5 reps don't produce 10 near-identical rows. */
function groupSteps(steps) {
  const key = s => `${s.kind}|${s.duration_sec}|${s.power_low}|${s.power_high}|${s.cadence_low}|${s.cadence_high}`;
  const groups = [];
  let i = 0;
  while (i < steps.length) {
    // pair-repeat: steps[i..i+1] repeated back to back
    if (i + 3 < steps.length + 1 && i + 1 < steps.length) {
      const k0 = key(steps[i]), k1 = key(steps[i + 1]);
      let reps = 1;
      let j = i + 2;
      while (j + 1 < steps.length && key(steps[j]) === k0 && key(steps[j + 1]) === k1) {
        reps++; j += 2;
      }
      if (reps >= 2) {
        groups.push({repeat: reps, items: [steps[i], steps[i + 1]]});
        i = j;
        continue;
      }
    }
    // single-step repeat
    {
      const k0 = key(steps[i]);
      let reps = 1;
      let j = i + 1;
      while (j < steps.length && key(steps[j]) === k0) { reps++; j++; }
      if (reps >= 2) {
        groups.push({repeat: reps, items: [steps[i]]});
        i = j;
        continue;
      }
    }
    groups.push({repeat: 1, items: [steps[i]]});
    i++;
  }
  return groups;
}

function stepSummaryText(s) {
  const pw = s.power_low != null ? fmtPower(s.power_low, s.power_high) : "-";
  const cad = s.cadence_low != null ? ` @ ${s.cadence_low === s.cadence_high ? s.cadence_low : s.cadence_low + "–" + s.cadence_high}rpm` : "";
  return `${fmtDuration(s.duration_sec)} @ ${pw}${cad}`;
}

function blockBarBackground(items) {
  const colorOf = s => (s.kind === "freeride" || s.kind === "maxeffort" || s.power_low == null)
    ? "#999" : ZONE_COLOR[zoneOf(s.power_low)];
  if (items.length === 1) {
    const s = items[0];
    if (s.power_low != null && s.power_low !== s.power_high) {
      return `linear-gradient(to right, ${ZONE_COLOR[zoneOf(s.power_low)]}, ${ZONE_COLOR[zoneOf(s.power_high)]})`;
    }
    return colorOf(s);
  }
  // Paired on/off (or longer) group: blend across the sequence so the bar
  // visually reads as one repeating unit, WhatsOnZwift-style.
  return `linear-gradient(to right, ${items.map(colorOf).join(", ")})`;
}

/** Left-column block list (this conversation's screenshot reference):
 * one full-width colored bar per (possibly repeat-grouped) step, with the
 * description centered inside as white text — replaces the earlier plain
 * text rows. */
function blockBarsHtml(steps) {
  const groups = groupSteps(steps);
  const rows = groups.map(g => {
    const prefix = g.repeat > 1 ? `${g.repeat}x ` : "";
    const text = g.items.map(stepSummaryText).join(", ");
    return `<div class="block-bar" style="background:${blockBarBackground(g.items)}">${prefix}${text}</div>`;
  });
  return `<div class="block-bars">${rows.join("")}</div>`;
}

// .zwo file content (name/description/tags) is untrusted free text — it can
// come from third-party sources (Zwift forums, workouts.wad extraction) —
// so anything from it must be escaped before landing in an innerHTML
// template. Never used for JS-object property access or as a selector.
function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function tagPillsHtml(tags) {
  return tags.map(tag => `<span class="tag-pill">${escapeHtml(tag)}</span>`).join("");
}

function qs(form) {
  const data = new FormData(form);
  const params = new URLSearchParams();
  for (const [key, val] of data.entries()) {
    if (val === "" || val === null) continue;
    params.set(key, val);
  }
  form.querySelectorAll(".check-grid[data-name]").forEach(grid => {
    const name = grid.dataset.name;
    const checked = [...grid.querySelectorAll("input:checked")].map(el => el.value);
    if (checked.length) params.set(name, checked.join(","));
  });
  return params;
}

// Last search results + their step breakdowns, kept around so sorting
// (issue: 候補一覧の並べ替え) just re-renders instead of re-querying.
let lastResults = [];
let lastStepsById = {};
let lastMatchedCount = null;
let currentOffset = 0;
let currentLimit = 20;

// Inline per-card detail (issue: 詳細を閉じても元のカード位置に戻らない).
// Only one card's detail is expanded at a time; sorting always collapses it
// since the card's position in the list is about to change anyway.
let expandedId = null;
let detailCache = {}; // workout id -> {w, steps} for the full detail record

function updateResultCountLabel() {
  const el = document.getElementById("result-count");
  if (lastMatchedCount == null) { el.textContent = ""; return; }
  const start = lastMatchedCount === 0 ? 0 : currentOffset + 1;
  const end = currentOffset + lastResults.length;
  el.textContent = t("results.count", {start, end, matched: lastMatchedCount});
}

function renderPagination() {
  const row = document.getElementById("pagination-row");
  if (lastMatchedCount == null || lastMatchedCount <= currentLimit) {
    row.hidden = true;
    // Belt-and-braces: don't leave a previous (larger) search's page
    // number/enabled-next lingering if something ever shows this row
    // while hidden should apply (see the CSS comment on .pagination-row).
    document.getElementById("page-indicator").textContent = "";
    document.getElementById("page-prev").disabled = true;
    document.getElementById("page-next").disabled = true;
    return;
  }
  row.hidden = false;
  const totalPages = Math.max(1, Math.ceil(lastMatchedCount / currentLimit));
  const currentPage = Math.floor(currentOffset / currentLimit) + 1;
  document.getElementById("page-indicator").textContent =
    t("results.page_indicator", {page: currentPage, total: totalPages});
  document.getElementById("page-prev").disabled = currentOffset <= 0;
  document.getElementById("page-next").disabled = currentOffset + currentLimit >= lastMatchedCount;
}

// Builds the /api/workouts query for a given page offset: the search-form
// fields plus 並べ替え (sort-field/sort-dir live outside the <form>, in the
// results panel, so qs(form) doesn't pick them up on its own).
function buildSearchParams(offset) {
  const form = document.getElementById("search-form");
  const params = qs(form);
  const sortField = document.getElementById("sort-field").value;
  const sortDir = document.getElementById("sort-dir").dataset.dir;
  if (sortField) params.set("sort_field", sortField);
  params.set("sort_dir", sortDir);
  params.set("tags_mode", document.getElementById("tags-mode").dataset.mode);
  params.set("offset", offset);
  return params;
}

// Fetches one page of results at the given offset — used both for a fresh
// search (offset 0) and for 並べ替え/改ページ, all of which now hit the
// server so ordering and paging are correct across the FULL matched set
// (owner decision 2026-09), not just whatever was already on screen.
async function fetchPage(offset) {
  const params = buildSearchParams(offset);
  const res = await fetch("/api/workouts?" + params.toString());
  const data = await res.json();

  // Fetch each result's step breakdown in parallel so the real §9 profile
  // (not just a placeholder) can be drawn for every card.
  const stepsList = await Promise.all(
    data.results.map(w => fetch(`/api/workouts/${w.id}/steps`).then(r => r.json()).catch(() => []))
  );

  lastResults = data.results;
  lastMatchedCount = data.matched;
  currentOffset = data.offset;
  currentLimit = data.limit;
  lastStepsById = {};
  data.results.forEach((w, i) => { lastStepsById[w.id] = stepsList[i]; });
  expandedId = null;

  updateResultCountLabel();
  renderResults();
  renderPagination();
}

async function runSearch(ev) {
  ev.preventDefault();
  await fetchPage(0);
}

function renderResults() {
  const container = document.getElementById("results");
  container.innerHTML = "";
  if (lastResults.length === 0) {
    container.innerHTML = `<p class="results-empty">${t("results.empty")}</p>`;
    return;
  }
  lastResults.forEach(w => {
    container.appendChild(renderCard(w, lastStepsById[w.id] || []));
  });
}

function renderCard(w, steps) {
  const wrap = document.createElement("div");
  wrap.className = "wcard-wrap";
  const isExpanded = expandedId === w.id;

  const div = document.createElement("div");
  div.className = "wcard" + (isExpanded ? " expanded" : "");
  div.innerHTML = `
    ${stepProfileSvg(steps, {cssClass: "profile-mini"})}
    <div class="main">
      <div class="name">
        <button class="star-toggle" data-id="${w.id}" title="${t(w.is_favorite ? "card.favorite_on" : "card.favorite_off")}">${w.is_favorite ? "★" : "☆"}</button>
        ${escapeHtml(w.name || w.filename)}${w.active_deliveries?.length
        ? `<span class="scheduled-badge" title="${escapeHtml(t("card.scheduled_dates", {dates: w.active_deliveries.join(", ")}))}">${t("card.scheduled")}</span>`
        : ""}</div>
      <div class="meta">${w.duration_min}${t("unit.min")} / TSS ${w.tss ?? "-"} / IF ${w.if ?? "-"} / ${w.primary_type} / ${w.structure_type}</div>
      <div class="tags">${tagPillsHtml(w.tags)}</div>
    </div>
    <div class="actions">
      <button class="secondary" data-action="detail" data-id="${w.id}">${isExpanded ? t("card.close") : t("card.details")}</button>
      <button class="primary" data-action="deliver" data-id="${w.id}" data-name="${escapeHtml(w.name || w.filename)}">${t("card.register")}</button>
    </div>
  `;
  div.querySelector('[data-action="detail"]').addEventListener("click", () => toggleDetail(w.id));
  div.querySelector('[data-action="deliver"]').addEventListener("click", () => promptDeliver(w.id, w.name || w.filename));
  div.querySelector(".star-toggle").addEventListener("click", () => toggleFavorite(w.id));
  wrap.appendChild(div);

  if (isExpanded) {
    const detailEl = document.createElement("div");
    detailEl.className = "wcard-detail";
    const cached = detailCache[w.id];
    detailEl.innerHTML = cached
      ? detailBodyHtml(cached.w, cached.steps)
      : `<p class="loading">${t("detail.loading")}</p>`;
    if (cached) detailEl.querySelector(".star-toggle").addEventListener("click", () => toggleFavorite(w.id));
    wrap.appendChild(detailEl);
  }

  return wrap;
}

function detailBodyHtml(w, steps) {
  const durText = fmtDurationLong(w.duration_min);
  return `
    <div class="detail-title-row">
      <h3><button class="star-toggle" data-id="${w.id}" title="${t(w.is_favorite ? "card.favorite_on" : "card.favorite_off")}">${w.is_favorite ? "★" : "☆"}</button> ${escapeHtml(w.name)}</h3>
      <a class="btn secondary btn-download" href="/api/workouts/${w.id}/download" download>⬇ .zwo</a>
    </div>
    <p class="meta-line">${t("detail.primary_type")} ${w.primary_type} / ${t("detail.structure")} ${w.structure_type} / ${t("detail.tags")} ${w.tags.map(escapeHtml).join(", ")}</p>
    <div class="detail-columns">
      <div class="detail-left">
        ${blockBarsHtml(steps)}
      </div>
      <div class="detail-right">
        ${stepProfileSvg(steps, {cssClass: "profile-large", reference: true})}
        <div class="summary-boxes">
          <div class="summary-box">
            <h4>${t("detail.overview")}</h4>
            <p>⏱ ${t("detail.duration")} ${durText}</p>
            <p>🔥 TSS: ${w.tss?.toFixed(1) ?? "-"}</p>
            <p>IF: ${w.if_frac?.toFixed(3) ?? "-"}</p>
          </div>
          <div class="summary-box">
            <h4>${t("detail.zone_distribution")}</h4>
            ${zoneDistributionHtml(w.zone_pcts, w.powered_duration_sec)}
          </div>
        </div>
      </div>
    </div>
    <p class="description">${escapeHtml(w.description || "")}</p>
  `;
}

// Opens/closes a card's inline detail in place (no page-jump). Clicking a
// different card's button while one is open collapses the previous one,
// since only one may be expanded at a time.
async function toggleDetail(id) {
  if (expandedId === id) {
    expandedId = null;
    renderResults();
    return;
  }
  expandedId = id;
  renderResults();

  if (!detailCache[id]) {
    try {
      const [w, steps] = await Promise.all([
        fetch(`/api/workouts/${id}`).then(r => r.json()),
        fetch(`/api/workouts/${id}/steps`).then(r => r.json()),
      ]);
      detailCache[id] = {w, steps};
    } catch (e) {
      if (expandedId === id) expandedId = null;
      renderResults();
      return;
    }
  }
  if (expandedId === id) renderResults();
}

// Favorites live in their own `favorites` table (not the `tags` table
// ingest.py wipes/rebuilds on every rescan) — see db.py. Mutates the
// already-fetched result/detail objects in place rather than re-querying,
// same as the rest of this file's local-state-then-rerender pattern.
async function toggleFavorite(id) {
  const w = lastResults.find(r => r.id === id);
  const wasFavorite = w ? w.is_favorite : detailCache[id]?.w?.is_favorite;
  const res = await fetch(`/api/workouts/${id}/favorite`, {method: wasFavorite ? "DELETE" : "PUT"});
  if (!res.ok) return;
  const data = await res.json();
  if (w) w.is_favorite = data.is_favorite;
  if (detailCache[id]) detailCache[id].w.is_favorite = data.is_favorite;
  renderResults();
}

function todayLocalIso() {
  const d = new Date();
  const pad = n => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

let deliverTargetId = null;

function promptDeliver(id, name) {
  deliverTargetId = id;
  document.getElementById("deliver-workout-name").textContent = name;
  document.getElementById("deliver-date").value = todayLocalIso();
  document.getElementById("deliver-time").value = "";
  document.getElementById("deliver-dialog").showModal();
}

function postDelivery(id, date, time, replace) {
  return fetch("/api/deliveries", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({workout_id: id, date, time: time || null, replace}),
  });
}

document.getElementById("deliver-cancel").addEventListener("click", () => {
  document.getElementById("deliver-dialog").close();
});

document.getElementById("deliver-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const id = deliverTargetId;
  const date = document.getElementById("deliver-date").value;
  const time = document.getElementById("deliver-time").value;
  if (!date) return;

  let res = await postDelivery(id, date, time, false);
  if (res.status === 409) {
    const detail = (await res.json()).detail;
    if (!confirm(detail + t("deliver.replace_confirm_suffix"))) return;
    res = await postDelivery(id, date, time, true);
  }
  if (!res.ok) {
    alert(t("deliver.failed", {msg: await res.text()}));
    return;
  }
  document.getElementById("deliver-dialog").close();
  alert(t("deliver.success"));
  loadDeliveries();
});

async function loadDeliveries() {
  const rows = await fetch("/api/deliveries").then(r => r.json());
  const container = document.getElementById("deliveries");
  container.innerHTML = "";
  if (rows.length === 0) {
    container.innerHTML = `<p>${t("deliveries.empty")}</p>`;
    return;
  }
  for (const d of rows) {
    const div = document.createElement("div");
    div.className = "dcard";
    div.innerHTML = `
      <span>${escapeHtml(d.scheduled_date)} - ${escapeHtml(d.workout_name)}</span>
      <button class="danger">${t("deliveries.remove")}</button>
    `;
    div.querySelector("button").addEventListener("click", async () => {
      if (!confirm(t("deliveries.remove_confirm"))) return;
      const res = await fetch(`/api/deliveries/${d.id}`, {method: "DELETE"});
      if (!res.ok) { alert(t("deliveries.remove_failed", {msg: await res.text()})); return; }
      loadDeliveries();
    });
    container.appendChild(div);
  }
}

// --- tag chips (issue④: show what tags are available) ---
function currentTagList() {
  const input = document.getElementById("tags-input");
  return input.value.split(",").map(s => s.trim()).filter(Boolean);
}

function syncTagChipHighlight() {
  const selected = new Set(currentTagList());
  document.querySelectorAll(".tag-chip").forEach(chip => {
    chip.classList.toggle("selected", selected.has(chip.dataset.tag));
  });
}

async function loadTagChips() {
  const tags = await fetch("/api/tags").then(r => r.json()).catch(() => []);
  const container = document.getElementById("tag-chips");
  container.innerHTML = tags.map(tg =>
    `<span class="tag-chip" data-tag="${escapeHtml(tg.tag)}">${escapeHtml(tg.tag)}<span class="n">${tg.count}</span></span>`
  ).join("");
  container.querySelectorAll(".tag-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const tag = chip.dataset.tag;
      const list = currentTagList();
      const idx = list.indexOf(tag);
      if (idx >= 0) list.splice(idx, 1); else list.push(tag);
      document.getElementById("tags-input").value = list.join(",");
      syncTagChipHighlight();
    });
  });
}

document.getElementById("search-form").addEventListener("submit", runSearch);
document.getElementById("deliveries-refresh").addEventListener("click", async (ev) => {
  // Reconciles against intervals.icu's actual calendar first — a delivery
  // cancelled directly there (or in Zwift) otherwise leaves a stale
  // "active" row here forever, since intervals events carry no client UID
  // to notify us of the deletion through (owner request, 2026-09).
  const btn = ev.currentTarget;
  btn.disabled = true;
  try {
    const res = await fetch("/api/deliveries/sync", {method: "POST"});
    if (!res.ok) {
      alert(t("deliveries.sync_failed", {msg: await res.text()}));
      return;
    }
  } finally {
    btn.disabled = false;
  }
  loadDeliveries();
});
document.getElementById("sort-field").addEventListener("change", () => {
  if (lastMatchedCount == null) return; // no search run yet — nothing to (re-)sort
  fetchPage(0);
});
document.getElementById("sort-dir").addEventListener("click", (ev) => {
  const btn = ev.currentTarget;
  const next = btn.dataset.dir === "asc" ? "desc" : "asc";
  btn.dataset.dir = next;
  btn.textContent = t(next === "asc" ? "results.asc" : "results.desc");
  if (lastMatchedCount == null) return;
  fetchPage(0);
});
document.getElementById("page-prev").addEventListener("click", () => {
  fetchPage(Math.max(0, currentOffset - currentLimit));
});
document.getElementById("page-next").addEventListener("click", () => {
  fetchPage(currentOffset + currentLimit);
});
document.getElementById("tags-input").addEventListener("input", syncTagChipHighlight);
document.getElementById("tags-mode").addEventListener("click", (ev) => {
  const btn = ev.currentTarget;
  const next = btn.dataset.mode === "and" ? "or" : "and";
  btn.dataset.mode = next;
  btn.textContent = next.toUpperCase();
});
document.getElementById("clear-form").addEventListener("click", () => {
  const form = document.getElementById("search-form");
  form.reset();
  form.querySelectorAll(".check-grid input:checked").forEach(el => el.checked = false);
  syncTagChipHighlight();
  const tagsModeBtn = document.getElementById("tags-mode");
  tagsModeBtn.dataset.mode = "and";
  tagsModeBtn.textContent = "AND";
  document.getElementById("sort-field").value = "";
  const sortDirBtn = document.getElementById("sort-dir");
  sortDirBtn.dataset.dir = "asc";
  sortDirBtn.textContent = t("results.asc");
  lastResults = [];
  lastStepsById = {};
  lastMatchedCount = null;
  currentOffset = 0;
  expandedId = null;
  document.getElementById("results").innerHTML = "";
  updateResultCountLabel();
  renderPagination();
});

// --- settings panel (owner request: configure/operate entirely from the
// browser — no hand-edited config files or CLI. A: data source + rescan,
// B: intervals.icu connection.) ---

function setStatus(el, text, kind) {
  el.textContent = text;
  el.classList.remove("ok", "err");
  if (kind) el.classList.add(kind);
}

async function loadSettings() {
  const s = await fetch("/api/settings").then(r => r.json()).catch(() => null);
  if (!s) return;
  document.getElementById("setting-zwo-dir").value = s.zwo_dir || "";
  document.getElementById("setting-athlete-id").value = s.intervals_athlete_id || "";
  document.getElementById("setting-hide-sample").checked = !!s.hide_sample_tag;

  const dirStatus = document.getElementById("zwo-dir-status");
  if (!s.zwo_dir) {
    setStatus(dirStatus, t("settings.status.dir_unset"), "err");
  } else if (!s.zwo_dir_exists) {
    setStatus(dirStatus, t("settings.status.dir_missing"), "err");
  } else {
    setStatus(dirStatus, t("settings.status.dir_ok"), "ok");
  }

  const keyStatus = document.getElementById("api-key-status");
  setStatus(keyStatus, t(s.intervals_key_set ? "settings.status.key_set" : "settings.status.key_unset"), s.intervals_key_set ? "ok" : "err");

  renderLastScan(s.last_scan);
  loadIngestErrors();
  loadConfig(); // re-fetch so the zone-config rows reflect the latest saved values, not a stale in-memory copy
}

function renderLastScan(last) {
  const el = document.getElementById("scan-status");
  if (!last) {
    setStatus(el, t("settings.status.no_scan_yet"), null);
    return;
  }
  setStatus(
    el,
    t("settings.status.last_scan", {
      at: last.at, mode: t(last.force ? "settings.mode_full" : "settings.mode_diff"),
      scanned: last.scanned, analyzed: last.analyzed, skipped: last.skipped_unchanged,
      removed: last.removed ?? 0, errors: last.errors,
    }),
    last.errors ? "err" : "ok",
  );
}

async function loadIngestErrors() {
  const rows = await fetch("/api/ingest-errors").then(r => r.json()).catch(() => []);
  document.getElementById("ingest-errors-count").textContent = t("settings.errors_count", {n: rows.length});
  const list = document.getElementById("ingest-errors-list");
  list.innerHTML = rows.length
    ? rows.map(r => `<div class="ingest-error-row"><div class="path">${escapeHtml(r.filepath)}</div><div class="msg">${escapeHtml(r.error)}</div></div>`).join("")
    : `<p>${t("settings.errors_none")}</p>`;

  // Header badge — visible without opening 設定, so a persistently-broken
  // file doesn't sit unnoticed (owner audit, 2026-09).
  const badge = document.getElementById("settings-error-badge");
  badge.textContent = String(rows.length);
  badge.hidden = rows.length === 0;
}

// zone_bounds shape: [[zone, upper_frac_or_null], ...] — matches
// settings.py's DEFAULT_ZONE_BOUNDS / GET /api/config exactly, so this can
// render either the live config or the client-side defaults below with the
// same function.
function renderZoneConfigRows(bounds, colors) {
  const container = document.getElementById("zone-config-rows");
  container.innerHTML = bounds.map(([zone, upper]) => `
    <div class="zone-config-row">
      <span class="zone-config-label">Z${zone} ${ZONE_NAME[zone]}</span>
      <label>${t("settings.zone_upper")}
        <input type="number" step="1" min="1" max="500" class="num-sm zone-upper" data-zone="${zone}"
          value="${upper === null ? "" : Math.round(upper * 100)}"
          ${upper === null ? `disabled placeholder="${t("settings.zone_upper_none")}"` : ""}>
        %FTP
      </label>
      <input type="color" class="zone-color" data-zone="${zone}" value="${colors[String(zone)]}">
    </div>
  `).join("");
}

// Mirrors settings.py's DEFAULT_ZONE_BOUNDS/DEFAULT_ZONE_COLORS (Zwift
// reference values) — used only by the "既定値を表示" button below, as a
// form-fill convenience; nothing is saved until the owner presses 保存.
const DEFAULT_ZONE_BOUNDS = [[1, 0.60], [2, 0.75], [3, 0.89], [4, 1.04], [5, 1.18], [6, null]];
const DEFAULT_ZONE_COLORS = {1: "#9aa0a6", 2: "#4c8bf5", 3: "#34a853", 4: "#fbbc04", 5: "#ff9800", 6: "#ea4335"};

document.getElementById("save-zone-config").addEventListener("click", async () => {
  const zone_bounds = [...document.querySelectorAll(".zone-upper")].map(el => {
    const zone = parseInt(el.dataset.zone, 10);
    const upper = el.disabled ? null : parseFloat(el.value) / 100;
    return [zone, upper];
  });
  const zone_colors = {};
  document.querySelectorAll(".zone-color").forEach(el => { zone_colors[el.dataset.zone] = el.value; });

  const statusEl = document.getElementById("zone-config-status");
  const res = await fetch("/api/config", {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({zone_bounds, zone_colors}),
  });
  if (!res.ok) {
    setStatus(statusEl, t("settings.status.save_failed", {msg: (await res.json()).detail}), "err");
    return;
  }
  await loadConfig();
  setStatus(statusEl, t("settings.status.saved_rescan_hint"), "ok");
});

document.getElementById("reset-zone-config").addEventListener("click", () => {
  renderZoneConfigRows(DEFAULT_ZONE_BOUNDS, DEFAULT_ZONE_COLORS);
  setStatus(document.getElementById("zone-config-status"), t("settings.status.defaults_shown"), null);
});

document.getElementById("save-tuning").addEventListener("click", async () => {
  const statusEl = document.getElementById("tuning-status");
  const tuning = collectTuning();
  const res = await fetch("/api/config", {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({tuning}),
  });
  if (!res.ok) {
    setStatus(statusEl, t("settings.status.save_failed", {msg: (await res.json()).detail}), "err");
    return;
  }
  await loadConfig();
  setStatus(statusEl, t("settings.status.saved_rescan_hint"), "ok");
});

document.getElementById("reset-tuning").addEventListener("click", () => {
  renderTuningForm(DEFAULT_TUNING);
  setStatus(document.getElementById("tuning-status"), t("settings.status.defaults_shown"), null);
});

document.getElementById("settings-toggle").addEventListener("click", () => {
  const panel = document.getElementById("settings-panel");
  panel.hidden = !panel.hidden;
  if (!panel.hidden) loadSettings();
});

// The filter form is long (many fields); on a narrow (mobile) viewport it
// would otherwise fill the whole screen above the fold, burying the
// results the ①自動ブラウズ change was meant to surface immediately —
// desktop keeps the form open by default, same as before this button
// existed (owner audit, 2026-09).
function setSearchFormCollapsed(collapsed) {
  const form = document.getElementById("search-form");
  const btn = document.getElementById("search-form-toggle");
  form.hidden = collapsed;
  btn.textContent = t(collapsed ? "search.toggle_expand" : "search.toggle_collapse");
}
document.getElementById("search-form-toggle").addEventListener("click", () => {
  setSearchFormCollapsed(!document.getElementById("search-form").hidden);
});
setSearchFormCollapsed(window.innerWidth <= 720);

document.getElementById("save-zwo-dir").addEventListener("click", async () => {
  const zwo_dir = document.getElementById("setting-zwo-dir").value.trim();
  if (!zwo_dir) return;
  const res = await fetch("/api/settings", {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({zwo_dir}),
  });
  if (!res.ok) { alert(t("settings.status.save_failed", {msg: await res.text()})); return; }
  loadSettings();
});

document.getElementById("setting-hide-sample").addEventListener("change", async (e) => {
  const res = await fetch("/api/settings", {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({hide_sample_tag: e.target.checked}),
  });
  if (!res.ok) { alert(t("settings.status.save_failed", {msg: await res.text()})); e.target.checked = !e.target.checked; return; }
  fetchPage(0); // reflect the new filter in whatever's currently on screen
});

document.getElementById("save-athlete-id").addEventListener("click", async () => {
  const intervals_athlete_id = document.getElementById("setting-athlete-id").value.trim();
  if (!intervals_athlete_id) return;
  const res = await fetch("/api/settings", {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({intervals_athlete_id}),
  });
  if (!res.ok) { alert(t("settings.status.save_failed", {msg: await res.text()})); return; }
  loadSettings();
});

document.getElementById("save-api-key").addEventListener("click", async () => {
  const input = document.getElementById("setting-api-key");
  const api_key = input.value.trim();
  if (!api_key) return;
  const res = await fetch("/api/settings/intervals-key", {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({api_key}),
  });
  if (!res.ok) { alert(t("settings.status.save_failed", {msg: await res.text()})); return; }
  input.value = "";
  loadSettings();
});

document.getElementById("test-connection").addEventListener("click", async () => {
  const el = document.getElementById("connection-status");
  setStatus(el, t("settings.status.checking"), null);
  const res = await fetch("/api/settings/test-connection", {method: "POST"});
  if (!res.ok) {
    setStatus(el, t("settings.status.conn_failed", {msg: await res.text()}), "err");
    return;
  }
  const data = await res.json();
  setStatus(el, t("settings.status.conn_success", {name: data.name || data.athlete_id}), "ok");
});

async function runIngest(force) {
  const btn = document.getElementById(force ? "rescan-force" : "rescan-diff");
  const other = document.getElementById(force ? "rescan-diff" : "rescan-force");
  const el = document.getElementById("scan-status");
  btn.disabled = true;
  other.disabled = true;
  setStatus(el, t("settings.status.scan_running"), null);
  try {
    const res = await fetch(`/api/ingest?force=${force}`, {method: "POST"});
    if (!res.ok) {
      setStatus(el, t("settings.status.scan_failed", {msg: await res.text()}), "err");
      return;
    }
    const stats = await res.json();
    setStatus(
      el,
      t("settings.status.scan_done", {
        scanned: stats.scanned, analyzed: stats.analyzed, skipped: stats.skipped_unchanged,
        removed: stats.removed ?? 0, errors: stats.errors,
      }),
      stats.errors ? "err" : "ok",
    );
    loadIngestErrors();
    loadTagChips(); // tag counts may have shifted
  } finally {
    btn.disabled = false;
    other.disabled = false;
  }
}
document.getElementById("rescan-diff").addEventListener("click", () => runIngest(false));
document.getElementById("rescan-force").addEventListener("click", () => runIngest(true));

applyStaticI18n();
loadDeliveries();
loadTagChips();
loadConfig();
loadIngestErrors(); // header badge only — the settings panel's own open also re-fetches for freshness
fetchPage(0); // no-filter search on load = a de facto "browse all" default view (owner audit, 2026-09)
