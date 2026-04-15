# VN URL Phishing Hard Cases Addon

Tai lieu nay ghi nhanh bo `phishing URL hard-case addon` duoc bo sung cho `URL Model` trong `Phase 34`.

## 1. Muc tieu

- tang mat do train quanh nhom `brand-subdomain spoof`
- tang mat do train quanh nhom `cloud-edge generic portal`
- giu bo addon nay tach rieng khoi raw feed chinh de de truy vet va de giai thich trong bao cao

## 2. File lien quan

- raw addon dir: `data/raw/vn_phishing_url_addon/`
- file phase 34:
  - `data/raw/vn_phishing_url_addon/vn_phishing_url_addon_2026-04-15_phase34_targeted_patterns.csv`
- dataset build:
  - `src/build_url_dataset.py`

## 3. Noi dung addon

Bo nay khong phai snapshot OpenPhish moi, ma la `curated targeted pattern rows` de bo sung quanh 2 archetype ma official cu van sot:

- `www.purchaseordersale.com.wellscreditfargo.com`
- `fasoasio-dtfhevakagcrhtcs.z02.azurefd.net/...`

Addon phase 34 them `14` URL:

- `6` row nhom `ecommerce_delivery / brand-subdomain spoof`
- `7` row nhom `generic_portal / cloud-edge`
- `1` row nhom `cloud_email_docs / hosted phishing`

## 4. Cach dung

Khong can lenh rieng. Khi chay:

```bash
python src/build_url_dataset.py
```

script se tu dong merge them cac file `*.csv` trong:

- `data/raw/vn_benign_url_addon/`
- `data/raw/vn_phishing_url_addon/`

truoc khi sort, dedup va ghi `url_model_dataset.parquet`.

## 5. Ghi chu

- `collected_at` cua addon phase 34 duoc gan vao ngay train (`2026-04-12`) de tranh bien ngay addon thanh holdout mixed-date moi.
- Day la bo patch co chu dich cho lexical train, khong dung de thay the cho raw feed phishing that.
