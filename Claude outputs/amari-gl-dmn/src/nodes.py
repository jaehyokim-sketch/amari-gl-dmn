"""17-노드 MNI 파셀레이션 정의.

DMN 6 + TPN 6 + SAL 3 + CLA 2 = 17 노드.
MNI 좌표는 Fox 2005 (PNAS), Power 2011 (Neuron), Buckner 2008 (Ann NY Acad),
Krimmel 2019 / Berman 2020 (Claustrum) 의 보고 좌표를 사용한다.

원본 JS Artifact(amari_gl_v7.html)의 `NODES` 배열과 1:1 대응한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Node:
    """단일 피질/피질하 노드."""

    id: str
    net: str          # 'DMN' | 'TPN' | 'SAL' | 'CLA'
    mni: tuple        # (x, y, z) in MNI152 space
    color: str        # 시각화용 hex 색상 (JS Artifact와 동일)


NODES: List[Node] = [
    # ── Default Mode Network ──────────────────────────────────────────────
    Node("mPFC",    "DMN", (0, 52, -6),     "#fb923c"),
    Node("PCC",     "DMN", (0, -56, 26),    "#e879f9"),
    Node("L_AG",    "DMN", (-46, -64, 28),  "#f59e0b"),
    Node("R_AG",    "DMN", (46, -64, 28),   "#10b981"),
    Node("L_MTG",   "DMN", (-60, -24, -12), "#34d399"),
    Node("R_MTG",   "DMN", (60, -24, -12),  "#fbbf24"),
    # ── Task-Positive Network ─────────────────────────────────────────────
    Node("L_dlPFC", "TPN", (-40, 26, 34),   "#60a5fa"),
    Node("R_dlPFC", "TPN", (40, 26, 34),    "#818cf8"),
    Node("L_FEF",   "TPN", (-26, -8, 50),   "#a5b4fc"),
    Node("R_FEF",   "TPN", (26, -8, 50),    "#6366f1"),
    Node("L_IPS",   "TPN", (-26, -58, 50),  "#4f46e5"),
    Node("R_IPS",   "TPN", (26, -58, 50),   "#7c3aed"),
    # ── Salience Network ──────────────────────────────────────────────────
    Node("ACC",     "SAL", (0, 22, 28),     "#f43f5e"),
    Node("L_AI",    "SAL", (-36, 12, 0),    "#ec4899"),
    Node("R_AI",    "SAL", (36, 12, 0),     "#db2777"),
    # ── Claustrum ─────────────────────────────────────────────────────────
    Node("L_CLA",   "CLA", (-17, 8, 0),     "#059669"),
    Node("R_CLA",   "CLA", (17, 8, 0),      "#10b981"),
]

NN: int = len(NODES)
IDS: List[str] = [n.id for n in NODES]

NETWORKS = ("DMN", "TPN", "SAL", "CLA")

NET_MEMBERS = {
    net: [n.id for n in NODES if n.net == net] for net in NETWORKS
}


def gidx(node_id: str) -> int:
    """노드 ID → 행렬 인덱스. 없으면 -1 (JS `gidx`와 동일 동작)."""
    try:
        return IDS.index(node_id)
    except ValueError:
        return -1
