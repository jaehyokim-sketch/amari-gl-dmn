# 확장 Amari-GL 방정식 — DMN 장거리 상관관계 시뮬레이션

**프리고진 비평형 열역학 · 신경과학 · 계산 시뮬레이션**  
Wonkwang KMED Acu · medicdog@wku.ac.kr

---

## 개요

이 저장소는 프리고진(Prigogine)의 산일구조(Dissipative Structure) 이론을 기반으로 Default Mode Network(DMN)의 장거리 상관관계를 확장 Amari-GL 방정식으로 시뮬레이션하고, 실측 fMRI BOLD 값과 정량 비교하는 인터랙티브 학술 보고서를 담고 있습니다.

## 핵심 방정식

```
τ ∂φ(r,t)/∂t = aφ − bφ³ + D∇²φ
              + Σⱼ Cᵢⱼ · φ̄ⱼ(t)   [구조적 DMN 연결]
              − g · φ_TPN(r,t)    [TPN 억압 결합]
              + η(r,t)            [확률적 요동]
```

- `a = σ − 1` (분기 파라미터, σ ≈ 1에서 임계점)
- `Cᵢⱼ` : 백질 트랙 기반 구조적 장거리 연결
- `η` : Gaussian 백색 소음 (열적 요동)

## 파일 구조

```
├── index.html    ← 전체 학술 보고서 + 인터랙티브 시뮬레이션 (단일 파일)
└── README.md     ← 이 파일
```

## GitHub Pages 배포 방법

### 1단계: GitHub 저장소 생성

```bash
# GitHub에서 새 저장소 생성 후 (예: amari-gl-dmn)
git init
git add index.html README.md
git commit -m "Initial: 확장 Amari-GL DMN 시뮬레이션 보고서"
git branch -M main
git remote add origin https://github.com/jaehyokim-sketch/amari-gl-dmn.git
git push -u origin main
```

### 2단계: GitHub Pages 활성화

1. GitHub 저장소 → **Settings** 탭 이동
2. 왼쪽 메뉴 → **Pages**
3. **Source**: `Deploy from a branch`
4. **Branch**: `main` / `/ (root)` 선택
5. **Save** 클릭

### 3단계: 배포 확인 (2–3분 소요)

```
https://jaehyokim-sketch.github.io/amari-gl-dmn/
```

---

## 시뮬레이션 파라미터

| 파라미터           | 기본값   | 의미                |
| -------------- | ----- | ----------------- |
| σ (분기 파라미터)    | 0.992 | 임계점 근방 (σ=1이 분기점) |
| c_DMN (DMN 결합) | 0.45  | 구조적 장거리 연결 강도     |
| g (TPN 억압)     | 0.25  | DMN–TPN 반상관 생성    |
| η₀ (소음)        | 0.07  | 열적 요동 진폭          |

## 주요 결과

| 측정 지표         | 시뮬레이션        | 실측값           | 참고문헌               |
| ------------- | ------------ | ------------- | ------------------ |
| rsFC mPFC–PCC | r ≈ 0.50     | 0.35–0.70     | Fox et al. 2005    |
| BOLD 피크 주파수   | 0.02–0.06 Hz | 0.01–0.10 Hz  | Biswal et al. 1995 |
| DMN–TPN 반상관   | r ≈ −0.25    | −0.45 ~ −0.15 | Fox et al. 2005    |
| 공간 상관 길이 ξ    | ~10–25 mm    | 12–35 mm      | Tagliazucchi 2012  |

## 기술 스택

- **순수 HTML/CSS/JavaScript** — 외부 의존성 없음 (CDN 불필요)
- **Euler-Maruyama 적분** — 확률적 GL PDE 수치 해석
- **Canvas 2D API** — 실시간 φ(r,t) 장 시각화
- **브라우저 내 rsFC 계산** — Pearson 상관 행렬 실시간 갱신

## 참고문헌 (주요)

- Prigogine & Stengers (1984). *Order Out of Chaos*
- Amari (1977). Biological Cybernetics, 27, 77–87
- Biswal et al. (1995). Magn Reson Med, 34, 537–541
- Fox et al. (2005). PNAS, 102, 9673–9678
- Haimovici et al. (2013). Physical Review Letters, 110, 178101

---

*Wonkwang KMED Acu · 2026 · 프리고진 산일구조 이론의 신경과학 적용*
