# THÔNG TIN ĐỀ TÀI ĐỒ ÁN CƠ SỞ

Tên đề tài (ghi IN HOA)  
XÂY DỰNG HỆ THỐNG PHÁT HIỆN WEBSITE LỪA ĐẢO (PHISHING) DỰA TRÊN URL

Sinh viên thực hiện:

- Họ tên: Kim Ngọc Hoàng
- MSSV: 2380600714
- Họ tên: Lê Anh Huy
- MSSV: 2380600820

# BÁO CÁO TIẾN ĐỘ

Nội dung

## 1.1 Mục tiêu

- Đánh giá lại đúng trạng thái `official current` của hệ thống trên bộ `expanded validation` để xác định chính xác pain point thực chiến còn lại.
- Giảm `false positive` cho `URL Model` trên các URL hợp lệ nhưng có pattern dễ bị nhầm với phishing như `login`, `portal`, `mail`, `.aspx`, `tra-cuu`, `ReturnUrl`.
- Xử lý các `false negative` còn lại của `URL Model`, sau đó chốt lại cấu hình `official` mới cho phần suy luận runtime.
- Hoàn thiện hướng tích hợp IDS phục vụ demo thật, bao gồm `runtime risk policy`, `curated benign runtime patch` và cầu nối log từ `Suricata/Zeek` vào dashboard.

## 1.2 Công việc thực hiện

- Rerun toàn bộ `expanded validation` theo đúng `official runtime`, đồng thời bổ sung report lỗi theo `category`, `token pattern` và `decision mode`.
- Thực hiện `URL hard-negative mining`, thu thập thêm `81` benign URL hard-case rows để retrain và so sánh các candidate giảm false positive.
- Mở rộng bộ `URL feature` từ `55` lên `66`, bổ sung thêm `14` phishing URL hard-case rows để xử lý các mẫu phishing khó còn sót.
- Promote lại `URL official` mới và đồng bộ các artifact liên quan như `official_model_registry`, `run_summary`, dashboard và tài liệu.
- Tách `runtime risk policy` thành file riêng, hiệu chỉnh lại ngưỡng `low / medium / high` cho `domain` và `url`.
- Bổ sung `curated benign runtime patch` cho một số domain/URL hợp lệ phục vụ hướng demo IDS thật.
- Xây dựng `bridge_ids_logs.py` để đọc log `Suricata eve.json` và `Zeek JSON`, sau đó đẩy dữ liệu sang dashboard qua API ingest.
- Cập nhật dashboard để hiển thị thêm `sensor`, `event type`, `observed time`, `src -> dest flow` và `decision mode`.

## 1.3 Kết quả đạt được

- Sau khi rerun `expanded validation` theo đúng `official runtime`, nhóm xác định được vấn đề lớn nhất không còn là `Domain false negative` mà đã chuyển sang `URL false positive` trên các URL benign hợp lệ.
- Với `Phase 33`, nhóm đã bổ sung thêm `81` benign URL hard-negative rows cho bộ train. Kết quả trên bộ `expanded` cải thiện từ `78.72%` lên `81.91%`, đồng thời giảm `false positive` của benign expanded từ `19/46` xuống `15/46`.
- Với `Phase 34`, nhóm mở rộng `URL feature` từ `55` lên `66` và thêm `14` phishing URL hard-case rows. Kết quả là `URL Model` xử lý được các mẫu phishing khó như `brand-subdomain spoof` và `cloud-edge generic portal`, đưa `false negative` của phishing expanded về `0/48`.
- Với `Phase 35`, nhóm đã chốt `URL official` mới là `official_current_66f_ann_mlp_full_540k_plus_url_hard_negative_hostaware_phishing_targeted`, đồng bộ lại registry, artifact model, dashboard và tài liệu kỹ thuật.
- Ở trạng thái official hiện tại, `Domain Model` đang dùng `26` feature với `Test PR-AUC = 0.8469`, còn `URL Model` dùng `66` feature với `Test PR-AUC = 0.9995`. Quy mô dataset official hiện tại là `120,006` dòng cho Domain và `540,023` dòng cho URL.
- Với `Phase 36`, nhóm đã tách `runtime risk policy` thành file riêng và hiệu chỉnh lại ngưỡng cảnh báo. Cấu hình hiện tại là:
- `Domain`: `low >= 0.55`, `medium >= 0.90`, `high >= 0.95`
- `URL`: `low >= 0.45`, `medium >= 0.75`, `high >= 0.98`
- Với `Phase 37`, nhóm bổ sung `curated benign runtime patch` cho một số domain/URL hợp lệ để phục vụ hướng demo IDS thật. Khi rerun lại bộ `expanded`, runtime hiện tại đạt `94/94`, `0 false positive`, `0 false negative`. Tuy nhiên nhóm ghi rõ đây là `runtime mitigation for demo`, không phải một vòng retrain model mới.
- Với `Phase 38`, nhóm đã xây dựng cầu nối `IDS JSON log -> bridge -> dashboard`. Bridge hiện hỗ trợ:
- `Suricata`: `dns`, `tls`, `http`
- `Zeek`: `dns`, `http`, `ssl/tls`
- Dashboard hiện không chỉ hiển thị kết quả dự đoán mà còn cho thấy đầy đủ ngữ cảnh vận hành như `sensor`, `event type`, `observed time`, `flow nguồn -> đích` và `decision mode`.

## 1.4 Khó khăn gặp phải

- Nhiều URL benign chính thống vẫn mang lexical pattern rất giống phishing, đặc biệt ở các nhóm `government`, `banking`, `university_portal`, nên việc giảm false positive không thể xử lý bằng một vòng train đơn lẻ.
- Trong quá trình tối ưu `URL Model`, mỗi lần giảm `false positive` đều có nguy cơ làm tăng `false negative`, vì vậy nhóm phải chia nhỏ thành nhiều phase để kiểm soát trade-off.
- Kết quả runtime sau khi thêm `curated benign patch` rất phù hợp cho demo, nhưng cần trình bày rõ để tránh nhầm lẫn giữa chất lượng `model official` và phần `runtime mitigation`.
- Hướng demo IDS thật trước đây mới dừng ở mức dashboard/API nội bộ, nên khi mở rộng sang `Suricata/Zeek` nhóm phải bổ sung thêm parser, metadata mapping và bridge riêng.

## 1.5 Kế hoạch tiếp theo

- Đóng gói luồng demo thành bộ script chạy nhanh theo hướng `one-click demo` để thuận tiện cho buổi bảo vệ.
- Chuẩn bị `demo checklist`, dữ liệu replay mẫu, case benign/phishing tiêu biểu và các ảnh chụp màn hình dự phòng.
- Tiếp tục rà soát curated runtime patch để giữ phạm vi hẹp, minh bạch và đúng mục tiêu demo IDS.
- Nếu tiếp tục mở rộng kỹ thuật, nhóm sẽ ưu tiên đánh giá trên log/traffic thật và giảm dần mức phụ thuộc vào patch runtime.
