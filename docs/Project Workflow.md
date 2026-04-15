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

- Variant official: `official_current_26f_hybrid_xgboost_ann_weighted_120k_curated_benign_override`
- Dataset official: `data/processed/official/domain_model_official.parquet`
- Model official: `models/domain/hybrid_xgboost_ann_weighted.joblib`
- Rows: `120,006`
- Phishing: `72,004`
- Benign: `48,002`
- Feature count: `26`

### 2.2. URL Model

- Variant official: `official_current_66f_ann_mlp_full_540k_plus_url_hard_negative_hostaware_phishing_targeted`
- Dataset official: `data/processed/official/url_model_official.parquet`
- Model official: `models/url/ann_mlp.joblib`
- Rows: `540,023`
- Phishing: `166,866`
- Benign: `373,157`
- Feature count: `66`

Ghi chu cho `URL Model`:

- bo official hien tai dung full `url_model_dataset.parquet` moi nhat
- da cong them `81` benign URL hard-negative rows tu `data/raw/vn_benign_url_addon/`
- da cong them `14` phishing URL hard-case rows tu `data/raw/vn_phishing_url_addon/`
- da mo rong URL feature de nhin them vao `hostname/subdomain` va `cloud-edge hosting`
- vi bo raw hien tai khong con du `3` moc thoi gian co du ca `benign` va `phishing` de split `train / validation / test`, URL training van dung `latest mixed-date holdout`

Thong tin chot official duoc load tu:

- `models/official_model_registry.json`
- `models/runtime_risk_policy.json`

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
- `vn_benign_url_addon` cho rieng `URL Model`
- `vn_phishing_url_addon` cho rieng `URL Model`

### 3.3. Thu muc lien quan

- `data/raw/openphish/`: OpenPhish raw theo ngay
- `data/raw/openphish_snapshots/`: OpenPhish raw theo `gio-phut`
- `data/raw/vn_benign_domain_addon/`: benign domain addon duoc bo sung rieng
- `data/raw/vn_benign_url_addon/`: benign URL hard-negative addon duoc bo sung rieng
- `data/raw/vn_benign_url_runtime_patch/`: curated benign URL runtime patch cho huong demo IDS
- `data/raw/vn_phishing_url_addon/`: phishing URL hard-case addon duoc bo sung rieng
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
- them cac file `*.csv` trong `data/raw/vn_benign_url_addon/`
- them cac file `*.csv` trong `data/raw/vn_phishing_url_addon/`

Output:

- `data/processed/url_model_dataset.parquet`
- `data/processed/url_model_dataset.stats.json`

Logic:

- chi giu `record_type = url`
- dat `sample_text = canonical_url`
- merge them `vn_benign_url_addon`
- merge them `vn_phishing_url_addon`
- sort theo `collected_at`, `label`
- dedup theo `sample_text`
- bo benign neu URL do da co nhan phishing

---

## 5. Feature engineering

### 5.1. `Domain Model`

Feature hien tai:

- tong cong `26` feature
- giu cac feature domain co ban cu
- bo sung them cac feature moi nhu:
  - `avg_token_length_domain`
  - `max_token_length_domain`
  - `suspicious_token_count`
  - `brand_like_token_count`
  - `mixed_alnum_token_count`
  - `brand_in_subdomain_only`
  - `brand_in_registered_domain`
  - `num_brand_mentions`
  - `closest_brand_similarity_ratio`
  - `token_entropy_max`
  - `consecutive_digit_run_max`

### 5.2. `URL Model`

Feature hien tai:

- tong cong `66` feature
- giu cac nhom lexical/path/query co san
- bo sung them cac feature moi nhu:
  - `avg_path_segment_length`
  - `max_path_segment_length`
  - `num_numeric_segments`
  - `num_mixed_segments`
  - `path_entropy`
  - `query_key_count`
  - `query_value_length_max`
  - `percent_encoded_ratio`
  - `path_has_login_segment`
  - `path_has_verify_segment`
  - `path_has_brand_segment`
  - `path_has_user_action_keyword`
  - `has_redirect_param`
  - `redirect_param_count`
  - `sensitive_param_count`
  - `base64_like_value_present`
  - `contains_double_slash_in_path`
  - `port_specified_flag`
  - `hostname_mixed_alnum_token_count`
  - `hostname_token_entropy_max`
  - `hostname_consecutive_digit_run_max`
  - `subdomain_mixed_alnum_token_count`
  - `subdomain_token_entropy_max`
  - `subdomain_consecutive_digit_run_max`
  - `hostname_contains_sensitive_keyword`
  - `hostname_order_delivery_keyword_count`
  - `subdomain_order_delivery_keyword_count`
  - `registered_domain_is_cloud_edge_hosting`
  - `registered_domain_is_user_content_hosting`

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
- `hybrid_lr_xgboost_ann_weighted`
- `hybrid_xgboost_ann_weighted`
- `hybrid_lr_xgboost_ann_calibrated`
- `hybrid_stack_meta_lr`

Metric tinh:

- `precision`
- `recall`
- `f1`
- `roc_auc`
- `pr_auc`

Metric mac dinh de chon:

- `pr_auc`

Luu y quan trong:

- voi `Domain Model`, repo hien chot `hybrid_xgboost_ann_weighted` lam official
- voi `URL Model`, repo hien chot `ann_mlp` lam official
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
- `src/bridge_ids_logs.py`

Lenh chay:

```bash
python src/run_ids_dashboard.py --host 127.0.0.1 --port 8080
```

Script nay tao Flask app bang:

- `src/phishing_url_ml/ids_dashboard_app.py`

### 8.2. Dau vao tu IDS hoac giao dien

He thong co `3` cach dua du lieu vao:

1. bridge log IDS that:
   - `python src/bridge_ids_logs.py --input ...`
   - ho tro `Suricata eve.json`, `Zeek dns/http/ssl JSON`
2. IDS/gui script ngoai goi API truc tiep:
   - `POST /api/predict`
   - `POST /api/ingest`
3. nguoi dung nhap tay tren giao dien:
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
  "source": "ids_browser_sensor",
  "metadata": {
    "sensor_name": "lab-suricata",
    "ids_event_type": "dns",
    "src_ip": "10.10.10.5",
    "dest_ip": "8.8.8.8"
  }
}
```

### 8.3. App nhan request

Trong `ids_dashboard_app.py`:

- `parse_request_payload()` doc JSON hoac form
- `api_predict()` xu ly du doan nhung khong ghi log
- `api_ingest()` xu ly du doan va ghi log vao runtime
- dashboard API giu nguyen `metadata` de UI co the hien `sensor`, `event type`, `src -> dest`

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
10. curated runtime override
   - `Domain Model`: doc `data/raw/vn_benign_domain_addon/*.csv`
   - `URL Model`: doc `data/raw/vn_benign_url_runtime_patch/*.csv`
   - neu trung exact hostname/exact URL da curate, event van duoc ghi log nhung ha ve `benign/minimal`

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
- `decision_mode`
- `model_name`
- `variant_name`
- `signals`
- `recommendation`
- `metadata`
- `sensor_name`
- `ids_event_type`
- `flow_summary`

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

Neu event den tu bridge IDS that, UI hien them:

- `sensor`
- `event type`
- `src -> dest flow`
- `decision mode`

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

### 9.4. Bridge log IDS that

```bash
python src/bridge_ids_logs.py --input C:\suricata\log\eve.json --format suricata-eve --sensor-name lab-suricata --follow
python src/bridge_ids_logs.py --input C:\zeek\logs\current\dns.log --format zeek-dns-json --sensor-name lab-zeek --follow
python src/bridge_ids_logs.py --input C:\zeek\logs\current\http.log --format zeek-http-json --sensor-name lab-zeek --follow
python src/bridge_ids_logs.py --input C:\zeek\logs\current\ssl.log --format zeek-ssl-json --sensor-name lab-zeek --follow
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

- `docs/Official Model Results - Current.md`
- `docs/IDS Dashboard Integration.md`
- `docs/Activity History.md`

---

## 11. Trang thai workflow hien tai

Nhung gi da san sang:

- pipeline data de train
- collector `OpenPhish` snapshot
- benign domain addon cho `Domain Model`
- benign URL hard-negative addon cho `URL Model`
- phishing URL hard-case addon cho `URL Model`
- official `Domain Model` va `URL Model`
- runtime risk policy cho IDS
- API runtime cho IDS
- dashboard web de monitor

Nhung gi van can tiep tuc:

- bo sung them bo real-world validation
- tiep tuc giam false positive cho nhom URL kho
- retrain dinh ky khi co du lieu moi
- canh chinh threshold theo muc tieu van hanh thuc te
