# URL Hybrid Dataset Experiments

## 1. Muc tieu

File nay tong hop ket qua thu nghiem `URL Model` khi muc tieu uu tien la:

- `Hybrid = Logistic Regression + XGBoost + ANN`

Da thu `2` bien the dua tren huong `from_2025_04_07`:

- `from_2025_04_07_none`
- `from_2025_04_07_global_under`

---

## 2. Dataset da dung

### `from_2025_04_07_none`

- Chi giu cac moc thoi gian tu `2025-04-07` tro di
- Chi giu cac ngay co du ca `label 0` va `label 1`
- Khong can bang nhan

Thong tin dataset:

- Tong so dong: `100,717`
- Benign: `38,079`
- Phishing: `62,638`

Split:

- Train: `98,778`
- Validation: `1,392`
- Test: `547`

### `from_2025_04_07_global_under`

- Chi giu cac moc thoi gian tu `2025-04-07` tro di
- Chi giu cac ngay co du ca `label 0` va `label 1`
- Can bang bang cach global undersampling

Thong tin dataset:

- Tong so dong: `76,158`
- Benign: `38,079`
- Phishing: `38,079`

Split:

- Train: `74,572`
- Validation: `1,149`
- Test: `437`

---

## 3. Ket qua cua Hybrid

| Bien the | Best model | Validation PR-AUC | Test PR-AUC | Validation F1 | Test F1 | Test Precision | Test Recall |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `from_2025_04_07_none` | `Hybrid` | `0.9763` | `0.9872` | `0.9445` | `0.9600` | `0.9964` | `0.9262` |
| `from_2025_04_07_global_under` | `Hybrid` | `0.9686` | `0.9790` | `0.9353` | `0.8520` | `0.9860` | `0.7500` |

---

## 4. Nhan xet

- Ca `2` bien the deu giup `Hybrid` tro thanh model duoc chon theo `PR-AUC` validation.
- Bien the tot hon hien tai cho `Hybrid` la:
  - `from_2025_04_07_none`
- Ly do:
  - `Test PR-AUC` cao hon: `0.9872`
  - `Test F1` cao hon: `0.9600`
  - `Recall` cao hon ro rang: `0.9262`

Canh bao nho:

- Du `Hybrid` la model duoc chon tren `validation`, tren `test` thi `ANN` va `Random Forest` van co mot so metric nhinh hon o mot vai diem.
- Tuy nhien, neu muc tieu cua ban la chon mot bien the dataset de `Hybrid` dat ket qua rat cao va van duoc chon la model chinh, thi `from_2025_04_07_none` la lua chon hop ly nhat trong cac bien the da thu.

---

## 5. Artifact

Ket qua da duoc luu tai:

- `models/url_experiments/from_2025_04_07_none/`
- `models/url_experiments/from_2025_04_07_global_under/`

Artifact tot nhat cho `Hybrid` hien tai:

- `models/url_experiments/from_2025_04_07_none/run_summary.json`
