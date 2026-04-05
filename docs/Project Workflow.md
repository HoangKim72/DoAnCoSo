# Project Workflow

## 1. Muc tieu hien tai

Du an nay xay dung pipeline du lieu va machine learning de phat hien phishing theo 2 bai toan:

- `Domain Model`: dung khi he thong chi thu duoc `domain / hostname / FQDN`
- `URL Model`: dung khi he thong thu duoc `full URL`

Workflow hien tai khong con la mot luong duy nhat, ma gom `2` nhanh:

1. luong train chinh
2. luong collector `OpenPhish` snapshot de tich luy du lieu raw theo thoi gian

---

## 2. Luong tong the hien tai

### 2.1. Luong train chinh

`download raw data` -> `normalize schema` -> `clean / parse / canonicalize / deduplicate` -> `build domain dataset` hoac `build url dataset` -> `extract features theo dataset_kind` -> `train / validate / test`

### 2.2. Luong collector snapshot

`collect OpenPhish snapshot moi 20 phut` -> `luu raw vao data/raw/openphish_snapshots/` -> `duoc normalize chung khi chay source openphish`

Luu y:

- nhanh collector nay van doc lap voi luong train chinh
- khi chay `normalize_data.py` cho source `openphish`, pipeline hien tai se doc ca:
  - `data/raw/openphish/`
  - `data/raw/openphish_snapshots/`
- neu mot snapshot bi copy sang ca `2` thu muc, du lieu raw se bi lap o buoc normalize va duoc giam anh huong o cac buoc clean / dedup sau do

---

## 3. Cau truc thu muc lien quan den workflow

- `data/raw/`: du lieu goc vua tai ve
- `data/raw/openphish/`: OpenPhish raw theo ngay va cac file snapshot da duoc dua vao train tu truoc
- `data/raw/openphish_snapshots/`: OpenPhish raw theo `gio-phut`, vua de archive vua duoc pipeline normalize doc truc tiep
- `data/processed/`: cac dataset sau khi normalize, clean, build
- `models/`: model da train va cac file metric
- `src/`: code pipeline
- `docs/`: tai lieu workflow, thong ke va ghi chu
- `scripts/`: script wrapper ho tro van hanh

---

## 4. Cac script trong luong train chinh

### 4.1. `src/download_data.py`

Nhiem vu:

- tai raw data tu Internet va luu vao `data/raw/`

Nguon hien dang su dung trong workflow:

- `tranco`
- `openphish`
- `news_sitemaps`
- `mendeley_phishing_url`
- `mendeley_legitphish`

Nguon co cau hinh nhung chua dung duoc trong thuc te:

- `phishtank`

Raw files duoc luu theo thu muc nguon, vi du:

- `data/raw/tranco/`
- `data/raw/openphish/`
- `data/raw/news_sitemaps/`
- `data/raw/mendeley_phishing_url/`
- `data/raw/mendeley_legitphish/`

### 4.2. `src/normalize_data.py`

Input:

- raw files trong `data/raw/`

Output:

- `data/processed/normalized_dataset.parquet`

Muc tieu:

- dua nhieu nguon du lieu ve cung mot schema chung

Schema chuan gom cac cot:

- `original_value`
- `label`
- `source`
- `collected_at`
- `record_type`
- `source_record_id`
- `source_rank`
- `source_target`

Luu y:

- `OpenPhish` la nguon opt-in, can them `--include-openphish` khi normalize
- khi source la `openphish`, `normalize_data.py` hien doc dong thoi raw tu `data/raw/openphish/` va `data/raw/openphish_snapshots/`

### 4.3. `src/clean_data.py`

Input:

- `data/processed/normalized_dataset.parquet`

Output:

- `data/processed/clean_master_dataset.parquet`
- `data/processed/clean_master_dataset.stats.json`

Viec script nay dang lam:

- parse URL hoac domain
- canonicalize hostname, registered domain va URL
- loai bo dong parse loi
- loai overlap positive/negative
- deduplicate theo:
  - `canonical_hostname` cho record `domain`
  - `canonical_url` cho record `url`

Output cua `clean_master_dataset.parquet` gom cac cot quan trong:

- cot goc va metadata: `original_value`, `label`, `source`, `collected_at`, `record_type`
- cot parse: `scheme`, `hostname`, `subdomain`, `domain`, `suffix`, `registered_domain`, `path`, `query`, `fragment`
- cot canonical: `canonical_domain`, `canonical_hostname`, `canonical_registered_domain`, `canonical_url`
- cot bo sung: `is_ip_host`, `source_record_id`, `source_rank`, `source_target`

### 4.4. `src/build_domain_dataset.py`

Input:

- `data/processed/clean_master_dataset.parquet`

Output:

- `data/processed/domain_model_dataset.parquet`
- `data/processed/domain_model_dataset.stats.json`

Logic hien tai:

- chi giu cac dong co `canonical_hostname` khong rong
- dat `sample_text = canonical_hostname`
- sap xep theo `collected_at`, `label`
- deduplicate theo `sample_text`
- loai bo benign neu trung voi host da co nhan phishing

Cot dau ra cua `domain_model_dataset.parquet`:

- `sample_text`
- `label`
- `source`
- `collected_at`
- `record_type`
- `hostname`
- `registered_domain`
- `subdomain`
- `suffix`
- `is_ip_host`
- `canonical_hostname`
- `canonical_registered_domain`
- `source_rank`

### 4.5. `src/build_url_dataset.py`

Input:

- `data/processed/clean_master_dataset.parquet`

Output:

- `data/processed/url_model_dataset.parquet`
- `data/processed/url_model_dataset.stats.json`

Logic hien tai:

- chi lay `record_type = url`
- chi giu cac dong co `canonical_url` khong rong
- dat `sample_text = canonical_url`
- sap xep theo `collected_at`, `label`
- deduplicate theo `sample_text`
- loai bo benign neu trung voi URL da co nhan phishing

Cot dau ra cua `url_model_dataset.parquet`:

- `sample_text`
- `label`
- `source`
- `collected_at`
- `hostname`
- `registered_domain`
- `path`
- `query`
- `fragment`
- `scheme`
- `is_ip_host`
- `canonical_hostname`
- `canonical_url`

---

## 5. Feature engineering hien tai

### 5.1. `src/phishing_url_ml/feature_engineering.py`

Workflow hien tai da tach rieng feature cho `domain` va `url`.

Ham chinh:

- `build_feature_frame(df, dataset_kind)`

Trong do:

- `dataset_kind = domain` -> goi `build_domain_feature_frame(df)`
- `dataset_kind = url` -> goi `build_url_feature_frame(df)`

### 5.2. Feature cua `Domain Model`

Bo feature hien tai:

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

Dac diem:

- tap trung vao `hostname`, `registered_domain`, `subdomain`, `suffix`
- khong phu thuoc vao `path`, `query`, `fragment`

### 5.3. Feature cua `URL Model`

Bo feature hien tai van la lexical feature cho URL, gom nhom thong tin nhu:

- do dai chuoi
- so luong ky tu dac trung nhu `.`, `-`, `_`, `/`, `?`, `&`, `=`, `@`, `%`
- do dai `hostname`, `registered_domain`, `subdomain`, `path`, `query`, `fragment`
- `digit_ratio`, `special_char_ratio`, `unique_char_ratio`
- entropy cua `sample` va `hostname`
- `subdomain_depth`, `path_depth`, `query_param_count`
- `suspicious_token_count`
- `uses_http_scheme`, `uses_https_scheme`, `has_fragment`, `has_query`, `has_ip_host`

---

## 6. Train va danh gia model

### 6.1. `src/train_baselines.py`

Script nay co the train cho:

- `--dataset-kind domain`
- `--dataset-kind url`

Input mac dinh:

- `data/processed/domain_model_dataset.parquet`
- hoac `data/processed/url_model_dataset.parquet`

Luong xu ly hien tai:

1. doc model dataset
2. bo cac ngay ma `label` khong du ca `0` va `1`
3. chia `train / validation / test` theo `collected_at`
4. tao feature theo `dataset_kind`
5. train tat ca candidate models tren `train`
6. danh gia tren `validation`
7. chon model tot nhat theo `selection_metric`, mac dinh la `pr_auc`
8. fit lai tat ca candidate models tren `train + validation`
9. danh gia tren `test`
10. luu selected model va cac bang metric

Luu y:

- de split temporal hop le, sau khi bo ngay one-class phai con it nhat `3` ngay
- neu bat `--write-splits`, script se ghi parquet split ra `data/processed/`

### 6.2. Candidate models hien tai

- `logistic_regression`
- `linear_svm`
- `random_forest`
- `xgboost`
- `ann_mlp`
- `hybrid_lr_xgboost_ann`

Model `hybrid_lr_xgboost_ann` la `soft voting` tren:

- `Logistic Regression`
- `XGBoost`
- `ANN (MLPClassifier)`

### 6.3. Metric dang duoc tinh

- `precision`
- `recall`
- `f1`
- `roc_auc`
- `pr_auc`

Metric mac dinh de chon model:

- `pr_auc`

### 6.4. Output cua buoc train

Thu muc output:

- `models/domain/`
- `models/url/`

Files chinh:

- `validation_metrics.csv`
- `test_metrics.csv`
- `model_comparison.csv`
- `run_summary.json`
- `<selected_model_name>.joblib`

Neu co `--write-splits`, se co them:

- `data/processed/domain_train.parquet`
- `data/processed/domain_val.parquet`
- `data/processed/domain_test.parquet`

hoac bo split tuong ung cho URL.

---

## 7. Luong collector `OpenPhish` snapshot

### 7.1. `src/collect_openphish_snapshots.py`

Script nay khong train model va khong sua dataset processed.

Muc tieu:

- thu thap `OpenPhish` raw snapshot lien tuc de tich luy du lieu phishing theo thoi gian

Che do hien tai:

- mac dinh: chay lien tuc trong terminal
- mac dinh moi `20` phut tai `1` snapshot
- co the dung `--run-once` neu chi muon tai `1` lan roi thoat

Output:

- `data/raw/openphish_snapshots/openphish_YYYY-MM-DD_HH-MM.txt`

Vi du:

- `data/raw/openphish_snapshots/openphish_2026-04-05_00-55.txt`

### 7.2. `scripts/run_openphish_snapshot_once.cmd`

Day la wrapper de goi collector o che do:

- `--include-openphish`
- `--run-once`

No huu ich neu muon dung voi `Task Scheduler`, nhung hien tai cach van hanh de nhat van la chay terminal truc tiep.

### 7.3. Trang thai tich hop

Hien tai:

- snapshot moi van duoc luu de archive
- snapshot trong `data/raw/openphish_snapshots/` da duoc dua vao luong normalize khi chay source `openphish`
- khong can copy thu cong sang `data/raw/openphish/` nua

---

## 8. Cac file thong ke va tai lieu ho tro

- `docs/Model Dataset Statistics.md`: thong ke source, class balance, input dau vao cua cac model dataset
- `docs/Inspect Clean Master Dataset.md`: cach kiem tra `clean_master_dataset`
- `docs/Inspect Model Datasets.md`: cach kiem tra `domain_model_dataset` va `url_model_dataset`
- `docs/export_domain_model_data.py`: export du lieu va ket qua `Domain Model`
- `docs/export_url_model_data.py`: export du lieu va ket qua `URL Model`

---

## 9. Lenh chay thuong dung

### 9.1. Chay luong train chinh

```bash
python src/download_data.py --sources tranco openphish news_sitemaps mendeley_phishing_url mendeley_legitphish --include-openphish
python src/normalize_data.py --sources tranco openphish news_sitemaps mendeley_phishing_url mendeley_legitphish --include-openphish
python src/clean_data.py
python src/build_domain_dataset.py
python src/build_url_dataset.py
python src/train_baselines.py --dataset-kind domain --write-splits
python src/train_baselines.py --dataset-kind url --write-splits
```

### 9.2. Chay collector `OpenPhish` bang terminal

```bash
python src/collect_openphish_snapshots.py --include-openphish
```

Neu chi muon test `1` lan:

```bash
python src/collect_openphish_snapshots.py --include-openphish --run-once
```

---

## 10. Trang thai workflow hien tai

Nhung gi da dung:

- pipeline du lieu chinh da hoan chinh toi muc co the train duoc
- da co `domain dataset` va `url dataset` rieng
- da tach feature rieng cho `Domain Model` va `URL Model`
- da benchmark them `XGBoost`, `ANN`, `Hybrid`
- da co collector de tich luy `OpenPhish` snapshot theo `gio-phut`
- da chot `2` cau hinh official va dua `Hybrid` thanh model mac dinh cho ca `domain` va `url`

Nhung gi chua dung hoan toan:

- `Domain Model` van la bai toan kho hon `URL Model`
- can tiep tuc retrain dinh ky khi co them du lieu moi de danh gia do on dinh theo thoi gian
- can xay dung them lop suy luan / risk scoring de phuc vu huong `IDS` va `dashboard`

Workflow hien tai vi vay duoc hieu nhu sau:

- luong train chinh da san sang
- luong snapshot da san sang
- snapshot `OpenPhish` da duoc noi vao pipeline du lieu chinh
- viec tiep theo la giu raw gon va retrain dinh ky khi muon cap nhat model
