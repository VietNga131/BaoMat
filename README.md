# BÀI THỰC HÀNH: TRIỂN KHAI WAF (WEB APPLICATION FIREWALL) TRÊN NGINX VỚI MODSECURITY & OWASP CRS

## 1. Giới thiệu bài thực hành
Bài thực hành nhằm mục tiêu dựng một "người gác cổng" (WAF - Web Application Firewall) sử dụng **Nginx + ModSecurity** kết hợp bộ luật nhận diện tấn công tiêu chuẩn **OWASP CRS (Core Rule Set)** đứng trước ứng dụng web mục tiêu có chủ đích chứa lỗ hổng **OWASP Juice Shop**.

### Kiến trúc hệ thống:
```
[Client / Attacker]
       |
       +----> Port 3000 --------> [OWASP Juice Shop Web] (Không qua WAF - trực tiếp)
       |
       +----> Port 8080 --------> [Nginx + ModSecurity WAF] ----(nếu hợp lệ)----> [OWASP Juice Shop Web]
                                             |
                                    (nếu phát hiện tấn công)
                                             v
                                      403 Forbidden
```

---

## 2. Giải thích cấu hình `docker-compose.yml`

```yaml
services:
  web:
    image: bkimminich/juice-shop
    ports: ["3000:3000"]
  waf:
    image: owasp/modsecurity-crs:nginx
    ports: ["8080:8080"]
    environment:
      BACKEND: http://web:3000
      MODSEC_RULE_ENGINE: "On"
      BLOCKING_PARANOIA: "1"
```

- **`web`**: Chạy container OWASP Juice Shop, ánh xạ cổng `3000` của host vào cổng `3000` của container.
- **`waf`**: Chạy Nginx tích hợp ModSecurity và bộ quy tắc OWASP CRS, ánh xạ cổng `8080` ra ngoài.
- **`BACKEND: http://web:3000`**: Định tuyến reverse proxy của Nginx WAF, khi request an toàn sẽ được chuyển tiếp tới service `web` ở cổng `3000`.
- **`MODSEC_RULE_ENGINE: "On"`**:
  - `On`: Bật chế độ chặn (Block) - nếu phát hiện vi phạm luật CRS, WAF lập tức ngắt kết nối và trả về mã lỗi `403 Forbidden`.
  - `DetectionOnly`: Chế độ chỉ ghi log giám sát, không chặn request.
- **`BLOCKING_PARANOIA: "1"`**: Mức độ nhạy (Paranoia Level) từ 1 đến 4.
  - Mức 1: Mức cơ bản, ít bị báo động nhầm (low false positive), chặn hầu hết các payload tấn công cơ bản.
  - Mức càng cao: Kiểm tra càng gắt gao nhưng dễ chặn nhầm các request bình thường.

---

## 3. Các bước triển khai & khởi động

Mở terminal (PowerShell hoặc CMD) tại thư mục `BaoMat`:

```powershell
cd "d:\Year 4\KTPM\Prac\BaoMat"
docker compose up -d
```

> **Lưu ý**: Lần đầu chạy, Docker sẽ tải 2 images `bkimminich/juice-shop` và `owasp/modsecurity-crs:nginx`. Quá trình tải có thể mất vài phút tùy tốc độ mạng.

Kiểm tra trạng thái các container:
```powershell
docker compose ps
```

---

## 4. Kịch bản kiểm thử & đánh giá kết quả

### Kịch bản 1: Tấn công SQL Injection khi KHÔNG có WAF
1. Mở trình duyệt truy cập thẳng cổng web Juice Shop:
   `http://localhost:3000/#/login`
2. Nhập thông tin đăng nhập:
   - **Email**: `' OR 1=1--`
   - **Mật khẩu**: `123456` (hoặc bất kỳ)
3. Nhấn **Log in**.
- **Kết quả mong đợi**: Đăng nhập thành công và được chuyển vào tài khoản `admin@juice-sh.op` (do câu lệnh SQL bị vô hiệu hóa mệnh đề điều kiện password bởi `' OR 1=1--`).

---

### Kịch bản 2: Tấn công SQL Injection khi CÓ WAF bảo vệ
1. Mở trình duyệt truy cập qua cổng của WAF:
   `http://localhost:8080/#/login`
2. Nhập thông tin đăng nhập y hệt như trên:
   - **Email**: `' OR 1=1--`
   - **Mật khẩu**: `123456`
3. Nhấn **Log in**.
- **Kết quả mong đợi**: Request bị WAF chặn đứng.
  - Trên giao diện web sẽ báo lỗi không đăng nhập được.
  - Mở DevTools (F12) -> tab **Network**, xem request gửi đến `/rest/user/login` sẽ thấy trả về HTTP status code **`403 Forbidden`**.

---

### Kịch bản 3: Đăng nhập bình thường (Request hợp lệ qua WAF)
1. Trên cổng WAF: `http://localhost:8080/#/login`
2. Nhập tài khoản và mật khẩu thật của admin:
   - **Email**: `admin@juice-sh.op`
   - **Mật khẩu**: `admin123`
3. Nhấn **Log in**.
- **Kết quả mong đợi**: Đăng nhập thành công vào trang quản trị bình thường. WAF nhận diện đây là traffic sạch nên cho phép đi qua reverse proxy tới backend.

---

### Kịch bản 4: Xem log của WAF để kiểm chứng luật chặn
Để kiểm tra xem ModSecurity đã kích hoạt luật nào khi phát hiện hành vi tấn công, chạy lệnh:

```powershell
docker compose logs waf
```

Hoặc lọc riêng các dòng cảnh báo:
```powershell
docker compose logs waf | Select-String "942100"
```

- **Kết quả mong đợi**:
  - Bạn sẽ thấy log cảnh báo có mã luật **`id "942100"`** (Rule thuộc nhóm SQL Injection Protection của OWASP CRS):
    ```text
    [msg "SQL Injection Attack Detected via libinjection"] [data "Matched Data: 1=1-- found within ARGS:email..."] [id "942100"]
    ModSecurity: Access denied with code 403 (phase 2)...
    ```

---

## 5. Dừng hệ thống khi kết thúc bài thực hành

Sau khi hoàn thành thực hành, bạn có thể dừng các container bằng lệnh:
```powershell
docker compose down
```
