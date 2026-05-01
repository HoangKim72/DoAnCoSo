# Project Workflow

## 1. Muc tieu cua du an

Du an nay xay dung he thong phat hien website phishing bang hoc may, theo 2 bai toan song song:

- `Domain Model`: dung khi he thong chi thu duoc `domain / hostname / FQDN / TLS SNI`
- `URL Model`: dung khi he thong thu duoc `full URL`

Repo hien tai khong chi gom phan train model, ma co day du 4 lop:

1. `Thu thap du lieu raw`
2. `Chuan hoa + lam sach + build dataset`
3. `Train va chon model official`
4. `Runtime suy luan + dashboard + bridge tu IDS`

Noi ngan gon:

`raw feeds -> normalized_dataset -> clean_master_dataset -> domain/url model dataset -> train -> official model -> runtime API/dashboard`

---

## 2. Trang thai official hien tai

### 2.1. Domain Model

- Variant official: `official_current_26f_hybrid_xgboost_ann_weighted_120k_curated_benign_override`
- Dataset official: `data/processed/official/domain_model_official.parquet`
- Model official: `models/domain/hybrid_xgboost_ann_weighted.joblib`
- Rows: `120,006`
- Benign: `48,002`
- Phishing: `72,004`
- Feature count: `26`

### 2.2. URL Model

- Variant official: `official_current_66f_ann_mlp_full_540k_plus_url_hard_negative_hostaware_phishing_targeted`
- Dataset official: `data/processed/official/url_model_official.parquet`
- Model official: `models/url/ann_mlp.joblib`
- Rows: `540,023`
- Benign: `373,157`
- Phishing: `166,866`
- Feature count: `66`

Thong tin chot official duoc dashboard va runtime doc tu:

- `models/official_model_registry.json`
- `models/runtime_risk_policy.json`

---

## 3. Cau truc du lieu va artifact chinh

### 3.1. Thu muc du lieu

- `data/raw/`: du lieu goc tai ve hoac curate thu cong
- `data/processed/`: du lieu sau normalize, clean, build dataset
- `data/processed/official/`: snapshot dataset official da chot
- `data/runtime/`: log su kien runtime va state cua IDS bridge
- `data/validation/`: seed va ket qua danh gia thuc chien
- `models/domain/`: artifact official cua Domain Model
- `models/url/`: artifact official cua URL Model

### 3.2. Cac file dau ra quan trong

| File | Y nghia |
| --- | --- |
| `data/processed/normalized_dataset.parquet` | Toan bo raw feeds da dua ve cung schema |
| `data/processed/clean_master_dataset.parquet` | Du lieu da parse, canonicalize, loai loi, loai overlap, dedup |
| `data/processed/domain_model_dataset.parquet` | Dataset dau vao cho Domain Model |
| `data/processed/url_model_dataset.parquet` | Dataset dau vao cho URL Model |
| `data/processed/official/domain_model_official.parquet` | Snapshot official cho domain |
| `data/processed/official/url_model_official.parquet` | Snapshot official cho url |
| `models/domain/run_summary.json` | Toan bo thong tin train, split, metric, feature cua domain official |
| `models/url/run_summary.json` | Toan bo thong tin train, split, metric, feature cua url official |
| `data/runtime/ids_events.jsonl` | Event log runtime cua dashboard/API |

---

## 4. Luong train: end-to-end tu raw den model

## 4.1. Buoc 1 - Thu thap raw data: `src/download_data.py`

### Muc dich

Tai du lieu raw ve `data/raw/` theo tung nguon.

### Dau vao cua script

- CLI arguments:
  - `--sources`
  - `--include-openphish`
  - `--overwrite`
  - `--news-publishers`
  - `--news-lookback-days`
  - `--news-max-urls-per-publisher`
  - `--news-max-sitemaps-per-publisher`

### Dau vao thuc te theo tung source

| Source | Dau vao that | Dang file raw |
| --- | --- | --- |
| `tranco` | `https://tranco-list.eu/top-1m.csv.zip` | `.csv.zip` |
| `openphish` | `https://openphish.com/feed.txt` | `.txt` |
| `phishtank` | `http://data.phishtank.com/data/online-valid.json` | `.json` |
| `mendeley_phishing_url` | Mendeley DOI `10.17632/vfszbj9b36.1` | `.zip` |
| `mendeley_legitphish` | Mendeley DOI `10.17632/hx4m73v2sf.1` | `.zip` |
| `news_sitemaps` | URL sitemap cua cac publisher trong `settings.py` | `.json` |

### Dau ra mac dinh

| Source | Thu muc raw | Vi du file |
| --- | --- | --- |
| `tranco` | `data/raw/tranco/` | `tranco_YYYY-MM-DD.csv.zip` |
| `openphish` | `data/raw/openphish/` | `openphish_YYYY-MM-DD.txt` |
| `phishtank` | `data/raw/phishtank/` | `phishtank_YYYY-MM-DD.json` |
| `mendeley_phishing_url` | `data/raw/mendeley_phishing_url/` | `mendeley_phishing_url_YYYY-MM-DD.zip` |
| `mendeley_legitphish` | `data/raw/mendeley_legitphish/` | `mendeley_legitphish_YYYY-MM-DD.zip` |
| `news_sitemaps` | `data/raw/news_sitemaps/` | `news_sitemaps_YYYY-MM-DD.json` |

### Ghi chu

- `OpenPhish` la source `opt-in`, chi duoc download khi co `--include-openphish`.
- `news_sitemaps` khong la file tai ve truc tiep, ma la file JSON duoc script tu thu thap tu cac sitemap publisher.

---

## 4.2. Buoc 2 - Normalize raw files: `src/normalize_data.py`

### Muc dich

Doc nhieu dinh dang raw khac nhau va dua ve chung mot schema.

### Dau vao cua script

- CLI arguments:
  - `--sources`
  - `--include-openphish`
  - `--start-date`
  - `--end-date`
  - `--tranco-top-n`
  - `--output`

### Dau vao file cua script

Script doc raw files bang `iter_raw_files()` trong `src/phishing_url_ml/utils.py`.

Ghi chu quan trong:

- Khi normalize source `openphish`, script doc ca:
  - `data/raw/openphish/`
  - `data/raw/openphish_snapshots/`

### Schema output chuan

File output `normalized_dataset.parquet` luon co cac cot:

| Cot | Y nghia |
| --- | --- |
| `original_value` | Gia tri goc, co the la domain hoac url |
| `label` | `0 = benign`, `1 = phishing` |
| `source` | Ten nguon du lieu |
| `collected_at` | Ngay gan cho sample |
| `record_type` | `domain` hoac `url` |
| `source_record_id` | ID goc cua record neu co |
| `source_rank` | Thu hang nguon, dung cho Tranco |
| `source_target` | Thong tin phu, vi du publisher hoac target brand |

### Mapping tung source khi normalize

| Source | `record_type` | `label` | `original_value` lay tu dau |
| --- | --- | --- | --- |
| `tranco` | `domain` | `0` | cot domain trong CSV |
| `openphish` | `url` | `1` | tung dong trong TXT |
| `phishtank` | `url` | `1` | truong `url` trong JSON |
| `news_sitemaps` | `url` | `0` | truong `url` trong JSON |
| `mendeley_phishing_url` | `url` | map tu cot `type` | cot `url` |
| `mendeley_legitphish` | `url` | map tu cot `ClassLabel` | cot `URL` |

### Dau ra mac dinh

- `data/processed/normalized_dataset.parquet`

### Y nghia

Day la file dau tien trong pipeline ma cac nguon da co chung schema, nhung chua parse domain/url, chua canonicalize, chua dedup.

---

## 4.3. Buoc 3 - Clean du lieu: `src/clean_data.py`

### Muc dich

Lam sach `normalized_dataset.parquet` de tao `clean_master_dataset.parquet`.

### Dau vao cua script

- Input mac dinh: `data/processed/normalized_dataset.parquet`

Script bat buoc file input phai co cac cot:

- `original_value`
- `label`
- `source`
- `collected_at`
- `record_type`

### Xu ly chinh

- Parse `domain` hoac `url` bang `build_parsed_record()`
- Canonicalize:
  - `canonical_hostname`
  - `canonical_registered_domain`
  - `canonical_url`
- Loai cac dong loi:
  - `unsupported_scheme`
  - `invalid_hostname`
  - `missing_hostname`
  - `invalid_url_parse`
- Loai overlap giua benign va phishing:
  - benign co `canonical_hostname` trung phishing bi loai
  - benign co `canonical_url` trung phishing bi loai
- Dedup:
  - `domain` dedup theo `canonical_hostname`
  - `url` dedup theo `canonical_url`

### Schema output chinh

| Cot | Y nghia |
| --- | --- |
| `original_value` | Gia tri goc truoc clean |
| `label` | `0/1` |
| `source` | Nguon |
| `collected_at` | Ngay thu thap |
| `record_type` | `domain` hoac `url` |
| `source_record_id` | ID goc |
| `source_rank` | Rank goc |
| `source_target` | Muc tieu/phu chu |
| `scheme` | `http/https` neu la URL |
| `hostname` | Hostname da parse |
| `subdomain` | Subdomain |
| `domain` | Domain phan than |
| `suffix` | TLD/public suffix |
| `registered_domain` | Registered domain |
| `path` | Path cua URL |
| `query` | Query cua URL |
| `fragment` | Fragment cua URL |
| `is_ip_host` | Co phai IP host hay khong |
| `canonical_domain` | Domain da canonicalize |
| `canonical_hostname` | Hostname da canonicalize |
| `canonical_registered_domain` | Registered domain da canonicalize |
| `canonical_url` | URL da canonicalize |

### Dau ra mac dinh

- `data/processed/clean_master_dataset.parquet`
- `data/processed/clean_master_dataset.stats.json`

### Y nghia

Day la file `master` da clean. Tu day pipeline tach thanh 2 nhanh:

- nhanh `domain`
- nhanh `url`

---

## 4.4. Buoc 4A - Build dataset cho Domain Model: `src/build_domain_dataset.py`

### Muc dich

Lay phan du lieu can cho bai toan domain va merge them benign domain addon curate.

### Dau vao cua script

- Input mac dinh: `data/processed/clean_master_dataset.parquet`
- Tu dong doc them tat ca `*.csv` trong:
  - `data/raw/vn_benign_domain_addon/`

### Script yeu cau input master co cac cot

- `label`
- `source`
- `collected_at`
- `hostname`
- `registered_domain`
- `canonical_hostname`

### Logic xu ly

- Chi giu row co `canonical_hostname` khac rong
- Dat `sample_text = canonical_hostname`
- Merge them benign domain addon
- Sort theo `collected_at`, `label`
- Dedup theo `sample_text`
- Neu 1 domain vua co nhan benign vua co nhan phishing thi giu phishing, bo benign overlap

### Schema output

| Cot | Y nghia |
| --- | --- |
| `sample_text` | Chuoi domain/hostname dua vao model |
| `label` | `0/1` |
| `source` | Nguon |
| `collected_at` | Ngay |
| `record_type` | Luon la `domain` |
| `hostname` | Hostname |
| `registered_domain` | Registered domain |
| `subdomain` | Subdomain |
| `suffix` | Suffix |
| `is_ip_host` | Co phai IP hay khong |
| `canonical_hostname` | Hostname canonical |
| `canonical_registered_domain` | Registered domain canonical |
| `source_rank` | Rank neu co |

### Dau ra mac dinh

- `data/processed/domain_model_dataset.parquet`
- `data/processed/domain_model_dataset.stats.json`

### Y nghia

Day la input truc tiep de train `Domain Model`.

---

## 4.5. Buoc 4B - Build dataset cho URL Model: `src/build_url_dataset.py`

### Muc dich

Lay phan du lieu can cho bai toan URL va merge them cac addon curate cho URL.

### Dau vao cua script

- Input mac dinh: `data/processed/clean_master_dataset.parquet`
- Tu dong doc them tat ca `*.csv` trong:
  - `data/raw/vn_benign_url_addon/`
  - `data/raw/vn_phishing_url_addon/`

### Script yeu cau input master co cac cot

- `label`
- `source`
- `collected_at`
- `canonical_url`
- `hostname`
- `path`
- `query`

### Logic xu ly

- Chi giu `record_type = url`
- Dat `sample_text = canonical_url`
- Merge them benign URL addon
- Merge them phishing URL addon
- Sort theo `collected_at`, `label`
- Dedup theo `sample_text`
- Neu 1 URL vua co benign vua co phishing thi bo benign overlap

### Schema output

| Cot | Y nghia |
| --- | --- |
| `sample_text` | URL canonical dua vao model |
| `label` | `0/1` |
| `source` | Nguon |
| `collected_at` | Ngay |
| `hostname` | Hostname |
| `registered_domain` | Registered domain |
| `path` | Path |
| `query` | Query |
| `fragment` | Fragment |
| `scheme` | `http/https` |
| `is_ip_host` | Co phai IP host hay khong |
| `canonical_hostname` | Hostname canonical |
| `canonical_url` | URL canonical |

### Dau ra mac dinh

- `data/processed/url_model_dataset.parquet`
- `data/processed/url_model_dataset.stats.json`

### Y nghia

Day la input truc tiep de train `URL Model`.

---

## 4.6. Buoc 5 - Feature engineering: `src/phishing_url_ml/feature_engineering.py`

### Muc dich

Bien doi `domain_model_dataset` va `url_model_dataset` thanh ma tran feature so de train model.

### Dau vao logic

- DataFrame chua `sample_text` va cac cot parse lien quan
- `dataset_kind = domain` hoac `url`

### Dau ra logic

- Feature frame so hoc dung de train va infer

### So feature hien tai

- `Domain Model`: `26` feature
- `URL Model`: `66` feature

### Vi du nhom feature

`Domain`:

- `domain_length`
- `subdomain_count`
- `contains_brand_name`
- `contains_sensitive_keyword`
- `closest_brand_similarity_ratio`
- `tld_risk_score`
- `is_idn_or_punycode`

`URL`:

- `sample_length`
- `hostname_length`
- `path_length`
- `query_param_count`
- `suspicious_token_count`
- `path_has_login_segment`
- `has_redirect_param`
- `registered_domain_is_cloud_edge_hosting`
- `registered_domain_is_user_content_hosting`

---

## 4.7. Buoc 6 - Train va chon model: `src/train_baselines.py`

### Muc dich

Train nhieu candidate models, so sanh metric, chon model tot nhat theo metric validation, sau do retrain va danh gia tren test.

### Dau vao cua script

- CLI arguments chinh:
  - `--dataset-kind`
  - `--input`
  - `--selection-metric`
  - `--write-splits`
  - `--output-dir`
  - `--models`
  - `--domain-balance-strategy`
  - `--split-strategy`

### Input parquet mac dinh

| `dataset_kind` | Input mac dinh |
| --- | --- |
| `domain` | `data/processed/domain_model_dataset.parquet` |
| `url` | `data/processed/url_model_dataset.parquet` |

### Script yeu cau file input co cac cot

- `sample_text`
- `label`
- `collected_at`

### Cac buoc xu ly ben trong

1. Doc dataset parquet
2. Kiem tra dataset co du `2` nhan hay khong
3. Tao split train/validation/test
4. Tao feature frame bang `build_feature_frame()`
5. Train cac candidate models
6. So sanh metric tren validation
7. Chon best model theo `selection_metric`
8. Train lai best model tren `train + validation`
9. Danh gia tren test
10. Luu model va artifact

### Candidate models hien co

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

### Split strategy

#### `domain`

- Mac dinh dung `temporal split`
- Truoc khi split, loai cac ngay chi co 1 nhan
- Co the can bang domain dataset bang:
  - `per_date_under`
  - `global_under`
  - `none`

#### `url`

- Uu tien `temporal split` neu du `3` moc mixed-label
- Neu khong du, co the fallback sang:
  - `url_latest_mixed_holdout`

### Dau ra cua script

Trong `models/domain/` hoac `models/url/`:

- `validation_metrics.csv`
- `test_metrics.csv`
- `model_comparison.csv`
- `<best_model_name>.joblib`
- `run_summary.json`

Neu co `--write-splits`, script ghi them:

- `data/processed/domain_train.parquet`
- `data/processed/domain_val.parquet`
- `data/processed/domain_test.parquet`

hoac:

- `data/processed/url_train.parquet`
- `data/processed/url_val.parquet`
- `data/processed/url_test.parquet`

### Y nghia cua `run_summary.json`

Day la file quan trong nhat de doc lai mot lan train. No ghi:

- input path
- split strategy
- balance strategy
- class distribution truoc/sau xu ly
- metric validation/test cua tung model
- model duoc chon
- split rows
- split dates
- feature columns
- duong dan artifact model

---

## 4.8. Buoc 7 - Dong bang snapshot official

Sau khi mot cau hinh duoc chon lam official, repo giu 2 lop artifact:

1. `model artifact`
2. `official dataset snapshot`

File lien quan:

- `models/official_model_registry.json`
- `data/processed/official/domain_model_official.parquet`
- `data/processed/official/url_model_official.parquet`

Y nghia:

- Runtime va dashboard khong tu dong doc model thoi diem train tam thoi
- Runtime chi doc model duoc khai bao trong `official_model_registry.json`

---

## 5. Luong runtime: tu input thuc te den ket qua dashboard

## 5.1. Khoi dong web app: `src/run_ids_dashboard.py`

### Dau vao

- CLI args:
  - `--host`
  - `--port`
  - `--debug`

### Dau ra

- Chay Flask app cua dashboard/API
- Default local URL:
  - `http://127.0.0.1:8080/dashboard`

### Route chinh

- `GET /health`
- `GET /dashboard`
- `GET /dashboard/events`
- `GET /api/events`
- `POST /api/predict`
- `POST /api/ingest`

---

## 5.2. Dau vao runtime

He thong runtime co 3 cach nhan du lieu:

1. Nguoi dung nhap tay tren dashboard
2. He thong ngoai goi API truc tiep
3. IDS bridge doc log tu Suricata/Zeek roi day vao API

### Payload runtime co dang

```json
{
  "dataset_kind": "domain",
  "value": "hocvudientu.hutech.edu.vn",
  "source": "ids_sensor",
  "metadata": {
    "sensor_name": "lab-suricata",
    "ids_event_type": "dns",
    "src_ip": "10.10.10.5",
    "dest_ip": "8.8.8.8"
  }
}
```

### Y nghia tung truong

| Truong | Y nghia |
| --- | --- |
| `dataset_kind` | `domain`, `url`, hoac `auto` |
| `value` | Gia tri can check |
| `source` | Nguon gui event |
| `metadata` | Thong tin phu de dashboard hien thi context |

---

## 5.3. Suy luan runtime: `src/phishing_url_ml/inference.py`

### Dau vao logic cua `predict_value()`

- `value`
- `dataset_kind`
- `source`
- `persist`
- `metadata`

### Cac buoc xu ly

1. `detect_dataset_kind()`
   - Neu `auto` thi tu suy ra la `domain` hay `url`
2. `load_official_model_bundle()`
   - Doc `models/official_model_registry.json`
   - Nap dung model official cho `domain` hoac `url`
3. `build_inference_row()`
   - Parse input thanh row co schema gan giong luc train
4. `build_feature_frame()`
   - Tao feature cho input runtime
5. `model.predict()`
   - Du doan `benign` hoac `phishing`
6. `normalized_score_for_model()`
   - Lay score tu `predict_proba` hoac `decision_function`
7. `risk_level_for_score()`
   - Gan `minimal / low / medium / high`
8. `curated benign override`
   - Neu model bao `phishing` nhung input nam trong danh sach benign da curate, runtime ha ket qua xuong `benign`
9. Tao event JSON de tra ve hoac ghi log

### Dau vao file cua runtime

| File | Duoc runtime doc de lam gi |
| --- | --- |
| `models/official_model_registry.json` | Biet model nao dang la official |
| `models/domain/*.joblib` | Model domain official |
| `models/url/*.joblib` | Model url official |
| `models/runtime_risk_policy.json` | Nguong risk level |
| `data/raw/vn_benign_domain_addon/*.csv` | Curated benign domain override |
| `data/raw/vn_benign_url_runtime_patch/*.csv` | Curated benign URL runtime patch |

### Dau ra cua `predict_value()`

Event JSON chua cac truong chinh:

| Truong | Y nghia |
| --- | --- |
| `dataset_kind` | domain/url |
| `raw_value` | Gia tri goc |
| `normalized_value` | Gia tri sau parse/canonicalize |
| `predicted_label` | `0/1` |
| `predicted_class` | `benign/phishing` |
| `score` | Diem cua model sau runtime |
| `risk_level` | `minimal/low/medium/high` |
| `model_name` | Ten model official dang dung |
| `variant_name` | Variant official |
| `decision_mode` | `model` hoac `model_plus_curated_benign_override` |
| `signals` | Cac tin hieu giai thich ngan |
| `recommendation` | Khuyen nghi de hien thi tren UI |
| `metadata` | Sensor, event type, flow, ... |

### Phan biet `model official quality` va `runtime mitigation`

- `model official quality`: chat luong thuan cua model da train
- `runtime mitigation`: cac rule runtime nhu `risk policy` va `curated benign override` de giam false positive khi demo/van hanh

Noi ngan gon:

- model la `bo nao`
- runtime mitigation la `lop xu ly bao quanh model`

---

## 5.4. Event log runtime

Neu request di qua `POST /api/ingest`, he thong ghi event vao:

- `data/runtime/ids_events.jsonl`

Moi dong la 1 event JSON.

Dashboard doc file nay de:

- hien recent events
- tinh tong so event
- tinh so phishing / benign / high risk
- show history page

---

## 5.5. Dashboard UI: `src/phishing_url_ml/ids_dashboard_app.py`

### Dau vao logic

- `load_events(limit=...)`
- `summarize_events(events)`
- `official_model_cards()`
- ket qua tu `predict_value()`

### Dau ra

- Trang checker chinh `/dashboard`
- Trang lich su `/dashboard/events`
- API JSON `/api/events`

### Dashboard hien gi

- Form nhap domain/url
- Ket qua suy luan
- Tong quan event
- Card thong tin 2 model official
- Recent logs
- Sensor, event type, observed time, flow, decision mode

---

## 5.6. Bridge tu IDS that: `src/bridge_ids_logs.py`

### Muc dich

Doc log JSON tu IDS that, chuyen thanh payload runtime va day vao `POST /api/ingest`.

### Dau vao cua script

- `--input`
- `--format`
- `--api-url`
- `--source`
- `--sensor-name`
- `--state-file`
- `--follow`
- `--start-at-end`
- `--poll-interval`
- `--timeout`
- `--dry-run`
- `--limit`
- `--continue-on-error`

### Dinh dang log duoc ho tro

- `suricata-eve`
- `zeek-dns-json`
- `zeek-http-json`
- `zeek-ssl-json`
- `zeek-tls-json`
- `auto`

### Mapping IDS -> model

| Nguon log | Truong IDS | Gia tri runtime | `dataset_kind` |
| --- | --- | --- | --- |
| Suricata DNS | `dns.rrname` / `dns.query` | domain | `domain` |
| Suricata TLS | `tls.sni` | domain | `domain` |
| Suricata HTTP | `http.hostname + http.url` | full URL | `url` |
| Zeek DNS | `query` | domain | `domain` |
| Zeek HTTP | `host + uri` | full URL | `url` |
| Zeek SSL/TLS | `server_name` | domain | `domain` |

### Metadata duoc bridge gui kem

- `sensor_name`
- `parser_format`
- `ids_event_type`
- `observed_at`
- `src_ip`
- `src_port`
- `dest_ip`
- `dest_port`
- `uid`
- `flow_id`
- `community_id`
- `log_path`
- `log_line_number`
- `http_method` neu co

### Dau ra

- Neu `--dry-run`: in JSON payload ra man hinh
- Neu gui that: POST tung event vao dashboard API
- Co the ghi state vao:
  - `data/runtime/ids_bridge_state.json`

---

## 6. Luong danh gia thuc chien

## 6.1. Seed validation

Thu muc:

- `data/validation/`

Seed file chinh:

- `vn_real_world_benign_seed.csv`
- `vn_real_world_phishing_seed.csv`
- `vn_real_world_validation_seed_expanded.csv`

### Schema seed validation

Script `src/evaluate_real_world_validation.py` yeu cau:

- `sample_id`
- `category`
- `dataset_kind`
- `input_value`
- `expected_label`
- `priority`

### Dau ra

Script tao:

- `*_detailed_*.csv`
- `*_by_dataset_kind_*.csv`
- `*_by_priority_*.csv`
- `*_by_category_*.csv`
- `*_errors_by_category_*.csv`
- `*_errors_by_token_pattern_*.csv`
- `*_summary_*.json`
- file report `.md`

Y nghia:

- Day la bo danh gia ngoai doi thuc, khong thay the cho holdout test cua training pipeline.

---

## 7. Lenh chay thong dung

### 7.1. Rebuild pipeline data

```bash
python src/download_data.py --sources tranco openphish news_sitemaps mendeley_phishing_url mendeley_legitphish --include-openphish
python src/normalize_data.py --sources tranco openphish news_sitemaps mendeley_phishing_url mendeley_legitphish --include-openphish
python src/clean_data.py
python src/build_domain_dataset.py
python src/build_url_dataset.py
```

### 7.2. Train lai model

```bash
python src/train_baselines.py --dataset-kind domain --write-splits
python src/train_baselines.py --dataset-kind url --write-splits
```

### 7.3. Chay dashboard

```bash
python src/run_ids_dashboard.py --host 127.0.0.1 --port 8080
```

### 7.4. Bridge log IDS that

```bash
python src/bridge_ids_logs.py --input C:\suricata\log\eve.json --format suricata-eve --sensor-name lab-suricata --follow
python src/bridge_ids_logs.py --input C:\zeek\logs\current\dns.log --format zeek-dns-json --sensor-name lab-zeek --follow
python src/bridge_ids_logs.py --input C:\zeek\logs\current\http.log --format zeek-http-json --sensor-name lab-zeek --follow
python src/bridge_ids_logs.py --input C:\zeek\logs\current\ssl.log --format zeek-ssl-json --sensor-name lab-zeek --follow
```

---

## 8. Bang tom tat: file nao nhan input gi, ghi output gi

| File | Input chinh | Output chinh | Vai tro |
| --- | --- | --- | --- |
| `src/download_data.py` | remote feeds + CLI args | file raw trong `data/raw/` | tai du lieu goc |
| `src/normalize_data.py` | raw files trong `data/raw/` | `normalized_dataset.parquet` | dua ve chung schema |
| `src/clean_data.py` | `normalized_dataset.parquet` | `clean_master_dataset.parquet` + stats | lam sach, parse, canonicalize |
| `src/build_domain_dataset.py` | `clean_master_dataset.parquet` + `vn_benign_domain_addon/*.csv` | `domain_model_dataset.parquet` + stats | tao dataset cho domain |
| `src/build_url_dataset.py` | `clean_master_dataset.parquet` + `vn_benign_url_addon/*.csv` + `vn_phishing_url_addon/*.csv` | `url_model_dataset.parquet` + stats | tao dataset cho url |
| `src/train_baselines.py` | `domain_model_dataset.parquet` hoac `url_model_dataset.parquet` | model `.joblib`, metrics CSV, `run_summary.json` | train va chon model |
| `src/run_ids_dashboard.py` | host/port CLI | Flask app local | chay API + dashboard |
| `src/phishing_url_ml/inference.py` | runtime payload + official registry + risk policy + curated patches | event JSON suy luan | logic infer runtime |
| `src/bridge_ids_logs.py` | IDS JSON log + API URL | POST vao `/api/ingest` + state file | nap log IDS vao dashboard |
| `src/evaluate_real_world_validation.py` | validation seed CSV | report CSV/JSON/MD | danh gia thuc chien |

---

## 9. Cach doc du an nhanh neu mo lai sau nay

Neu can quay lai du an va nam lai nhanh, nen doc theo thu tu nay:

1. `models/official_model_registry.json`
2. `models/domain/run_summary.json`
3. `models/url/run_summary.json`
4. `docs/Official Model Results - Current.md`
5. `docs/VN Real-World Validation Results - expanded.md`
6. file nay: `docs/Project Workflow.md`

Neu can chay demo:

1. chay `python src/run_ids_dashboard.py`
2. mo `http://127.0.0.1:8080/dashboard`
3. neu co log IDS, chay them `python src/bridge_ids_logs.py --input ... --format ... --follow`

---

## 10. Tong ket ngan

Ban chat cua du an la:

- `Du lieu raw` tu nhieu nguon
- duoc `normalize`
- duoc `clean`
- duoc tach thanh `domain dataset` va `url dataset`
- duoc `train` de chon model official
- sau do duoc dua vao `runtime API/dashboard`
- va co the nhan input truc tiep tu `Suricata` hoac `Zeek`

Vi vay, day la mot he thong phishing detection hoan chinh theo kieu:

`data pipeline + machine learning models + runtime inference + IDS demo integration`
