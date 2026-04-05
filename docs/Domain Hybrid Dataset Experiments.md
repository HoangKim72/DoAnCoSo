# Domain Hybrid Dataset Experiments

## 1. Muc tieu

File nay tong hop cac lan thu nghiem tren `Domain Model` de tim bo dataset phu hop hon cho:

- `Hybrid = Logistic Regression + XGBoost + ANN`

Muc tieu cua cac thu nghiem nay la:

- chay nhieu bien the dataset khac nhau
- so sanh metric cua rieng `Hybrid`
- tim cau hinh nao giup `Hybrid` dat metric cao nhat

Khong can them nguon ngoai nhu `Kaggle` o giai doan nay, vi cac bien the tren dataset hien co da cho thay kha ro xu huong.

---

## 2. Cac bien the da thu

### `full_none`

- Dung toan bo `domain_model_dataset.parquet`
- Khong can bang nhan

### `full_global_under`

- Dung toan bo `domain_model_dataset.parquet`
- Can bang bang cach undersample theo toan bo dataset ve bang so luong lop nho hon

### `full_per_date_under`

- Dung toan bo `domain_model_dataset.parquet`
- Can bang theo tung `collected_at`

### `no_2026_04_02_none`

- Bo ngay `2026-04-02`
- Khong can bang nhan

### `no_2026_04_02_global_under`

- Bo ngay `2026-04-02`
- Can bang theo toan bo dataset

### `from_2025_04_07_none`

- Chi giu du lieu tu `2025-04-07` tro di
- Khong can bang nhan

### `from_2025_04_07_global_under`

- Chi giu du lieu tu `2025-04-07` tro di
- Can bang theo toan bo dataset

---

## 3. Ket qua cua rieng Hybrid

| Bien the | Balance strategy | Rows sau xu ly | Benign | Phishing | Validation PR-AUC | Test PR-AUC | Validation F1 | Test F1 | Best model duoc chon |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `from_2025_04_07_global_under` | `global_under` | 54,042 | 27,021 | 27,021 | `0.9821` | `0.9846` | `0.8961` | `0.9318` | `Hybrid` |
| `full_global_under` | `global_under` | 165,264 | 82,632 | 82,632 | `0.9353` | `0.9705` | `0.8079` | `0.8499` | `XGBoost` |
| `from_2025_04_07_none` | `none` | 163,639 | 136,618 | 27,021 | `0.9498` | `0.9492` | `0.8858` | `0.9007` | `Hybrid` |
| `full_none` | `none` | 330,477 | 247,845 | 82,632 | `0.8877` | `0.9433` | `0.8042` | `0.8327` | `XGBoost` |
| `full_per_date_under` | `per_date_under` | 165,264 | 82,632 | 82,632 | `0.6512` | `0.6191` | `0.6185` | `0.6568` | `ANN` |
| `no_2026_04_02_global_under` | `global_under` | 164,782 | 82,391 | 82,391 | `0.4596` | `0.5375` | `0.5894` | `0.5868` | `Linear SVM` |
| `no_2026_04_02_none` | `none` | 230,416 | 148,025 | 82,391 | `0.3870` | `0.4789` | `0.4611` | `0.4476` | `ANN` |

---

## 4. Nhan xet chinh

### Cau hinh cho metric cao nhat cua Hybrid

Bien the tot nhat cho `Hybrid` trong nhung gi da thu la:

- `from_2025_04_07_global_under`

Ly do:

- `Validation PR-AUC`: `0.9821`
- `Test PR-AUC`: `0.9846`
- `Hybrid` cung la model duoc chon tot nhat trong chinh bien the nay

### Cau hinh tot nhung bao thu hon

Neu uu tien bo dataset lon hon va van muon `Hybrid` rat manh, bien the dang can nhac la:

- `full_global_under`

Ly do:

- van dung toan bo cac moc thoi gian
- dataset sau xu ly lon hon nhieu: `165,264` dong
- `Hybrid` dat `Test PR-AUC = 0.9705`, van rat cao

### Cau hinh khong nen dung

Khong nen uu tien:

- `full_per_date_under`
- `no_2026_04_02_none`
- `no_2026_04_02_global_under`

Vi:

- metric cua `Hybrid` giam manh
- bo ngay `2026-04-02` lam model mat nhieu tin hieu huu ich
- `per_date_under` lam dataset bi cat qua manh o nhung ngay co phishing rat it

---

## 5. Ket luan de chon

Neu muc tieu cua ban la:

### Chon bo dataset de Hybrid co chi so cao nhat

Nen chon:

- `from_2025_04_07_global_under`

### Chon bo dataset can bang hon giua kich thuoc va hieu nang

Nen chon:

- `full_global_under`

---

## 6. Artifact tuong ung

Ket qua da duoc luu tai:

- `models/domain_experiments/full_none/`
- `models/domain_experiments/full_global_under/`
- `models/domain_experiments/no_2026_04_02_none/`
- `models/domain_experiments/no_2026_04_02_global_under/`
- `models/domain_experiments/from_2025_04_07_none/`
- `models/domain_experiments/from_2025_04_07_global_under/`

Va cau hinh `full_per_date_under` hien dang nam trong:

- `models/domain/`

---

## 7. Buoc tiep theo neu can

Neu ban chon mot trong hai cau hinh tot nhat o tren, buoc tiep theo nen la:

1. co dinh cau hinh do thanh workflow chinh cho `Domain Model`
2. export lai file thong ke / summary theo cau hinh da chon
3. neu muon nang tiep nua, khi do moi can can nhac xin y kien ban de them nguon ngoai nhu `Kaggle`
