# VN Real-World Validation Results

- Input seed: `data\validation\vn_real_world_validation_seed_expanded.csv`
- Detailed results: `data\validation\results\vn_real_world_validation_seed_expanded_detailed_20260412_202808.csv`
- Evaluated at: `2026-04-12T20:28:08+07:00`

## 1. Tong quan

- Tong so case: `94`
- So case dung ky vong: `57`
- So false positive: `27`
- So false negative: `10`
- Match rate: `60.64%`
- So case loi khi predict: `0`

## 2. File tong hop

- Theo `dataset_kind`: `data\validation\results\vn_real_world_validation_seed_expanded_by_dataset_kind_20260412_202808.csv`
- Theo `priority`: `data\validation\results\vn_real_world_validation_seed_expanded_by_priority_20260412_202808.csv`
- Theo `category`: `data\validation\results\vn_real_world_validation_seed_expanded_by_category_20260412_202808.csv`

## 3. Case sai noi bat

- `BU001` | `url` | `https://hocphi.hcmus.edu.vn/dang-nhap` | pred=`phishing` | score=`0.858556` | risk=`high`
- `U014` | `url` | `https://myweb3metwallet.com/` | pred=`benign` | score=`0.484918` | risk=`low`
- `P007` | `domain` | `www.ttkpayevent.shop` | pred=`benign` | score=`0.248759` | risk=`minimal`
- `P001` | `domain` | `securepaypaldigitalwallet.com` | pred=`benign` | score=`0.203148` | risk=`minimal`
- `P008` | `domain` | `www.connectwallet.xyz` | pred=`benign` | score=`0.185214` | risk=`minimal`
- `P024` | `domain` | `recaudos-postpago.com` | pred=`benign` | score=`0.079553` | risk=`minimal`
- `P014` | `domain` | `myweb3metwallet.com` | pred=`benign` | score=`0.069768` | risk=`minimal`
- `P019` | `domain` | `elster-anfrage.com` | pred=`benign` | score=`0.046096` | risk=`minimal`
- `BU002` | `url` | `http://daotao.hutech.edu.vn/default.aspx?flag=XemDiemThi&page=nhapmasv` | pred=`phishing` | score=`0.999692` | risk=`high`
- `BU024` | `url` | `https://datafiles.hanoi.gov.vn/gov-hni/6244/VanBan/2026/4/10/CV-1501-2026.pdf` | pred=`phishing` | score=`0.999638` | risk=`high`

## 4. Nhan xet nhanh

- Bo nay gom ca `benign` va `phishing`, nen can doc dong thoi false positive, false negative va match rate.
- Day la bo kiem tra thuc chien bo sung, khong thay the cho test set hoc may chinh.
