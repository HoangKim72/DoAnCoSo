# VN URL Hard Negative Addon

Tai lieu nay ghi nhanh bo `benign URL hard-negative addon` duoc bo sung cho `URL Model` trong `Phase 33`.

## 1. Muc tieu

- giam `URL false positive` tren cac URL benign kho ngoai doi that
- uu tien nhom:
  - `government`
  - `banking`
  - `university_portal`
- uu tien pattern:
  - `http`
  - `login`
  - `cas`
  - `mail`
  - `portal`
  - `.aspx`
  - `tra-cuu`
  - `ReturnUrl`
  - `Request`

## 2. File lien quan

- seed site focus: `data/curated/vn_url_hard_negative_seed_sites.csv`
- collector: `src/build_vn_benign_url_hard_negative_addon.py`
- raw addon dir: `data/raw/vn_benign_url_addon/`

## 3. Cach tao addon

Collector se:

- crawl tu homepage, robots, sitemap qua logic co san trong `collect_vn_benign_train_addon.py`
- rank URL theo `hard_negative_score`
- uu tien:
  - `http_scheme`
  - `deep_subdomain`
  - `login / cas / request / account / tra-cuu`
  - `.aspx`, `.pdf`
  - query dang `service`, `ReturnUrl`
- loai exact overlap voi:
  - `data/processed/official/url_model_official.parquet`
  - `data/validation/vn_real_world_benign_seed_expanded.csv`
  - cac file addon URL da co san trong `data/raw/vn_benign_url_addon/`

Lenh chay:

```bash
python src/build_vn_benign_url_hard_negative_addon.py
```

## 4. Ghi chu them

- bo collector tu dong giai quyet tot nhom `http`, `.aspx`, `deep_subdomain`, `pdf`
- voi mot so pattern hiem nhung quan trong nhu `ACB Request`, `MOJ CAS/Login`, `MOET Account/Login`, da bo sung them mot file `curated pattern variant`
- file `curated pattern variant` khong dung exact row trong validation seed, chi dung pattern benign tu domain chinh thong de train lexical model tot hon

## 5. Cach di vao train

`src/build_url_dataset.py` hien da tu dong doc them moi file `*.csv` trong:

- `data/raw/vn_benign_url_addon/`

Khi rebuild:

```bash
python src/build_url_dataset.py
```

bo addon se duoc merge vao `url_model_dataset.parquet` truoc khi train.
