# VN Real-World Phishing Validation Results

- Input seed: `data\validation\vn_real_world_phishing_seed_expanded.csv`
- Detailed results: `data\validation\results\vn_real_world_phishing_seed_expanded_detailed_20260415_134157.csv`
- Evaluated at: `2026-04-15T13:41:57+07:00`
- Prediction modes: `official_runtime`
- Curated runtime overrides applied: `0`

## 1. Tong quan

- Tong so case: `48`
- So case dung ky vong: `48`
- So phishing duoc nhan dien dung: `48`
- Ty le nhan dien dung: `100.00%`
- So false negative: `0`
- Ty le false negative: `0.00%`
- So case loi khi predict: `0`

## 2. File tong hop

- Theo `dataset_kind`: `data\validation\results\vn_real_world_phishing_seed_expanded_by_dataset_kind_20260415_134157.csv`
- Theo `priority`: `data\validation\results\vn_real_world_phishing_seed_expanded_by_priority_20260415_134157.csv`
- Theo `category`: `data\validation\results\vn_real_world_phishing_seed_expanded_by_category_20260415_134157.csv`
- Loi theo `category`: `data\validation\results\vn_real_world_phishing_seed_expanded_errors_by_category_20260415_134157.csv`
- Loi theo `token pattern`: `data\validation\results\vn_real_world_phishing_seed_expanded_errors_by_token_pattern_20260415_134157.csv`
- Loi theo `category + token pattern`: `data\validation\results\vn_real_world_phishing_seed_expanded_errors_by_category_token_pattern_20260415_134157.csv`

## 3. False Negative noi bat

- Khong co false negative nao trong lan chay nay.

## 4. Token pattern noi bat

- Khong co token pattern loi nao trong lan chay nay.

## 5. Nhan xet nhanh

- Bo nay chi gom case `phishing`, nen chi so can nhin truoc mat la `false negative` va `ty le nhan dien dung`.
- Neu false negative tap trung vao mot nhom nhu `cloud_email_docs` hay `banking_payment`, can bo sung them mau phishing cung kieu vao bo danh gia va bo train.
- Day la bo kiem tra thuc chien bo sung, khong thay the cho test set hoc may chinh.
