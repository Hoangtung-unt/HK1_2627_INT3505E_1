## week4
## 1. Xác định resources trong miền
- **Người dùng:** `users` (thông tin hồ sơ/profile sẽ được gộp chung vào tài nguyên này).
- **Bài viết:** `posts`
- **Bình luận:** `comments`
- **Thẻ phân loại:** `tags`
- **Đăng ký theo dõi (Follow):** Thể hiện mối quan hệ giữa các users,  `followers` (người theo dõi) và `following` (người đang theo dõi).
- ## 2. Phân loại Collection / Item / Sub-resource
### Users
- **Collection:** 
  - `GET /users` 
  - `POST /users` 
- **Item:** 
  - `GET /users/{id}` 
  - `PATCH /users/{id}` 
- **Sub-resource:** 
  - `GET /users/{id}/posts` 
  - `GET /users/{id}/followers`
  - `GET /users/{id}/following` 
  - `POST /users/{id}/following` 

### Posts
- **Collection:** 
  - `GET /posts`
  - `POST /posts` 
- **Item:** 
  - `GET /posts/{id}`
  - `PATCH /posts/{id}` 
  - `DELETE /posts/{id}`
- **Sub-resource:** 
  - `GET /posts/{id}/comments` 
  - `POST /posts/{id}/comments`
  - `GET /posts/{id}/tags` 
  - `POST /posts/{id}/tags` 

### Comments
- **Item:** 
  - `PATCH /comments/{id}` 
  - `DELETE /comments/{id}` 
### Tags
- **Collection:**
  - `GET /tags` 
- **Sub-resource:**
  - `GET /tags/{id}/posts`
## 3. Sơ đồ cây endpoint và Version segment
- **Version segment:** Sử dụng `/api/v1` 
**Sơ đồ cây (Endpoint Tree):**
```text
/api/v1
│
├── /users
│   ├── /{id}
│   │   ├── /posts
│   │   ├── /followers
│   │   └── /following
│
├── /posts
│   ├── /{id}
│   │   ├── /comments
│   │   └── /tags
│
├── /comments
│   └── /{id}
│
└── /tags
    └── /{id}
        └── /posts
