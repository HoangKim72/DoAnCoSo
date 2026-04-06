# Official Model Training Summary

File nay tong hop nhanh `2` cau hinh official dang duoc su dung trong du an, bao gom quy mo dataset thuc te va metric sau khi train.

## 1. Dataset va model dang dung

| Loai model | Variant official                                           | Model dang dung         | So luong dataset | Phishing |   Benign | So feature |
| ---------- | ---------------------------------------------------------- | ----------------------- | ---------------: | -------: | -------: | ---------: |
| `domain`   | `from_2025_04_07_global_under_plus_vn_benign_domain_addon` | `hybrid_lr_xgboost_ann` |         `54,191` | `27,021` | `27,170` |       `15` |
| `url`      | `from_2025_04_07_none`                                     | `hybrid_lr_xgboost_ann` |        `100,717` | `62,638` | `38,079` |       `37` |

## 2. Metric sau khi train

| Loai model | Validation Precision | Validation Recall | Validation F1 | Validation ROC-AUC | Validation PR-AUC | Test Precision | Test Recall |  Test F1 | Test ROC-AUC | Test PR-AUC |
| ---------- | -------------------: | ----------------: | ------------: | -----------------: | ----------------: | -------------: | ----------: | -------: | -----------: | ----------: |
| `domain`   |             `1.0000` |          `0.8117` |      `0.8961` |           `0.9479` |          `0.9827` |       `0.9947` |    `0.8282` | `0.9038` |     `0.9579` |    `0.9850` |
| `url`      |             `0.9963` |          `0.8978` |      `0.9445` |           `0.9669` |          `0.9763` |       `0.9964` |    `0.9262` | `0.9600` |     `0.9780` |    `0.9872` |

## 3. Kich thuoc split khi train

| Loai model | Train rows | Validation rows | Test rows | Train dates                | Validation date | Test date    |
| ---------- | ---------: | --------------: | --------: | -------------------------- | --------------- | ------------ |
| `domain`   |   `53,197` |           `670` |     `324` | `2025-04-07`, `2026-04-02` | `2026-04-04`    | `2026-04-05` |
| `url`      |   `98,778` |         `1,392` |     `547` | `2025-04-07`, `2026-04-02` | `2026-04-04`    | `2026-04-05` |

## 4. Ghi chu

- `Domain Model` dang dung dataset official da duoc bo sung them `benign domain addon` tu `data/raw/vn_benign_domain_addon/`.
- `URL Model` giu nguyen bo official da chot truoc do.
- Metric trong bang nay la metric cua `model dang duoc dashboard va API load thuc te`, khong phai metric cua model top-1 theo `pr_auc` neu co thay doi thu cong o buoc chot official.
