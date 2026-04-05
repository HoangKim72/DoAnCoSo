# Activity History

## 1. Tổng quan nhanh

Đồ án này xây dựng hệ thống phát hiện website phishing bằng học máy, theo 2 hướng:

- `Domain Model`: dùng khi chỉ thu được `domain / hostname / FQDN`
- `URL Model`: dùng khi thu được `full URL`

Mục tiêu cuối cùng:

- xây dựng pipeline dữ liệu có thể tái sử dụng
- tạo dataset sạch để huấn luyện mô hình
- benchmark nhiều mô hình
- chọn hướng phù hợp để tích hợp về sau vào bối cảnh `IDS`

---

## 2. Timeline Theo Ngày Và Phase

### Trước `2026-04-04`

#### Phase 1. Dựng pipeline dữ liệu nền tảng

Đã hoàn thành các script chính:

- `src/download_data.py`: tải dữ liệu raw theo nguồn
- `src/normalize_data.py`: chuẩn hóa nhiều nguồn về cùng schema
- `src/clean_data.py`: parse, canonicalize, lọc lỗi, dedup, loại overlap
- `src/build_domain_dataset.py`: tạo dataset cho `Domain Model`
- `src/build_url_dataset.py`: tạo dataset cho `URL Model`
- `src/train_baselines.py`: train và so sánh mô hình
- `src/phishing_url_ml/news_sitemaps.py`: lấy `benign URL candidates` từ news sitemap

Helper dùng chung đã có:

- parse URL/domain
- tách `scheme`, `hostname`, `subdomain`, `registered_domain`, `path`, `query`
- canonicalize URL/domain
- loại query tracking phổ biến

Nguồn dữ liệu chính đang dùng:

- `Tranco`: nguồn `benign domain`
- `OpenPhish community feed`: nguồn `phishing URL`
- `News sitemaps` từ `AP`, `NPR`, `Reuters`: nguồn `benign URL candidates`
- `Mendeley Phishing URL dataset`
- `Mendeley LegitPhish Dataset`

Nguồn chưa dùng được:

- `PhishTank`: chưa có `app key`

#### Phase 2. Tạo dataset xử lý xong cho train

Đã chạy được pipeline thật và tạo các file:

- `data/processed/normalized_dataset.parquet`
- `data/processed/clean_master_dataset.parquet`
- `data/processed/domain_model_dataset.parquet`
- `data/processed/url_model_dataset.parquet`

Ý nghĩa của từng file:

- `normalized_dataset.parquet`: dữ liệu từ nhiều nguồn đã đưa về cùng schema
- `clean_master_dataset.parquet`: dữ liệu đã parse, canonicalize, dedup và gắn nhãn sạch hơn
- `domain_model_dataset.parquet`: dữ liệu đầu vào dành riêng cho `Domain Model`
- `url_model_dataset.parquet`: dữ liệu đầu vào dành riêng cho `URL Model`

#### Phase 3. Train baseline ban đầu

Đã benchmark nhóm baseline đầu tiên:

- `Logistic Regression`
- `Linear SVM`
- `Random Forest`

Đã có temporal split cho cả `domain` và `url`:

- `train`
- `validation`
- `test`

Đã bổ sung cách xử lý cho `URL Model`:

- thêm nguồn `news_sitemaps` để tăng `benign URL candidates`
- bỏ qua những ngày chỉ có một nhãn trước khi temporal split

---

### `2026-04-04`

#### Phase 4. Mở rộng benchmark mô hình

Đã mở rộng `src/train_baselines.py` để train thêm:

- `XGBoost`
- `ANN (MLPClassifier)`
- `Hybrid`: `Logistic Regression + XGBoost + ANN`

Đồng thời mở rộng output để dễ so sánh:

- `models/domain/validation_metrics.csv`
- `models/domain/test_metrics.csv`
- `models/domain/model_comparison.csv`
- `models/url/validation_metrics.csv`
- `models/url/test_metrics.csv`
- `models/url/model_comparison.csv`

Đã cập nhật:

- `requirements.txt`: thêm `xgboost`
- `docs/export_url_model_data.py`: export thêm bảng metric mới

#### Phase 5. Ghi nhận kết quả full train gần nhất

Kết quả full train gần nhất trước khi tách feature riêng:

`Domain Model`

- mô hình được chọn theo `PR-AUC` validation: `ANN`
- trên test:
  - `Hybrid`: `PR-AUC ~ 0.8103`
  - `XGBoost`: `PR-AUC ~ 0.8043`
  - `ANN`: `PR-AUC ~ 0.8005`
- validation của domain vẫn rất khó vì split ngày `2026-04-02` cực lệch lớp

`URL Model`

- mô hình được chọn theo `PR-AUC` validation: `ANN`
- validation `PR-AUC` của `ANN`: `~ 0.9609`
- test `PR-AUC` của `ANN`: `~ 0.9696`
- trên test, `Random Forest` cao nhất: `PR-AUC ~ 0.9740`

Nhận xét sau phase này:

- `URL Model` đang ổn hơn rõ rệt
- `Domain Model` khó hơn vì chỉ dùng `hostname/domain`
- dữ liệu đang có `distribution shift` theo thời gian

#### Phase 6. Bổ sung tài liệu hỗ trợ kiểm tra dữ liệu

Đã tạo và cập nhật thêm:

- `docs/Project Workflow.md`
- `docs/Inspect Clean Master Dataset.md`
- `docs/Inspect Model Datasets.md`
- `docs/export_domain_model_data.py`
- `docs/export_url_model_data.py`
- `docs/Model Dataset Statistics.md`

---

### `2026-04-05`

#### Phase 7. Thu thập `OpenPhish` theo snapshot

Đã tạo:

- `src/collect_openphish_snapshots.py`

Chức năng:

- chạy liên tục bằng terminal
- mặc định mỗi `20` phút tải một snapshot
- lưu vào thư mục riêng `data/raw/openphish_snapshots/`
- tên file có `YYYY-MM-DD_HH-MM` để tránh trùng

Đã bổ sung thêm file hỗ trợ:

- `scripts/run_openphish_snapshot_once.cmd`
- `docs/OpenPhish Task Scheduler.md`

Hiện có các snapshot ví dụ:

- `openphish_2026-04-04_23-42.txt`
- `openphish_2026-04-05_00-55.txt`

Lưu ý quan trọng:

- `openphish_snapshots` là kho raw để tích lũy theo thời gian
- pipeline train hiện tại đã đọc được cả `data/raw/openphish/` và `data/raw/openphish_snapshots/` khi normalize source `openphish`
- không cần copy snapshot thủ công sang `openphish/` nữa

#### Phase 8. Tách riêng feature cho `Domain Model` và `URL Model`

Đã cập nhật `src/phishing_url_ml/feature_engineering.py` để tách 2 hướng feature riêng.

`Domain Model` hiện dùng bộ feature chuyên cho domain:

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

`URL Model` vẫn giữ bộ lexical feature cho URL, path, query.

Đã cập nhật `src/train_baselines.py` để chọn feature theo `dataset_kind`.

Kết quả kiểm tra nhanh:

- `Domain Model`: `15` feature riêng
- `URL Model`: `37` feature riêng
- smoke test train cho cả `domain` và `url` đều chạy được

Lưu ý:

- sau phase này mới chỉ smoke test
- chưa rerun full train trên toàn bộ dataset mới nhất
- vì vậy `models/domain/run_summary.json` và `models/url/run_summary.json` vẫn là kết quả full train cũ

#### Phase 9. Rà lại thống kê dataset và input đầu vào

Đã cập nhật `docs/Model Dataset Statistics.md` để ghi rõ:

- input đầu vào của `domain_model_dataset.parquet`
- input đầu vào của `url_model_dataset.parquet`
- source nào đi vào mỗi model dataset
- số lượng tổng, số phishing, số benign

Số liệu hiện tại:

- `normalized_dataset`: `1,305,188`
- `clean_master_dataset`: `641,038`
- `domain_model_dataset`: `329,713`
- `url_model_dataset`: `540,234`

Phân bố nhãn hiện tại:

- `clean_master_dataset`: `475,383` benign, `165,655` phishing
- `domain_model_dataset`: `247,308` benign, `82,405` phishing
- `url_model_dataset`: `374,579` benign, `165,655` phishing

---

## 3. Trạng thái hiện tại

### Phase hiện tại của dự án

Đồ án đang ở giai đoạn:

- pipeline dữ liệu đã chạy được
- đã có dataset riêng cho `domain` và `url`
- đã benchmark được nhiều mô hình hơn baseline ban đầu
- đã tách feature riêng cho `domain` và `url`
- đã có collector để tích lũy `OpenPhish` theo thời gian

### Những gì đang ổn

- luồng `download -> normalize -> clean -> build dataset -> train` đã rõ
- `URL Model` đang cho kết quả khá tốt
- tài liệu nội bộ đã đầy đủ hơn để kiểm tra dữ liệu và metric

### Những gì chưa ổn

- `Domain Model` vẫn chưa ổn định bằng `URL Model`
- `distribution shift` giữa các ngày vẫn còn mạnh
- `openphish_snapshots` đã đi vào pipeline train chính thông qua bước normalize
- chưa full retrain sau khi tách bộ feature mới cho `Domain Model`

---

## 4. Việc Tiếp Theo

### Phase kế tiếp nên làm

#### Phase 10. Ổn định hóa luồng snapshot trong pipeline

- giữ quy ước rõ ràng giữa `data/raw/openphish/` và `data/raw/openphish_snapshots/`
- tránh duplicate raw cùng một snapshot ở cả hai thư mục
- quyết định khi nào cần rebuild dataset và retrain sau mỗi đợt snapshot mới

#### Phase 11. Full retrain với feature mới

- retrain lại `Domain Model`
- retrain lại `URL Model`
- cập nhật lại `run_summary.json`, `validation_metrics.csv`, `test_metrics.csv`, `model_comparison.csv`

#### Phase 12. Đánh giá cho hướng `IDS`

- đánh giá lại riêng `Domain Model`
- xác định threshold phù hợp cho cảnh báo
- xem mô hình hiện tại đã đủ dùng cho `dashboard/alert` hay chưa

---

## 5. Ghi chú ngắn để mai nối việc

Khi mở dự án lại, nên bắt đầu từ 3 việc này:

1. rà lại raw `openphish` để tránh trùng snapshot giữa `openphish/` và `openphish_snapshots/`
2. chạy lại full training với bộ feature domain mới rồi đánh giá lại `Domain Model`
3. chốt ngưỡng và cách suy luận cho hướng `IDS`
