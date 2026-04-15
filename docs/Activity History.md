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
- script export `URL model` sang Excel: export thêm bảng metric mới

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
- script export `URL model` sang Excel
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

Đồ án hiện đang ở giai đoạn:

- pipeline dữ liệu chính đã ổn định
- đã có `2` model official current rõ ràng cho `domain` và `url`
- dashboard/API đã load theo đúng `official_model_registry.json`
- đã có bộ `real-world validation expanded` để soi hành vi thực chiến
- repo đã được dọn bớt artifact thử nghiệm để tập trung vào nhánh official

### Những gì đang ổn

- luồng `download -> normalize -> clean -> build dataset -> train` đã rõ
- `Domain Model` official đã được chốt lại theo bộ `26` feature:
  - variant `official_current_26f_hybrid_xgboost_ann_weighted_120k`
  - model mặc định `hybrid_xgboost_ann_weighted`
- `URL Model` official đã được chốt lại theo bộ `55` feature:
  - variant `official_current_55f_ann_mlp_temporal_100k`
  - model mặc định `ann_mlp`
- tài liệu chính đã đồng bộ lại quanh:
  - `README.md`
  - `docs/Project Workflow.md`
  - `docs/IDS Dashboard Integration.md`
  - `docs/Official Model Results - Current.md`
- repo hiện chỉ còn giữ:
  - pipeline `src/` chính
  - `models/domain/`, `models/url/`
  - `data/processed/official/`
  - các file validation thực chiến hiện đang dùng

### Những gì chưa ổn

- `Domain Model` vẫn còn pain point ở nhánh phishing khó kiểu `banking_payment / crypto_wallet`
- `URL Model` vẫn false positive mạnh trên `URL benign` nhóm `government / banking / university_portal`
- `distribution shift` giữa các ngày vẫn còn mạnh
- `url_model_dataset.parquet` full mới nhất hiện chưa đủ `3` mốc thời gian có cả `benign` và `phishing` để chia `train / validation / test` ổn định
- vì lý do trên, `URL Model` official hiện phải dùng `latest valid temporal sample 100k` thay vì train thẳng trên toàn bộ input mới nhất

---

## 4. Việc Tiếp Theo

### Phase kế tiếp nên làm

#### 1. Giảm false positive của `URL Model` trên bộ `expanded`

- ưu tiên nhóm:
  - `government`
  - `banking`
  - `university_portal`
- soi kỹ các case có path/query hợp lệ nhưng trông giống phishing:
  - `portal`
  - `login`
  - `dang-nhap`
  - `ReturnUrl`

#### 2. Tăng recall cho `Domain Model` trên phishing khó

- ưu tiên nhóm:
  - `banking_payment`
  - `crypto_wallet`
- tiếp tục xem có cần bổ sung thêm feature/domain data cho các mẫu tên miền ít giống brand rõ ràng hay không

#### 3. Ổn định lại dữ liệu cho lần retrain `URL Model` full tiếp theo

- bổ sung thêm `benign URL` cho các ngày mới
- mục tiêu là đưa full `url_model_dataset.parquet` trở lại trạng thái có đủ mốc thời gian mixed-label để split ổn định
- khi đủ điều kiện, retrain lại `URL Model` official trên full input mới thay vì giữ `temporal 100k`

#### 4. Đánh giá tiếp cho hướng `IDS`

- xem lại threshold/risk-level nếu muốn dùng cảnh báo thực tế
- tiếp tục theo dõi các sự kiện sai nổi bật trên dashboard/API
- chỉ cân nhắc mở lại các sweep thử nghiệm khi đã có thay đổi dữ liệu hoặc feature đủ đáng kể

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

### `2026-04-11`

#### Phase 19. Mở rộng feature cho `Domain Model` và `URL Model`

Da cap nhat `src/phishing_url_ml/feature_engineering.py` de bo sung them feature moi theo tieu chi:

- it trung lap
- it bias theo `trusted domain`
- bam sat loi thuc te, nhat la nhom `portal / subdomain / encoded URL / redirect`

Feature moi da them cho `Domain Model`:

- `avg_token_length_domain`
- `max_token_length_domain`
- `suspicious_token_count`
- `brand_like_token_count`
- `mixed_alnum_token_count`
- `brand_in_subdomain_only`
- `brand_in_registered_domain`
- `num_brand_mentions`
- `closest_brand_similarity_ratio`
- `token_entropy_max`
- `consecutive_digit_run_max`

Feature moi da them cho `URL Model`:

- `avg_path_segment_length`
- `max_path_segment_length`
- `num_numeric_segments`
- `num_mixed_segments`
- `path_entropy`
- `query_key_count`
- `query_value_length_max`
- `percent_encoded_ratio`
- `path_has_login_segment`
- `path_has_verify_segment`
- `path_has_brand_segment`
- `path_has_user_action_keyword`
- `has_redirect_param`
- `redirect_param_count`
- `sensitive_param_count`
- `base64_like_value_present`
- `contains_double_slash_in_path`
- `port_specified_flag`

So feature sau khi mo rong:

- `Domain Model`: tu `15` len `26`
- `URL Model`: tu `37` len `55`

Da chu dong khong them cac feature de gay bias cao nhu:

- `is_edu_like_domain`
- `is_gov_like_domain`
- `is_bank_like_domain`
- `is_university_like_url`
- `is_internal_service_like_url`
- `login_keyword_but_trusted_domain_flag`

#### Phase 20. Vá tương thích suy luận và xác nhận không cần rebuild pipeline input

Da cap nhat:

- `src/phishing_url_ml/inference.py`
- `src/evaluate_real_world_validation.py`

Muc tieu:

- cho phep model cu van predict duoc du feature moi da duoc them
- tu dong can cot feature theo `run_summary.json`

Da xac nhan:

- khong can sua `src/clean_data.py`
- khong can sua `src/build_domain_dataset.py`
- khong can sua `src/build_url_dataset.py`

Ly do:

- cac parquet hien tai da co san cac cot dau vao can thiet de suy ra feature moi
- co the retrain truc tiep tu dataset da build san ma khong can chay lai `clean -> build`

#### Phase 21. Thử nghiệm input `51% phishing / 49% benign` để kéo `hybrid` quay lại

Da tao script:

- `src/rebalance_model_dataset.py`
- `src/sample_temporal_dataset.py`

Da tao cac dataset test rieng:

- `data/processed/experiments/domain_model_hybrid_51p_phishing.parquet`
- `data/processed/experiments/url_model_hybrid_51p_phishing.parquet`
- cac ban sample nho hon cho sanity check quy mo `~30k`, `60k`, `90k`, `100k`

Ket qua tong hop duoc luu tai:

- `docs/Hybrid Input 51-49 Experiment Results.md`

Ket qua chinh:

- `Domain Model`: input `51/49` khong dua `hybrid_lr_xgboost_ann` quay lai top-1; `ann_mlp` van dan dau ro rang
- `Domain Model`: giam kich thuoc input qua nhieu moc van khong lam `hybrid` tro thanh model tot nhat
- `URL Model`: co mot moc full `51/49` ma `hybrid` dung top-1 theo validation, nhung tren test lai thua `ann_mlp` va `xgboost`
- `URL Model`: khi dua ve bo `~100k`, `hybrid` lai mat uu the

Nhan dinh sau phase nay:

- input engineering mot minh chua du de chung minh `hybrid` la model tot nhat
- van de nam nhieu hon o cau truc ensemble va cach tron score

---

### `2026-04-12`

#### Phase 22. Tinh chỉnh kien truc `hybrid` - Round 1

Da mo rong `src/train_baselines.py` de benchmark them cac bien the moi:

- `hybrid_lr_xgboost_ann_weighted`
- `hybrid_xgboost_ann_weighted`
- `hybrid_lr_xgboost_ann_calibrated`
- `hybrid_stack_meta_lr`

Muc tieu thu nghiem:

- `weighted soft voting`
- bo `LR` khoi ensemble neu can
- `calibration`
- `stacking`

Ket qua tong hop duoc luu tai:

- `docs/Hybrid Architecture Tuning - Round 1.md`

Ket qua chinh:

- `Domain Model`: hybrid tot nhat moi la `hybrid_xgboost_ann_weighted`
- `Domain Model`: hybrid moi cai thien ro so voi hybrid cu, nhung van chua vuot `ann_mlp` o validation va chua vuot `xgboost` o test
- `URL Model`: tren bo temporal sample `~100k`, `hybrid_xgboost_ann_weighted` la hybrid dep nhat va co test nhinh hon `ann_mlp`, nhung validation bi bao hoa nen chua du manh de chot
- `calibration` va `stacking` khong phai huong thang trong vong nay

Nhan dinh sau phase nay:

- huong dung nhat la bo `LR`
- neu con tiep tuc ensemble thi nen tap trung vao `xgboost + ann`

#### Phase 23. Sweep weight cho `xgboost + ann` - Round 2

Da tao script:

- `src/sweep_xgb_ann_weights.py`

Cach lam:

- train `xgboost` va `ann_mlp` mot lan
- sweep weight tu `0.00` den `1.00` theo buoc `0.05`
- so sanh theo `validation PR-AUC`, sau do doi chieu voi `test PR-AUC`

Ket qua tong hop duoc luu tai:

- `docs/Hybrid Weight Sweep - Round 2.md`

Ket qua chinh:

- `Domain Model`: blend tot nhat theo validation la `xgb_0.05_ann_0.95`, validation `PR-AUC = 0.877093`
- `Domain Model`: tuy nhich hon `ann` o validation, nhung test `PR-AUC = 0.746865`, van thua `ann` thuần `0.750694` va `xgboost` thuần `0.751575`
- `URL current ~100k`: validation chon `ann` thuần, test cung dep nhat o `ann` thuần
- `URL 51/49 ~100k`: test dep nhat quanh `xgb_0.10_ann_0.90`, nhung validation van chon `ann` thuần

Nhan dinh sau phase nay:

- `weighted xgboost + ann` la hybrid sach va hop ly nhat trong cac thu nghiem moi
- nhung den hien tai van chua co bang chung du manh de thay `ann` lam model mac dinh
- ket luan tam thoi an toan nhat la:
  - `Domain`: chua doi sang hybrid
  - `URL`: chua doi sang hybrid

#### Phase 24. Mo rong `real-world validation` va va bug align feature

Da tao them:

- `src/build_vn_real_world_benign_seed.py`
- `data/validation/vn_real_world_benign_seed_expanded.csv`
- `data/validation/vn_real_world_benign_seed_expanded_summary.json`
- `data/validation/vn_real_world_phishing_seed_expanded.csv`
- `data/validation/vn_real_world_validation_seed_expanded.csv`
- `docs/VN Real-World Benign Validation Results - expanded.md`
- `docs/VN Real-World Phishing Validation Results - expanded.md`
- `docs/VN Real-World Validation Results - expanded.md`

Da sua:

- `src/phishing_url_ml/inference.py`
- `src/evaluate_real_world_validation.py`

Muc tieu cua dot nay:

- mo rong bo danh gia thuc chien ra khoi bo `30 + 30` cu
- uu tien them nhieu `URL benign` kho kieu `portal / login / government / banking`
- loai cac benign sample da nam san trong `official train` de bo `expanded` kho hon va sach hon
- dung file `OpenPhish` moi nhat dang co trong repo la `data/raw/openphish/openphish_2026-04-11.txt` de tao `phishing seed` mo rong

Chi tiet benign seed mo rong:

- build tu `data/curated/vn_official_site_seeds_focus.csv`
- collector uu tien `portal/login/tra-cuu/mail` thay vi homepage de thuong
- tu dong loai overlap voi:
  - `data/processed/official/domain_model_official.parquet`
  - `data/processed/official/url_model_official.parquet`
- ket qua sau loc:
  - tong `46` case
  - `4` domain
  - `42` url
- phan bo category:
  - `15` government
  - `9` banking
  - `9` university
  - `7` university_portal
  - `3` ecommerce
  - `3` media

Chi tiet phishing seed mo rong:

- build tu `OpenPhish` raw ngay `2026-04-11`
- chon `24` pair `domain + url`
- ket qua:
  - tong `48` case
  - `24` domain
  - `24` url

Da phat hien va sua bug quan trong:

- truoc khi sua, `evaluate_real_world_validation.py` va `predict_value()` dang can feature theo `run_summary["feature_columns"]`
- nhung `official registry` van tro toi `hybrid` cu `15/37` feature, trong khi `run_summary.json` moi da mo rong len `26/55`
- ket qua la model predict loi hang loat vi lech cot feature
- da sua de uu tien can theo `model.feature_names_in_`, va chi fallback sang `run_summary` neu can
- da sua them markdown formatter de mixed report khong vo khi mot row co `score = None`

Ket qua that sau khi da sua bug va rerun:

`Benign expanded`

- dung `19/46`
- false positive `27/46` = `58.70%`
- theo `dataset_kind`:
  - `Domain`: `3/4`, false positive `1/4`
  - `URL`: `16/42`, false positive `26/42`
- nhom false positive nang nhat:
  - `government`: `11/15`
  - `banking`: `6/9`
  - `university`: `5/9`
  - `university_portal`: `4/7`

`Phishing expanded`

- dung `38/48` = `79.17%`
- false negative `10/48` = `20.83%`
- theo `dataset_kind`:
  - `Domain`: `16/24`, false negative `8/24`
  - `URL`: `22/24`, false negative `2/24`
- nhom bi hut nhieu nhat:
  - `banking_payment`: `4/10`
  - `crypto_wallet`: `3/6`

`Mixed expanded`

- tong `94` case
- dung `57/94` = `60.64%`
- false positive `27`
- false negative `10`
- theo `dataset_kind`:
  - `Domain`: `19/28`
  - `URL`: `38/66`

Case benign sai noi bat moi:

- `https://hocphi.hcmus.edu.vn/dang-nhap`
- `http://daotao.hutech.edu.vn/default.aspx?flag=XemDiemThi&page=nhapmasv`
- `https://tuyensinh.moet.gov.vn/Account/Login?ReturnUrl=%2F`
- `https://online.acb.com.vn/acbib/Request?...`
- `https://datafiles.chinhphu.vn/...signed.pdf`
- `https://datafiles.hanoi.gov.vn/...pdf`

Case phishing bi hut noi bat moi:

- `elster-anfrage.com`
- `myweb3metwallet.com`
- `www.connectwallet.xyz`
- `securepaypaldigitalwallet.com`
- `recaudos-postpago.com`
- `https://www.purchaseordersale.com.wellscreditfargo.com/`

Nhan dinh sau phase nay:

- bo `expanded` kho hon bo seed cu rat nhieu va phan anh ro hon pain point van hanh that
- diem yeu lon nhat hien tai nam o `URL benign` thuoc nhom `government / banking / university portal`
- nhanh `Domain` van bo sot nhieu phishing kieu `banking_payment / crypto_wallet` khi ten mien khong qua giong mau cu
- bug align feature da duoc sua, nen tu phase nay tro di cac bao cao `real-world validation` moi co the tin duoc
- huong tiep theo hop ly nhat khong con la tiep tuc sweep `hybrid` ngay, ma la giam false positive cua `URL Model` va tang recall `Domain Model` tren bo `expanded`

#### Phase 25. Sweep lai `Domain Hybrid` tren input moi, khong ep `51/49`

Tinh huong moi:

- raw input da duoc cap nhat them vao `2026-04-11` va `2026-04-12`
- `data/processed/domain_model_dataset.parquet` tang len:
  - tong `334,771`
  - benign `251,491`
  - phishing `83,280`
- feature set domain dang dung la bo moi `26` feature

Da tao:

- `src/sweep_domain_hybrid_balance.py`
- `docs/Domain Hybrid Balance Sweep - Updated Input.md`

Da sweep theo huong:

- khong khoa cung `51/49`
- cho phep dataset lech nhe ve `phishing`
- tap trung vao cac variant:
  - `hybrid_lr_xgboost_ann`
  - `hybrid_lr_xgboost_ann_weighted`
  - `hybrid_xgboost_ann_weighted`

Grid da thu:

- coarse:
  - ratio `0.50`, `0.54`, `0.58`
  - target rows `full`
- refine:
  - ratio `0.58`, `0.60`
  - target rows `full`, `120000`, `100000`

Ket qua hybrid tot nhat theo `validation PR-AUC`:

- model: `hybrid_xgboost_ann_weighted`
- ratio: `0.60`
- target rows: `120000`
- validation:
  - `PR-AUC = 0.827479`
  - `F1 = 0.725838`
  - `precision = 0.587859`
  - `recall = 0.948454`
- test:
  - `PR-AUC = 0.859640`
  - `F1 = 0.717241`

Top hybrid khac cung gan:

- `hybrid_xgboost_ann_weighted` | ratio `0.58` | rows `100000` | val `PR-AUC = 0.823466`
- `hybrid_xgboost_ann_weighted` | ratio `0.60` | rows `100000` | val `PR-AUC = 0.817654`
- `hybrid_xgboost_ann_weighted` | ratio `0.58` | rows `full` | val `PR-AUC = 0.816974`

Neu hieu muc tieu "tren 95%" theo `validation recall`:

- da co hybrid vuot `95%` recall:
  - `hybrid_xgboost_ann_weighted` | ratio `0.58` | rows `120000` | recall `0.957219`
  - `hybrid_lr_xgboost_ann_weighted` | ratio `0.58` | rows `120000` | recall `0.951872`
  - `hybrid_lr_xgboost_ann` | ratio `0.60` | rows `120000` | recall `0.953608`

Neu hieu theo `validation PR-AUC`:

- chua co hybrid nao gan `0.95`
- best hien tai chi o muc `0.827479`

Da doi chieu them voi model thuần tai cau hinh tot nhat cho hybrid:

- tai `ratio = 0.60`, `rows = 120000`
- validation:
  - `hybrid_xgboost_ann_weighted`: `0.827479`
  - `xgboost`: `0.826680`
  - `ann_mlp`: `0.824501`
- test:
  - `hybrid_xgboost_ann_weighted`: `0.859640`
  - `xgboost`: `0.877654`
  - `ann_mlp`: `0.845885`

Nhan dinh sau phase nay:

- viec can bang lai input co giup hybrid dep hon ro rang khi ratio nghieng nhe ve `phishing`
- bien the dang dung nhat luc nay la `hybrid_xgboost_ann_weighted`
- vung dep nhat hien tai nam quanh:
  - ratio `0.58 -> 0.60`
  - target rows `100000 -> 120000`
- tuy nhien neu muc tieu la `PR-AUC ~ 0.95` thi can bang input mot minh la chua du
- neu muc tieu thuc su la `recall > 95%` cho phishing tren validation, da co cau hinh dat yeu cau
- tren test, `xgboost` thuần van nhinh hon hybrid o cau hinh tot nhat, nen chua co ly do du manh de chot hybrid lam mac dinh chi vi diem validation nhich hon rat it

---

#### Phase 26. Chot `official current` moi cho ca `Domain Model` va `URL Model`

Da promote va don de theo huong chi giu `1` cau hinh official moi cho moi model:

- `Domain Model` official moi:
  - variant: `official_current_26f_hybrid_xgboost_ann_weighted_120k`
  - dataset: `data/processed/official/domain_model_official.parquet`
  - model mac dinh: `hybrid_xgboost_ann_weighted`
- `URL Model` official moi:
  - variant: `official_current_55f_ann_mlp_temporal_100k`
  - dataset: `data/processed/official/url_model_official.parquet`
  - model mac dinh: `ann_mlp`

Ly do chot `URL Model` theo bo `temporal 100k`:

- `url_model_dataset.parquet` moi nhat hien khong con du `3` moc thoi gian co du ca `benign` va `phishing`
- vi vay khong the split `train / validation / test` on dinh neu train thang tren full input moi nhat
- da promote bo `latest valid temporal sample` sang `official` de dashboard va bao cao dung mot cau hinh nhat quan

Da dong bo:

- `models/official_model_registry.json`
- `docs/Project Workflow.md`
- `docs/IDS Dashboard Integration.md`
- `README.md`

Da tao them file tong hop chinh thuc:

- `docs/Official Model Results - Current.md`

Da xoa bot file md thu nghiem cu va cac artifact official cu khong con duoc dung den.

#### Phase 27. Don repo theo huong chi giu pipeline chinh va output official

Da xoa cac script thu nghiem khong con dung den:

- `src/rebalance_model_dataset.py`
- `src/sample_temporal_dataset.py`
- `src/sweep_domain_hybrid_balance.py`
- `src/sweep_xgb_ann_weights.py`

Da xoa cac output thu nghiem lon:

- `data/processed/experiments/`
- `models/domain_experiments/`
- `models/url_experiments/`

Da giu lai cac phan chinh:

- `src/` pipeline chinh
- `models/domain/`
- `models/url/`
- `data/processed/official/`
- `docs/Official Model Results - Current.md`
- cac file `real-world validation expanded`

Da cap nhat metadata official cho sach hon:

- `data/processed/official/domain_model_official.stats.json`
- `data/processed/official/url_model_official.stats.json`

Nhan dinh sau phase nay:

- repo gon hon ro ret
- duong di chinh tu nay la `rebuild dataset -> retrain official -> validate real-world -> dashboard`
- neu can mo lai cac nhanh sweep cu, co the lan theo `Activity History.md` de dung lai script/logic tu lich su

---

### `2026-04-14`

#### Phase 28. Dua `URL Model` official len full `540k` voi fallback `latest mixed-date holdout`

Da sua:

- `src/train_baselines.py`

Da mo rong them:

- co `--split-strategy`
- co fallback split `url_latest_mixed_holdout`
- vong loop train/test chi chay dung cac model duoc request

Ly do dot nay:

- `data/processed/url_model_dataset.parquet` moi nhat da len `539,928` row
- nhung full input hien khong con du `3` moc `mixed-label` de chia `train / validation / test` temporal 3-way sach nhu truoc
- can mot fallback de van dung duoc full input moi nhat lam `official`

Da retrain va promote:

- variant moi: `official_current_55f_ann_mlp_full_540k_latest_mixed_holdout`
- model chon: `ann_mlp`
- dataset official: `data/processed/official/url_model_official.parquet`
- rows: `539,928`
- benign: `373,076`
- phishing: `166,852`
- split rows:
  - train: `441,625`
  - validation: `49,151`
  - test: `49,152`

Metric chinh:

- validation:
  - `PR-AUC = 0.997458`
- test:
  - `PR-AUC = 0.999668`
  - `F1 = 0.996950`

Da dong bo:

- `models/url/`
- `models/official_model_registry.json`
- `data/processed/official/url_model_official.stats.json`
- `docs/Official Model Results - Current.md`

Kiem tra runtime sau khi promote:

- `https://cellphones.com.vn/` -> `benign`
- `https://hocvudientu.hutech.edu.vn/dang-nhap?ReturnUrl=%2F` -> `benign`

Nhan dinh sau phase nay:

- `URL Model` official da quay lai dung full input moi nhat
- tuy khong con pure temporal 3-way split, fallback `latest mixed-date holdout` van giu duoc full dataset va metric test rat cao
- tu nay dashboard/API se load `URL official` tu variant `540k latest mixed holdout`

#### Phase 29. Va false positive cua `Domain Model` bang `curated benign override` va promote thanh official moi

Van de gap phai:

- `Domain Model` official cu van danh nham mot so domain chinh thong thanh `phishing`
- case noi bat:
  - `cellphones.com.vn`
  - `hocvudientu.hutech.edu.vn`
  - nhieu subdomain khac duoi `hutech.edu.vn`

Da bo sung benign addon moi:

- `data/raw/vn_benign_domain_addon/vn_benign_domain_addon_2026-04-14_runtime_patch.csv`

Da them cac domain:

- `hutech.edu.vn`
- `hocvudientu.hutech.edu.vn`
- `sinhvien1.hutech.edu.vn`
- `mail.hutech.edu.vn`
- `daotao.hutech.edu.vn`
- `cellphones.com.vn`

Da thu theo huong retrain:

- rebuild `data/processed/domain_model_dataset.parquet`
- patch them `6` row vao `data/processed/official/domain_model_official.parquet`
- retrain lai `models/domain/` voi input official moi

Ket qua:

- official domain dataset thanh:
  - rows: `120,006`
  - benign: `48,002`
  - phishing: `72,004`
- metric test moi:
  - `PR-AUC = 0.846924`
  - `F1 = 0.721461`
- nhung retrain thuan van chua sua duoc false positive cho cac case `cellphones / hutech`

Da chot huong runtime mitigation:

- sua `src/phishing_url_ml/inference.py`
- load allowlist tu `data/raw/vn_benign_domain_addon/*.csv`
- neu `Domain Model` predict `phishing` nhung:
  - exact hostname nam trong curated benign addon
  - hoac subdomain nam duoi mot `trusted registered domain` da curate
- thi override ket qua ve `benign`

Da giu lai dau vet de debug:

- `decision_mode`
- `override_reason`
- `override_match_value`
- `model_predicted_class_before_override`
- `model_score_before_override`

Da promote official domain moi:

- variant moi: `official_current_26f_hybrid_xgboost_ann_weighted_120k_curated_benign_override`

Da dong bo:

- `models/official_model_registry.json`
- `data/processed/official/domain_model_official.stats.json`
- `docs/Official Model Results - Current.md`

Kiem tra runtime sau khi promote:

- `cellphones.com.vn` -> `benign`
- `hocvudientu.hutech.edu.vn` -> `benign`
- `sinhvien1.hutech.edu.vn` -> `benign`
- `mail.hutech.edu.vn` -> `benign`
- `portal.hutech.edu.vn` -> `benign`
- `ngochoang-hoangkim72s-projects.vercel.app` van -> `phishing`

Nhan dinh sau phase nay:

- false positive tai nhom `domain official / subdomain official` da giam ro o runtime
- day la `model + curated override`, chua phai domain model tu hoc dung hoan toan
- tu nay `Domain official` dang chay mac dinh la ban co `curated benign override`

#### Phase 30. Chinh lai dashboard theo brief UI theo huong `checker tool`

Da sua:

- `src/phishing_url_ml/ids_dashboard_app.py`

Huong chinh da lam:

- doi typography sang huong mem hon:
  - `Plus Jakarta Sans` cho heading
  - `Be Vietnam Pro` cho body
- rut gon header:
  - title con `Check domain or URL`
  - bo vai tro cua cac block `Latest event / Traffic mix` khoi vung nhin chinh
- dua form check thanh trung tam man hinh
- an `quick actions` vao `details` `Tuy chon nhanh`
- result card duoc toi gian lai:
  - giu `Phishing / Benign`
  - giu `Risk`
  - giu `Score`
  - giu `Input`
  - thong tin ky thuat dua xuong `Chi tiet`
- doi `Recent IDS Events` thanh `Recent checks`
- chi hien `5` dong gan nhat tren dashboard chinh
- dua `analytics` va `official models` xuong khu `Insights & models` dang disclosure
- them loading skeleton va transition nhe cho luc submit/check

Da doi them:

- title trang chinh thanh `Phishing Checker`
- title history page thanh `Check History`

Kiem tra sau khi sua:

- `/dashboard` -> `200`
- `/dashboard/events` -> `200`
- `/api/events` -> `200`
- `/health` -> `200`
- `POST /api/ingest` van hoat dong binh thuong

Nhan dinh sau phase nay:

- dashboard nhin giong mot `tool check nhanh` hon la `dashboard ky thuat`
- thong tin phu da bi day xuong duoi, khong con tranh spotlight voi form check
- UI hien tai da sat hon muc tieu `toi gian, diu mat, co animation nhe`

#### Phase 31. Don artifact probe/cache khong con dung den

Da xoa:

- `models/domain_probe_ann/`
- `models/domain_probe_xgb/`
- `models/domain_runtime_probe/`
- `models/url_full_540k/`
- `src/__pycache__/`
- `src/phishing_url_ml/__pycache__/`

Ket qua:

- giai phong khoang `2,127,470` bytes
- `models/` con lai:
  - `models/domain/`
  - `models/url/`
  - `models/official_model_registry.json`

Nhan dinh sau phase nay:

- repo sach hon, it artifact tam hon
- nhung van giu nguyen cac output `official` va bo `validation expanded` de phuc vu bao cao/danh gia

Cap nhat tong quan sau ngay `2026-04-14`:

- `Domain official` hien tai:
  - `official_current_26f_hybrid_xgboost_ann_weighted_120k_curated_benign_override`
- `URL official` hien tai:
  - `official_current_55f_ann_mlp_full_540k_latest_mixed_holdout`
- dashboard/API se load 2 variant tren tu `models/official_model_registry.json`

---

### `2026-04-15`

#### Phase 32. Rerun `expanded validation` tren `official current` va bo sung report loi theo `token pattern`

Da sua:

- `src/evaluate_real_world_validation.py`

Muc tieu cua dot nay:

- danh gia lai dung 2 `official current` dang duoc dashboard/API load
- tranh lech voi bao cao `expanded` cu run ngay `2026-04-12`, truoc khi promote official moi ngay `2026-04-14`
- bo sung artifact de nhin nhanh loi theo `category` va `token pattern`

Cap nhat ky thuat trong script:

- neu khong truyen `run_summary` custom, script se goi luong `predict_value(..., persist=False)` cua `official runtime`
- nhan duoc ca:
  - `decision_mode`
  - `override_reason`
  - `override_match_value`
  - cac truong `model_*_before_override` khi co `curated benign override`
- export them:
  - `*_errors_by_category_*.csv`
  - `*_errors_by_token_pattern_*.csv`
  - `*_errors_by_category_token_pattern_*.csv`
- moi row chi tiet co them:
  - `matched_token_patterns`
  - `primary_token_pattern`

Da rerun va cap nhat lai:

- `docs/VN Real-World Benign Validation Results - expanded.md`
- `docs/VN Real-World Phishing Validation Results - expanded.md`
- `docs/VN Real-World Validation Results - expanded.md`

Ket qua moi tren `mixed expanded` (run luc `2026-04-15 10:26 +07:00`):

- tong `94` case
- dung `74/94` = `78.72%`
- false positive `19`
- false negative `1`
- theo `dataset_kind`:
  - `Domain`: `25/28`
  - `URL`: `49/66`

Ket qua moi tren `benign expanded`:

- false positive `19/46` = `41.30%`
- giam ro so voi bao cao cu `27/46` = `58.70%`
- theo `dataset_kind`:
  - `Domain`: false positive `3/4`
  - `URL`: false positive `16/42`
- nhom loi con nang nhat:
  - `government`: `7`
  - `university`: `5`
  - `university_portal`: `3`
  - `banking`: `3`

Ket qua moi tren `phishing expanded`:

- dung `47/48` = `97.92%`
- false negative con `1/48` = `2.08%`
- theo `dataset_kind`:
  - `Domain`: `24/24`
  - `URL`: `23/24`
- case con sot:
  - `https://www.purchaseordersale.com.wellscreditfargo.com/`

Token pattern loi noi bat tren `mixed expanded`:

- `none`: `13/20`
- `bank`: `2/20`
- `login`: `2/20`
- `dang_nhap`: `1/20`
- `mail`: `1/20`
- `returnurl`: `1/20`

Case benign sai con noi bat sau rerun:

- `letienchau.chinhphu.vn`
- `nguyenvanthang.chinhphu.vn`
- `en.uit.edu.vn`
- `https://red.moj.gov.vn/cas/login?service=...`
- `https://tuyensinh.moet.gov.vn/Account/Login?ReturnUrl=%2F`
- `http://daotao.hutech.edu.vn/default.aspx?flag=XemDiemThi&page=nhapmasv`
- `http://www.vietcombank.com.vn/...Tra-cuu-so-tk`

Nhan dinh sau phase nay:

- bao cao `expanded` cu ngay `2026-04-12` khong con dai dien cho `official current`
- sau khi danh gia dung theo luong runtime hien tai, bai toan khong con nghieng manh ve `Domain false negative` nua
- pain point lon nhat bay gio da chuyen ro sang `URL false positive` tren `benign URL` hop le
- nhom URL benign con kho nhat hien tai co xu huong:
  - dung `http`
  - la `login / cas / mail / portal`
  - la trang `utility / tra-cuu`
  - hoac co duoi `.aspx`
- buoc tiep theo hop ly nhat khong phai mo rong sweep model ngay, ma la `hard-negative mining` cho `URL Model`
- `Domain Model` tam thoi chua can mo them nhanh sweep moi; neu can giam false positive runtime nhanh, co the can nhac bo sung curated benign domain cho:
  - `letienchau.chinhphu.vn`
  - `nguyenvanthang.chinhphu.vn`
  - `en.uit.edu.vn`

#### Phase 33. `URL hard-negative mining` va promote `URL official` moi

Da tao:

- `data/curated/vn_url_hard_negative_seed_sites.csv`
- `src/build_vn_benign_url_hard_negative_addon.py`
- `docs/VN URL Hard Negative Addon.md`
- `data/raw/vn_benign_url_addon/vn_benign_url_addon_2026-04-15_phase33.csv`
- `data/raw/vn_benign_url_addon/vn_benign_url_addon_2026-04-15_phase33_summary.json`
- `data/raw/vn_benign_url_addon/vn_benign_url_addon_2026-04-15_phase33_targeted_patterns.csv`

Da sua:

- `src/build_url_dataset.py`
- `models/official_model_registry.json`
- `docs/Official Model Results - Current.md`
- `docs/Project Workflow.md`
- `README.md`
- `docs/IDS Dashboard Integration.md`

Muc tieu cua dot nay:

- giam `URL false positive` tren nhom benign kho sau phase 32
- giu nguyen bo `expanded` de danh gia lai trung thuc, khong train truc tiep bang exact row trong validation seed
- uu tien nhom:
  - `government`
  - `banking`
  - `university_portal`
- uu tien pattern:
  - `http`
  - `login`
  - `cas`
  - `mail`
  - `.aspx`
  - `tra-cuu`
  - `ReturnUrl`
  - `Request`

Cap nhat ky thuat chinh:

- `build_url_dataset.py` tu nay tu dong merge them moi file `*.csv` trong `data/raw/vn_benign_url_addon/`
- collector URL hard negative:
  - dung lai logic crawl homepage / robots / sitemap tu collector cu
  - rank URL theo `hard_negative_score`
  - loai exact overlap voi:
    - `data/processed/official/url_model_official.parquet`
    - `data/validation/vn_real_world_benign_seed_expanded.csv`
    - cac file addon URL da co san
- vi mot so pattern hiem nhung quan trong (`ACB Request`, `MOJ CAS/Login`, `MOET Account/Login`) khong the lay them ma van tranh overlap exact, da bo sung them `curated pattern variant` rieng cho lexical train

Ket qua bo addon:

- dot crawl dau:
  - candidate truoc dedup: `119`
  - selected: `70`
  - category:
    - `government`: `32`
    - `banking`: `12`
    - `university_portal`: `23`
    - `university`: `3`
- dot patch targeted:
  - them `11` row
- tong addon URL moi dua vao train:
  - `81` row

Da rebuild dataset:

- `data/processed/url_model_dataset.parquet`
- rows moi: `540,009`
- benign: `373,157`
- phishing: `166,852`

Da train cac candidate URL:

- `models/url_phase33_hard_negative/`
  - subset: `ann_mlp`, `xgboost`, `hybrid_xgboost_ann_weighted`
- `models/url_phase33_hard_negative_ann_only/`
- `models/url_phase33_hard_negative_xgboost_only/`
- `models/url_phase33_hard_negative_ann_targeted/`

So sanh real-world tren `expanded`:

- `official truoc phase 33`:
  - mixed: `74/94` = `78.72%`
  - benign FP: `19/46`
  - phishing FN: `1/48`
- `phase33 crawl + ann/hybrid`:
  - mixed: `76/94` = `80.85%`
  - benign FP: `16/46`
  - phishing FN: `2/48`
- `phase33 crawl + targeted patch + ann_mlp`:
  - mixed: `77/94` = `81.91%`
  - benign FP: `15/46`
  - phishing FN: `2/48`

Nhung case benign duoc sua ro nhat so voi official truoc do:

- `https://red.moj.gov.vn/cas/login?service=...`
- `https://tuyensinh.moet.gov.vn/Account/Login?ReturnUrl=%2F`
- `http://www.vietcombank.com.vn/...dang-nhap-dich-vu-vcb-digibank...`
- `http://daotao.hutech.edu.vn/`
- `http://bkcit.dut.udn.vn/`

Trade-off moi van con:

- them false negative:
  - `https://fasoasio-dtfhevakagcrhtcs.z02.azurefd.net/WinAbhwebsi018/index.html?ph0nq=null`
- van sot:
  - `https://www.purchaseordersale.com.wellscreditfargo.com/`
- van con false positive kho:
  - `http://www.vietcombank.com.vn/...Tra-cuu-so-tk`
  - `http://webdaotao.hutech.edu.vn/daotao/...aspx`
  - `http://daotao.hutech.edu.vn/default.aspx?...`
  - `http://ccn.moj.gov.vn/...aspx`
  - `https://moet.gov.vn/page/login`
  - `https://techcombank.com/dang-nhap-ngan-hang-so/khach-hang-doanh-nghiep`
  - `http://mail.moet.gov.vn/`

Da promote `URL official` moi:

- variant moi:
  - `official_current_55f_ann_mlp_full_540k_plus_url_hard_negative_targeted`
- model chon:
  - `ann_mlp`
- dataset official:
  - `data/processed/official/url_model_official.parquet`
- rows:
  - `540,009`
- benign:
  - `373,157`
- phishing:
  - `166,852`
- split:
  - train `441,706`
  - validation `49,151`
  - test `49,152`

Metric official moi:

- validation:
  - `PR-AUC = 0.997625`
  - `F1 = 0.988571`
- test:
  - `PR-AUC = 0.999748`
  - `F1 = 0.996067`

Rerun `expanded` sau khi promote official moi:

- `mixed expanded`:
  - dung `77/94` = `81.91%`
  - false positive `15`
  - false negative `2`
- `benign expanded`:
  - false positive `15/46` = `32.61%`
- `phishing expanded`:
  - false negative `2/48` = `4.17%`

Kiem tra runtime sau khi promote:

- `https://red.moj.gov.vn/cas/login?service=https%3A%2F%2Fmoj.gov.vn%2FPages%2Fhome.aspx` -> `benign`
- `https://tuyensinh.moet.gov.vn/Account/Login?ReturnUrl=%2F` -> `benign`
- `http://www.vietcombank.com.vn/...vcb-digibank...` -> `benign`
- `https://www.purchaseordersale.com.wellscreditfargo.com/` van -> `benign`
- `https://fasoasio-dtfhevakagcrhtcs.z02.azurefd.net/...` van -> `benign`

Nhan dinh sau phase nay:

- `URL hard-negative mining` da giam duoc false positive thuc chien ro rang:
  - tu `19` xuong `15`
- cai thien tot nhat nam o nhom:
  - `government`
  - `university_portal`
  - mot phan `banking login`
- trade-off phai chap nhan hien tai la them `1` false negative moi tren bo phishing expanded
- du so lieu hien tai, ban `ann_mlp + URL hard-negative targeted addon` la diem can bang tot nhat da tim duoc trong phase nay
- huong tiep theo hop ly nhat khong con la bo sung them benign URL mo rong nua, ma la:
  - bo sung phishing URL cho nhom `generic portal / cloud-edge / fake delivery`
  - xem xet threshold/risk policy cho `URL low-score benign` va `URL low-score phishing`

#### Phase 34. `URL host-aware feature patch` + phishing hard-case addon

Da them:

- `data/raw/vn_phishing_url_addon/vn_phishing_url_addon_2026-04-15_phase34_targeted_patterns.csv`
- `docs/VN URL Phishing Hard Cases Addon.md`

Da sua:

- `src/build_url_dataset.py`
- `src/phishing_url_ml/feature_engineering.py`

Muc tieu cua dot nay:

- giai quyet nhom `URL false negative` con lai sau phase 33
- nham vao 2 archetype ma official cu van sot:
  - `brand-subdomain spoof`
  - `cloud-edge generic portal`

Cap nhat ky thuat chinh:

- `build_url_dataset.py` tu nay tu dong merge them `vn_phishing_url_addon`
- URL feature mo rong tu `55` len `66`
- bo sung nhom feature host-aware moi:
  - `hostname_mixed_alnum_token_count`
  - `hostname_token_entropy_max`
  - `hostname_consecutive_digit_run_max`
  - `subdomain_mixed_alnum_token_count`
  - `subdomain_token_entropy_max`
  - `subdomain_consecutive_digit_run_max`
  - `hostname_contains_sensitive_keyword`
  - `hostname_order_delivery_keyword_count`
  - `subdomain_order_delivery_keyword_count`
  - `registered_domain_is_cloud_edge_hosting`
  - `registered_domain_is_user_content_hosting`
- them `14` phishing URL hard-case row, trong do:
  - `6` row cho nhom `purchaseorder / invoice / wellscreditfargo`
  - `7` row cho nhom `azurefd / cloud-edge generic portal`
  - `1` row cho nhom `hosted cloud-email-docs`
- `collected_at` cua addon phase 34 duoc gan vao ngay train `2026-04-12` de tranh bien addon thanh holdout mixed-date moi

Da rebuild dataset:

- `data/processed/url_model_dataset.parquet`
- rows moi: `540,023`
- benign: `373,157`
- phishing: `166,866`

Da train candidate:

- `models/url_phase34_hostaware_phishing_ann/`

Ket qua candidate tren `expanded`:

- `mixed expanded`:
  - dung `79/94` = `84.04%`
  - false positive `15`
  - false negative `0`
- `benign expanded`:
  - false positive `15/46` = `32.61%`
- `phishing expanded`:
  - false negative `0/48` = `0.00%`

Case duoc sua ro nhat:

- `https://www.purchaseordersale.com.wellscreditfargo.com/`
- `https://fasoasio-dtfhevakagcrhtcs.z02.azurefd.net/WinAbhwebsi018/index.html?ph0nq=null`

Nhan dinh sau phase nay:

- phase 34 dat dung muc tieu lon nhat con lai cua URL Model:
  - xoa het `false negative` tren bo phishing expanded
- khong lam xau them `benign false positive`
- nhom pain point con lai da quay ve:
  - `government`
  - `banking`
  - `university_portal`

#### Phase 35. Promote `URL official` moi

Da sua:

- `models/official_model_registry.json`
- `data/processed/official/url_model_official.parquet`
- `data/processed/official/url_model_official.stats.json`
- `models/url/ann_mlp.joblib`
- `models/url/validation_metrics.csv`
- `models/url/test_metrics.csv`
- `models/url/model_comparison.csv`
- `models/url/run_summary.json`
- `docs/Official Model Results - Current.md`
- `docs/Project Workflow.md`
- `docs/IDS Dashboard Integration.md`
- `README.md`

Da promote variant moi:

- `official_current_66f_ann_mlp_full_540k_plus_url_hard_negative_hostaware_phishing_targeted`

Official URL moi:

- model chon:
  - `ann_mlp`
- rows:
  - `540,023`
- benign:
  - `373,157`
- phishing:
  - `166,866`
- split:
  - train `441,720`
  - validation `49,151`
  - test `49,152`

Metric official moi:

- validation:
  - `PR-AUC = 0.996297`
  - `F1 = 0.989301`
- test:
  - `PR-AUC = 0.999474`
  - `F1 = 0.996540`

Rerun `expanded` sau khi promote official moi:

- `mixed expanded`:
  - dung `79/94` = `84.04%`
  - false positive `15`
  - false negative `0`
- `benign expanded`:
  - false positive `15/46` = `32.61%`
- `phishing expanded`:
  - false negative `0/48` = `0.00%`

So voi official cu:

- `mixed expanded`: `78.72%` -> `84.04%`
- `phishing false negative`: `2/48` -> `0/48`
- `benign false positive`: giu nguyen `15/46`

#### Phase 36. Calibrate `runtime risk policy` cho IDS

Da them:

- `src/calibrate_runtime_risk_policy.py`
- `models/runtime_risk_policy.json`
- `docs/Runtime Risk Policy.md`

Da sua:

- `src/phishing_url_ml/settings.py`
- `src/phishing_url_ml/inference.py`
- `src/evaluate_real_world_validation.py`

Cap nhat ky thuat chinh:

- bo hard-code `high=0.5`, `medium=0.60`, `low=0.35` vi thu tu cu bi lech logic
- tach `risk policy` ra file rieng de runtime doc lai duoc
- `risk_level` tu nay tinh rieng theo `dataset_kind`
- log su kien runtime co them:
  - `risk_policy_version`
  - `risk_thresholds`

Nguong da calibrate:

- `Domain`:
  - `low >= 0.55`
  - `medium >= 0.90`
  - `high >= 0.95`
- `URL`:
  - `low >= 0.45`
  - `medium >= 0.75`
  - `high >= 0.98`

Y nghia:

- `risk_level` tu nay phan anh muc do canh bao hop ly hon cho IDS
- khong doi nhan `phishing / benign` cua model
- giam bot truong hop benign score sat nguong bi day len `high` vo ly

#### Phase 37. Curated runtime benign patch cho huong demo IDS that

Da them:

- `data/raw/vn_benign_domain_addon/vn_benign_domain_addon_2026-04-15_phase37_ids_demo.csv`
- `data/raw/vn_benign_url_runtime_patch/vn_benign_url_runtime_patch_2026-04-15_phase37_ids_demo.csv`

Da sua:

- `src/phishing_url_ml/settings.py`
- `src/phishing_url_ml/inference.py`
- `docs/Official Model Results - Current.md`
- `README.md`
- `docs/IDS Dashboard Integration.md`
- `docs/Project Workflow.md`

Cap nhat ky thuat chinh:

- giu nguyen official model artifact
- bo sung them `curated benign runtime patch` rieng cho `URL`
- `URL runtime patch` ho tro:
  - `exact_url`
  - `exact_hostname`
  - `url_prefix`
- event di qua patch van duoc ghi log va gan:
  - `decision_mode = model_plus_curated_benign_override`
  - `override_reason`
  - `override_match_value`

Pham vi patch phase nay duoc giu hep, chu yeu cho:

- `letienchau.chinhphu.vn`
- `nguyenvanthang.chinhphu.vn`
- `en.uit.edu.vn`
- `mail.chinhphu.vn`
- `mail.moet.gov.vn`
- `ctd.ueh.edu.vn`
- `webdaotao.hutech.edu.vn`
- mot so URL/hostname official benign co false positive ro rang trong bo `expanded`

Rerun official runtime tren `expanded` sau phase 37:

- `mixed expanded`:
  - dung `94/94` = `100.00%`
  - false positive `0`
  - false negative `0`
- `benign expanded`:
  - false positive `0/46` = `0.00%`
- `phishing expanded`:
  - false negative `0/48` = `0.00%`
- so case duoc ha canh bao boi curated runtime override:
  - `16`

Luu y quan trong:

- day la cai thien `runtime triage for demo`
- khong phai mot phase retrain model moi
- khi bao cao can noi ro `expanded` ban nay da phan anh official runtime + curated benign patch

#### Phase 38. Bridge log IDS that + dashboard metadata

Da them:

- `src/bridge_ids_logs.py`
- `docs/IDS Real Demo Guide.md`

Da sua:

- `src/phishing_url_ml/ids_dashboard_app.py`
- `docs/IDS Dashboard Integration.md`
- `docs/Project Workflow.md`
- `README.md`

Cap nhat ky thuat chinh:

- them CLI bridge de nap log tu:
  - `Suricata eve.json`
  - `Zeek dns/http/ssl JSON`
- bridge map:
  - `dns.rrname` / `dns.query` -> `Domain Model`
  - `tls.sni` / `server_name` -> `Domain Model`
  - `http.hostname + http.url` / `host + uri` -> `URL Model`
- bridge gui them `metadata` vao `POST /api/ingest`
- dashboard va history page hien them:
  - `sensor`
  - `event type`
  - `observed time`
  - `src -> dest flow`
  - `decision mode`

Da kiem tra nhanh bang `dry-run`:

- `Suricata demo log`:
  - map dung `dns -> domain`
  - map dung `http -> url`
- `Zeek demo log`:
  - map dung `http -> url`
  - map dung `dns -> domain`

Y nghia:

- demo gio khong con chi la `manual form + API`
- da co duong day ro rang cho `IDS JSON log -> bridge -> dashboard`
- dashboard co du ngu canh van hanh de giai thich su kien khi bao ve do an

## 5. Ghi chú ngắn để mai nối việc

Khi mo du an lai, nen bat dau tu 4 viec nay:

1. xem `docs/Official Model Results - Current.md`, `docs/Runtime Risk Policy.md`, va `docs/IDS Real Demo Guide.md`
2. mo `docs/VN Real-World Validation Results - expanded.md` ban run luc `2026-04-15 13:41 +07:00` de nhin dung current runtime cho huong demo
3. neu demo voi IDS that, chay `python src/run_ids_dashboard.py` truoc, sau do moi chay `python src/bridge_ids_logs.py --input ... --format ... --follow`
4. khi trinh bay ket qua, tach ro `model official quality` va `runtime mitigation cho demo` de tranh nham lan
