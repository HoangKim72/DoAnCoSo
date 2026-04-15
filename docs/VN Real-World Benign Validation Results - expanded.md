# VN Real-World Benign Validation Results

- Input seed: `data\validation\vn_real_world_benign_seed_expanded.csv`
- Detailed results: `data\validation\results\vn_real_world_benign_seed_expanded_detailed_20260412_202759.csv`
- Evaluated at: `2026-04-12T20:27:59+07:00`

## 1. Tong quan

- Tong so case: `46`
- So case dung ky vong: `19`
- So false positive: `27`
- Ty le false positive: `58.70%`
- So case loi khi predict: `0`

## 2. File tong hop

- Theo `dataset_kind`: `data\validation\results\vn_real_world_benign_seed_expanded_by_dataset_kind_20260412_202759.csv`
- Theo `priority`: `data\validation\results\vn_real_world_benign_seed_expanded_by_priority_20260412_202759.csv`
- Theo `category`: `data\validation\results\vn_real_world_benign_seed_expanded_by_category_20260412_202759.csv`

## 3. False Positive noi bat

- `BU001` | `url` | `https://hocphi.hcmus.edu.vn/dang-nhap` | score=`0.858556` | risk=`high` | priority=`critical`
- `BU002` | `url` | `http://daotao.hutech.edu.vn/default.aspx?flag=XemDiemThi&page=nhapmasv` | score=`0.999692` | risk=`high` | priority=`high`
- `BU024` | `url` | `https://datafiles.hanoi.gov.vn/gov-hni/6244/VanBan/2026/4/10/CV-1501-2026.pdf` | score=`0.999638` | risk=`high` | priority=`high`
- `BU019` | `url` | `https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/4/66.16-nqcp.signed.pdf` | score=`0.999419` | risk=`high` | priority=`high`
- `BU021` | `url` | `https://datafiles.chinhphu.vn/cpp/files/vbpq/2026/4/103-nqcp.signed.pdf` | score=`0.999237` | risk=`high` | priority=`high`
- `BU009` | `url` | `https://tuyensinh.moet.gov.vn/Account/Login?ReturnUrl=%2F` | score=`0.998831` | risk=`high` | priority=`high`
- `BU011` | `url` | `http://www.vietcombank.com.vn/en/Personal/Cong-cu-Tien-ich/Tra-cuu-so-tk` | score=`0.998558` | risk=`high` | priority=`high`
- `BU022` | `url` | `https://datafiles.hanoi.gov.vn/gov-hni/1/vannt/bando2025.jpg` | score=`0.998091` | risk=`high` | priority=`high`
- `BU012` | `url` | `http://www.vietcombank.com.vn/KHCN/Cong-cu-Tien-ich/Tra-cuu-so-tk` | score=`0.997202` | risk=`high` | priority=`high`
- `BU015` | `url` | `https://online.acb.com.vn/acbib/Request?dse_applicationId=-1&dse_operatio=&dse_pageId=1&dse_sessionId=pJFREim3YBIuFmWZD2Thm9L` | score=`0.997075` | risk=`high` | priority=`high`

## 4. Nhan xet nhanh

- Bo nay chi gom case `benign`, nen chi so can nhin truoc mat la `false positive`.
- Neu false positive tap trung vao `university_portal` hoac `banking`, can uu tien xem lai `Domain Model` va cac URL login/portal hop le.
- Day la bo kiem tra thuc chien bo sung, khong thay the cho test set hoc may chinh.
