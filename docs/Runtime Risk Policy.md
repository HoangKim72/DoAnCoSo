# Runtime Risk Policy

- Calibration reference: `mixed expanded` snapshot dung trong Phase 36 threshold tuning ngay `2026-04-15`
- Authoritative runtime file: `models\runtime_risk_policy.json`
- Generated at: `2026-04-15T12:45:51+07:00`
- Policy version: `2026-04-15_phase36_calibrated`

## 1. Thresholds

- `Domain`: low >= `0.55`, medium >= `0.90`, high >= `0.95`
- `URL`: low >= `0.45`, medium >= `0.75`, high >= `0.98`

## 2. Summary

### 2.1. `domain`

- Rows: `28`
- Risk counts: `{'minimal': 1, 'low': 6, 'medium': 5, 'high': 16}`
- Expected benign by risk: `{'minimal': 1, 'low': 0, 'medium': 3, 'high': 0}`
- Expected phishing by risk: `{'minimal': 0, 'low': 6, 'medium': 2, 'high': 16}`
- Score summary all: `{'min': 0.01, 'p25': 0.901066, 'median': 0.972886, 'p75': 0.998108, 'max': 0.999821}`
- Score summary false positive: `{'min': 0.903293, 'p25': 0.921406, 'median': 0.939519, 'p75': 0.942149, 'max': 0.944778}`
- Score summary true positive: `{'min': 0.568613, 'p25': 0.931232, 'median': 0.984513, 'p75': 0.99864, 'max': 0.999821}`

### 2.2. `url`

- Rows: `66`
- Risk counts: `{'minimal': 30, 'low': 2, 'medium': 2, 'high': 32}`
- Expected benign by risk: `{'minimal': 30, 'low': 2, 'medium': 2, 'high': 8}`
- Expected phishing by risk: `{'minimal': 0, 'low': 0, 'medium': 0, 'high': 24}`
- Score summary all: `{'min': 0.0, 'p25': 0.00692, 'median': 0.762952, 'p75': 1.0, 'max': 1.0}`
- Score summary false positive: `{'min': 0.535177, 'p25': 0.767183, 'median': 0.996331, 'p75': 0.999838, 'max': 1.0}`
- Score summary true positive: `{'min': 0.986996, 'p25': 0.999962, 'median': 1.0, 'p75': 1.0, 'max': 1.0}`

## 3. Notes

- Muc tieu cua policy nay la bien `risk_level` thanh tin hieu van hanh hop ly hon cho IDS, khong thay doi nhan `phishing/benign` cua model.
- `URL high` duoc day len cao hon de giu nhom true phishing manh trong `expanded` o muc canh bao cao, trong khi mot so benign score sat nguong se ha xuong `medium` hoac `low`.
- `Domain high` duoc dat cao hon de tranh nang canh bao qua som cho cac hostname benign bi model score cao truoc khi co them runtime triage.
