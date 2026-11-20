#!/usr/bin/env python3
"""기본 시뮬레이션 실행 + 문헌 FC 검증.

사용법:
    python scripts/run_simulation.py
    python scripts/run_simulation.py --sigma 0.99 --beta 0.5 --seed 7
    python scripts/run_simulation.py --samples 1600 --save results/run1
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import (  # noqa: E402
    EMPR_FC, GLParams, SimConfig, fc_correlation, network_blocks,
    run_simulation, sc_degree, validate,
)
from src.nodes import IDS  # noqa: E402


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="확장 Amari-GL DMN+CLA 시뮬레이션")
    ap.add_argument("--sigma", type=float, default=0.985, help="분기 파라미터 σ")
    ap.add_argument("--beta", type=float, default=0.45, help="전역 억압 β")
    ap.add_argument("--noise", type=float, default=0.09, help="잡음 진폭")
    ap.add_argument("--dt", type=float, default=0.08, help="적분 스텝 (s)")
    ap.add_argument("--warmup", type=float, default=60.0, help="warmup 구간 (s)")
    ap.add_argument("--samples", type=int, default=800, help="BOLD 샘플 수")
    ap.add_argument("--seed", type=int, default=42, help="난수 시드")
    ap.add_argument("--ensemble", type=int, default=1,
                    help="앙상블 크기. N>1 이면 seed, seed+1, … 로 N회 실행 후 "
                         "FC 를 평균한다 (유한표본 잡음 감소)")
    ap.add_argument("--save", type=str, default=None,
                    help="결과 저장 경로 접두사 (예: results/run1)")
    return ap.parse_args()


def main() -> int:
    a = parse_args()

    cfg = SimConfig(
        gl=GLParams(sigma=a.sigma, beta=a.beta, noise=a.noise),
        dt=a.dt,
        warmup=a.warmup,
        n_samples=a.samples,
        seed=a.seed,
    )

    print("=" * 72)
    print("  확장 Amari-GL 방정식 · DMN + Claustrum 17-노드 시뮬레이션 (v3 / V7)")
    print("=" * 72)
    print(f"  σ = {cfg.gl.sigma}   β = {cfg.gl.beta}   noise = {cfg.gl.noise}")
    print(f"  DT = {cfg.dt}s   실효 TR = {cfg.effective_tr:.2f}s   "
          f"warmup = {cfg.warmup}s")
    print(f"  샘플 {cfg.n_samples}개  →  총 {cfg.duration:.0f}s "
          f"({cfg.duration / 60:.1f}분)   seed = {cfg.seed}")
    if a.ensemble > 1:
        print(f"  앙상블 {a.ensemble}회 (seed {a.seed}–{a.seed + a.ensemble - 1}) "
              f"FC 평균")
    print()

    res = run_simulation(cfg)
    if a.ensemble > 1:
        fcs = [res.fc]
        for k in range(1, a.ensemble):
            cfg_k = replace(cfg, seed=a.seed + k)
            fcs.append(run_simulation(cfg_k).fc)
        res.fc = np.mean(fcs, axis=0)

    # ── 검증표 ───────────────────────────────────────────────────────────
    rows = validate(res.fc)
    print("─" * 72)
    print(f"  {'검증 항목':<26}{'시뮬':>10}{'문헌':>10}{'허용범위':>18}{'판정':>8}")
    print("─" * 72)
    for r in rows:
        rng = f"[{r.lo:+.2f}, {r.hi:+.2f}]"
        print(f"  {r.label:<24}{r.simulated:>+10.3f}{r.literature:>+10.3f}"
              f"{rng:>18}{r.mark:>9}")
    n_pass = sum(r.passed for r in rows)
    print("─" * 72)
    print(f"  합격 {n_pass}/{len(rows)}")
    print()

    # ── 전체 FC 상관 ─────────────────────────────────────────────────────
    r_all = fc_correlation(res.fc)
    print("─" * 72)
    print(f"  시뮬 FC vs 문헌 FC (상삼각 136쌍) Pearson r = {r_all:.4f}")
    print(f"  ※ 논문 V7 보고값: r = 0.922  (docs/PORTING_NOTES.md 의 재현 편차 참고)")
    print(f"     Python 포팅 재현값 — 단일 실행 0.81–0.87, 앙상블 30회 ≈ 0.896")
    print("─" * 72)
    print()

    # ── 네트워크 블록 ────────────────────────────────────────────────────
    blocks = network_blocks(res.fc)
    emp_blocks = network_blocks(EMPR_FC)
    print("─" * 72)
    print(f"  {'네트워크 블록':<18}{'시뮬':>12}{'문헌':>12}{'차이':>12}")
    print("─" * 72)
    for k in blocks:
        d = blocks[k] - emp_blocks[k]
        print(f"  {k:<18}{blocks[k]:>+12.3f}{emp_blocks[k]:>+12.3f}{d:>+12.3f}")
    print("─" * 72)

    # ── 저장 ─────────────────────────────────────────────────────────────
    if a.save:
        out = ROOT / a.save
        out.parent.mkdir(parents=True, exist_ok=True)
        np.save(f"{out}_fc.npy", res.fc)
        np.save(f"{out}_bold.npy", res.bold)
        summary = {
            "params": cfg.gl.as_dict(),
            "dt": cfg.dt,
            "effective_tr": cfg.effective_tr,
            "n_samples": cfg.n_samples,
            "seed": cfg.seed,
            "r_vs_literature": r_all,
            "validation": [
                {"label": r.label, "simulated": r.simulated,
                 "literature": r.literature, "passed": r.passed}
                for r in rows
            ],
            "network_blocks": blocks,
            "sc_degree": dict(zip(IDS, sc_degree().tolist())),
        }
        with open(f"{out}_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"\n  저장 완료: {out}_fc.npy / _bold.npy / _summary.json")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
