"""matplotlib 공통 설정 — 한글 폰트 자동 탐색 및 영문 폴백.

macOS(AppleGothic), Windows(Malgun Gothic), Linux(NanumGothic / Noto Sans CJK)
순으로 설치된 한글 폰트를 찾는다. 찾지 못하면 그림 라벨을 영문으로 대체하여
네모(tofu) 글리프가 뜨지 않게 한다.

사용:
    from src.plotting import setup_fonts, L
    korean = setup_fonts()
    ax.set_xlabel(L("β (전역 억압)", "beta (global inhibition)"))
"""

from __future__ import annotations

__all__ = ["setup_fonts", "korean_available", "L"]

_KOREAN_FONTS = (
    "AppleGothic",          # macOS
    "Apple SD Gothic Neo",  # macOS
    "Malgun Gothic",        # Windows
    "NanumGothic",          # Linux (fonts-nanum)
    "NanumBarunGothic",
    "Noto Sans CJK KR",
    "Noto Sans KR",
    "UnDotum",
)

_korean: bool | None = None


def setup_fonts() -> bool:
    """한글 폰트를 설정한다. 성공하면 True, 폴백이면 False."""
    global _korean
    if _korean is not None:
        return _korean

    import matplotlib
    from matplotlib import font_manager

    installed = {f.name for f in font_manager.fontManager.ttflist}
    chosen = next((f for f in _KOREAN_FONTS if f in installed), None)

    if chosen:
        matplotlib.rcParams["font.family"] = chosen
        _korean = True
    else:
        _korean = False

    # 한글 폰트에서 마이너스 기호가 깨지는 문제 방지
    matplotlib.rcParams["axes.unicode_minus"] = False
    return _korean


def korean_available() -> bool:
    """setup_fonts() 결과 캐시. 미호출 시 자동 호출."""
    return setup_fonts()


def L(ko: str, en: str) -> str:
    """한글 폰트가 있으면 ko, 없으면 en 을 반환한다."""
    return ko if korean_available() else en
