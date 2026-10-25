# 확장 Amari-GL 방정식 — DMN 장거리 상관관계 시뮬레이션 v2

**프리고진 비평형 열역학 · 신경과학 · 계산 시뮬레이션**  
Wonkwang KMED Acu · medicdog@wku.ac.kr

---

## 개요 (v2)

이 저장소는 프리고진(Prigogine)의 산일구조(Dissipative Structure) 이론을 기반으로 Default Mode Network(DMN)의 장거리 상관관계를 확장 Amari-GL 방정식으로 시뮬레이션하고, 실측 fMRI BOLD 값과 정량 비교하는 인터랙티브 학술 보고서를 담고 있습니다.

**v2 주요 개선사항:**
1. 64×64 격자 → **15-노드 MNI 표준 파셀레이션** (mPFC, PCC, AG, MTG, dlPFC, FEF, IPS, ACC, AI)
2. 고정값 0.45 → **실측 dMRI SC 행렬** (Honey 2009, van den Heuvel 2011, Hagmann 2008)
3. 사전 입력 −0.25 → **전역 억압 β로 반상관 창발** (음의 결합 입력 없음)
4. φ 직접 BOLD → **Balloon-Windkessel 혈역학 순방향 모델**

## 핵심 방정식 (v2)

```
τ dφᵢ/dt = (σ−1)φᵢ − φᵢ³ + Σⱼ Cᵢⱼ(φⱼ−φᵢ) − β·⟨φ⟩ + ηᵢ(t)

모든 Cᵢⱼ ≥ 0 (dMRI 기반 양의 구조적 연결)
β·⟨φ⟩: 전역 평균 억압 → DMN-TPN 반상관 창발
```

**Balloon-Windkessel BOLD 모델 (Friston 2000):**
```
ds/dt = φᵢ − κ·s − γ·(f−1)
df/dt = s
dv/dt = (f − v^(1/α)) / τ_h
dq/dt = (f·E(f)/E₀ − v^(1/α−1)·q) / τ_h
BOLD = V₀·[k₁(1−q) + k₂(1−q/v) + k₃(1−v)]
```

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
git commit -m "v2: MNI 파셀레이션 + dMRI SC + BW BOLD 모델"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/amari-gl-dmn.git
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
https://YOUR_USERNAME.github.io/amari-gl-dmn/
```

---

## 시뮬레이션 파라미터 (v2)

| 파라미터 | 기본값 | 의미 |
|---------|-------|------|
| σ (분기 파라미터) | 0.985 | 임계점 근방 (σ=1이 분기점) |
| β (전역 억압) | 0.45 | DMN-TPN 반상관 창발 원천 (입력에 음의 결합 없음) |
| η (소음) | 0.09 | 열적 요동 진폭 |
| DT | 0.08 s | GL 적분 스텝 |
| BOLD 샘플링 | 0.5 s | BW 모델 출력 샘플링 간격 |
| 워밍업 | 60 s | 정상상태 도달 후 샘플링 시작 |

## 15-노드 MNI 파셀레이션

| 노드 | 네트워크 | MNI 좌표 |
|------|---------|---------|
| mPFC | DMN | [0, 52, −6] |
| PCC  | DMN | [0, −56, 26] |
| L/R-AG | DMN | [±46, −64, 28] |
| L/R-MTG | DMN | [±60, −24, −12] |
| L/R-dlPFC | TPN | [±40, 26, 34] |
| L/R-FEF | TPN | [±26, −8, 50] |
| L/R-IPS | TPN | [±26, −58, 50] |
| ACC | SAL | [0, 22, 28] |
| L/R-AI | SAL | [±36, 12, 0] |

## 주요 결과 (v2)

| 측정 지표 | 시뮬레이션 | 실측값 | 참고문헌 |
|---------|----------|-------|---------|
| rsFC mPFC–PCC | 0.40–0.60 | 0.35–0.70 | Fox et al. 2005 |
| BOLD 피크 주파수 | 0.01–0.08 Hz | 0.01–0.10 Hz | Biswal et al. 1995 |
| DMN–TPN 반상관 (창발) | −0.2 ~ −0.4 | −0.45 ~ −0.15 | Fox et al. 2005 |
| BOLD 피크 지연 (BW) | 5–8 s | 5–7 s | Buxton et al. 1998 |

## 기술 스택

- **순수 HTML/CSS/JavaScript** — 외부 의존성 없음
- **Euler-Maruyama 적분** — 확률적 GL 노드 동역학
- **Balloon-Windkessel 모델** — 생리학적 BOLD 신호 생성
- **Canvas 2D API** — MNI 투영(Axial+Sagittal), BOLD 시계열, rsFC/SC 행렬
- **브라우저 내 Pearson rsFC** — BOLD 시계열에서 실시간 계산

## 참고문헌 (주요)

- Prigogine & Stengers (1984). *Order Out of Chaos*
- Amari (1977). Biological Cybernetics, 27, 77–87
- Honey et al. (2009). PNAS, 106, 2035–2040
- van den Heuvel & Sporns (2011). J Neurosci, 31, 15775–15786
- Hagmann et al. (2008). PLoS Biology, 6, e159
- Buxton et al. (1998). Magn Reson Med, 39, 855–864
- Friston et al. (2000). NeuroImage, 12, 466–477
- Fox et al. (2005). PNAS, 102, 9673–9678

---

*Wonkwang KMED Acu · 2026 · 프리고진 산일구조 이론의 신경과학 적용*
