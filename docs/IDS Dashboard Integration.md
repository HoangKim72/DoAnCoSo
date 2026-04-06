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
- `src/phishing_url_ml/inference.py`
  - load `official models`
  - parse input
  - build feature
  - predict
  - luu event vao log
- `src/phishing_url_ml/ids_dashboard_app.py`
  - API cho IDS
  - dashboard HTML
- `data/runtime/ids_events.jsonl`
  - noi luu lich su su kien sau khi goi `POST /api/ingest`

## 3. Model dang duoc su dung

App dang dung dung `2` cau hinh official da chot:

- `Domain Model`: `from_2025_04_07_global_under_plus_vn_benign_domain_addon`
- `URL Model`: `from_2025_04_07_none`

Model mac dinh:

- `Domain Model`: `hybrid_lr_xgboost_ann`
- `URL Model`: `hybrid_lr_xgboost_ann`

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
  "source": "ids_proxy_sensor"
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
- `model_name`
- `variant_name`
- `signals`
- `recommendation`

## 7. Ghi chu

- Day la luong phu hop cho `demo`, `PoC` va tich hop noi bo trong do an.
- Neu muon dua sang moi truong nghiem tuc hon, nen bo sung:
  - auth cho API
  - queue / message broker
  - persistent database thay vi `jsonl`
  - rate limit
  - log rotation
  - calibration threshold theo muc tieu van hanh
