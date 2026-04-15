# Việc cần làm để chỉnh lại giao diện theo hướng tối giản, dịu mắt, có animation

## Mục tiêu tổng thể

- Biến trang từ kiểu dashboard kỹ thuật thành một tool check nhanh, hiện đại, dễ nhìn
- Tập trung vào 1 thao tác chính: nhập domain hoặc URL để kiểm tra
- Giảm tối đa thông tin phụ, mô tả dài và các khối gây nhiễu
- Bổ sung animation nhẹ để giao diện có cảm giác mượt và cao cấp hơn

---

## 1. Chỉnh typography cho dịu mắt hơn

### Việc cần làm

- Đổi font heading sang một font mềm hơn:
  - Manrope
  - Plus Jakarta Sans
  - Be Vietnam Pro
- Đổi font body sang font dễ đọc:
  - Inter
  - Be Vietnam Pro
- Giảm mật độ chữ đậm trên toàn trang
- Chỉ dùng font-weight:
  - 700 cho title chính
  - 600 cho heading nhỏ
  - 400 hoặc 500 cho body text
- Tăng line-height cho text mô tả và label
- Giảm cỡ chữ của badge, chip, text phụ

### Kết quả mong muốn

- Chữ nhìn mềm hơn, hiện đại hơn
- Bớt cảm giác cứng và nặng như dashboard admin
- Dễ đọc hơn khi nhìn lâu

---

## 2. Rút gọn header thật mạnh

### Việc cần làm

- Giữ lại một tiêu đề ngắn:
  - `Phishing Checker`
  - hoặc `Check domain or URL`
- Bỏ các đoạn mô tả dài giải thích chức năng
- Xóa các chip phụ như:
  - Check first
  - Result card ngay dưới form
- Thu nhỏ hoặc bỏ hẳn các block:
  - Latest event
  - Traffic mix
- Nếu cần giữ, chuyển chúng xuống dưới hoặc ẩn trong vùng phụ

### Kết quả mong muốn

- Phần trên cùng sạch, thoáng, nhìn vào là hiểu ngay đây là công cụ check
- Không bị phân tán sự chú ý trước khi nhập dữ liệu

---

## 3. Chỉ giữ một khối check chính ở trung tâm

### Việc cần làm

- Thiết kế lại layout theo kiểu centered tool
- Đặt khối check ở giữa trang, chiều rộng vừa phải
- Trong khối check chỉ giữ:
  - selector Domain / URL
  - ô input
  - nút `Kiểm tra`
- Bỏ bớt các nút phụ khỏi trạng thái mặc định:
  - Sample domain
  - Sample URL
  - Dùng lại lần trước
  - Xóa nhanh
- Nếu cần, chuyển các nút phụ vào menu nhỏ hoặc icon phụ
- Làm input lớn hơn, sạch hơn, dễ nhìn hơn
- Làm CTA button nổi rõ nhưng không quá gắt

### Kết quả mong muốn

- Người dùng tập trung vào đúng 1 thao tác chính
- Giao diện nhìn giống product/tool hơn là dashboard

---

## 4. Xóa phần giải thích chức năng trong UI

### Việc cần làm

- Bỏ các đoạn text kiểu hướng dẫn dài trong từng section
- Không giải thích cách dùng ngay trên giao diện
- Chỉ giữ label ngắn, rõ nghĩa
- Dùng placeholder tốt hơn để thay cho mô tả
- Nếu cần hỗ trợ, dùng tooltip nhỏ hoặc icon info rất gọn

### Ví dụ nên đổi

- Thay:
  - `Chọn loại input, dán giá trị cần kiểm tra và xem kết quả ngay bên dưới...`
- Bằng:
  - `Loại`
  - `Giá trị cần kiểm tra`

### Kết quả mong muốn

- Giao diện trông gọn, sang và đỡ giống tài liệu hướng dẫn
- Người dùng không bị ngợp bởi chữ

---

## 5. Thiết kế lại result card theo hướng tối giản

### Việc cần làm

- Sau khi check, chỉ hiện một result card lớn ngay dưới form
- Trong card chỉ giữ các thông tin quan trọng:
  - Kết quả: Phishing / Benign
  - Risk: High / Minimal / Low
  - Score
  - Input đã kiểm tra
- Ẩn khỏi màn hình chính các thông tin kỹ thuật như:
  - Model
  - Variant
  - Source
  - Signal count
  - Recommendation dài
- Nếu vẫn cần, chuyển các thông tin đó vào:
  - accordion `Chi tiết`
  - modal
  - drawer bên phải

### Kết quả mong muốn

- Người dùng nhìn phát hiểu ngay kết quả
- Không bị chìm trong thông tin kỹ thuật

---

## 6. Làm ít box hơn, ít card con hơn

### Việc cần làm

- Bỏ kiểu mỗi field nằm trong một card nhỏ riêng
- Giảm số lớp card lồng nhau
- Trong result card, hiển thị dữ liệu theo layout gọn:
  - 2 cột
  - hoặc 1 khối chính + 1 hàng metadata nhỏ
- Giảm số lượng pill/badge lặp lại
- Chỉ giữ badge cho trạng thái quan trọng:
  - verdict
  - risk

### Kết quả mong muốn

- Giao diện bớt vụn
- Mắt di chuyển tự nhiên hơn
- Trông cao cấp hơn

---

## 7. Làm lại màu sắc theo hướng nhẹ và cao cấp hơn

### Việc cần làm

- Giảm số màu nổi xuất hiện cùng lúc
- Chọn 1 màu nhấn chính cho toàn trang
- Dùng nền sáng dịu:
  - trắng ngà
  - xám rất nhạt
- Dùng text màu slate hoặc gray đậm thay vì đen gắt
- Dùng màu risk kiểu muted:
  - đỏ dịu cho High
  - xanh/olive dịu cho Minimal hoặc Benign
- Giảm độ chói của nút chính
- Giảm màu xanh ngọc xuất hiện quá nhiều ở badge/chip

### Kết quả mong muốn

- Giao diện mềm hơn, bớt “gắt”
- Nhìn hiện đại và đỡ rối hơn

---

## 8. Ẩn bớt phần Recent Logs trên trang chính

### Việc cần làm

- Đổi tên `Recent IDS Events` thành `Recent checks`
- Trên trang chính chỉ hiển thị 3 đến 5 dòng gần nhất
- Chỉ giữ các cột thật cần thiết:
  - Time
  - Type
  - Input
  - Risk
  - Result
- Chuyển chi tiết thành:
  - expandable row
  - drawer
  - hoặc trang riêng
- Thêm nút `View all`
- Không để bảng dài chiếm nhiều chiều cao màn hình

### Kết quả mong muốn

- Log vẫn có nhưng không chiếm spotlight
- Trang chính vẫn tập trung vào chức năng check

---

## 9. Ẩn hoặc chuyển toàn bộ analytics và model info xuống dưới

### Việc cần làm

- Bỏ `Tổng quan`, `Official Models`, `Traffic mix`, `Latest event` khỏi vùng chính
- Chuyển các section đó thành:
  - tab phụ
  - accordion
  - vùng footer dashboard
- Không hiển thị mặc định khi người dùng mới vào trang
- Nếu cần analytics, chỉ giữ 1 đến 2 chỉ số nhỏ

### Kết quả mong muốn

- Trang chính gọn
- Toàn bộ nội dung phụ không còn cạnh tranh với khối check

---

## 10. Thêm animation nhẹ, mượt, không phô

### Việc cần làm

- Thêm animation khi result card xuất hiện:
  - fade in
  - slide up nhẹ
- Thêm hover nhẹ cho button:
  - nâng lên 1 đến 2px
  - shadow mềm hơn
- Thêm hiệu ứng focus cho input:
  - border sáng hơn
  - glow nhẹ
- Thêm transition cho badge trạng thái
- Thêm hover mềm cho row trong bảng recent checks
- Thêm skeleton hoặc loading state mượt khi đang check

### Rule animation nên dùng

- Duration hover/focus:
  - 160ms đến 220ms
- Duration card enter:
  - 240ms đến 320ms
- Easing:
  - ease-out
  - hoặc cubic-bezier mềm
- Không dùng animation quá mạnh:
  - không bounce mạnh
  - không zoom lớn
  - không nhiều thành phần chuyển động cùng lúc

### Kết quả mong muốn

- UI có cảm giác sống động nhưng vẫn tinh tế
- Tăng cảm giác “premium”

---

## 11. Chuẩn hóa spacing và độ thoáng

### Việc cần làm

- Giảm số section trên màn hình chính
- Tăng khoảng trắng giữa các khối chính
- Dùng padding đều cho card:
  - khoảng 20 đến 24px
- Tăng chiều cao input và button:
  - khoảng 52 đến 56px
- Dùng border-radius đồng nhất:
  - card 16 đến 20px
  - input/button 14 đến 16px
- Giảm viền đậm, ưu tiên border mỏng và shadow nhẹ

### Kết quả mong muốn

- Giao diện thở hơn
- Có nhịp thị giác tốt hơn
- Nhìn gọn và hiện đại hơn

---

## 12. Đề xuất cấu trúc mới cho trang

### Thứ tự hiển thị nên là

1. Header rất gọn
2. Check card chính
3. Result card
4. Recent checks mini list
5. Khu vực phụ ẩn hoặc tab riêng

### Không nên để ở đầu trang

- Analytics
- Model cards
- Traffic mix
- Latest event
- Explanation text dài

---

## 13. Việc ưu tiên làm trước

### Ưu tiên cao

- Đổi font toàn bộ giao diện
- Rút gọn header
- Bỏ toàn bộ text giải thích dài
- Thiết kế lại form check theo hướng centered
- Thiết kế lại result card tối giản
- Giảm số lượng card con và badge

### Ưu tiên trung bình

- Rút gọn recent checks
- Ẩn analytics và model info
- Làm lại màu sắc dịu hơn
- Chuẩn hóa spacing, radius, shadow

### Ưu tiên thấp

- Thêm quick actions
- Thêm animation nâng cao
- Tạo tab riêng cho analytics / models / logs

---

## 14. Definition of Done

- Trang nhìn giống một công cụ check nhanh, không còn giống dashboard kỹ thuật
- Font chữ mềm, dễ đọc, bớt đậm
- Màn hình đầu chỉ còn khối check và kết quả là trọng tâm
- Thông tin phụ được ẩn, thu gọn hoặc chuyển xuống dưới
- Không còn các đoạn text dài giải thích chức năng
- Animation xuất hiện vừa đủ, nhẹ và mượt
- Tổng thể giao diện sạch hơn, hiện đại hơn, dễ nhìn hơn
