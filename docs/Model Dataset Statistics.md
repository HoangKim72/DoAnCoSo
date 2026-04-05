# Model Dataset Statistics

File nay thong ke truc tiep tu 2 dataset cuoi cung duoc dua vao huan luyen:

- `data/processed/domain_model_dataset.parquet`
- `data/processed/url_model_dataset.parquet`

Luu y:

- So lieu ben duoi la so lieu sau khi da `normalize`, `clean`, `dedup` va `build dataset`.
- So lieu duoc tinh theo cot `source` va `label` thuc te trong file parquet, khong suy dien theo ten nguon.
- Tap thuat toan hien dang duoc benchmark cho ca 2 loai model gom:
  - `LR`: `Logistic Regression`
  - `SVM`: `Linear SVM`
  - `RF`: `Random Forest`
  - `XGB`: `XGBoost`
  - `ANN`: `MLPClassifier`
  - `Hybrid`: `Logistic Regression + XGBoost + ANN`

## Input Dau Vao Cua Tung File

### `data/processed/domain_model_dataset.parquet`

- File input truc tiep: `data/processed/clean_master_dataset.parquet`
- Script tao file: `src/build_domain_dataset.py`
- Dieu kien loc chinh:
  - chi giu cac dong co `canonical_hostname` khac rong
  - dat `sample_text = canonical_hostname`
  - `drop_duplicates` theo `sample_text`
  - loai bo cac dong `benign` neu `sample_text` bi trung voi mot `positive host`
- Cac source dang co trong file hien tai:
  - `mendeley_legitphish`
  - `mendeley_phishing_url`
  - `openphish`
  - `tranco`
- Cac cot dau ra hien tai:
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

### `data/processed/url_model_dataset.parquet`

- File input truc tiep: `data/processed/clean_master_dataset.parquet`
- Script tao file: `src/build_url_dataset.py`
- Dieu kien loc chinh:
  - chi giu cac dong co `record_type = url`
  - chi giu cac dong co `canonical_url` khac rong
  - dat `sample_text = canonical_url`
  - `drop_duplicates` theo `sample_text`
  - loai bo cac dong `benign` neu `sample_text` bi trung voi mot `positive url`
- Cac source dang co trong file hien tai:
  - `mendeley_legitphish`
  - `mendeley_phishing_url`
  - `news_sitemaps`
  - `openphish`
- Cac cot dau ra hien tai:
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

## Lien He Giua Raw Data Va 2 File Nay

- `clean_master_dataset.parquet` duoc tao tu `normalized_dataset.parquet`.
- `normalized_dataset.parquet` duoc tao tu raw data trong `data/raw/`.
- Hien tai pipeline chinh doc `openphish` tu ca:
  - `data/raw/openphish/`
  - `data/raw/openphish_snapshots/`
- Nghia la cac snapshot moi da co the di vao `normalized_dataset.parquet` khi chay `normalize_data.py` voi source `openphish`.
- De tranh lap raw khong can thiet, khong nen copy cung mot snapshot vao ca `2` thu muc.

## Bang Thong Ke Chi Tiet

| Loai | Thuat toan | Nguon dataset | So luong dataset | So luong phishing | So luong benign |
| --- | --- | --- | ---: | ---: | ---: |
| `domain model` | `LR, SVM, RF, XGB, ANN, Hybrid` | `mendeley_legitphish` | 61,409 | 26,075 | 35,334 |
| `domain model` | `LR, SVM, RF, XGB, ANN, Hybrid` | `mendeley_phishing_url` | 166,838 | 55,611 | 111,227 |
| `domain model` | `LR, SVM, RF, XGB, ANN, Hybrid` | `openphish` | 946 | 946 | 0 |
| `domain model` | `LR, SVM, RF, XGB, ANN, Hybrid` | `tranco` | 101,284 | 0 | 101,284 |
| `domain model` | `LR, SVM, RF, XGB, ANN, Hybrid` | `TONG` | 330,477 | 82,632 | 247,845 |
| `url model` | `LR, SVM, RF, XGB, ANN, Hybrid` | `mendeley_legitphish` | 98,303 | 61,446 | 36,857 |
| `url model` | `LR, SVM, RF, XGB, ANN, Hybrid` | `mendeley_phishing_url` | 439,537 | 103,315 | 336,222 |
| `url model` | `LR, SVM, RF, XGB, ANN, Hybrid` | `news_sitemaps` | 1,858 | 0 | 1,858 |
| `url model` | `LR, SVM, RF, XGB, ANN, Hybrid` | `openphish` | 1,192 | 1,192 | 0 |
| `url model` | `LR, SVM, RF, XGB, ANN, Hybrid` | `TONG` | 540,890 | 165,953 | 374,937 |

## Tom Tat Nhanh

- `Domain Model` dang dung du lieu tu `mendeley_legitphish`, `mendeley_phishing_url`, `openphish`, `tranco`.
- `URL Model` dang dung du lieu tu `mendeley_legitphish`, `mendeley_phishing_url`, `news_sitemaps`, `openphish`.
- Tong so dong cua `Domain Model` hien tai la `330,477`.
- Tong so dong cua `URL Model` hien tai la `540,890`.
