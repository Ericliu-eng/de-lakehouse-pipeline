# Pipeline flow animation

`pipeline-flow.gif` is a 21-second illustrated project data flow, generated offline
at 1.5x playback speed.
It is not an execution recording. The dashboard price is explicitly illustrative.
`pipeline-flow.html` provides playback controls and a reduced-motion mode;
`pipeline-flow.png` is the still overview.

The flow includes daily ingestion, Tiingo history, date-range recovery,
orchestration, and optional CLI reporting. Staging is in Python memory. The
PostgreSQL boundary contains warehouse facts, metadata, marts, and run records;
`pipeline_runs` is separate from the three-write ingestion transaction.

Quality checks inspect committed rows and gate the mart rebuild. Both daily
summary and latest price read `market_bars`; volume rank reads the daily summary.
Only latest price feeds the current serving API, which must be started separately.

Backfills are separate commands and do not run the daily watermark filter or
automatically rebuild marts. Tiingo compares overlapping closes and inserts only
missing rows. Date-range recovery reconciles checkpoints with database dates.
CLI orchestration records run start/finish and optionally reports to PipeGuard;
the Dagster path does not currently use this recording/reporting mechanism.
Solid arrows show data dependencies; dashed arrows show checks, control, or
optional side channels. The animation does not execute APIs or commands.

To rebuild, install Pillow in a development environment and run:

```bash
python docs/demo/render_demo.py
```

The renderer uses Segoe UI on Windows, DejaVu Sans on Linux, or Arial on macOS.
Edit `render_demo.py` for the drawing and timing, and `player-template.html`
for playback controls. Generated files are self-contained and make no network
requests. Open the generated HTML in a browser to pause or step through.
