# 🎯 PROMPT TỐI ƯU UI – PHISHING CHECKER DASHBOARD

## 1. Mục tiêu

Thiết kế lại giao diện **Phishing Checker Dashboard** theo hướng:

* Tối giản (minimal)
* Tập trung vào dữ liệu chính
* Giảm chữ, tăng trực quan
* Phù hợp demo kỹ thuật (ML + IDS)

---

## 2. Nguyên tắc giữ nguyên

* **Giữ nguyên layout tổng thể**
* **Giữ nguyên màu sắc (dark theme gradient hiện tại)**
* **Không thay đổi cấu trúc trang chính (Dashboard / Kiểm tra / Báo cáo / Thống kê / Cài đặt)**

---

## 3. Nguyên tắc thay đổi (QUAN TRỌNG)

### 3.1 Giảm chữ tối đa

* ❌ XÓA:

  * toàn bộ đoạn mô tả dài
  * các block "Soft UI briefing"
  * text giải thích UX/UI

* ✔ GIỮ:

  * tiêu đề ngắn gọn
  * label cần thiết
  * dữ liệu chính

---

### 3.2 Chuẩn hóa ngôn ngữ

* ✔ Chuyển **100% sang tiếng Việt**
* Không dùng tiếng Anh lẫn lộn:

  * "Dashboard" → "Bảng điều khiển"
  * "Runtime ready" → "Đang hoạt động"
  * "Total checks" → "Tổng lượt kiểm tra"

---

### 3.3 Sidebar (menu trái)

Tối giản lại:

#### Hiện tại:

* quá nhiều chữ + mô tả

#### Sau khi sửa:

* chỉ giữ:

  * icon
  * tên ngắn

```text
🔍 Kiểm tra
📊 Thống kê
📄 Báo cáo
⚙️ Cài đặt
```

* ❌ Xóa mô tả phụ bên dưới
* ✔ thu gọn chiều rộng sidebar

---

### 3.4 Header

#### Thay đổi:

* ❌ Bỏ:

  * text dài
  * thông tin phụ

* ✔ Giữ:

  * tên hệ thống
  * trạng thái (dot xanh)

#### Dark/Light mode:

* 👉 chuyển sang **góc phải màn hình**
* dạng toggle icon (🌙 / ☀️)
* không đặt chung header block

---

## 4. Khu vực kiểm tra (core feature)

### 4.1 Giữ layout hiện tại

* Dropdown chọn loại:

  * Domain / URL
* Input
* Button "Kiểm tra"

👉 Layout OK → giữ nguyên

---

### 4.2 Tối giản text

* ❌ Xóa toàn bộ đoạn mô tả dài
* ✔ chỉ giữ:

```text
Loại kiểm tra
Giá trị
[ Kiểm tra ]
```

---

## 5. Thêm chức năng mới: REALTIME IDS LOG

### 5.1 Mục tiêu

* Hiển thị log realtime (giả lập từ IDS / Suricata)
* Trực quan hóa risk bằng biểu đồ

---

### 5.2 Thiết kế

#### Block mới:

```text
[ Realtime Log ]
```

### Thành phần:

#### (A) Biểu đồ risk (quan trọng nhất)

* dạng:

  * line chart hoặc bar chart
* trục:

  * X: thời gian
  * Y: mức độ risk

#### (B) Feed log realtime

* hiển thị:

  * domain/url
  * risk
  * timestamp

---

### 5.3 Flow

```text
Log → Model → Risk score → Chart → Lưu vào lịch sử
```

---

## 6. Lịch sử kiểm tra (History)

### 6.1 Thay đổi lớn

* ❌ Không hiển thị full table dài
* ✔ chỉ hiển thị:

👉 **10 dòng mới nhất**

---

### 6.2 UI đề xuất

```text
Lịch sử gần nhất

[ dòng 1 ]
[ dòng 2 ]
...
[ dòng 10 ]
```

* nếu > 10:

  * ✔ scroll bên trong card
  * ✔ hoặc nút "Xem thêm"

---

### 6.3 Cột giữ lại

* Thời gian
* Input (URL/domain)
* Risk
* Kết quả

👉 ❌ bỏ:

* mô tả dài
* text dư thừa

---

## 7. Thống kê (Analytics)

### Giữ:

* Pie chart phishing vs benign

### Tối giản:

* ❌ bỏ text dài giải thích
* ✔ chỉ giữ:

  * số lượng
  * tỷ lệ %

---

## 8. Cài đặt (Settings)

### Giữ:

* thông tin model

### Tối giản:

* ❌ bỏ mô tả dài
* ✔ chỉ giữ:

```text
Model Domain
- tên
- số feature
- độ chính xác

Model URL
- tương tự
```

---

## 9. Nguyên tắc thiết kế tổng thể

* Ưu tiên:

  * **data > text**
  * **visual > description**
* UI hướng:

  * dashboard kỹ thuật
  * không phải landing page

---

## 10. Kết quả mong muốn

Sau khi refactor:

* Giao diện:

  * gọn hơn ~40–60% text
* Tập trung:

  * input + output + biểu đồ
* Có thêm:

  * realtime IDS simulation
* Phù hợp:

  * demo ML + security system

---

## 11. Tóm tắt thay đổi chính

| Thành phần | Thay đổi                 |
| ---------- | ------------------------ |
| Sidebar    | Thu gọn, bỏ mô tả        |
| Header     | Dọn sạch, move dark mode |
| Check form | Giữ layout, bỏ text      |
| History    | Chỉ 10 dòng + scroll     |
| Realtime   | Thêm chart + log         |
| Language   | 100% tiếng Việt          |

---

**End of Prompt**
