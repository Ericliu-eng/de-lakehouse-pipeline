"""Render the README flow animation offline (requires Pillow).

One daily Alpha Vantage load walks through every pipeline step: a throttled
request with backoff, raw landing, typed staging, the watermark filter, the
three-write transaction, the quality gate, the mart rebuild, serving, and the
run report to PipeGuard. A Tiingo history backfill then takes the insert-only
path. It is an illustration of the implemented flow, not a recording. Prices
and the run id are examples; the evidence numbers come from
docs/proof/2026-09-25-benchmark.md.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
W, H, S, FPS = 1200, 620, 3, 24  # S: supersampling factor for smooth edges
OUT = 1.5  # output scale: 1800 x 930 px stays sharp on high-DPI screens
OW, OH = round(W * OUT), round(H * OUT)
FADE_SECONDS = 0.3  # highlight transitions between beats

BG, PANEL, SOFT, LINE = "#f7f8fa", "#ffffff", "#f3f5f8", "#d9dee6"
TEXT, MUTED, DIM, WIRE = "#202735", "#626d7d", "#9aa4b2", "#b7c0cc"
ACCENT, GREEN, AMBER, RED = "#1f7a8c", "#26734d", "#94611d", "#b33b3b"
TINT = {ACCENT: "#e8f3f5", GREEN: "#e9f4ee", AMBER: "#fbf3e6", RED: "#fbeeee"}

ALPHA, TIINGO, RUNS = (30, 100, 160, 95), (30, 205, 160, 95), (30, 310, 160, 120)
INGEST = (225, 100, 240, 290)
WAREHOUSE, GATE = (500, 100, 260, 190), (500, 320, 260, 70)
DAILY, RANK, LATEST = (800, 100, 370, 100), (800, 215, 370, 100), (800, 330, 370, 100)
DETAIL, EVIDENCE = (30, 445, 440, 95), (500, 445, 670, 95)
SLOT = {"alpha": (110, 172), "tiingo": (110, 277), "ingest": (345, 352),
        "warehouse": (630, 252), "latest": (1090, 380)}
STEPS = ["retry 429 / 5xx, back off", "land raw JSON (+ S3)",
         "validate fields, cast types", "keep ts > watermark"]
TABLES = [("market_bars", "+1 row"), ("pipeline_metadata", "→ 10-02"),
          ("load_metadata", "+1 audit")]

BEATS = [  # (caption, code line, explanation, seconds)
    ("Alpha Vantage throttles; the client backs off", "429 → wait 1 s → 503 → wait 2 s → 200",
     "Up to 4 attempts; API keys are masked in every error", 3.2),
    ("The raw payload lands before it is parsed", "data/raw/2026-10-02/AAPL/stock.json",
     "Optional S3 copy: raw/alpha_vantage/symbol=AAPL/date=…/", 2.8),
    ("Staging validates and types every bar", "100 records → StagedMarketBar(ts, symbol, OHLCV)",
     "A missing field fails the run before any warehouse write", 2.8),
    ("The watermark keeps only newer bars", "ts > last_watermark (2026-10-01)  →  1 of 100",
     "Rerunning the same payload loads 0 rows", 3.2),
    ("Three writes commit together", "market_bars · pipeline_metadata · load_metadata",
     "If the audit insert fails, all three roll back", 3.0),
    ("The quality gate checks committed rows", "not null · unique (ts, symbol) · ≥ 0 · fresh ≤ 14 d",
     "Any failure stops the run before the marts", 3.2),
    ("The marts rebuild after the gate passes", "market_bars → daily summary → volume rank",
     "Latest price also reads market_bars directly", 3.2),
    ("FastAPI serves the latest price", "GET /latest-price  ·  GET /dashboard",
     "Reads mart_symbol_latest_price; values here are examples", 2.8),
    ("The run is recorded, then reported", "pipeline_runs → POST /runs  (external_run_id)",
     "Best effort with a 5 s timeout: a slow monitor never fails a load", 3.2),
    ("Tiingo backfills history without overwriting", "INSERT … ON CONFLICT (ts, symbol) DO NOTHING",
     "Existing daily bars win; overlapping closes are compared", 3.6),
    ("Every claim has a saved benchmark", "make benchmark  →  docs/proof/2026-09-25-benchmark.md",
     "Saved payloads replayed into a throwaway PostgreSQL 16", 3.2),
]
HOLD_SECONDS = 3.0
# Run feed: (beat, t, kind, text)
EVENTS = [(0, 0.05, "run", "run 3f9c started"), (0, 0.35, "retry", "429 · retry in 1 s"),
          (0, 0.65, "retry", "503 · retry in 2 s"), (3, 0.6, "run", "100 received · 1 new"),
          (5, 0.75, "pass", "checks 6/6 pass"), (6, 0.95, "run", "marts rebuilt"),
          (8, 0.55, "pass", "reported SUCCESS")]
EVIDENCE_ITEMS = [("History backfill", "97,276 rows · 7.2 s"),
                  ("Identical rerun", "0 new rows · 0 dupes"),
                  ("Quality checks", "60 / 60 in 0.4 s")]
FONTS = {}


def font(size, weight="regular"):
    key = size, weight
    if key not in FONTS:
        names = {"regular": ("segoeui.ttf", "DejaVuSans.ttf"),
                 "bold": ("segoeuib.ttf", "DejaVuSans-Bold.ttf"),
                 "mono": ("consola.ttf", "DejaVuSansMono.ttf")}[weight]
        for path in (Path("C:/Windows/Fonts") / names[0],
                     Path("/usr/share/fonts/truetype/dejavu") / names[1],
                     Path("/System/Library/Fonts/Supplemental/Arial.ttf")):
            if path.exists():
                FONTS[key] = ImageFont.truetype(str(path), size * S)
                break
        else:
            raise RuntimeError("Install Segoe UI, DejaVu, or Arial to render the animation.")
    return FONTS[key]


def ease(t):
    """Cubic ease-in-out: gentle start and stop for every movement."""
    t = min(1.0, max(0.0, t))
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def span(t, start, end):
    """Progress of t through [start, end], clamped to 0..1."""
    return min(1.0, max(0.0, (t - start) / (end - start)))


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(2))


def mix(a, b, t):
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def after(beat, t, at_beat, at_t):
    """True once the story has reached (at_beat, at_t)."""
    return (beat, t) >= (at_beat, at_t)


class Frame:
    def __init__(self):
        self.image = Image.new("RGB", (W * S, H * S), BG)
        self.d = ImageDraw.Draw(self.image)

    def rect(self, box, fill, outline=None, width=1, radius=10):
        x, y, w, h = box
        self.d.rounded_rectangle((x * S, y * S, (x + w) * S, (y + h) * S), radius * S,
                                 fill=fill, outline=outline, width=width * S)

    def text(self, x, y, value, size=16, fill=TEXT, weight="regular"):
        self.d.text((x * S, y * S), value, fill=fill, font=font(size, weight))

    def width(self, value, size, weight="regular"):
        return self.d.textlength(value, font=font(size, weight)) / S

    def line(self, points, fill=WIRE, width=2, dashed=False, phase=0.0):
        pts = [(x * S, y * S) for x, y in points]
        if not dashed:
            self.d.line(pts, fill=fill, width=width * S, joint="curve")
            return
        for a, b in zip(pts, pts[1:]):
            length = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
            step, dash = 12 * S, 6 * S
            d = -step + (phase % 1) * step
            while d < length:
                p, q = max(0, d), min(length, d + dash)
                if q > p:
                    self.d.line([lerp(a, b, p / length), lerp(a, b, q / length)],
                                fill=fill, width=width * S)
                d += step

    def arrow(self, x, y, direction, fill=WIRE):
        shapes = {"right": [(-8, -5), (0, 0), (-8, 5)], "up": [(-5, 8), (0, 0), (5, 8)],
                  "left": [(8, -5), (0, 0), (8, 5)], "down": [(-5, -8), (0, 0), (5, -8)]}
        self.d.polygon([((x + dx) * S, (y + dy) * S) for dx, dy in shapes[direction]], fill=fill)

    def pill(self, x, y, label, color, size=11, filled=False, level=1.0):
        w = self.width(label, size, "bold") + 16
        fill = mix(BG, color, level) if filled else PANEL
        ink = mix(BG, PANEL, level) if filled else mix(PANEL, color, level)
        self.rect((x, y, w, size + 10), fill, mix(BG, color, level), 1, radius=(size + 10) // 2)
        self.text(x + 8, y + 3, label, size, ink, "bold")
        return w


def look(color):
    return (TINT[color], color, color) if color else (PANEL, LINE, ACCENT)


def blend_look(previous, current, k):
    return tuple(mix(x, y, k) for x, y in zip(look(previous), look(current)))


def node(f, box, title, detail="", tag=None, style=None, title_size=18):
    fill, border, tag_color = style or look(None)
    f.rect(box, fill, border, 2 if border != LINE else 1)
    x, y, _, _ = box
    if tag:
        f.text(x + 14, y + 11, tag, 11, tag_color, "bold")
    f.text(x + 14, y + (27 if tag else 11), title, title_size, TEXT, "bold")
    if detail:
        f.text(x + 14, y + (53 if tag else 37), detail, 13, MUTED)


def card(f, center, label, note, tag=None, color=ACCENT):
    cx, cy = center
    f.rect((cx - 68, cy - 19, 140, 46), "#e3e8ef", radius=8)  # soft drop shadow
    f.rect((cx - 70, cy - 22, 140, 46), PANEL, color, 2, radius=8)
    f.text(cx - 59, cy - 17, label, 13, TEXT, "bold")
    f.text(cx - 59, cy + 3, note, 11, MUTED, "mono")
    if tag:
        tw = f.width(tag, 9, "bold") + 10
        f.rect((cx + 60 - tw, cy - 14, tw, 14), color, radius=7)
        f.text(cx + 65 - tw, cy - 13, tag, 9, PANEL, "bold")


def mart(f, box, name, detail, status, status_color, style):
    node(f, box, name, style=style)
    x, y, _, _ = box
    f.pill(x + 22 + f.width(name, 18, "bold"), y + 13, status, status_color, 10)
    f.text(x + 14, y + 38, detail, 13, MUTED)


def highlights(beat, t, final=False):
    lit = dict.fromkeys(("alpha", "tiingo", "runs", "ingest", "warehouse", "gate",
                         "daily", "rank", "latest", "evidence"))
    if final:
        lit.update(warehouse=GREEN, evidence=GREEN)
        return lit
    if beat == 0:
        lit.update(alpha=AMBER if t < 0.75 else ACCENT, ingest=ACCENT, runs=ACCENT if t < 0.2 else None)
    elif beat in (1, 2):
        lit.update(ingest=ACCENT)
    elif beat == 3:
        lit.update(ingest=ACCENT, warehouse=AMBER if 0.15 < t < 0.55 else None)
    elif beat == 4:
        lit.update(warehouse=GREEN if t > 0.7 else ACCENT)
    elif beat == 5:
        lit.update(warehouse=ACCENT if t < 0.3 else None, gate=GREEN if t > 0.7 else ACCENT)
    elif beat == 6:
        lit.update(gate=GREEN if t < 0.2 else None,
                   daily=(GREEN if t > 0.4 else ACCENT) if t > 0.1 else None,
                   rank=(GREEN if t > 0.75 else ACCENT) if t > 0.45 else None,
                   latest=(GREEN if t > 0.75 else ACCENT) if t > 0.45 else None)
    elif beat == 7:
        lit.update(latest=ACCENT)
    elif beat == 8:
        lit.update(runs=GREEN if t > 0.55 else ACCENT)
    elif beat == 9:
        lit.update(tiingo=ACCENT if t < 0.4 else None, ingest=ACCENT if 0.15 < t < 0.75 else None,
                   warehouse=(GREEN if t > 0.85 else ACCENT) if t > 0.55 else None)
    else:
        lit.update(evidence=GREEN if t > 0.3 else None)
    return lit


def draw_frame(beat, t, final=False):
    f = Frame()
    f.rect((30, 28, 5, 28), ACCENT, radius=2)
    f.text(46, 22, "de-lakehouse", 28, TEXT, "bold")
    f.text(46 + f.width("de-lakehouse", 28, "bold") + 16, 33,
           "Incremental loads, a quality gate, and insert-only history backfills", 16, MUTED)
    tag = "ILLUSTRATED FLOW"
    f.text(1170 - f.width(tag, 11, "bold"), 36, tag, 11, DIM, "bold")

    k = ease(span(t, 0, FADE_SECONDS / BEATS[beat][3])) if beat and not final else 1.0
    now, before = highlights(beat, t, final), (highlights(beat - 1, 1.0) if beat else {})
    style = {key: blend_look(before.get(key), now.get(key), k) for key in now}

    # Wiring: solid = data, dashed = checks, control, and reporting.
    for y in (150, 255):
        f.line([(190, y), (225, y)])
        f.arrow(225, y, "right")
    f.line([(465, 195), (500, 195)])
    f.arrow(500, 195, "right")
    f.line([(760, 195), (780, 195)])
    f.line([(780, 150), (780, 380)])
    for y in (150, 380):
        f.line([(780, y), (800, y)])
        f.arrow(800, y, "right")
    f.line([(1140, 200), (1140, 215)])
    f.arrow(1140, 215, "down")
    gating = now["gate"] is not None
    f.line([(630, 290), (630, 320)], ACCENT if gating else WIRE, 2, True, t * 4)
    f.arrow(630, 320, "down", ACCENT if gating else WIRE)
    passed = after(beat, t, 5, 0.7) or final
    f.line([(760, 355), (780, 355)], GREEN if passed else WIRE, 2, True, t * 4)
    reporting = now["runs"] is not None
    f.line([(225, 372), (190, 372)], ACCENT if reporting else WIRE, 2, True, t * 4)
    f.arrow(191, 372, "left", ACCENT if reporting else WIRE)

    node(f, ALPHA, "Alpha Vantage", tag="SOURCE · DAILY", style=style["alpha"])
    node(f, TIINGO, "Tiingo", tag="SOURCE · HISTORY", style=style["tiingo"])

    # Ingest + stage, with its steps lit in order.
    node(f, INGEST, "Ingest + stage", "Python · one symbol per run", "CLI OR DAGSTER", style=style["ingest"])
    f.text(INGEST[0] + 14, INGEST[1] + 86, "STEPS, IN ORDER", 10, MUTED, "bold")
    active = {0: 0, 1: 1, 2: 2, 3: 3}.get(beat) if not final else None
    if beat == 9 and 0.15 < t < 0.75:
        active = 2
    for i, step in enumerate(STEPS):
        y = INGEST[1] + 106 + i * 26
        if active == i:
            f.rect((INGEST[0] + 10, y - 3, INGEST[2] - 20, 23), TINT[ACCENT], ACCENT, 1, radius=6)
        f.text(INGEST[0] + 18, y, f"{i + 1}  {step}", 13, ACCENT if active == i else TEXT)

    # Warehouse: the three tables written in one transaction.
    node(f, WAREHOUSE, "Warehouse", tag="POSTGRESQL · ONE TRANSACTION", style=style["warehouse"])
    written = after(beat, t, 4, 0.2) and beat < 9 or final
    for i, (table, change) in enumerate(TABLES):
        y = WAREHOUSE[1] + 62 + i * 22
        f.text(WAREHOUSE[0] + 14, y, table, 12, TEXT, "mono")
        shown = 1.0 if final or beat > 4 else ease(span(t, 0.2 + i * 0.15, 0.35 + i * 0.15))
        label, color = change, GREEN
        if i == 0 and (beat == 9 or final):  # the backfill path never updates a row
            label, color, shown = "insert-only", ACCENT, 1.0
        elif not written:
            continue
        if shown > 0:
            f.text(WAREHOUSE[0] + WAREHOUSE[2] - 14 - f.width(label, 11, "bold"), y + 1, label, 11,
                   mix(PANEL, color, shown), "bold")

    # Quality gate.
    node(f, GATE, "Quality gate", "6 checks for the loaded symbol", style=style["gate"])
    g_status, g_color = "WAITING", DIM
    if beat == 5 and t <= 0.7:
        g_status, g_color = "CHECKING", ACCENT
    elif passed:
        g_status, g_color = "6 / 6 PASS", GREEN
    f.pill(GATE[0] + GATE[2] - 14 - f.width(g_status, 10, "bold") - 16, GATE[1] + 13, g_status, g_color, 10)

    # Marts: stale until the gate passes, then rebuilt in dependency order.
    def mart_status(start, end):
        if final or beat > 6 or beat == 6 and t > end:
            return "BUILT", GREEN
        if beat == 6 and t > start:
            return "BUILDING", ACCENT
        return "STALE", DIM

    mart(f, DAILY, "Daily summary", "one row per symbol and day · from market_bars",
         *mart_status(0.1, 0.4), style["daily"])
    mart(f, RANK, "Volume rank", "daily volume rank · from daily summary",
         *mart_status(0.45, 0.75), style["rank"])
    l_status, l_color = mart_status(0.45, 0.75)
    if beat == 7:
        l_status, l_color = "SERVING", ACCENT
    mart(f, LATEST, "Latest price", "one row per symbol",
         l_status, l_color, style["latest"])

    # PipeGuard: run feed with the latest three events.
    node(f, RUNS, "PipeGuard", tag="RUN RECORD", style=style["runs"])
    f.text(RUNS[0] + 14, RUNS[1] + 51, "pipeline_runs → /runs", 11, MUTED)
    events = [e for e in EVENTS if final or after(beat, t, e[0], e[1])][-3:]
    colors = {"retry": AMBER, "pass": GREEN}
    for i, (_, _, kind, label) in enumerate(events):
        f.text(RUNS[0] + 14, RUNS[1] + 72 + i * 15, label, 10, colors.get(kind, MUTED), "mono")

    # The daily AAPL batch.
    if beat < 9 and not final:
        pos, note, tag, color = SLOT["alpha"], "attempt 1 · 429", "AV", AMBER
        if beat == 0:
            note = ("attempt 1 · 429" if t < 0.35 else "attempt 2 · 503" if t < 0.65
                    else "attempt 3 · 200")
            color = AMBER if t < 0.75 else ACCENT
        elif beat == 1:
            pos, color = lerp(SLOT["alpha"], SLOT["ingest"], ease(span(t, 0.05, 0.45))), ACCENT
            note = "raw JSON saved" if t > 0.5 else "100 records"
        elif beat == 2:
            pos, color = SLOT["ingest"], ACCENT
            note = "100 typed rows" if t > 0.45 else "100 records"
        elif beat == 3:
            pos, color = SLOT["ingest"], ACCENT
            note = "1 new · 99 older" if t > 0.6 else "100 typed rows"
        elif beat == 4:
            pos = lerp(SLOT["ingest"], SLOT["warehouse"], ease(span(t, 0.05, 0.4)))
            note, color = ("committed", GREEN) if t > 0.7 else ("1 new row", ACCENT)
        else:
            pos, note, color = SLOT["warehouse"], "committed", GREEN
        card(f, pos, "AAPL · daily", note, tag, color)

    # The latest-price row the API serves.
    if after(beat, t, 6, 0.75) or final:
        note = "GET /latest-price" if beat == 7 else "close · 2026-10-02"
        card(f, SLOT["latest"], "AAPL  $333.69", note, "API", ACCENT if beat == 7 else GREEN)

    # The Tiingo history batch.
    if beat == 9 or beat == 10 or final:
        pos, note, color = SLOT["tiingo"], "1980 → 2026", ACCENT
        if beat == 9:
            pos = lerp(SLOT["tiingo"], SLOT["ingest"], ease(span(t, 0.12, 0.4)))
            pos = lerp(pos, SLOT["warehouse"], ease(span(t, 0.55, 0.8)))
            note = "+11,359 bars" if t > 0.4 else note
            if t > 0.85:
                note, color = "existing kept", GREEN
        else:
            pos, note, color = SLOT["warehouse"], "existing kept", GREEN
        card(f, pos, "AAPL", note, "TIINGO", color)

    # Beat-specific overlays.
    if beat == 0 and 0.3 < t < 0.75:
        go = ease(span(t, 0.3, 0.42)) if t < 0.5 else ease(span(t, 0.52, 0.64))
        x = 225 - 35 * go
        f.line([(225, 178), (x, 178)], AMBER, 2, True)
        f.arrow(x, 178, "left", AMBER)
    if beat == 3 and 0.15 < t < 0.6:
        level = ease(span(t, 0.15, 0.3))
        f.line([(500, 245), (465, 245)], mix(BG, AMBER, level), 2, True, t * 4)
        f.arrow(466, 245, "left", mix(BG, AMBER, level))
    if beat == 4:
        level = ease(span(t, 0.7, 0.85))
        if level > 0:
            f.pill(WAREHOUSE[0] + WAREHOUSE[2] - 132, WAREHOUSE[1] - 28, "COMMITTED TOGETHER", GREEN, 10,
                   True, level)
    if beat == 5 or beat == 6 and t < 0.3:
        level = 1.0 if beat == 6 else ease(span(t, 0.7, 0.85))
        f.text(GATE[0] + 14, GATE[1] + GATE[3] + 8, "pass → rebuild marts · fail → stop here", 11,
               mix(BG, GREEN, level), "bold")

    # Saved evidence: values light up in the last beat.
    fill, border, tag_color = style["evidence"]
    f.rect(EVIDENCE, fill, border, 2 if border != LINE else 1)
    f.text(EVIDENCE[0] + 14, EVIDENCE[1] + 11, "SAVED EVIDENCE · DOCS/PROOF · REPLAYED BENCHMARK", 11,
           tag_color, "bold")
    shown = 1.0 if final else (ease(span(t, 0.3, 0.65)) if beat == 10 else 0.0)
    column = (EVIDENCE[2] - 28) / 3
    for i, (label, value) in enumerate(EVIDENCE_ITEMS):
        x = EVIDENCE[0] + 14 + i * column
        f.text(x, EVIDENCE[1] + 34, label, 12, MUTED)
        f.text(x, EVIDENCE[1] + 56, value if shown > 0 else "saved report", 15,
               mix(DIM, GREEN, shown) if shown > 0 else DIM, "bold")

    caption, code, explanation, _ = BEATS[beat]
    if final:
        caption = "Land raw, load past the watermark, gate on quality, then serve"
        code = "One daily load, one history backfill"
        explanation = "No duplicate keys, no partial writes, no unchecked marts"
    f.rect(DETAIL, PANEL, LINE, 1)
    f.text(DETAIL[0] + 16, DETAIL[1] + 18, code, 13, ACCENT, "mono")
    f.text(DETAIL[0] + 16, DETAIL[1] + 52, explanation, 14, MUTED)

    f.rect((30, 558, 1140, 1), LINE, radius=0)
    count = f"{beat + 1:02d} / {len(BEATS):02d}" if not final else "Lakehouse"
    f.text(30, 579, count, 13, ACCENT, "bold")
    f.text(105 if not final else 112, 575, caption, 19, TEXT, "bold")
    legend = "Solid: data   Dashed: checks and control"
    f.text(1170 - f.width(legend, 11), 581, legend, 11, DIM)
    return f.image.resize((OW, OH), Image.LANCZOS)


def main():
    frames = []
    for beat, (*_, seconds) in enumerate(BEATS):
        count = round(seconds * FPS)
        frames += [draw_frame(beat, i / (count - 1)) for i in range(count)]
        print(f"beat {beat + 1}/{len(BEATS)}", flush=True)
    final = draw_frame(len(BEATS) - 1, 1.0, final=True)
    frames += [final] * round(HOLD_SECONDS * FPS)
    # Loop seam: fade out to the empty canvas, then fade the opening frame in.
    blank, fade = Image.new("RGB", (OW, OH), BG), round(FADE_SECONDS * FPS)
    frames += [Image.blend(final, blank, ease((i + 1) / fade)) for i in range(fade)]
    frames[:fade] = [Image.blend(blank, frames[i], ease((i + 1) / fade)) for i in range(fade)]

    # One shared palette keeps colors stable between frames (no flicker).
    picks = frames[:: max(1, len(frames) // 16)][:16]
    sample = Image.new("RGB", (OW, OH * len(picks)))
    for i, frame in enumerate(picks):
        sample.paste(frame, (0, i * OH))
    palette = sample.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    quantized = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    quantized[0].save(ROOT / "lakehouse-flow.gif", save_all=True, append_images=quantized[1:],
                      duration=round(1000 / FPS), loop=0, optimize=True, disposal=1)
    final.save(ROOT / "lakehouse-flow.png", optimize=True)
    size = (ROOT / "lakehouse-flow.gif").stat().st_size / 1024 / 1024
    print(f"{len(frames) / FPS:.1f}s, {len(frames)} frames, {size:.2f} MiB")


if __name__ == "__main__":
    main()
