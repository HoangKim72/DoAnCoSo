# Project Workflow

## 1. Muc tieu hien tai

Du an hien tai co `2` bai toan chinh:

- `Domain Model`: dung khi he thong chi lay duoc `domain / hostname / FQDN`
- `URL Model`: dung khi he thong lay duoc `full URL`

Repo dang van hanh theo `3` luong:

1. luong thu thap va xu ly du lieu de train
2. luong collector `OpenPhish` snapshot de tich luy raw feed
3. luong runtime `IDS -> interface -> dashboard`

---

## 2. Cau hinh official hien tai

### 2.1. Domain Model

- Variant official: `from_2025_04_07_global_under_plus_vn_benign_domain_addon`
- Dataset official: `data/processed/official/domain_model_official.parquet`
- Model official: `models/domain/hybrid_lr_xgboost_ann.joblib`
- Rows: `54,191`
- Phishing: `27,021`
- Benign: `27,170`
- Feature count: `15`

### 2.2. URL Model

- Variant official: `from_2025_04_07_none`
- Dataset official: `data/processed/official/url_model_official.parquet`
- Model official: `models/url/hybrid_lr_xgboost_ann.joblib`
- Rows: `100,717`
- Phishing: `62,638`
- Benign: `38,079`
- Feature count: `37`

Thong tin chot official duoc load tu:

- `models/official_model_registry.json`

---

## 3. Luong du lieu de train

### 3.1. Tong quan

Luong chinh:

`download raw` -> `normalize` -> `clean` -> `build domain/url dataset` -> `feature engineering` -> `train / validation / test`

### 3.2. Cac nguon du lieu dang dung

- `tranco`
- `openphish`
- `openphish_snapshots`
- `news_sitemaps`
- `mendeley_phishing_url`
- `mendeley_legitphish`
- `vn_benign_domain_addon` cho rieng `Domain Model`

### 3.3. Thu muc lien quan

- `data/raw/openphish/`: OpenPhish raw theo ngay
- `data/raw/openphish_snapshots/`: OpenPhish raw theo `gio-phut`
- `data/raw/vn_benign_domain_addon/`: benign domain addon duoc bo sung rieng
- `data/processed/`: dataset sau normalize, clean, build
- `data/processed/official/`: dataset official da dong bang
- `models/domain/`: artifact official cua `Domain Model`
- `models/url/`: artifact official cua `URL Model`
- `data/runtime/`: event log khi dashboard/API dang chay

---

## 4. Cac buoc xu ly du lieu

### 4.1. `src/download_data.py`

Dung de tai raw feed vao `data/raw/`.

Vi du:

- `tranco` vao `data/raw/tranco/`
- `openphish` vao `data/raw/openphish/`
- `news_sitemaps` vao `data/raw/news_sitemaps/`

### 4.2. `src/normalize_data.py`

Input:

- tat ca raw files trong `data/raw/`

Output:

- `data/processed/normalized_dataset.parquet`

Schema chuan:

- `original_value`
- `label`
- `source`
- `collected_at`
- `record_type`
- `source_record_id`
- `source_rank`
- `source_target`

Luu y:

- khi normalize `openphish`, script doc ca `data/raw/openphish/` va `data/raw/openphish_snapshots/`
- `openphish` van la source opt-in, can `--include-openphish`

### 4.3. `src/clean_data.py`

Input:

- `data/processed/normalized_dataset.parquet`

Output:

- `data/processed/clean_master_dataset.parquet`
- `data/processed/clean_master_dataset.stats.json`

Tac vu:

- parse domain/url
- canonicalize hostname va URL
- loai dong parse loi
- loai overlap positive/negative
- dedup theo `canonical_hostname` va `canonical_url`

### 4.4. `src/build_domain_dataset.py`

Input:

- `data/processed/clean_master_dataset.parquet`
- them cac file `*.csv` trong `data/raw/vn_benign_domain_addon/`

Output:

- `data/processed/domain_model_dataset.parquet`
- `data/processed/domain_model_dataset.stats.json`

Logic:

- giu cac dong co `canonical_hostname`
- dat `sample_text = canonical_hostname`
- merge them `vn_benign_domain_addon`
- sort theo `collected_at`, `label`
- dedup theo `sample_text`
- bo benign neu domain do da co nhan phishing

### 4.5. `src/build_url_dataset.py`

Input:

- `data/processed/clean_master_dataset.parquet`

Output:

- `data/processed/url_model_dataset.parquet`
- `data/processed/url_model_dataset.stats.json`

Logic:

- chi giu `record_type = url`
- dat `sample_text = canonical_url`
- sort theo `collected_at`, `label`
- dedup theo `sample_text`
- bo benign neu URL do da co nhan phishing

---

## 5. Feature engineering

### 5.1. `Domain Model`

Feature hien tai:

- `domain_length`
- `subdomain_count`
- `num_tokens_domain`
- `num_hyphens`
- `digit_ratio`
- `entropy_domain`
- `contains_brand_name`
- `contains_sensitive_keyword`
- `edit_distance_to_top_brand`
- `tld_risk_score`
- `brand_position_score`
- `registered_domain_length`
- `consonant_run_max`
- `char_repeat_ratio`
- `is_idn_or_punycode`

### 5.2. `URL Model`

Feature hien tai:

- lexical length features
- special-char counts
- entropy features
- depth features
- query param features
- suspicious token features
- scheme/query/fragment/IP flags

Ham build feature:

- `src/phishing_url_ml/feature_engineering.py`
- `build_feature_frame(df, dataset_kind)`

---

## 6. Train va danh gia

### 6.1. `src/train_baselines.py`

Script train cho:

- `--dataset-kind domain`
- `--dataset-kind url`

Luong xu ly:

1. doc dataset parquet
2. bo cac ngay chi co 1 nhan
3. chia `train / validation / test` theo `collected_at`
4. tao feature theo `dataset_kind`
5. train cac candidate models
6. danh gia tren `validation`
7. fit lai tren `train + validation`
8. danh gia tren `test`
9. ghi `validation_metrics.csv`, `test_metrics.csv`, `model_comparison.csv`, `run_summary.json`

Candidate models:

- `logistic_regression`
- `linear_svm`
- `random_forest`
- `xgboost`
- `ann_mlp`
- `hybrid_lr_xgboost_ann`

Metric tinh:

- `precision`
- `recall`
- `f1`
- `roc_auc`
- `pr_auc`

Metric mac dinh de chon:

- `pr_auc`

Luu y quan trong:

- voi `Domain Model`, repo hien chot `hybrid_lr_xgboost_ann` lam official
- voi `URL Model`, repo cung dang chot `hybrid_lr_xgboost_ann` lam official
- benchmark cua cac model khac van duoc giu trong `model_comparison.csv`

---

## 7. Luong collector OpenPhish

### 7.1. `src/collect_openphish_snapshots.py`

Muc tieu:

- tai snapshot OpenPhish moi theo chu ky

Che do hien tai:

- mac dinh chay lien tuc trong terminal
- mac dinh moi `20` phut lay `1` snapshot
- co the dung `--run-once`

Output:

- `data/raw/openphish_snapshots/openphish_YYYY-MM-DD_HH-MM.txt`

### 7.2. Trang thai tich hop

Snapshot trong `data/raw/openphish_snapshots/` da duoc normalize truc tiep.

Nghia la:

- khong can copy thu cong sang `data/raw/openphish/`
- khi rebuild dataset, snapshot moi se vao pipeline qua `normalize_data.py`

---

## 8. Luong van hanh thuc te: IDS -> interface -> dashboard

Day la luong runtime dang duoc su dung khi chay web app.

### 8.1. Khoi dong web app

Script:

- `src/run_ids_dashboard.py`

Lenh chay:

```bash
python src/run_ids_dashboard.py --host 127.0.0.1 --port 8080
```

Script nay tao Flask app bang:

- `src/phishing_url_ml/ids_dashboard_app.py`

### 8.2. Dau vao tu IDS hoac giao dien

He thong co `2` cach dua du lieu vao:

1. IDS/gui script ngoai goi API:
   - `POST /api/predict`
   - `POST /api/ingest`
2. nguoi dung nhap tay tren giao dien:
   - `http://127.0.0.1:8080/dashboard`
   - form `Manual Check`

Input co the la:

- `domain`
- `url`
- hoac `auto`

Payload co dang:

```json
{
  "dataset_kind": "domain",
  "value": "hocvudientu.hutech.edu.vn",
  "source": "ids_browser_sensor"
}
```

### 8.3. App nhan request

Trong `ids_dashboard_app.py`:

- `parse_request_payload()` doc JSON hoac form
- `api_predict()` xu ly du doan nhung khong ghi log
- `api_ingest()` xu ly du doan va ghi log vao runtime

Neu payload loi:

- app tra `400`
- dashboard hien loi ngay trong result panel

### 8.4. Luong suy luan model

Trong `src/phishing_url_ml/inference.py`, ham `predict_value()` thuc hien:

1. `detect_dataset_kind()`
   - neu `auto` thi tu xac dinh la `domain` hay `url`
2. `load_official_model_bundle()`
   - doc `models/official_model_registry.json`
   - nap dung model official cho `domain` hoac `url`
3. `build_inference_row()`
   - parse input
   - canonicalize hostname / URL
   - tao 1 dataframe cung schema voi luc train
4. `build_feature_frame()`
   - tao feature theo `dataset_kind`
5. model `predict()`
   - du doan `benign` hay `phishing`
6. `normalized_score_for_model()`
   - lay score tu `predict_proba` hoac `decision_function`
7. `risk_level_for_score()`
   - gan `minimal / low / medium / high`
8. `summarize_signals()`
   - trich mot so tin hieu noi bat de hien thi len giao dien
9. `recommendation_for_prediction()`
   - tao thong diep khuyen nghi

### 8.5. Ghi log event

Neu request di qua:

- `POST /api/ingest`

thi app goi:

- `append_event()`

de ghi tung event vao:

- `data/runtime/ids_events.jsonl`

Moi event gom:

- `dataset_kind`
- `raw_value`
- `normalized_value`
- `predicted_class`
- `score`
- `risk_level`
- `model_name`
- `variant_name`
- `signals`
- `recommendation`

### 8.6. Dashboard render giao dien

Khi browser vao:

- `GET /dashboard`

route `dashboard()` se:

1. goi `load_events(limit=100)`
   - doc `data/runtime/ids_events.jsonl`
   - sap xep event moi nhat len truoc
2. goi `summarize_events()`
   - tinh tong event, phishing event, high-risk event, domain/url split
3. goi `official_model_cards()`
   - doc registry + run summary
   - lay metric chinh cua `2` model official
4. render template HTML trong `ids_dashboard_app.py`

Giao dien hien tai gom:

- Hero section
- Tong quan nhanh
- Form `Manual Check`
- Card `Official Models`
- Bang `Recent IDS Events`

Mot so thong tin phu hien bang:

- icon `i`
- tooltip khi di chuot vao

### 8.7. Y nghia cua giao dien

`Dashboard` trong repo hien tai la lop hien thi va thao tac:

- nhan input thu cong
- goi chung luong API voi IDS
- doc event log runtime
- hien ket qua model official

No khong train model, khong rebuild dataset, va khong sua official dataset.

---

## 9. Lenh chay thuong dung

### 9.1. Rebuild dataset

```bash
python src/download_data.py --sources tranco openphish news_sitemaps mendeley_phishing_url mendeley_legitphish --include-openphish
python src/normalize_data.py --sources tranco openphish news_sitemaps mendeley_phishing_url mendeley_legitphish --include-openphish
python src/clean_data.py
python src/build_domain_dataset.py
python src/build_url_dataset.py
```

### 9.2. Train lai

```bash
python src/train_baselines.py --dataset-kind domain --write-splits
python src/train_baselines.py --dataset-kind url --write-splits
```

### 9.3. Chay collector OpenPhish

```bash
python src/collect_openphish_snapshots.py --include-openphish
```

### 9.4. Chay dashboard

```bash
python src/run_ids_dashboard.py --host 127.0.0.1 --port 8080
```

Dashboard:

```text
http://127.0.0.1:8080/dashboard
```

---

## 10. File docs nen xem cung

- `docs/Official Model Training Summary.md`
- `docs/Official Hybrid Configurations.md`
- `docs/IDS Dashboard Integration.md`
- `docs/Activity History.md`

---

## 11. Trang thai workflow hien tai

Nhung gi da san sang:

- pipeline data de train
- collector `OpenPhish` snapshot
- benign domain addon cho `Domain Model`
- official `Domain Model` va `URL Model`
- API runtime cho IDS
- dashboard web de monitor

Nhung gi van can tiep tuc:

- bo sung them bo real-world validation
- tiep tuc giam false positive cho nhom URL kho
- retrain dinh ky khi co du lieu moi
- canh chinh threshold theo muc tieu van hanh thuc te
