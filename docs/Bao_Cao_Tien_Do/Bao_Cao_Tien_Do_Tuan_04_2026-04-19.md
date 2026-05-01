# THONG TIN DE TAI DO AN CO SO

Ten de tai (ghi IN HOA)  
XAY DUNG HE THONG PHAT HIEN WEBSITE LUA DAO (PHISHING) DUA TREN URL

Sinh vien thuc hien:

- Ho ten: Kim Ngoc Hoang
- MSSV: 2380600714
- Ho ten: Le Anh Huy
- MSSV: 2380600820

# BAO CAO TIEN DO TUAN 04

Thoi gian bao cao: `2026-04-12` den `2026-04-19`

## 1.1 Muc tieu

- Danh gia lai dung `official current` tren bo `expanded validation` de xac dinh pain point thuc chien con lai.
- Giam `URL false positive` tren nhom benign kho nhu `government`, `banking`, `university_portal`.
- Xu ly cac `URL false negative` con lai va chot lai `URL official` moi cho he thong.
- Hoan thien runtime IDS theo huong demo that, gom `risk policy`, `curated benign patch`, va cau noi log `Suricata/Zeek`.

## 1.2 Cong viec thuc hien

- Rerun toan bo `expanded validation` theo dung `official runtime`, dong thoi bo sung report loi theo `category` va `token pattern`.
- Thuc hien `URL hard-negative mining`, thu them `81` benign URL hard-case rows, retrain va so sanh candidate de giam false positive.
- Mo rong `URL feature` tu `55` len `66`, bo sung them `14` phishing URL hard-case rows, sau do promote `URL official` moi.
- Hieu chinh `runtime risk policy` cho `domain` va `url`, sua luong suy luan de log them `risk_policy_version`, `risk_thresholds`.
- Bo sung `curated benign runtime patch` cho demo IDS that va them `bridge_ids_logs.py` de nap log `Suricata eve.json` / `Zeek JSON` vao dashboard.
- Cap nhat dashboard de hien them `sensor`, `event type`, `observed time`, `src -> dest flow`, `decision mode`, va dong bo lai tai lieu.

## 1.3 Ket qua dat duoc

| Hang muc | Domain Model | URL Model | Ghi chu |
| --- | --- | --- | --- |
| Bien the official hien tai | `official_current_26f_hybrid_xgboost_ann_weighted_120k_curated_benign_override` | `official_current_66f_ann_mlp_full_540k_plus_url_hard_negative_hostaware_phishing_targeted` | Da dong bo vao `models/official_model_registry.json` |
| So luong dataset input thuc te | `120,006` dong | `540,023` dong | URL da duoc bo sung addon benign va phishing trong tuan nay |
| So luong phishing | `72,004` dong | `166,866` dong | Domain giu can bang tot; URL giu full phan bo huu ich cho bai toan |
| So luong benign | `48,002` dong | `373,157` dong | Dung de doi chieu class balance giua hai bai toan |
| So feature | `26` | `66` | URL da duoc mo rong them nhom host-aware feature |
| Validation PR-AUC | `0.8171` | `0.9963` | Chi so chon cau hinh official |
| Test PR-AUC | `0.8469` | `0.9995` | Chi so tong hop quan trong cho bai toan lech lop |
| F1-Score | `0.7215` | `0.9965` | Theo doi can bang precision va recall tren holdout test |
| Precision | `0.5874` | `0.9993` | Chi so danh gia mo hinh |
| Recall | `0.9349` | `0.9938` | Chi so danh gia mo hinh |
| Danh gia `expanded` theo official runtime | `28/28` dung | `66/66` dung | Ket qua runtime hien tai dat `94/94`, `0 FP`, `0 FN`; co `16` case benign duoc ha canh bao boi curated runtime override |
| Risk policy runtime | `low >= 0.55`, `medium >= 0.90`, `high >= 0.95` | `low >= 0.45`, `medium >= 0.75`, `high >= 0.98` | Da tach thanh file rieng `models/runtime_risk_policy.json` |
| Tich hop IDS demo | `DNS`, `TLS SNI` | `HTTP host + path`, `full URL` | Da them bridge tu `Suricata` va `Zeek` vao dashboard |

Ket qua noi bat trong tuan:

- Phase 32 cho thay pain point lon nhat khong con la `Domain false negative`, ma chuyen ro sang `URL false positive` tren benign URL hop le.
- Phase 33 giam `benign false positive` tren bo `expanded` tu `19/46` xuong `15/46`.
- Phase 34 xoa het `URL false negative` tren bo phishing `expanded`, dua ket qua ve `0/48`.
- Phase 35 chot `URL official` moi voi `66` feature va dong bo vao dashboard/API.
- Phase 36 hoan thien `runtime risk policy` rieng cho `domain` va `url`.
- Phase 37 dua runtime demo len muc `94/94` tren bo `expanded`, nhung da ghi chu ro day la `runtime mitigation for demo`, khong phai retrain model moi.
- Phase 38 bo sung luong `IDS JSON log -> bridge -> dashboard`, giup demo giong he thong that hon thay vi chi nhap tay tren form.

## 1.4 Kho khan gap phai

- Bo `expanded validation` cho thay rat nhieu URL benign chinh thong van co lexical pattern giong phishing, dac biet o nhom `login`, `portal`, `mail`, `.aspx`, `tra-cuu`, `ReturnUrl`.
- Trong qua trinh giam `URL false positive`, mo hinh co luc xuat hien trade-off lam tang `false negative`, nen phai chia nho thanh nhieu phase (`hard-negative`, `host-aware`, `phishing hard-case`) moi tim duoc diem can bang tot.
- Ket qua runtime sau `curated benign patch` rat dep cho demo, nhung can tach bach voi chat luong model thuan de tranh danh gia nham.
- Luong demo IDS truoc do moi dung o muc dashboard/API noi bo; viec ket noi voi log `Suricata` va `Zeek` can bo sung them parser, metadata, va bridge rieng.

## 1.5 Ke hoach tiep theo

- Dong goi luong demo thanh bo script chay nhanh, uu tien huong `one-click demo` cho dashboard va replay log IDS.
- Chuan bi `demo checklist`, case benign/phishing tieu bieu, va screenshot/video du phong de phuc vu bao ve.
- Tiep tuc ra soat curated runtime patch de giu pham vi hep, minh bach, dung voi muc tieu demo IDS.
- Neu tiep tuc mo rong ky thuat, uu tien danh gia tren log/traffic that va giam phu thuoc vao patch runtime thay vi mo rong sweep model tren dien rong.
