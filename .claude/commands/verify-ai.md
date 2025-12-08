---
name: verify-ai
description: AI 프로젝트 TIER 0/TIER 1 검증 (완료 전 MUST BE USED)
---

# AI 프로젝트 검증

## TIER 0 (필수)
- [ ] Train/Val/Test 분리 (데이터 누수 없음)
- [ ] 오버피팅 체크: train-test gap < 10%
- [ ] 재현성: random seed 고정

## TIER 1 (Task별)

### Classification
- [ ] Confusion matrix
- [ ] Precision, Recall, F1
- [ ] Class imbalance 처리

### Regression
- [ ] RMSE, MAE, R²
- [ ] Residual 분석

### 공통
- [ ] Cross-validation 수행
- [ ] Feature importance 분석
- [ ] Error analysis 완료
