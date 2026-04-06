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

#### Phase 13. Tích hợp `IDS` và `Dashboard`

- đã tạo lớp suy luận dùng `official hybrid models` cho cả `domain` và `url`
- đã tạo app local để:
  - nhận event từ IDS qua API
  - suy luận bằng model official
  - lưu log sự kiện
  - hiển thị kết quả trên dashboard
- các file mới chính:
  - `src/phishing_url_ml/inference.py`
  - `src/phishing_url_ml/ids_dashboard_app.py`
  - `src/run_ids_dashboard.py`
  - `docs/IDS Dashboard Integration.md`

Kết quả sau phase này:

- repo không còn chỉ dừng ở mức train model
- đã có luồng `IDS -> predict -> dashboard`
- có thể demo bằng API và giao diện web local

---

### `2026-04-06`

#### Phase 14. Đánh giá thực chiến bằng `VN real-world benign seed`

Đã tạo và chạy bộ kiểm tra thực chiến:

- `data/validation/vn_real_world_benign_seed.csv`
- `src/evaluate_real_world_validation.py`
- `docs/VN Real-World Benign Validation Results.md`

Kết quả chính của lần chạy đầu tiên:

- tổng `30` case benign
- đúng kỳ vọng `23`
- false positive `7`
- tỷ lệ false positive `23.33%`
- không có lỗi runtime khi predict

Kết quả theo loại model:

- `Domain Model`: false positive `5/15` = `33.33%`
- `URL Model`: false positive `2/15` = `13.33%`

Điểm đáng chú ý:

- nhóm `critical`: false positive `4/4`
- nhóm `university_portal`: false positive `7/10`
- các case sai nổi bật tập trung ở:
  - `hocvudientu.hutech.edu.vn`
  - `sinhvien1.hutech.edu.vn`
  - `daotao.hutech.edu.vn`
  - `mail.hutech.edu.vn`
  - `portal.hcmus.edu.vn`

Nhận định sau phase này:

- vấn đề lớn nhất hiện tại không nằm ở `dashboard`
- vấn đề nằm ở `Domain Model` và một phần `URL Model` khi gặp `subdomain / portal` hợp lệ ngoài đời thực
- bộ `vn_real_world_benign_seed` được giữ lại làm bộ test thực chiến, không dùng để train

#### Phase 15. Tạo `VN benign train addon` để bổ sung dữ liệu train

Đã tạo:

- `data/curated/vn_official_site_seeds.csv`
- `data/curated/vn_official_site_seeds_focus.csv`
- `src/collect_vn_benign_train_addon.py`
- `data/curated/vn_real_world_benign_train_addon_domains.csv`
- `data/curated/vn_real_world_benign_train_addon_urls.csv`
- `docs/VN Benign Train Addon.md`

Luồng thu thập:

- lấy URL nội bộ từ `homepage`
- đọc `robots.txt`
- đọc `sitemap`
- lọc giữ các URL thuộc cùng `registered_domain`
- canonicalize URL rồi tách thêm danh sách hostname / domain

Kết quả đợt thu thập focus đầu tiên:

- `278` URL rows
- `150` domain rows
- tổng `428` benign samples bổ sung

Nhóm nguồn thu được tốt:

- `university`
- `government`
- `banking`

Một số sample hữu ích đã có trong addon:

- `hocvudientu.hutech.edu.vn`
- `sinhvien1.hutech.edu.vn`
- `portal.hcmus.edu.vn`
- `online.acb.com.vn`
- `vcbdigibank.vietcombank.com.vn`

Một số nguồn chưa lấy tốt ở lượt này:

- `tphcm.gov.vn`
- `bidv.com.vn`
- `cellphones.com.vn`
- `hcmut.edu.vn`

Nhận định sau phase này:

- đã có một bộ benign bổ sung riêng cho train
- bộ này tách biệt với bộ `seed` dùng để test
- đủ dữ liệu để thử một vòng `augment -> retrain -> evaluate lại`

#### Phase 16. Thử nghiệm `augment -> retrain -> evaluate lại`

Đã tạo dataset thí nghiệm mới bằng cách:

- giữ nguyên `official datasets`
- cộng thêm `vn_real_world_benign_train_addon`
- chỉ gán dữ liệu addon vào các ngày đang thuộc `train`
- không đụng `validation` và `test`

Artifact chính:

- `data/processed/experiments/domain_model_official_plus_vn_benign_addon.parquet`
- `data/processed/experiments/url_model_official_plus_vn_benign_addon.parquet`
- `models/domain_experiments/official_plus_vn_benign_addon/`
- `models/url_experiments/official_plus_vn_benign_addon/`

Kết quả retrain:

- `Domain experiment` chọn `ann_mlp`
- `URL experiment` vẫn chọn `hybrid_lr_xgboost_ann`

Đánh giá lại trên `vn_real_world_benign_seed`:

- trước augment:
  - false positive `7/30` = `23.33%`
  - `Domain Model`: `5/15`
  - `URL Model`: `2/15`
- sau augment:
  - false positive `2/30` = `6.67%`
  - `Domain Model`: `0/15`
  - `URL Model`: `2/15`

Những case còn sai sau augment:

- `https://hocvudientu.hutech.edu.vn/dang-nhap?ReturnUrl=%2F`
- `https://sinhvien1.hutech.edu.vn/elearning/hoc-vu/lich-thi`

Nhận định sau phase này:

- việc bổ sung vài trăm benign samples mới có tác dụng rõ rệt
- cải thiện mạnh nhất nằm ở `Domain Model`
- nhóm còn khó nhất bây giờ là `URL university_portal` có path/query giống mẫu phishing
- hướng tiếp theo hợp lý là tạo thêm `VN real-world phishing seed` và xem có cần augment riêng cho `URL Model` hay không

#### Phase 17. Dựng `VN real-world phishing seed` và so sánh `official` với bản đang test

Đã tạo:

- `src/build_openphish_phishing_seed.py`
- `data/validation/vn_real_world_phishing_seed.csv`
- `docs/VN Real-World Phishing Validation Set.md`
- `docs/VN Real-World Phishing Validation Results - official.md`
- `docs/VN Real-World Phishing Validation Results - official_plus_vn_benign_addon.md`

Nguồn seed:

- lấy từ `OpenPhish snapshot` mới nhất
- không đưa vào `official datasets`
- chỉ dùng để đánh giá riêng khả năng bắt phishing

Kết quả trên `phishing seed`:

- `official`:
  - đúng `25/30`
  - false negative `5/30` = `16.67%`
- `official_plus_vn_benign_addon`:
  - đúng `24/30`
  - false negative `6/30` = `20.00%`

So sánh theo từng model:

- `Domain Model`:
  - `official`: đúng `13/15`
  - `experiment`: đúng `12/15`
- `URL Model`:
  - `official`: đúng `12/15`
  - `experiment`: đúng `12/15`

Case phishing bị hụt thêm ở bản test:

- `accounts.binanceuz.co`

Ghép `benign seed` + `phishing seed` để nhìn trade-off thực chiến:

- `official`:
  - đúng `48/60` = `80.00%`
  - `Domain`: `23/30`
  - `URL`: `25/30`
- `official_plus_vn_benign_addon`:
  - đúng `52/60` = `86.67%`
  - `Domain`: `27/30`
  - `URL`: `25/30`

Nhận định sau phase này:

- bản test chưa nên thay toàn bộ `official` ngay
- nhưng nó rất hứa hẹn cho `Domain Model`, vì:
  - giảm false positive ngoài đời thực rất mạnh
  - chỉ đổi lấy `1` case phishing bị hụt thêm trong seed hiện tại
- `URL Model` gần như chưa thay đổi, nên chưa cần thay
- hướng an toàn nhất tiếp theo là:
  - giữ `official` hiện tại
  - tiếp tục tinh chỉnh riêng nhánh `domain experiment`
  - chỉ cân nhắc thay `Domain Model` trước nếu các vòng test tiếp theo vẫn giữ lợi thế này

#### Phase 18. Promote `Domain Model` bản test thành official, giữ nguyên `URL Model`

Da chot va ap dung:

- `Domain Model` official moi:
  - variant: `from_2025_04_07_global_under_plus_vn_benign_domain_addon`
  - dataset: `data/processed/official/domain_model_official.parquet`
  - model mac dinh: `hybrid_lr_xgboost_ann`
- `URL Model` official:
  - giu nguyen variant `from_2025_04_07_none`
  - giu nguyen model mac dinh `hybrid_lr_xgboost_ann`

Thay doi ky thuat da ap dung:

- tao file nguon rieng cho benign domain addon:
  - `data/raw/vn_benign_domain_addon/vn_benign_domain_addon_2026-04-06.csv`
- sua `src/build_domain_dataset.py` de tu dong doc `data/raw/vn_benign_domain_addon/*.csv`
- train lai official `Domain Model` vao:
  - `models/domain/hybrid_lr_xgboost_ann.joblib`
  - `models/domain/run_summary.json`
  - `models/domain/validation_metrics.csv`
  - `models/domain/test_metrics.csv`
  - `models/domain/model_comparison.csv`
- cap nhat `models/official_model_registry.json`

Smoke test sau khi promote:

- `Domain Model` official moi da predict `hocvudientu.hutech.edu.vn` thanh `benign`
- `URL Model` van giu hanh vi cu, nghia la nhom `university portal URL` van can tiep tuc xu ly rieng o cac phase sau

Cap nhat sau do:

- theo quyet dinh cuoi cung, `Domain Model` official tiep tuc giu `hybrid_lr_xgboost_ann`
- voi dataset official moi co benign addon, `hybrid` van predict `hocvudientu.hutech.edu.vn` thanh `benign`

Da don de bot roi:

- xoa dataset experiment va model experiment cua `official_plus_vn_benign_addon`
- xoa report test tam cua bien the do
- xoa cac file curated trung gian chi dung cho dot test
- xoa script build dataset experiment mot lan va cache `__pycache__`

Nhan dinh sau phase nay:

- nhanh `domain` da duoc thay chinh thuc theo huong giam false positive ngoai doi thuc
- nhanh `url` chua du ly do de thay, nen van giu official cu
- tu nay neu can bo sung benign domain hop le, uu tien bo vao `data/raw/vn_benign_domain_addon/` de pipeline doc thang

---

## 5. Ghi chú ngắn để mai nối việc

Khi mở dự án lại, nên bắt đầu từ 3 việc này:

1. mở rộng thêm `phishing seed` và `benign seed` để bộ đánh giá thực chiến đỡ nhỏ
2. tinh chỉnh tiếp cho `URL Model`, nhất là nhóm `university portal URL`
3. theo dõi thêm các case phishing domain như `accounts.binanceuz.co` để xem `Domain Model` official moi co can bo sung them mau phishing hay khong
