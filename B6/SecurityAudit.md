# Báo Cáo Kiểm Toán Bảo Mật (Security Audit) - Social Network API

Tài liệu này liệt kê 7 điểm có nguy cơ rò rỉ dữ liệu, thông tin xác thực hoặc bị vượt quyền trong quá trình thiết kế và triển khai 3 endpoint: `POST /auth/login`, `POST /auth/refresh` và `GET /posts/{id}`, kèm theo biện pháp khắc phục.

---

## 1. Lộ nội dung bài viết riêng tư qua lỗ hổng BOLA (OWASP API1:2023)
* **Điểm có thể lộ:** Tại endpoint `GET /posts/{id}`, nếu backend chỉ dừng lại ở bước xác thực JWT (`@jwt_required`) và kiểm tra scope (`posts:read`) mà quên kiểm tra mối quan hệ sở hữu giữa `current_user` và bài viết `{id}`, kẻ tấn công (User A) có thể thay đổi tuần tự tham số `{id}` trên URL (ví dụ: `/posts/1024`, `/posts/1025`) để đọc toàn bộ bài viết ở chế độ riêng tư (`private`) hoặc chỉ dành cho bạn bè (`friends`) của người dùng khác (User B).
* **Biện pháp khắc phục:**
  * Bắt buộc áp dụng lớp kiểm tra thứ 3 (Ownership / ABAC policy) tại mọi endpoint nhận ID đối tượng.
  * Truy vấn `author_id` và `visibility` của bài viết từ DB; từ chối với mã `403 Forbidden` (hoặc `404 Not Found` để chống dò sự tồn tại của ID) nếu `visibility == 'private'` và `str(post.author_id) != str(current_user.id)` (trừ trường hợp có role quản trị phù hợp).

## 2. Lộ thông tin nhạy cảm qua Response DTO và JWT Payload (OWASP API3:2023 & Rủi ro PII)
* **Điểm có thể lộ:**
  1. **Tại `GET /posts/{id}` (Excessive Data Exposure):** Nếu lập trình viên trả trực tiếp bản ghi từ cơ sở dữ liệu (echo raw DB row) hoặc serialize toàn bộ đối tượng `User` đính kèm bài viết, response JSON có thể làm lộ `password_hash`, `email` cá nhân, số điện thoại hoặc địa chỉ IP của tác giả bài viết.
  2. **Tại `POST /auth/login` & `/auth/refresh`:** Phần Payload của JWT (dạng JWS) chỉ được mã hóa Base64URL chứ không được mã hóa bảo mật (ai có token đều giải mã đọc được plaintext). Việc đưa thông tin định danh cá nhân nhạy cảm (PII), mật khẩu hoặc secret nội bộ vào claims sẽ làm lộ dữ liệu ngay lập tức.
* **Biện pháp khắc phục:**
  * Sử dụng Data Transfer Object (DTO / Schema whitelist) để chỉ định rõ các trường được phép trả về ở `GET /posts/{id}` (`id`, `author_id`, `author_display_name`, `content`, `visibility`, `created_at`).
  * Trong JWT Payload chỉ lưu định danh tối thiểu (`sub`, `roles`, `scopes`, `exp`, `iat`, `jti`), tuyệt đối không chứa PII hay secret.

## 3. Lộ danh sách tài khoản (User Enumeration) và lộ mật khẩu qua tấn công vét cạn tại `POST /auth/login` (OWASP API2:2023)
* **Điểm có thể lộ:**
  * **Qua thông báo lỗi:** Trả về lỗi phân biệt rõ `"Email không tồn tại"` và `"Sai mật khẩu"` giúp kẻ tấn công dò quét được danh sách email người dùng hợp lệ trong mạng xã hội.
  * **Qua thời gian phản hồi (Timing Attack):** Khi email không tồn tại trong DB, hàm login trả lỗi ngay lập tức (~2ms), trong khi nếu email tồn tại thì phải chạy hàm băm Argon2id/bcrypt (~200ms). Sự chênh lệch thời gian này làm lộ sự tồn tại của tài khoản.
  * **Thiếu Rate-Limit:** Kẻ tấn công dùng danh sách tài khoản bị lộ để thực hiện Credential Stuffing / Brute-force mật khẩu.
* **Biện pháp khắc phục:**
  * Luôn trả về một mã lỗi và thông điệp chung (`401 Unauthorized - invalid_credentials`) cho mọi trường hợp đăng nhập thất bại.
  * Nếu không tìm thấy email trong DB, vẫn thực hiện verify với một dummy hash cố định để cân bằng thời gian phản hồi.
  * Áp dụng Rate-Limiting theo IP và theo tài khoản tại `/auth/login`, trả về `429 Too Many Requests` khi vượt ngưỡng.

## 4. Đánh cắp JWT Token ở phía Client do lưu trữ không an toàn (XSS & Token Leakage)
* **Điểm có thể lộ:** Sau khi nhận cặp `access` và `refresh` token từ `POST /auth/login`, nếu ứng dụng Web SPA lưu trực tiếp các token này vào `localStorage` hoặc `sessionStorage`, bất kỳ lỗ hổng Cross-Site Scripting (XSS) nào trên trang hoặc từ thư viện bên thứ ba đều có thể chạy lệnh `localStorage.getItem('token')` để đánh cắp toàn bộ phiên đăng nhập của người dùng.
* **Biện pháp khắc phục:**
  * Đối với ứng dụng Web: Cân nhắc mô hình BFF (Backend-For-Frontend) hoặc lưu Refresh Token trong Cookie với các cờ bảo mật `HttpOnly`, `Secure`, và `SameSite=Strict/Lax` (kèm cơ chế chống CSRF), chỉ giữ Access Token ngắn hạn trong bộ nhớ RAM (in-memory state) của ứng dụng.

## 5. Rò rỉ và tái sử dụng Token đã đăng xuất do thiếu cơ chế Revocation & TTL quá dài
* **Điểm có thể lộ:** Vì JWT có tính chất stateless, nếu `access` token được cấu hình thời gian sống (`exp`) quá dài (hoặc không có `exp`), hoặc khi người dùng bấm Logout / phát hiện lộ token nhưng server không có cơ chế thu hồi, kẻ tấn công chiếm được Access Token hoặc Refresh Token vẫn có thể tiếp tục gọi `POST /auth/refresh` và `GET /posts/{id}` hợp lệ.
* **Biện pháp khắc phục:**
  * Thiết lập TTL ngắn cho Access Token (ví dụ: 15 phút / 900 giây) và TTL hợp lý cho Refresh Token (ví dụ: 30 ngày).
  * Gắn định danh duy nhất `jti` cho mỗi token. Triển khai cơ chế thu hồi (Revocation) bằng cách kiểm tra `jti` trong Redis Blocklist (`@jwt.token_in_blocklist_loader`) và áp dụng Refresh Token Rotation (mỗi lần gọi `/auth/refresh` sẽ vô hiệu hóa refresh token cũ và cấp cặp mới).

## 6. Giả mạo Token do lỗi cấu hình thuật toán ký JWT hoặc lộ khóa bí mật (Secret Key)
* **Điểm có thể lộ:**
  * **Hardcode / Commit Secret lên Git:** Lưu `JWT_SECRET_KEY` trực tiếp trong mã nguồn khiến khóa bị lộ trên kho lưu trữ Git, cho phép kẻ tấn công tự ký JWT với role `admin` và mọi scope.
  * **Lỗi thuật toán (`alg=none` hoặc Algorithm Confusion HS/RS):** Nếu server không giới hạn allowlist thuật toán, kẻ tấn công có thể đổi header thành `alg: "none"` để bỏ qua bước kiểm tra chữ ký, hoặc dùng Public Key của thuật toán bất đối xứng `RS256` làm khóa đối xứng HMAC cho `HS256` để đánh lừa server.
* **Biện pháp khắc phục:**
  * Cấp phát `JWT_SECRET_KEY` (ngẫu nhiên từ CSPRNG, độ dài $\ge 256$ bit cho HS256) thông qua biến môi trường hoặc Secret Manager; thiết lập kế hoạch xoay vòng khóa (rotate key) sử dụng header `kid`.
  * Cấu hình cứng danh sách thuật toán cho phép (allowlist, ví dụ chỉ nhận `["HS256"]` hoặc `["RS256"]`) và luôn xác minh đầy đủ các claims `exp`, `iss` (issuer), `aud` (audience).

## 7. Lộ mật khẩu người dùng và Token trong hệ thống Log hoặc khi lộ Database
* **Điểm có thể lộ:**
  * **Trong Server Log / Reverse Proxy:** Ghi log toàn bộ request body của `POST /auth/login` (lộ plaintext `password`) hoặc log toàn bộ request header `Authorization: Bearer ...` của `GET /posts/{id}` và `POST /auth/refresh` (lộ JWT đang còn hiệu lực cho những ai có quyền đọc log).
  * **Trong Database:** Lưu mật khẩu bằng các hàm băm nhanh không có salt (MD5, SHA-1, SHA-256) khiến toàn bộ mật khẩu bị giải mã bằng Rainbow Table hoặc GPU cracking nếu DB bị rò rỉ.
* **Biện pháp khắc phục:**
  * Cấu hình middleware/logger che (mask/redact) tuyệt đối các trường `password`, `access`, `refresh` và header `Authorization` trước khi ghi log; bắt buộc dùng HTTPS ở mọi môi trường để chống nghe lén trên đường truyền.
  * Sử dụng **Argon2id** (ví dụ: `memory_cost=65536`, `time_cost=3`, `parallelism=4`) hoặc **bcrypt** (cost $\ge 12$) có salt riêng biệt cho từng mật khẩu trước khi lưu vào DB.