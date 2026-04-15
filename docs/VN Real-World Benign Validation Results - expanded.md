# VN Real-World Benign Validation Results

- Input seed: `data\validation\vn_real_world_benign_seed_expanded.csv`
- Detailed results: `data\validation\results\vn_real_world_benign_seed_expanded_detailed_20260415_134157.csv`
- Evaluated at: `2026-04-15T13:41:57+07:00`
- Prediction modes: `official_runtime`
- Curated runtime overrides applied: `16`

## 1. Tong quan

- Tong so case: `46`
- So case dung ky vong: `46`
- So false positive: `0`
- Ty le false positive: `0.00%`
- So case loi khi predict: `0`

## 2. File tong hop

- Theo `dataset_kind`: `data\validation\results\vn_real_world_benign_seed_expanded_by_dataset_kind_20260415_134157.csv`
- Theo `priority`: `data\validation\results\vn_real_world_benign_seed_expanded_by_priority_20260415_134157.csv`
- Theo `category`: `data\validation\results\vn_real_world_benign_seed_expanded_by_category_20260415_134157.csv`
- Loi theo `category`: `data\validation\results\vn_real_world_benign_seed_expanded_errors_by_category_20260415_134157.csv`
- Loi theo `token pattern`: `data\validation\results\vn_real_world_benign_seed_expanded_errors_by_token_pattern_20260415_134157.csv`
- Loi theo `category + token pattern`: `data\validation\results\vn_real_world_benign_seed_expanded_errors_by_category_token_pattern_20260415_134157.csv`

## 3. False Positive noi bat

- Khong co false positive nao trong lan chay nay.

## 4. Token pattern noi bat

- Khong co token pattern loi nao trong lan chay nay.

## 5. Nhan xet nhanh

- Bo nay chi gom case `benign`, nen chi so can nhin truoc mat la `false positive`.
- Neu false positive tap trung vao `university_portal` hoac `banking`, can uu tien xem lai `Domain Model` va cac URL login/portal hop le.
- Day la bo kiem tra thuc chien bo sung, khong thay the cho test set hoc may chinh.
