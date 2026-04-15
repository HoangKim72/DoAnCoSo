# IDS Real Demo Guide

File nay mo ta cach demo theo huong `IDS that -> bridge -> dashboard`.

## 1. Muc tieu

Demo nen tra loi duoc 3 cau hoi:

1. IDS that bat duoc truong nao?
2. Khi chi co `domain` thi he thong xu ly ra sao, khi co `full URL` thi xu ly ra sao?
3. Canh bao co len dashboard voi du ngu canh van hanh (`sensor`, `event type`, `src -> dest`) hay khong?

## 2. Luong demo de xuat

Chay `3` terminal:

1. dashboard:

```bash
python src/run_ids_dashboard.py --host 127.0.0.1 --port 8080
```

2. bridge IDS:

```bash
python src/bridge_ids_logs.py --input C:\suricata\log\eve.json --format suricata-eve --sensor-name lab-suricata --follow
```

hoac voi Zeek:

```bash
python src/bridge_ids_logs.py --input C:\zeek\logs\current\dns.log --format zeek-dns-json --sensor-name lab-zeek --follow
python src/bridge_ids_logs.py --input C:\zeek\logs\current\http.log --format zeek-http-json --sensor-name lab-zeek --follow
python src/bridge_ids_logs.py --input C:\zeek\logs\current\ssl.log --format zeek-ssl-json --sensor-name lab-zeek --follow
```

3. terminal sinh traffic hoac replay log:

- mo trang phishing test trong lab an toan
- hoac replay `eve.json` / `Zeek JSON` da co san

## 3. Mapping du lieu IDS -> model

- `Suricata DNS`
  - `dns.rrname` / `dns.query` -> `Domain Model`
- `Suricata TLS`
  - `tls.sni` -> `Domain Model`
- `Suricata HTTP`
  - `http.hostname` + `http.url` -> `URL Model`
- `Zeek DNS`
  - `query` -> `Domain Model`
- `Zeek HTTP`
  - `host` + `uri` -> `URL Model`
- `Zeek SSL/TLS`
  - `server_name` -> `Domain Model`

Neu bridge chi tao duoc `domain`, dashboard van suy luan duoc bang `Domain Model`.
Neu bridge tao duoc `full URL`, dashboard uu tien `URL Model`.

## 4. Metadata nen hien khi demo

Dashboard hien duoc:

- `source`
- `sensor`
- `event type`
- `observed time`
- `src -> dest flow`
- `decision mode`

Vi vay khi demo nen chon log co day du:

- `src_ip`
- `dest_ip`
- `src_port`
- `dest_port`
- `timestamp`

## 5. Curated runtime patch

Huong demo hien co them curated benign runtime patch:

- `Domain`: doc tu `data/raw/vn_benign_domain_addon/*.csv`
- `URL`: doc tu `data/raw/vn_benign_url_runtime_patch/*.csv`

Muc dich:

- giam false positive tren mot so hostname/URL official de demo IDS on dinh hon
- khong thay doi model artifact official
- event van duoc ghi log va hien `decision_mode = model_plus_curated_benign_override`

Khi bao cao, nen noi ro day la `runtime mitigation for demo`, khong phai bang chung rang model da hoc duoc tat ca case do.

## 6. Demo script ngan gon

Kich ban de trinh bay nhanh:

1. gui mot `TLS SNI` benign nhu `mail.chinhphu.vn`
2. cho thay dashboard nhan `domain`, context IDS, va ha muc canh bao nho curated runtime patch
3. gui mot `HTTP URL` phishing kho ma official moi bat dung
4. cho thay event len `high risk`
5. mo trang history de xem `src -> dest`, `sensor`, `decision mode`

## 7. Gioi han can noi truoc

- pipeline hien tai phu hop `demo`, `PoC`, va lab integration
- event log van la `jsonl`, chua co queue/database
- chua co auth/rate limit cho API
- curated runtime patch la triage cho demo, khong nen xem la thay the cho model improvement
