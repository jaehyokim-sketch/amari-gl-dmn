# Amari-GL 기반 DMN·TPN·SAL·CLA 장거리 상관관계 시뮬레이션 — 선행연구 비교 정리

> 연구자: 교수 (medicdog@wku.ac.kr) | Wonkwang KMED Acu  
> 작성일: 2026-09-19  
> 대상 시뮬레이션: Extended Amari-GL v3 + Balloon-Windkessel BOLD 모델, 17-node MNI 파셀

---

## 개요

본 시뮬레이션은 **Amari-GL(Amari–Ginzburg–Landau) 방정식**을 확장하여 대뇌 안정상태 기능 네트워크(DMN·TPN·SAL·CLA)의 장거리 상관관계를 재현하고, 이 현상이 **프리고진(Prigogine)의 소산구조(dissipative structure)** 원리에 따른 비평형 자기조직화임을 논증한다. 아래에 동일한 연구 방법 및 결과를 공유하는 선행연구를 6개 주제로 분류·정리한다.

---

## 주제 1 — Amari 신경장 방정식 및 전뇌 신경장 모델

| 저자 | 연도 | 저널 | 핵심 내용 | 유사점 |
|------|------|------|-----------|--------|
| Amari SI | 1977 | Biol. Cybern. | 측면억제 신경장의 패턴 형성 동역학 원본 방정식 제안 | Amari-GL의 직접 원형; τdφ/dt = F(φ) + Σ W*φ |
| Bressloff PC | 2012 | Rev. Mod. Phys. | 신경장 이론의 수학적 정리; 평균장·분기 분석 | GL 퍼텐셜 V(φ) = -(σ-1)φ²/2 + φ⁴/4 의 이론적 배경 |
| Sanz-Leon P et al. | 2022 | Front. Comput. Neurosci. | 전뇌 네트워크 모델 종합 리뷰: 물리학에서 임상까지 | 신경장→BOLD 파이프라인의 방법론 비교 기준 제시 |
| Pang JC et al. | 2023 | Nature | 뇌 기하학적 제약이 기능 조직 결정; 신경장 고유모드 분석 | 구조(SC)→기능(FC) 예측의 지형학적 확장 |

---

## 주제 2 — Stuart-Landau / Hopf 분기 전뇌 모델 (가장 근접한 선행연구)

| 저자 | 연도 | 저널 | 핵심 내용 | 유사점 |
|------|------|------|-----------|--------|
| Deco G et al. | 2017 | Sci. Rep. | Stuart-Landau 진동자를 SC에 연결; Hopf 분기점 근방(a≈0)에서 안정상태 FC 재현 r=0.71 | 방정식 구조·SC→FC 방법론 동일; σ↔a 매개변수 역할 동일 |
| Hansen EC et al. | 2015 | NeuroImage | Hopf 분기 모델로 안정상태 FC 동역학 스위칭 재현 | 임계점 근방 잡음 구동 요동 → 네트워크 전환 메커니즘 공유 |
| Deco G & Jirsa VK | 2012 | J. Neurosci. | 피질 잡음-구동 요동; 임계성·다안정성·유령 끌개 이론 | 초임계/아임계 분기 이론 배경 동일; σ=0.985 설정의 근거 |
| Kringelbach ML et al. | 2020 | Nat. Rev. Neurosci. | 전뇌 Hopf 모델로 metastability → 의식·수면·질환 설명 | GL 분기 구조가 뇌 상태 전환을 지배한다는 결론 일치 |

### Deco 2017 vs 본 Amari-GL v3 직접 비교

| 항목 | Deco 2017 | 본 Amari-GL v3 |
|------|-----------|----------------|
| 로컬 동역학 | Stuart-Landau: ż = (a+iω)z − |z|²z | Amari-GL: τdφ/dt = (σ-1)φ − φ³ |
| 분기 유형 | Hopf (초임계, 복소) | 피치포크 (초임계, 실수) |
| 임계 매개변수 | a = 0 | σ = 1 |
| 결합 방식 | SC 기반 확산 | SC 기반 확산 + -β⟨φ⟩ |
| BOLD 모델 | Balloon-Windkessel | Balloon-Windkessel (동일) |
| 검증 r값 | ~0.71 | 0.922 |
| 반상관 메커니즘 | 일부 음성 SC | 전역 억제항만 (음성 SC 불필요) |
| RSN 포함 | DMN+TPN | DMN+TPN+SAL+CLA |

---

## 주제 3 — Balloon-Windkessel BOLD 전진 모델 + SC→FC 예측

| 저자 | 연도 | 저널 | 핵심 내용 | 유사점 |
|------|------|------|-----------|--------|
| Honey CJ et al. | 2009 | PNAS | 최초의 SC→FC 예측; Balloon-Windkessel + 신경질량 모델 | 방법 파이프라인의 직접 원형 |
| Deco G et al. | 2013 | J. Neurosci. | SC + 느린 선형 요동으로 rsFC 창발; BW BOLD 결합 | 구조↔기능 관계의 이론적 근거 |
| Hermundstad AM et al. | 2013 | PNAS | 안정상태 및 과제 FC의 구조적 기반 | SC가 FC 분산의 약 50% 설명 |
| Friston KJ et al. | 2000 | NeuroImage | Balloon-Windkessel 원본; κ, γ, τ, α, E₀, V₀ 매개변수 정의 | 본 연구 BW 매개변수의 직접 출처 |

---

## 주제 4 — DMN–TPN 반상관 창발 메커니즘

| 저자 | 연도 | 저널 | 핵심 내용 | 유사점 |
|------|------|------|-----------|--------|
| Fox MD et al. | 2005 | PNAS | DMN-TPN 반상관 최초 발견 | 본 시뮬레이션의 재현 목표 |
| Chang C & Glover GH | 2010 | NeuroImage | GSR 없이도 반상관 존재; 생리적 잡음 제거 후에도 유지 | -β⟨φ⟩ 전역 억제 정당화 |
| Murphy K & Fox MD | 2017 | NeuroImage | 전역신호 회귀는 시간적 다운-가중 처리; 반상관 실재성 재확인 | GSR ↔ -β⟨φ⟩ 의 방법론적 동치성 |
| Anticorrelation (competitive landscape) | 2025 | ScienceDirect | 반상관이 동적·경쟁적 신경 지형에서 창발 | 음성SC 없는 창발 메커니즘과 개념 일치 |

---

## 주제 5 — 자기조직 임계성(SOC) · 프리고진 소산구조 이론

| 저자 | 연도 | 저널 | 핵심 내용 | 유사점 |
|------|------|------|-----------|--------|
| Beggs JM & Plenz D | 2003 | J. Neurosci. | 신경 눈사태(neuronal avalanche) 발견; 1/f 멱함수 분포 → SOC | σ=0.985 임계점 근방 설정의 신경생물학적 근거 |
| Haimovici A et al. | 2013 | Phys. Rev. Lett. | Ising 모델 + 인간 SC → 임계점에서만 RSN 창발 (r~0.75) | 임계성 → RSN 창발의 계산 증명 |
| Tagliazucchi E et al. | 2012 | Front. Physiol. | fMRI 점과정 분석으로 대규모 뇌 동역학의 임계성 입증; 멱법칙 | 임계 상관길이 ξ∝|σ-1|^{-ν}→∞ 이론의 실험적 지지 |
| Prigogine I & Stengers I | 1984 | Order Out of Chaos | 소산구조 이론: 비평형 개방계, 비선형 동역학, 자발적 시공간 패턴 | DMN 장거리 상관을 소산구조로 해석하는 이론 원천 |
| Bak P et al. | 1987 | Phys. Rev. Lett. | 자기조직 임계성(SOC) 원본; 모래더미 모델, 1/f 잡음 | η=0.09 + σ=0.985 조합이 SOC 작동점 설정 |

### 프리고진 소산구조 3기준과 Amari-GL 대응

| 소산구조 기준 | Amari-GL 수식 대응 |
|-------------|-------------------|
| ① 비평형 개방계 | η(t): 외부 잡음 에너지 입력 / -β⟨φ⟩: 소산 경로 |
| ② 비선형 동역학 | (σ-1)φ - φ³: GL 퍼텐셜, 피치포크 분기 |
| ③ 자발적 시공간 패턴 창발 | ΣCᵢⱼ(φⱼ-φᵢ): SC 기반 공간 확산 → 장거리 상관 |

---

## 주제 6 — Claustrum 기능연결성

| 저자 | 연도 | 저널 | 핵심 내용 | 유사점 |
|------|------|------|-----------|--------|
| Torgerson CM et al. | 2024 | PLOS One | HCP 기반 인간 CLA FC 지도; 전두·두정·측두엽과 광범위 연결 | L/R_CLA 노드 설정의 데이터 출처 |
| White MG et al. | 2018 | Front. Neuroanat. | 쥐 CLA 안정상태 FC; DMN·SAL·TPN 모두와 연결 | CLA = 다중 네트워크 허브 |
| Marmoset CLA study | 2025 | PubMed | 마모셋 CLA; 동측·대측 반구간 연결 확인 | CLA 반구간 연결의 진화적 보존 → L/R 쌍 설정 정당화 |
| Crick FC & Koch C | 2005 | Phil. Trans. R. Soc. | CLA = 피질 오케스트라 지휘자; 의식과 주의 통합 허브 | CLA의 '피질 지휘자' 해석의 이론적 근원 |

---

## 종합 비교표: 전뇌 모델 방법론

| 연구 | 로컬 모델 | SC 결합 | BOLD | 반상관 메커니즘 | r값 | RSN |
|------|-----------|---------|------|----------------|-----|-----|
| **본 Amari-GL v3** | GL 퍼텐셜 (실수) | ΣCᵢⱼ(φⱼ-φᵢ) | BW | -β⟨φ⟩ 전역억제 | **0.922** | DMN+TPN+SAL+CLA |
| Deco 2017 | Stuart-Landau (복소) | SC 확산 | BW | 일부 음성 SC | ~0.71 | DMN+TPN |
| Honey 2009 | Wilson-Cowan | SC | BW | 없음 | ~0.54 | DMN 중심 |
| Haimovici 2013 | Ising 스핀 | SC | 없음 | N/A | ~0.75 | 전체 RSN |
| Hansen 2015 | Hopf | SC | BW | 일부 | ~0.60 | DMN+TPN |
| Deco 2013 | 선형 요동 | SC | BW | 없음 | ~0.56 | DMN 중심 |

---

## 본 연구의 선행연구 대비 기여점

1. **Amari-GL 실수형 피치포크 분기**: Stuart-Landau 복소 Hopf(Deco 2017)와 동등한 이론적 엄밀성을 실수 GL 형식으로 구현
2. **음성 SC 없이 DMN-TPN 반상관 창발**: -β⟨φ⟩만으로 반상관 재현 → Fox 2005 현상에 대한 최소 메커니즘 제안
3. **프리고진 소산구조로의 통합 해석**: 임계성, SOC, 비평형 열역학을 단일 Amari-GL 프레임으로 통합
4. **SAL·CLA 명시적 포함**: 기존 DMN+TPN 2-시스템에서 4-시스템(+SAL, +CLA)으로 확장
5. **높은 검증 r값**: r=0.922 (Deco 2017 r~0.71, Honey 2009 r~0.54 대비 우수)

---

## 참고문헌

1. Amari SI (1977). *Biol. Cybern.* 27, 77–87.
2. Honey CJ et al. (2009). *PNAS* 106, 2035–2040. https://pubmed.ncbi.nlm.nih.gov/19188601/
3. Fox MD et al. (2005). *PNAS* 102, 9673–9678. https://www.pnas.org/doi/10.1073/pnas.0504136102
4. Deco G et al. (2013). *J. Neurosci.* 33, 11239–11252. https://www.jneurosci.org/content/33/27/11239
5. Haimovici A et al. (2013). *Phys. Rev. Lett.* 110, 178101. https://link.aps.org/doi/10.1103/PhysRevLett.110.178101
6. Deco G & Jirsa VK (2012). *J. Neurosci.* 32, 3366–3375.
7. Deco G et al. (2017). *Sci. Rep.* 7, 3815. https://www.nature.com/articles/s41598-017-03073-5
8. Beggs JM & Plenz D (2003). *J. Neurosci.* 23, 11167–11177.
9. Tagliazucchi E et al. (2012). *Front. Physiol.* 3, 15. https://www.frontiersin.org/articles/10.3389/fphys.2012.00015
10. Chang C & Glover GH (2010). *NeuroImage* 59, 1420–1428. https://pubmed.ncbi.nlm.nih.gov/21889994/
11. Murphy K & Fox MD (2017). *NeuroImage* 144, 56–68. https://pubmed.ncbi.nlm.nih.gov/28089677/
12. Hansen EC et al. (2015). *NeuroImage* 105, 525–535.
13. Torgerson CM et al. (2024). *PLOS One*. https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0298349
14. White MG et al. (2018). *Front. Neuroanat.* https://pmc.ncbi.nlm.nih.gov/articles/PMC6395398/
15. Prigogine I & Stengers I (1984). *Order Out of Chaos*. Bantam Books.
16. Bak P et al. (1987). *Phys. Rev. Lett.* 59, 381–384.
17. Crick FC & Koch C (2005). *Phil. Trans. R. Soc. B* 360, 1271–1279.
18. Sanz-Leon P et al. (2022). *Front. Comput. Neurosci.* https://www.frontiersin.org/journals/computational-neuroscience/articles/10.3389/fncom.2022.866517/full
19. Pang JC et al. (2023). *Nature* 618, 566–574. https://www.nature.com/articles/s41586-023-06098-1
20. Hermundstad AM et al. (2013). *PNAS* 110, 6169–6174. https://www.pnas.org/doi/10.1073/pnas.1219562110
