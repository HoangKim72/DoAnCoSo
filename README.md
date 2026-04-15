# DoAnCoSo

Pipeline nay dung de thu thap du lieu, lam sach, tao dataset va train baseline models cho de tai phat hien website phishing dua tren URL/domain bang hoc may.

## Cai dat

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Cau truc chinh

```text
data/
  raw/
    phishtank/
    openphish/
    openphish_snapshots/
    vn_benign_domain_addon/
    vn_benign_url_addon/
    vn_benign_url_runtime_patch/
    vn_phishing_url_addon/
    news_sitemaps/
    tranco/
  processed/
    experiments/
    official/
models/
src/
  phishing_url_ml/
  download_data.py
  normalize_data.py
  clean_data.py
  build_domain_dataset.py
  build_url_dataset.py
  bridge_ids_logs.py
  train_baselines.py
  run_ids_dashboard.py
```

## Quy trinh khuyen nghi

```bash
python src/download_data.py
python src/normalize_data.py
python src/clean_data.py
python src/build_domain_dataset.py
python src/build_url_dataset.py
python src/train_baselines.py --dataset-kind domain --write-splits
```

Neu muon lay bo du lieu thuc te dang duoc cau hinh trong repo nay:

```bash
python src/download_data.py --sources tranco openphish news_sitemaps mendeley_phishing_url mendeley_legitphish --include-openphish
python src/normalize_data.py --sources tranco openphish news_sitemaps mendeley_phishing_url mendeley_legitphish --include-openphish
python src/clean_data.py
python src/build_domain_dataset.py
python src/build_url_dataset.py
```

Neu muon bo sung `benign URL` moi tu cac publisher uy tin qua news sitemap:

```bash
python src/download_data.py --sources news_sitemaps --news-lookback-days 7 --news-max-urls-per-publisher 500
```

## Cac file dau ra chinh

- `data/processed/normalized_dataset.parquet`
- `data/processed/clean_master_dataset.parquet`
- `data/processed/domain_model_dataset.parquet`
- `data/processed/url_model_dataset.parquet`
- `models/domain/validation_metrics.csv`
- `models/domain/test_metrics.csv`
- `models/domain/model_comparison.csv`
- `models/domain/run_summary.json`
- `models/url/validation_metrics.csv`
- `models/url/test_metrics.csv`
- `models/url/model_comparison.csv`
- `models/url/run_summary.json`
- `data/runtime/ids_events.jsonl`

## IDS va Dashboard

Repo hien da co app nhe de:

- nhan `domain` hoac `URL` tu IDS
- suy luan bang `official models`
- luu lich su su kien
- hien thi dashboard de theo doi canh bao
- nap log IDS that tu `Suricata eve.json` hoac `Zeek JSON` thong qua bridge script

Chay local:

```bash
python src/run_ids_dashboard.py --host 127.0.0.1 --port 8080
```

Bridge log IDS that vao dashboard:

```bash
python src/bridge_ids_logs.py --input C:\suricata\log\eve.json --format suricata-eve --sensor-name lab-suricata --follow
python src/bridge_ids_logs.py --input C:\zeek\logs\current\dns.log --format zeek-dns-json --sensor-name lab-zeek --follow
python src/bridge_ids_logs.py --input C:\zeek\logs\current\http.log --format zeek-http-json --sensor-name lab-zeek --follow
python src/bridge_ids_logs.py --input C:\zeek\logs\current\ssl.log --format zeek-ssl-json --sensor-name lab-zeek --follow
```

Mo dashboard:

```text
http://127.0.0.1:8080/dashboard
```

API cho IDS:

- `POST /api/predict`: du doan nhung khong ghi log
- `POST /api/ingest`: du doan va ghi vao `data/runtime/ids_events.jsonl`
- `GET /api/events`: doc cac su kien gan day
- `GET /health`: kiem tra trang thai app va model

Vi du gui domain tu PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8080/api/ingest" `
  -ContentType "application/json" `
  -Body '{"dataset_kind":"domain","value":"paypal-account-security-check.com","source":"ids_browser_sensor"}'
```

Vi du gui URL:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8080/api/ingest" `
  -ContentType "application/json" `
  -Body '{"dataset_kind":"url","value":"http://example-login-verify.com/account/reset?token=12345","source":"ids_proxy_sensor"}'
```

## Gia dinh va canh bao quan trong

- `mendeley_phishing_url` la dataset `Phishing URL dataset` (DOI `10.17632/vfszbj9b36.1`, `CC BY 4.0`).
- `mendeley_legitphish` la dataset `LegitPhish Dataset` (DOI `10.17632/hx4m73v2sf.1`, `CC BY 4.0`).
- Voi 2 dataset Mendeley o tren, cot `collected_at` duoc gan theo ngay cong bo snapshot cua dataset (`2024-04-02` va `2025-04-07`) de co the danh gia theo thoi gian tren cac moc du lieu khac nhau.
- `OpenPhish` duoc de o che do opt-in, vi dieu khoan cong dong cua ho hien tai noi dich vu chi danh cho muc dich ca nhan; neu do an cua ban can dung nghiem tuc cho nghien cuu hoc thuat, nen xem chuong trinh Academic Use cua OpenPhish truoc khi bat source nay.
- `news_sitemaps` thu thap `benign URL candidates` tu sitemap cua cac publisher uy tin. Cac URL nay duoc weak-label la `label 0`, sau do van di qua buoc clean, overlap removal va dedup truoc khi train.
- `Tranco` mac dinh chi lay `100000` domain dau de pipeline nhe hon cho cac lan thu nghiem dau. Co the doi bang `--tranco-top-n 1000000`.
- `url_model_dataset.parquet` da co du 2 nhan tong the, nhung neu moc thoi gian moi nhat khong co `benign URL` thi `train_baselines.py --dataset-kind url` se dung o buoc temporal split/test.
- `train_baselines.py` chi chia train/validation/test theo thoi gian. Script hien tai se tu dong bo qua cac ngay chi co 1 nhan truoc khi split, nhung van can toi thieu `3` ngay con lai co du ca `label 0` va `label 1`.
- `train_baselines.py` hien so sanh `Logistic Regression`, `Linear SVM`, `Random Forest`, `XGBoost`, `ANN (MLP)` va cac bien the `hybrid` moi.
- `Domain Model` official hien dang dung `hybrid_xgboost_ann_weighted`.
- `URL Model` official hien dang dung `ann_mlp`.
- `build_domain_dataset.py` hien tu dong nap them benign domain addon tu `data/raw/vn_benign_domain_addon/*.csv`.
- `build_url_dataset.py` hien tu dong nap them benign URL addon tu `data/raw/vn_benign_url_addon/*.csv`.
- `build_url_dataset.py` hien tu dong nap them phishing URL addon tu `data/raw/vn_phishing_url_addon/*.csv`.
- Runtime IDS hien co them curated benign URL patch tu `data/raw/vn_benign_url_runtime_patch/*.csv` de giam false positive o mot so hostname/URL official phuc vu demo.
- `risk_level` trong runtime IDS duoc doc tu `models/runtime_risk_policy.json`.
- Neu `metadata` duoc gui kem theo event IDS, dashboard se hien them `sensor`, `event type`, va `src -> dest flow`.
