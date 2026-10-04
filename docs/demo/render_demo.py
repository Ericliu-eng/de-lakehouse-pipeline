"""Build the README flow animation offline (requires Pillow)."""

from html import escape
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
WIDTH, HEIGHT, FPS = 1500, 1000, 10
PLAYBACK_SPEED = 1.5
BG, PANEL, BORDER = '#0b1423', '#142336', '#405a70'
TEXT, MUTED, GREEN, BLUE = '#eef5ff', '#b5c6d8', '#65edc2', '#9cc7ff'
GRAY, RED = '#718397', '#e59a9f'
FONTS = {}

# Data dependencies are read from the daily pipeline, backfill, and mart SQL.
# Dashed links are control, checks, or optional reporting; solid links carry data.
PURPLE = '#c4adff'
PHASES = [
    ('Daily prices land as raw JSON', 'Alpha Vantage daily ingestion. Optional S3 upload runs before staging.', 2.1,
     ['source','raw'], [[[130,280],[265,280],[265,380],[400,380]]]),
    ('Validate and type in Python memory', 'Raw JSON becomes typed records in memory, not a staging database.', 2.1,
     ['raw','stage'], [[[400,380],[665,380]]]),
    ('Daily route: filter by watermark', 'Read the watermark per source and symbol; keep only newer timestamps.', 2.1,
     ['stage','incremental'], [[[665,380],[805,380],[805,260],[980,260]]]),
    ('Commit facts, watermark, and load audit', 'The three writes commit or roll back together. Empty batches skip these writes.', 2.1,
     ['incremental','warehouse'], [[[980,260],[1150,260],[1150,630],[195,630],[195,800]]]),
    ('Quality checks inspect committed data', 'Failure stops the mart rebuild. Already committed ingestion stays in PostgreSQL.', 2.1,
     ['warehouse','quality'], [[[195,747],[370,747],[370,585],[625,585]]]),
    ('market_bars to Daily Summary', 'After quality passes, SQL builds daily summaries from market_bars.', 2.1,
     ['warehouse','daily'], [[[195,800],[440,800],[440,745],[660,745]]]),
    ('market_bars to Latest Price', 'A second SQL mart keeps the latest price row for every symbol.', 2.1,
     ['warehouse','latest'], [[[195,800],[440,800],[440,865],[660,865]]]),
    ('Daily Summary to Volume Rank', 'Volume Rank reads mart_daily_symbol_summary, not market_bars directly.', 2.1,
     ['daily','rank'], [[[660,745],[960,745]]]),
    ('CLI run record to optional PipeGuard', 'CLI records start and finish in pipeline_runs. Reporting is best-effort; Dagster bypasses it.', 2.1,
     ['runs','monitor'], [[[975,861],[1140,861],[1140,578],[1305,578]]]),
    ('Latest Price to FastAPI', 'The separately started API queries the latest available row across symbols.', 2.1,
     ['latest','api'], [[[660,865],[810,865],[810,920],[1160,920],[1160,745],[1305,745]]]),
    ('FastAPI renders the dashboard', 'The server renders the symbol, latest close, and database source. Values shown are examples.', 2.1,
     ['api','dashboard'], [[[1305,745],[1305,871]]]),
    ('Separate route: Tiingo history backfill', 'Tiingo: raw + typed staging, compare overlapping closes, insert missing bars. Rebuild marts separately.', 3.6,
     ['tiingo','raw','stage','history','warehouse'],
     [[[130,440],[265,440],[265,380],[400,380],[665,380],[805,380],[805,395],[980,395],[1150,395],[1150,630],[195,630],[195,800]]]),
    ('Separate route: recover missing dates', 'Reuse an Alpha Vantage payload; database dates and checkpoints select missing days. No daily watermark filter.', 3,
     ['source','raw','stage','recovery','warehouse'],
     [[[130,280],[265,280],[265,380],[400,380],[665,380],[805,380],[805,530],[980,530],[1150,530],[1150,630],[195,630],[195,800]]]),
    ('The complete project data flow', 'Daily ingestion, separate historical recovery, SQL marts, serving, and optional CLI monitoring.', 1.8,
     ['source','tiingo','raw','stage','incremental','history','recovery','warehouse','quality','daily','latest','rank','runs','monitor','api','dashboard'], []),
]


def font(size, bold=False, mono=False):
    key = size, bold, mono
    if key not in FONTS:
        windows = 'consola.ttf' if mono else ('segoeuib.ttf' if bold else 'segoeui.ttf')
        linux = 'DejaVuSansMono.ttf' if mono else ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')
        candidates = [Path('C:/Windows/Fonts') / windows,
                      Path('/usr/share/fonts/truetype/dejavu') / linux,
                      Path('/System/Library/Fonts/Supplemental/Arial.ttf')]
        selected = next((p for p in candidates if p.exists()), None)
        if selected is None:
            raise RuntimeError('Install Segoe UI, DejaVu Sans, or Arial to render the demo.')
        FONTS[key] = ImageFont.truetype(str(selected), size)
    return FONTS[key]


class Canvas:
    """One drawing source for the raster GIF and the vector HTML player."""

    def __init__(self):
        self.image = Image.new('RGB', (WIDTH, HEIGHT), BG)
        self.draw = ImageDraw.Draw(self.image)
        self.svg = [f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}"/>']

    def rect(self, x, y, w, h, fill, radius=0, stroke=None, width=1):
        self.draw.rounded_rectangle((x, y, x+w, y+h), radius, fill, stroke, width)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke or "none"}" stroke-width="{width}"/>')

    def text(self, x, y, value, size=18, fill=TEXT, bold=False, mono=False, center=False):
        face = font(size, bold, mono)
        if center:
            x -= self.draw.textlength(value, font=face)/2
        self.draw.text((x, y), value, fill=fill, font=face, anchor='lt')
        family = 'Consolas,monospace' if mono else 'Segoe UI,Arial,sans-serif'
        self.svg.append(f'<text x="{x}" y="{y+size*.84}" fill="{fill}" font-family="{family}" font-size="{size}" font-weight="{700 if bold else 400}">{escape(value)}</text>')

    def line(self, points, fill=BORDER, width=2, dashed=False):
        if dashed:
            for a, b in zip(points, points[1:]):
                distance = ((a[0]-b[0])**2 + (a[1]-b[1])**2)**.5
                for d in range(0, int(distance), 10):
                    p1 = [a[k] + (b[k]-a[k])*d/distance for k in (0, 1)]
                    p2 = [a[k] + (b[k]-a[k])*min(d+5, distance)/distance for k in (0, 1)]
                    self.draw.line([tuple(p1), tuple(p2)], fill=fill, width=width)
        else:
            self.draw.line([tuple(p) for p in points], fill=fill, width=width, joint='curve')
        pts = ' '.join(f'{x},{y}' for x, y in points)
        self.svg.append(f'<polyline points="{pts}" fill="none" stroke="{fill}" stroke-width="{width}"'+(' stroke-dasharray="5 5"' if dashed else '')+'/>')

    def ellipse(self, x, y, w, h, fill, stroke=None):
        self.draw.ellipse((x, y, x+w, y+h), fill, stroke, 2)
        self.svg.append(f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="{fill}" stroke="{stroke or "none"}" stroke-width="2"/>')

    def polygon(self, points, fill, stroke):
        self.draw.polygon(points, fill=fill)
        self.draw.line(points+[points[0]], fill=stroke, width=2, joint='curve')
        self.svg.append(f'<polygon points="{" ".join(f"{x},{y}" for x,y in points)}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')

    def arrow(self, x, y, direction='right', fill=BORDER):
        if direction == 'right':
            pts = [(x-6,y-4),(x,y),(x-6,y+4)]
        elif direction == 'down':
            pts = [(x-4,y-6),(x,y),(x+4,y-6)]
        else:
            pts = [(x-4,y+6),(x,y),(x+4,y+6)]
        self.line(pts, fill)


def base_scene(phase):
    c = Canvas()
    active = set(PHASES[phase][3])
    complete = phase == len(PHASES)-1
    link = GREEN if complete else BORDER
    c.rect(30,27,5,30,GREEN,2)
    c.text(49,25,'Market data lakehouse',32,bold=True)
    c.text(30,73,'Daily loads + historical recovery + analytical serving',18,MUTED)
    c.text(1175,33,'PROJECT FLOW / ILLUSTRATED',14,MUTED,bold=True)

    # The upper strip describes orchestration, rather than another data store.
    c.rect(30,112,1400,65,PANEL,10,BORDER)
    c.text(49,124,'ORCHESTRATION',12,BLUE,bold=True)
    c.text(49,145,'CLI or Dagster: ingest → quality checks → rebuild marts',19,bold=True)
    c.text(880,125,'Dagster: enable the daily schedule to automate runs',15,MUTED)
    c.text(880,149,'CLI only: persist run records + optional PipeGuard reports',15,PURPLE)

    # Storage boundary includes fact tables, analytical marts, and run records.
    c.rect(30,660,1090,284,'#101d2c',14,BORDER)
    c.text(405,675,'POSTGRESQL  /  FACTS + MARTS + RUN RECORDS',16,BLUE,bold=True)

    def edge(points, direction='right', color=link, dashed=False, arrow=True):
        c.line(points,color,2,dashed)
        if arrow:
            c.arrow(*points[-1],direction,fill=color)

    edge([(230,280),(265,280),(265,380),(300,380)])
    edge([(230,440),(265,440),(265,380),(300,380)])
    edge([(500,380),(560,380)])
    for y in (260,395,530):
        edge([(770,380),(805,380),(805,y),(850,y)])
        edge([(1110,y),(1150,y)],arrow=False)
    edge([(1150,260),(1150,630),(195,630),(195,710)],'down')
    edge([(400,320),(400,273)],'up',BLUE,True)
    c.rect(322,220,156,53,PANEL,8,BORDER)
    c.text(400,233,'Optional S3',18,BLUE,center=True)
    c.text(419,286,'raw payload copy',13,MUTED)

    # Quality reads committed data; its PASS is a control dependency on rebuilding.
    edge([(325,747),(370,747),(370,585),(480,585)],color=BLUE,dashed=True)
    c.text(385,555,'check',13,BLUE)
    edge([(720,620),(720,650)],'down',BLUE,True)
    c.text(745,637,'PASS enables the mart rebuild',14,BLUE)
    edge([(770,585),(825,585)],color=RED,dashed=True,arrow=False)
    c.text(835,579,'FAIL: stop rebuild',15,RED)

    # Real SQL lineage: Daily Summary feeds Volume Rank; Latest reads facts directly.
    edge([(325,800),(440,800),(440,745),(550,745)])
    edge([(440,800),(440,865),(550,865)])
    edge([(770,745),(850,745)])
    edge([(770,865),(810,865),(810,920),(1160,920),(1160,745),(1180,745)])
    edge([(1305,790),(1305,823)],'down')

    # Monitoring is explicitly separate from the data load transaction.
    edge([(1095,861),(1140,861),(1140,578),(1180,578)],color=PURPLE,dashed=True)

    def node(key,x,y,w,h,title,detail,tag=None):
        on = key in active
        color = PURPLE if key in ('runs','monitor') else GREEN
        c.rect(x,y,w,h,'#173b3a' if on else PANEL,10,color if on else BORDER,2 if on else 1)
        if tag:
            c.text(x+15,y+12,tag,12,color if on else BLUE,bold=True)
        title_offset = 30 if tag else (10 if h >= 80 else 8)
        c.text(x+w/2,y+title_offset,title,20,TEXT,bold=True,center=True)
        c.text(x+w/2,y+h-24,detail,16,MUTED,center=True)

    node('source',30,225,200,106,'Alpha Vantage','Daily + date ranges','SOURCE API')
    node('tiingo',30,385,200,106,'Tiingo','Historical prices','SOURCE API')
    node('raw',300,320,200,120,'Raw JSON','Local disk','LANDING')
    node('stage',560,320,210,120,'Validate + Type','Python memory','STAGING')
    node('incremental',850,215,260,90,'Watermark filter','Daily: newer timestamps')
    node('history',850,350,260,90,'Insert missing bars','Tiingo: reconcile overlaps')
    node('recovery',850,485,260,90,'Date-range recovery','DB dates + checkpoint')
    c.text(665,460,'Typed rows take the selected route',14,MUTED,center=True)
    c.text(35,521,'BACKFILL COMMANDS ARE SEPARATE',12,BLUE,bold=True)
    c.text(35,545,'They skip existing dates.',16,MUTED)
    c.text(35,569,'Rebuild marts after backfilling.',16,MUTED)

    node('quality',480,550,290,70,'Quality gate','Keys · ranges · freshness')

    # Only these three writes are inside the shared ingestion transaction.
    on = 'warehouse' in active
    c.rect(65,710,260,190,'#173b3a' if on else PANEL,10,GREEN if on else BORDER,2 if on else 1)
    c.text(195,724,'INGESTION TRANSACTION',12,GREEN,bold=True,center=True)
    c.text(195,753,'market_bars',23,TEXT,mono=True,center=True)
    c.text(195,811,'pipeline_metadata',17,MUTED,mono=True,center=True)
    c.text(195,839,'load_metadata',17,MUTED,mono=True,center=True)
    c.text(195,874,'Commit / rollback together',14,GREEN,center=True)
    node('daily',550,710,220,80,'Daily Summary','From market_bars')
    node('rank',850,710,220,80,'Volume Rank','From Daily Summary')
    node('latest',550,825,220,80,'Latest Price','From market_bars')
    node('runs',850,827,245,68,'pipeline_runs','CLI start + finish records')
    node('monitor',1180,530,250,96,'PipeGuard','Optional · CLI only')
    node('api',1180,700,250,90,'FastAPI','/latest-price + /dashboard')
    c.text(1305,676,'START SERVICE SEPARATELY',12,MUTED,center=True)
    on = 'dashboard' in active
    c.rect(1180,823,250,107,'#173b3a' if on else PANEL,10,GREEN if on else BORDER,2 if on else 1)
    c.text(1195,836,'PRICE DASHBOARD',12,MUTED,bold=True)
    c.text(1195,862,'AAPL  $123.45' if phase >= 10 else 'Symbol / latest close',22 if phase >= 10 else 18,TEXT,bold=True)
    c.text(1195,903,'database · illustrative values',14,MUTED)

    c.rect(30,962,1400,1,BORDER)
    count = len(PHASES)-1
    c.text(30,976,f'{min(phase+1,count):02d} / {count:02d}',14,GREEN,bold=True)
    c.text(115,974,PHASES[phase][0],19,TEXT,bold=True)
    c.text(1075,976,'Solid: data   Dashed: control / optional',14,MUTED)
    return c


def point_at(path, fraction):
    lengths = [((b[0]-a[0])**2+(b[1]-a[1])**2)**.5 for a,b in zip(path,path[1:])]
    target = min(1,max(0,fraction))*sum(lengths)
    for (a,b),length in zip(zip(path,path[1:]),lengths):
        if target <= length:
            ratio = target/length if length else 0
            return tuple(a[k]+(b[k]-a[k])*ratio for k in (0,1))
        target -= length
    return path[-1]


def packets(draw, paths, fraction, monitoring=False):
    for path in paths:
        for trail in range(3):
            t = fraction*1.3-trail*.13
            if 0 <= t <= 1:
                x,y = point_at(path,t)
                colors = [PURPLE,'#9d84d7','#746294'] if monitoring else [GREEN,'#42bdab','#318c85']
                color = colors[trail]
                draw.rounded_rectangle((x-8,y-4,x+8,y+4),3,fill=color)
                draw.line((x-4,y-1,x+3,y-1),fill=BG,width=1)


def main():
    bases = [base_scene(i) for i in range(len(PHASES))]
    palette_source = Image.new('RGB',(WIDTH,HEIGHT*len(bases)))
    for i,c in enumerate(bases):
        palette_source.paste(c.image,(0,i*HEIGHT))
    palette = palette_source.quantize(colors=128)
    frames = []
    scenes = []
    for phase,(title,description,seconds,active,paths) in enumerate(PHASES):
        base = bases[phase]
        frame_count = max(2, round(seconds*FPS/PLAYBACK_SPEED))
        for frame in range(frame_count):
            im = base.image.copy()
            packets(ImageDraw.Draw(im),paths,frame/(frame_count-1),monitoring=phase == 8)
            frames.append(im.quantize(palette=palette,dither=Image.Dither.NONE))
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{escape(title)}">'
               + ''.join(base.svg) + '<g id="packets" aria-hidden="true"></g></svg>')
        scenes.append(dict(title=title,description=description,seconds=frame_count/FPS,paths=paths,svg=svg,monitoring=phase == 8))
        print(f'Rendered {phase+1}/{len(PHASES)}',flush=True)
    frames[0].save(ROOT/'pipeline-flow.gif',save_all=True,append_images=frames[1:],duration=100,
                   loop=0,optimize=True,disposal=1)
    bases[-1].image.save(ROOT/'pipeline-flow.png')
    html = (ROOT/'player-template.html').read_text(encoding='utf-8')
    (ROOT/'pipeline-flow.html').write_text(html.replace('/* SCENES */ []',json.dumps(scenes)),encoding='utf-8')
    print(f'{len(frames)/FPS:.1f}s; {(ROOT/"pipeline-flow.gif").stat().st_size/1024/1024:.2f} MiB')


if __name__ == '__main__':
    main()
