# VN Real-World Phishing Validation Results

- Input seed: `data\validation\vn_real_world_phishing_seed_expanded.csv`
- Detailed results: `data\validation\results\vn_real_world_phishing_seed_expanded_detailed_20260412_202803.csv`
- Evaluated at: `2026-04-12T20:28:03+07:00`

## 1. Tong quan

- Tong so case: `48`
- So case dung ky vong: `38`
- So phishing duoc nhan dien dung: `38`
- Ty le nhan dien dung: `79.17%`
- So false negative: `10`
- Ty le false negative: `20.83%`
- So case loi khi predict: `0`

## 2. File tong hop

- Theo `dataset_kind`: `data\validation\results\vn_real_world_phishing_seed_expanded_by_dataset_kind_20260412_202803.csv`
- Theo `priority`: `data\validation\results\vn_real_world_phishing_seed_expanded_by_priority_20260412_202803.csv`
- Theo `category`: `data\validation\results\vn_real_world_phishing_seed_expanded_by_category_20260412_202803.csv`

## 3. False Negative noi bat

- `P019` | `domain` | `elster-anfrage.com` | score=`0.046096` | risk=`minimal` | priority=`critical`
- `P014` | `domain` | `myweb3metwallet.com` | score=`0.069768` | risk=`minimal` | priority=`critical`
- `P024` | `domain` | `recaudos-postpago.com` | score=`0.079553` | risk=`minimal` | priority=`critical`
- `P008` | `domain` | `www.connectwallet.xyz` | score=`0.185214` | risk=`minimal` | priority=`critical`
- `P001` | `domain` | `securepaypaldigitalwallet.com` | score=`0.203148` | risk=`minimal` | priority=`critical`
- `P007` | `domain` | `www.ttkpayevent.shop` | score=`0.248759` | risk=`minimal` | priority=`critical`
- `U014` | `url` | `https://myweb3metwallet.com/` | score=`0.484918` | risk=`low` | priority=`critical`
- `U004` | `url` | `https://www.purchaseordersale.com.wellscreditfargo.com/` | score=`0.339722` | risk=`minimal` | priority=`high`
- `P022` | `domain` | `robiox.com.py` | score=`0.421195` | risk=`low` | priority=`high`
- `P012` | `domain` | `yahoooo.info` | score=`0.015127` | risk=`minimal` | priority=`medium`

## 4. Nhan xet nhanh

- Bo nay chi gom case `phishing`, nen chi so can nhin truoc mat la `false negative` va `ty le nhan dien dung`.
- Neu false negative tap trung vao mot nhom nhu `cloud_email_docs` hay `banking_payment`, can bo sung them mau phishing cung kieu vao bo danh gia va bo train.
- Day la bo kiem tra thuc chien bo sung, khong thay the cho test set hoc may chinh.
