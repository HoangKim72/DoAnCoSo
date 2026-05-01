# BÁO CÁO NHANH TUẦN 06

Tên đề tài: `Xây dựng hệ thống phát hiện website lừa đảo (phishing) dựa trên URL`

Mốc số liệu trong file này được tổng hợp từ `docs/Bao_Cao_Tien_Do/Bao_Cao_Tien_Do_Tuan_06.docx` và các artifact thật đang có trong repo tại thời điểm `2026-04-20`.

## 1. Tóm tắt nhanh

- Hệ thống hiện đã chốt `2` mô hình chính thức: `Domain Model` và `URL Model`.
- Pipeline đã chạy được end-to-end: `thu thập dữ liệu -> normalize -> clean -> build dataset -> train -> runtime IDS/dashboard`.
- Trọng tâm kỹ thuật của tuần này là tối ưu `URL Model`: thêm `81` benign URL hard-negative rows, thêm `14` phishing URL hard-case rows, và mở rộng feature từ `55` lên `66`.
- Ở mức `model official`, kết quả test hiện tại là:
  - `Domain Model`: `PR-AUC = 0.8469`, `F1 = 0.7215`
- `URL Model`: `PR-AUC = 0.9995`, `F1 = 0.9965`
- Ở mức `runtime demo`, bộ `expanded validation` hiện đạt `94/94` đúng, nhưng có `16` case được hạ cảnh báo bởi `curated benign override`, nên khi báo cáo cần tách rõ giữa `chất lượng model` và `runtime mitigation cho demo`.

### 1.1. Bảng tóm tắt nhanh để đưa vào slide

| Model | Model official | Số feature | Input rows | Validation PR-AUC | Test PR-AUC | File chứa thông số |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `Domain Model` | `hybrid_xgboost_ann_weighted` | `26` | `120,006` | `0.8171` | `0.8469` | `models/domain/run_summary.json`, `models/domain/validation_metrics.csv`, `models/domain/test_metrics.csv` |
| `URL Model` | `ann_mlp` | `66` | `540,023` | `0.9963` | `0.9995` | `models/url/run_summary.json`, `models/url/validation_metrics.csv`, `models/url/test_metrics.csv` |

## 2. Snapshot dữ liệu toàn hệ thống

### 2.1. Quy mô dữ liệu hiện tại

| Chỉ số | Giá trị thực tế | Ghi chú |
| --- | ---: | --- |
| Tổng dữ liệu thu được sau normalize | `3,262,670` rows | 4 nguồn chính hiện có dữ liệu thật trong snapshot |
| Dữ liệu sau clean | `644,773` rows | Sau parse, canonicalize, loại overlap và dedup |
| Rows lỗi bị loại | `8,321` | Chủ yếu là `unsupported_scheme` |
| Rows benign bị loại do overlap | `47,467` | Tránh trùng giữa benign và phishing |
| Rows bị loại do trùng lặp | `2,562,109` | Dedup theo `canonical_hostname` và `canonical_url` |
| Domain candidate dataset | `334,775` rows | Dataset đầu vào cho bài toán domain |
| URL candidate dataset | `540,023` rows | Dataset đầu vào cho bài toán URL |
| Official input cho `Domain Model` | `120,006` rows | `48,002` benign, `72,004` phishing |
| Official input cho `URL Model` | `540,023` rows | `373,157` benign, `166,866` phishing |
| Validation / test holdout của domain | `323 / 281` rows | Theo split thời gian |
| Validation / test holdout của URL | `49,151 / 49,152` rows | `latest mixed-date holdout` |
| Real-world expanded validation | `94` cases | `46` benign + `48` phishing |
| Curated benign URL hard-negative thêm trong tuần | `81` rows | `70` crawl + `11` targeted patterns |
| Curated phishing URL hard-case thêm trong tuần | `14` rows | Bổ sung cho Phase 34 |
| Curated benign URL runtime patch cho demo | `11` rows | Chỉ dùng ở runtime demo |
| Curated benign domain addon hiện có trong repo | `163` rows | Dùng cho domain dataset và runtime override |

Ghi chú: `Domain Model` hiện không dùng toàn bộ `334,775` candidate rows mà đang dùng cấu hình official đã chốt ở mức `120,006` rows.

### 2.2. Phân bố theo nguồn dữ liệu chính

| Nguồn | Rows sau normalize | Rows sau clean |
| --- | ---: | ---: |
| `mendeley_phishing_url` | `2,250,880` | `439,534` |
| `mendeley_legitphish` | `506,090` | `98,303` |
| `tranco` | `500,000` | `104,845` |
| `openphish` | `5,700` | `2,091` |

## 3. Các mô hình chính thức hiện tại

| Bài toán | Variant official | Model chính thức | Số feature | Input rows | Validation PR-AUC | Test PR-AUC | Test F1 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `Domain` | `official_current_26f_hybrid_xgboost_ann_weighted_120k_curated_benign_override` | `hybrid_xgboost_ann_weighted` | `26` | `120,006` | `0.8171` | `0.8469` | `0.7215` |
| `URL` | `official_current_66f_ann_mlp_full_540k_plus_url_hard_negative_hostaware_phishing_targeted` | `ann_mlp` | `66` | `540,023` | `0.9963` | `0.9995` | `0.9965` |

### 3.1. Chỉ số test quan trọng

- `Domain Model`: `Precision = 0.5874`, `Recall = 0.9349`, `F1 = 0.7215`, `ROC-AUC = 0.7227`, `PR-AUC = 0.8469`
- `URL Model`: `Precision = 0.9993`, `Recall = 0.9938`, `F1 = 0.9965`, `ROC-AUC = 0.9988`, `PR-AUC = 0.9995`

### 3.2. Tình trạng đánh giá thực chiến

- Bộ `expanded validation` hiện có `94` case thực tế: `46` benign và `48` phishing.
- Nếu đánh giá theo `official runtime` hiện tại, hệ thống đạt `94/94`, `0 false positive`, `0 false negative`.
- Tuy nhiên có `16` case benign được hạ cảnh báo bởi `curated benign override`, vì vậy đây là kết quả `runtime demo`, không phải chất lượng thuần của model.

### 3.3. Risk policy hiện tại cho runtime IDS

- `Domain`: `low >= 0.55`, `medium >= 0.90`, `high >= 0.95`
- `URL`: `low >= 0.45`, `medium >= 0.75`, `high >= 0.98`

## 4. Những gì đã làm được trong tuần qua

- Rerun lại toàn bộ `expanded validation` theo đúng `official runtime`, từ đó xác định pain point lớn nhất hiện tại là `URL false positive` trên các URL hợp lệ, không còn là `Domain false negative`.
- Thực hiện `URL hard-negative mining`, thu thêm `81` benign URL hard-case rows để retrain.
- Bổ sung `14` phishing URL hard-case rows cho các mẫu khó như `brand-subdomain spoof` và `cloud-edge generic portal`.
- Mở rộng bộ `URL feature` từ `55` lên `66`, bổ sung nhóm feature `host-aware`.
- Promote lại `URL official` mới thành `official_current_66f_ann_mlp_full_540k_plus_url_hard_negative_hostaware_phishing_targeted`.
- Tách `runtime risk policy` thành file riêng và hiệu chỉnh ngưỡng cảnh báo cho `domain` và `url`.
- Bổ sung `curated benign runtime patch` phục vụ hướng demo IDS thật.
- Xây dựng `bridge_ids_logs.py` để nạp log từ `Suricata eve.json` và `Zeek JSON` vào dashboard qua API.
- Cập nhật dashboard để hiển thị thêm `sensor`, `event type`, `observed time`, `src -> dest flow` và `decision mode`.

## 5. Kết quả nổi bật nên nhấn mạnh khi trình bày

- Chất lượng `URL Model` đã tăng rõ trong tuần này:
  - `mixed expanded`: từ `78.72%` lên `81.91%`, sau đó lên `84.04%`
  - `benign false positive`: từ `19/46` xuống `15/46`
  - `phishing false negative`: từ `2/48` xuống `0/48`
- `URL Model` hiện là nhánh mạnh nhất của hệ thống với `66` feature và `Test PR-AUC = 0.9995`.
- `Domain Model` hiện dùng `26` feature, phù hợp cho tình huống IDS chỉ lấy được `domain / hostname / SNI`, với `Test PR-AUC = 0.8469`.
- Hệ thống không còn chỉ dừng ở mức train offline, mà đã có luồng demo thực tế:
  - `IDS JSON log -> bridge -> dashboard`
  - hỗ trợ `Suricata` và `Zeek`
  - runtime có `risk policy`, log sự kiện, lịch sử kiểm tra và context mạng
- Với cấu hình demo hiện tại, runtime đạt `94/94` trên bộ expanded, đủ tốt để trình diễn với giảng viên.

## 6. Điểm cần nói rõ với giảng viên

- Cần tách bạch `model official quality` và `runtime mitigation for demo`.
- Kết quả `94/94` là kết quả của `official runtime` có thêm `curated benign override`, không phải là kết quả test thuần của mô hình.
- `URL Model` hiện đang dùng chiến lược `latest mixed-date holdout` thay vì pure temporal 3-way split, vì snapshot dữ liệu full hiện chỉ còn `2` mốc thời gian có đủ cả hai nhãn.
- Pain point kỹ thuật còn lại chủ yếu là `URL false positive` trên các URL hợp lệ nhưng có pattern rất giống phishing như `login`, `portal`, `mail`, `.aspx`, `tra-cuu`, `ReturnUrl`.

## 7. Bước tiếp theo của đồ án

- Đóng gói luồng demo thành bộ script chạy nhanh theo hướng `one-click demo`.
- Chuẩn bị `demo checklist`, dữ liệu replay mẫu, các case benign/phishing tiêu biểu và screenshot dự phòng.
- Tiếp tục rà soát `curated runtime patch` để giữ phạm vi hẹp, minh bạch và đúng mục tiêu demo.
- Nếu còn thời gian mở rộng kỹ thuật, ưu tiên đánh giá thêm trên `log/traffic` thật và giảm dần mức phụ thuộc vào patch runtime.

## 8. Nguồn số liệu đã dùng để tổng hợp

- `docs/Bao_Cao_Tien_Do/Bao_Cao_Tien_Do_Tuan_06.docx`
- `docs/Bao_Cao_Tien_Do/Bao_Cao_Tien_Do_Tuan_06.md`
- `models/official_model_registry.json`
- `models/domain/run_summary.json`
- `models/url/run_summary.json`
- `models/runtime_risk_policy.json`
- `data/processed/clean_master_dataset.stats.json`
- `data/processed/domain_model_dataset.stats.json`
- `data/processed/url_model_dataset.stats.json`
- `data/processed/official/domain_model_official.stats.json`
- `data/processed/official/url_model_official.stats.json`
- `data/validation/results/vn_real_world_validation_seed_expanded_summary_20260415_134158.json`
- `data/validation/results/vn_real_world_benign_seed_expanded_summary_20260415_134157.json`
- `data/validation/results/vn_real_world_phishing_seed_expanded_summary_20260415_134157.json`
