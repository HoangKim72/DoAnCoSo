# Official Hybrid Configurations

## 1. Muc tieu

File nay chot `2` cau hinh chinh thuc cua du an sau qua trinh thu nghiem.

Tu thoi diem nay:

- `Hybrid = Logistic Regression + XGBoost + ANN`
- se duoc coi la model mac dinh cho ca `Domain Model` va `URL Model`

Dong thoi:

- van giu lai ket qua benchmark cua tat ca cac model da chay
- de phuc vu bao cao, so sanh va doi chieu sau nay

---

## 2. Cau hinh official da chot

### Domain Model

Cau hinh official:

- Variant: `from_2025_04_07_global_under`
- Frozen dataset: `data/processed/official/domain_model_official.parquet`
- Tong so dong: `54,042`
- Benign: `27,021`
- Phishing: `27,021`
- So feature: `15`
- Default model: `hybrid_lr_xgboost_ann`

Artifact mac dinh:

- `models/domain/hybrid_lr_xgboost_ann.joblib`
- `models/domain/run_summary.json`
- `models/domain/validation_metrics.csv`
- `models/domain/test_metrics.csv`
- `models/domain/model_comparison.csv`

Metric chinh cua official `Hybrid`:

- Validation `PR-AUC`: `0.9821`
- Test `PR-AUC`: `0.9846`
- Test `F1`: `0.9318`

### URL Model

Cau hinh official:

- Variant: `from_2025_04_07_none`
- Frozen dataset: `data/processed/official/url_model_official.parquet`
- Tong so dong: `100,717`
- Benign: `38,079`
- Phishing: `62,638`
- So feature: `37`
- Default model: `hybrid_lr_xgboost_ann`

Artifact mac dinh:

- `models/url/hybrid_lr_xgboost_ann.joblib`
- `models/url/run_summary.json`
- `models/url/validation_metrics.csv`
- `models/url/test_metrics.csv`
- `models/url/model_comparison.csv`

Metric chinh cua official `Hybrid`:

- Validation `PR-AUC`: `0.9763`
- Test `PR-AUC`: `0.9872`
- Test `F1`: `0.9600`

---

## 3. Cac thu muc da dong bang

Frozen official datasets:

- `data/processed/official/domain_model_official.parquet`
- `data/processed/official/domain_model_official.stats.json`
- `data/processed/official/url_model_official.parquet`
- `data/processed/official/url_model_official.stats.json`

Official model outputs:

- `models/domain/`
- `models/url/`

Archive cac ket qua mac dinh truoc khi chot official:

- `models/domain_experiments/full_per_date_under/`
- `models/url_experiments/full_current_default/`

---

## 4. Cac ket qua benchmark van duoc giu lai

Ket qua cua tat ca cac model van duoc giu trong:

- `validation_metrics.csv`
- `test_metrics.csv`
- `model_comparison.csv`

Moi file tren deu ghi day du cho:

- `logistic_regression`
- `linear_svm`
- `random_forest`
- `xgboost`
- `ann_mlp`
- `hybrid_lr_xgboost_ann`

Ngoai ra, cac bien the dataset da thu nghiem van duoc giu trong:

- `models/domain_experiments/`
- `models/url_experiments/`

---

## 5. Quy uoc tu nay

Neu can suy luan mac dinh cho he thong, uu tien dung:

- `models/domain/hybrid_lr_xgboost_ann.joblib`
- `models/url/hybrid_lr_xgboost_ann.joblib`

Neu can lam bao cao va so sanh model:

- doc metric tu `models/domain/model_comparison.csv`
- doc metric tu `models/url/model_comparison.csv`
- doi chieu them voi cac thu muc trong `models/domain_experiments/` va `models/url_experiments/`
