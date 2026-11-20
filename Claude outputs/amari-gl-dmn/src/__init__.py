"""확장 Amari-GL 방정식 DMN + Claustrum 장거리 상관 시뮬레이션.

비평형 열역학적 산일구조(Prigogine) 관점에서 Default Mode Network 의 발현을
확장 Amari–Ginzburg–Landau 방정식으로 모사하고, Balloon–Windkessel 혈역학
순방향 모델을 거쳐 얻은 BOLD rsFC 를 문헌 FC 및 OpenNeuro 실측과 비교한다.

원본 대화형 논문: https://claude.ai/artifact/5x7jEdNb7Sw7yA1VZzc28S (V7)
"""

from .amari_gl import GLParams, gl_step
from .analysis import fc_correlation, network_blocks, validate
from .balloon import BWParams, BWState, bold_signal, bw_step
from .connectivity import EMPR_FC, EMPR_PAIRS, SC, build_sc, sc_degree
from .nodes import IDS, NN, NODES, NET_MEMBERS, Node, gidx
from .simulate import SimConfig, SimResult, run_simulation

__version__ = "7.0.0"

__all__ = [
    "GLParams", "gl_step",
    "BWParams", "BWState", "bw_step", "bold_signal",
    "SC", "EMPR_FC", "EMPR_PAIRS", "build_sc", "sc_degree",
    "NODES", "NN", "IDS", "NET_MEMBERS", "Node", "gidx",
    "SimConfig", "SimResult", "run_simulation",
    "fc_correlation", "network_blocks", "validate",
    "__version__",
]
