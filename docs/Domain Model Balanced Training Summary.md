# Domain Model Balanced Training Summary

## 1. Muc tieu

File nay ghi lai cau hinh train moi cua `Domain Model` sau khi can bang du lieu.

Can bang hien tai duoc thuc hien trong `src/train_baselines.py` theo cach:

- chi ap dung cho `--dataset-kind domain`
- can bang theo tung `collected_at`
- moi ngay se duoc undersample ve bang so luong cua lop it hon

Ket qua:

- so luong `phishing` va `benign` sau khi dua vao train pipeline la bang nhau

---

## 2. So lieu truoc va sau khi can bang

### Truoc khi can bang

- Tong so dataset: `330,477`
- So luong phishing: `82,632`
- So luong benign: `247,845`

### Sau khi can bang

- Tong so dataset: `165,264`
- So luong phishing: `82,632`
- So luong benign: `82,632`

---

## 3. Thong tin feature

- Loai model: `Domain Model`
- So feature: `15`

Danh sach feature:

- `domain_length`
- `subdomain_count`
- `num_tokens_domain`
- `num_hyphens`
- `digit_ratio`
- `entropy_domain`
- `contains_brand_name`
- `contains_sensitive_keyword`
- `edit_distance_to_top_brand`
- `tld_risk_score`
- `brand_position_score`
- `registered_domain_length`
- `consonant_run_max`
- `char_repeat_ratio`
- `is_idn_or_punycode`

---

## 4. Bang tong hop thuat toan

| Thuat toan | So feature | Tong so dataset | So phishing | So benign |
| --- | ---: | ---: | ---: | ---: |
| Logistic Regression | 15 | 165,264 | 82,632 | 82,632 |
| Linear SVM | 15 | 165,264 | 82,632 | 82,632 |
| Random Forest | 15 | 165,264 | 82,632 | 82,632 |
| XGBoost | 15 | 165,264 | 82,632 | 82,632 |
| ANN (MLPClassifier) | 15 | 165,264 | 82,632 | 82,632 |
| Hybrid: Logistic Regression + XGBoost + ANN | 15 | 165,264 | 82,632 | 82,632 |

---

## 5. Phan bo sau khi chia split

| Split | Tong so dataset | So phishing | So benign |
| --- | ---: | ---: | ---: |
| Train | 163,854 | 81,927 | 81,927 |
| Validation | 956 | 478 | 478 |
| Test | 454 | 227 | 227 |

Split dates hien tai:

- `Train`: `2024-04-02`, `2025-04-07`, `2026-04-02`
- `Validation`: `2026-04-04`
- `Test`: `2026-04-05`

---

## 6. Ghi chu

- Sau khi can bang, `Domain Model` khong con bi lech nhan theo tong the.
- Tuy nhien, chat luong model van can danh gia bang metric thuc nghiem, khong chi dua vao viec can bang so luong dong.
- Ket qua train moi nhat sau can bang dang duoc luu trong:
  - `models/domain/run_summary.json`
  - `models/domain/validation_metrics.csv`
  - `models/domain/test_metrics.csv`
  - `models/domain/model_comparison.csv`
