# Multi-AP Coordination Grouping (TAG-ST)

Traffic-Aware Grouping with Spatial-Temporal coordination for IEEE 802.11bn multi-AP coordination.
RSSI-based BSS grouping + per-TXOP combination of Co-SR / Co-TDMA according to latency-sensitive traffic distribution + H-MAB learning of slot lengths and group-wise transmit power.

- `docs/RESEARCH_NOTES.md` — idea, experiment setup, results, feedback log, remaining paper checks, extension plan
- `sim/` — simulator v1.9 and runners (`run_parallel_v1_9.py`, `run_ablation_v1_9.py`, `cmp_wait.py`, `plot_paper_figs.py`)
- `results/` — 100-run result JSONs used in the MobiSec 2026 paper
- `figures/` — paper figures (Fig. 7–9) and diagrams (Fig. 1 grouping, Fig. 2 flowchart)
- `paper/` — reference list in the MobiSec template format

Quick start:

```bash
cd sim
python run_parallel_v1_9.py            # main experiments (load / LS-STA ratio)
python run_ablation_v1_9.py --n 100    # component ablation at 1000 Mbps
python cmp_wait.py 8                   # wait vs no-wait in distributed mode
python plot_paper_figs.py              # paper figures from results JSON
```
