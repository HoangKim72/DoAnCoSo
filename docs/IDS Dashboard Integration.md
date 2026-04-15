# IDS Dashboard Integration

File nay mo ta luong tich hop `IDS -> model inference -> dashboard` trong repo hien tai.

## 1. Muc tieu

Khi nguoi dung truy cap mot trang web, IDS co the gui:

- `domain`
- hoac `full URL`

ve app local. App se:

1. chon `Domain Model` hoac `URL Model`
2. trich xuat feature tu input vua nhan
3. suy luan bang `official model`
4. luu log su kien
5. hien thi len dashboard de theo doi

## 2. Thanh phan moi

- `src/run_ids_dashboard.py`
  - lenh chay web app local
- `src/bridge_ids_logs.py`
  - bridge log `Suricata/Zeek JSON` vao `POST /api/ingest`
- `src/phishing_url_ml/inference.py`
  - load `official models`
  - parse input
  - build feature
  - predict
  - luu event vao log
- `data/raw/vn_benign_url_runtime_patch/`
  - curated runtime patch cho mot so URL/hostname benign dung cho huong demo IDS that
- `src/phishing_url_ml/ids_dashboard_app.py`
  - API cho IDS
  - dashboard HTML
- `data/runtime/ids_events.jsonl`
  - noi luu lich su su kien sau khi goi `POST /api/ingest`

## 3. Model dang duoc su dung

App dang dung `2` cau hinh official da chot:

- `Domain Model`: `official_current_26f_hybrid_xgboost_ann_weighted_120k_curated_benign_override`
- `URL Model`: `official_current_66f_ann_mlp_full_540k_plus_url_hard_negative_hostaware_phishing_targeted`

Model mac dinh:

- `Domain Model`: `hybrid_xgboost_ann_weighted`
- `URL Model`: `ann_mlp`

## 4. Cach chay

Tu thu muc goc repo:

```bash
python src/run_ids_dashboard.py --host 127.0.0.1 --port 8080
```

Mo trinh duyet:

```text
http://127.0.0.1:8080/dashboard
```

## 5. Cac endpoint

### `GET /health`

Dung de kiem tra app da san sang hay chua.

### `POST /api/predict`

Du doan nhung khong ghi log.

Body JSON:

```json
{
  "dataset_kind": "domain",
  "value": "secure-paypal-check.com",
  "source": "ids_sensor"
}
```

### `POST /api/ingest`

Du doan va ghi su kien vao `data/runtime/ids_events.jsonl`.

Body JSON:

```json
{
  "dataset_kind": "url",
  "value": "http://example-login-verify.com/account/reset?token=12345",
  "source": "ids_proxy_sensor",
  "metadata": {
    "sensor_name": "lab-suricata",
    "ids_event_type": "http",
    "src_ip": "10.0.2.15",
    "dest_ip": "198.51.100.10"
  }
}
```

### `GET /api/events`

Doc cac event gan day.

Co the truyen:

- `limit`

Vi du:

```text
/api/events?limit=50
```

## 6. Dau ra cua mot su kien

Moi event se co cac truong chinh:

- `dataset_kind`
- `raw_value`
- `normalized_value`
- `predicted_class`
- `score`
- `risk_level`
- `risk_policy_version`
- `model_name`
- `variant_name`
- `decision_mode`
- `signals`
- `recommendation`
- `metadata`
- `sensor_name`
- `ids_event_type`
- `flow_summary`

## 7. Cach nap log IDS that

### `Suricata eve.json`

```bash
python src/bridge_ids_logs.py --input C:\suricata\log\eve.json --format suricata-eve --sensor-name lab-suricata --follow
```

Bridge nay se tu map:

- `dns.rrname` / `dns.query` -> `Domain Model`
- `tls.sni` -> `Domain Model`
- `http.hostname` + `http.url` -> `URL Model`

### `Zeek JSON`

```bash
python src/bridge_ids_logs.py --input C:\zeek\logs\current\dns.log --format zeek-dns-json --sensor-name lab-zeek --follow
python src/bridge_ids_logs.py --input C:\zeek\logs\current\http.log --format zeek-http-json --sensor-name lab-zeek --follow
python src/bridge_ids_logs.py --input C:\zeek\logs\current\ssl.log --format zeek-ssl-json --sensor-name lab-zeek --follow
```

Bridge nay se tu map:

- `query` -> `Domain Model`
- `host` + `uri` -> `URL Model`
- `server_name` -> `Domain Model`

## 8. Ghi chu

- Day la luong phu hop cho `demo`, `PoC` va tich hop noi bo trong do an.
- Runtime `risk_level` hien duoc calibrate rieng cho `domain` va `url` qua `models/runtime_risk_policy.json`.
- Runtime hien co them curated benign URL patch de ha canh bao gia tren mot so hostname/URL official duoc dung cho huong demo IDS that. Cac event nay van duoc ghi log va duoc danh dau bang `decision_mode = model_plus_curated_benign_override`.
- Neu muon dua sang moi truong nghiem tuc hon, nen bo sung:
  - auth cho API
  - queue / message broker
  - persistent database thay vi `jsonl`
  - rate limit
  - log rotation
  - calibration threshold theo muc tieu van hanh
