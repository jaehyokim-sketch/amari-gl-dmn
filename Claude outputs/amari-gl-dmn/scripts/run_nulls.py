"""귀무모형 사다리 실행 — Amari-GL 의 r 이 단순 설명을 넘어서는지 검정한다.

사용 예:
    python scripts/run_nulls.py
    python scripts/run_nulls.py --ensemble 30 --samples 4000
    python scripts/run_nulls.py --sigma 1.25 --beta 0.80 --ensemble 10
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from src.amari_gl import GLParams              # noqa: E402
from src.nulls import run_null_ladder          # noqa: E402
from src.simulate import SimConfig             # noqa: E402

LINE = "─" * 78


def main() -> None:
    ap = argparse.ArgumentParser(description="귀무모형 사다리")
    ap.add_argument("--sigma", type=float, default=0.985)
    ap.add_argument("--beta", type=float, default=0.45)
    ap.add_argument("--noise", type=float, default=0.09)
    ap.add_argument("--samples", type=int, default=800)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--ensemble", type=int, default=10,
                    help="앙상블 크기 (단일 실행 r 은 시드마다 ±0.02 흔들린다)")
    ap.add_argument("--rewire", type=int, default=5,
                    help="N3 의 독립 가중치 치환 횟수")
    a = ap.parse_args()

    cfg = SimConfig(
        gl=GLParams(sigma=a.sigma, beta=a.beta, noise=a.noise),
        n_samples=a.samples,
        seed=a.seed,
    )

    print("=" * 78)
    print("  귀무모형 사다리 — 모델의 r 이 단순 설명을 넘어서는가")
    print("=" * 78)
    print(f"  σ = {a.sigma}   β = {a.beta}   noise = {a.noise}")
    print(f"  샘플 {a.samples}개 · 앙상블 {a.ensemble}회 · N3 치환 {a.rewire}회")
    print("  표적: EMPR_FC (문헌 합성 기준행렬) 상삼각 136쌍")
    print()
    print("  ※ 진행에 시간이 걸린다 (전체모형 + N3 + N4b 시뮬레이션)", flush=True)
    print()

    results, r_full = run_null_ladder(cfg, ensemble=a.ensemble,
                                      n_rewire=a.rewire)

    print(LINE)
    print(f"  {'코드':<6}{'모형':<34}{'r':>8}  {'Δ vs 전체':>10}  적합")
    print(LINE)
    print(f"  {'—':<6}{'전체 Amari-GL (비교 기준)':<32}{r_full:>8.3f}  "
          f"{'—':>10}  {'—':>4}")
    print(LINE)

    for n in results:
        delta = r_full - n.r
        fitted = "예" if n.fitted_to_target else "아니오"
        print(f"  {n.code:<6}{n.label:<32}{n.r:>8.3f}  {delta:>+10.3f}  {fitted}")
        if n.note:
            print(f"  {'':<6}{'· ' + n.note}")
    print(LINE)

    # ─── 판정 ───────────────────────────────────────────────────────────
    valid = [n for n in results if n.r == n.r]      # NaN 제외
    best = max(valid, key=lambda n: n.r)
    margin = r_full - best.r

    print()
    print("  판정")
    print(LINE)
    print(f"  최강 귀무모형: {best.code} ({best.label}) r = {best.r:.3f}")
    print(f"  전체 모형과의 차이: {margin:+.3f}")
    print()

    if margin <= 0:
        print("  ✕ 전체 모델이 귀무모형을 넘지 못했다.")
        print("    r 값은 블록 구조·거리·선형 확산으로 이미 설명되는 수준이며,")
        print("    GL 비선형 동역학의 고유 기여를 주장할 수 없다.")
    elif margin < 0.02:
        print("  △ 차이가 앙상블 변동폭(±0.02) 수준이다.")
        print("    유의한 개선이라고 보기 어렵다. 앙상블·샘플 수를 늘려 재확인할 것.")
    else:
        print("  ✓ 전체 모델이 모든 귀무모형을 상회한다.")

    n4b = next((n for n in results if n.code == "N4b"), None)
    if n4b is not None and n4b.r == n4b.r:
        d4 = r_full - n4b.r
        print()
        print(f"  선형 대조 (N4b): Δ = {d4:+.3f}")
        if d4 < 0.02:
            print("    → −φ³ 비선형항이 FC 패턴 재현에 기여한다는 근거가 약하다.")
            print("      임계성·분기 논증을 이 결과 위에 세우기 어렵다.")
            print("      (docs/재검증_계획.md §7 의 사전 합의 사항 참조)")
        else:
            print("    → 비선형항이 선형 확산을 넘어서는 기여를 한다.")
    print(LINE)


if __name__ == "__main__":
    main()
