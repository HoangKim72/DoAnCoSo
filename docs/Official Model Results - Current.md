# Official Model Results - Current

File nay tong hop duy nhat bo ket qua train dang duoc coi la `official current` cho ca `Domain Model` va `URL Model`.

## 1. Cau hinh official

| Model | Variant official | Model chon | Dataset official | Rows | Benign | Phishing | Feature |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `Domain` | `official_current_26f_hybrid_xgboost_ann_weighted_120k_curated_benign_override` | `hybrid_xgboost_ann_weighted` | `data/processed/official/domain_model_official.parquet` | `120,006` | `48,002` | `72,004` | `26` |
| `URL` | `official_current_66f_ann_mlp_full_540k_plus_url_hard_negative_hostaware_phishing_targeted` | `ann_mlp` | `data/processed/official/url_model_official.parquet` | `540,023` | `373,157` | `166,866` | `66` |

## 2. Ket qua validation va test

| Model | Validation Precision | Validation Recall | Validation F1 | Validation ROC-AUC | Validation PR-AUC | Test Precision | Test Recall | Test F1 | Test ROC-AUC | Test PR-AUC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `Domain` | `0.5879` | `0.9485` | `0.7258` | `0.6813` | `0.8171` | `0.5874` | `0.9349` | `0.7215` | `0.7227` | `0.8469` |
| `URL` | `0.9976` | `0.9811` | `0.9893` | `0.9907` | `0.9963` | `0.9993` | `0.9938` | `0.9965` | `0.9988` | `0.9995` |

## 3. Split khi train

| Model | Train rows | Validation rows | Test rows | Train dates | Validation date | Test date |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `Domain` | `119,402` | `323` | `281` | `2024-04-02`, `2025-04-07`, `2026-04-02`, `2026-04-04`, `2026-04-05` | `2026-04-11` | `2026-04-12` |
| `URL` | `441,720` | `49,151` | `49,152` | `2024-04-02`, `2026-04-02`, `2026-04-04`, `2026-04-05`, `2026-04-06`, `2026-04-11`, `2026-04-12`, `2026-04-15` | `2025-04-07` | `2025-04-07` |

## 4. Ghi chu ngan

- `Domain Model` official la cau hinh hybrid moi nhat da duoc retrain tren file official hien tai va co them `curated benign override` o runtime cho exact hostname hoac trusted registered domain trong `vn_benign_domain_addon`.
- `URL Model` official hien da dung full `url_model_dataset.parquet` moi nhat, co them `81` benign URL hard-negative rows tu `data/raw/vn_benign_url_addon/`, them `14` phishing URL hard-case rows tu `data/raw/vn_phishing_url_addon/`, va mo rong URL feature len `66` de nhin ro hon vao `hostname/subdomain`.
- Vi full dataset hien chi con `2` moc mixed-label (`2024-04-02`, `2025-04-07`), URL training van dung `latest mixed-date holdout` thay cho pure temporal 3-way split.
- Runtime IDS hien doc them policy tu `models/runtime_risk_policy.json` de gan `risk_level` rieng cho `domain` va `url`.
- Runtime IDS hien co them curated benign URL patch tu `data/raw/vn_benign_url_runtime_patch/*.csv` de giam false positive tren mot so hostname/URL official phuc vu demo. Cac event di qua patch nay van duoc danh dau bang `decision_mode = model_plus_curated_benign_override`.
