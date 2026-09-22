from flask import Flask, jsonify, make_response, request

app = Flask(__name__)

BOOKS = [
    {"id": 1, "title": "Nhà Giả Kim", "author": "Paulo Coelho"},
    {"id": 2, "title": "Hoàng Tử Bé", "author": "Saint-Exupéry"},
    {"id": 3, "title": "Đắc Nhân Tâm", "author": "Dale Carnegie"},
    {"id": 4, "title": "1984", "author": "George Orwell"},
    {"id": 5, "title": "Sapiens: Lược Sử Loài Người", "author": "Yuval Noah Harari"},
    {"id": 6, "title": "Bố Già", "author": "Mario Puzo"},
    {"id": 7, "title": "Suối Nguồn", "author": "Ayn Rand"},
    {"id": 8, "title": "Tội Ác Và Hình Phạt", "author": "Fyodor Dostoevsky"},
    {"id": 9, "title": "Không Gia Đình", "author": "Hector Malot"},
    {"id": 10, "title": "Bắt Trẻ Đồng Xanh", "author": "J.D. Salinger"},
    {"id": 11, "title": "Trại Súc Vật", "author": "George Orwell"},
    {"id": 12, "title": "Mật Mã Da Vinci", "author": "Dan Brown"},
    {"id": 13, "title": "Hai Vạn Dặm Dưới Đáy Biển", "author": "Jules Verne"},
    {"id": 14, "title": "Đường Xưa Mây Trắng", "author": "Thích Nhất Hạnh"},
    {"id": 15, "title": "Tuổi Trẻ Đáng Giá Bao Nhiêu", "author": "Rosie Nguyễn"},
]

DEFAULT_SIZE, MAX_SIZE = 20, 100


@app.get("/books")
def list_books():
  try:
    page = int(request.args.get("page", 1))
    size = int(request.args.get("size", DEFAULT_SIZE))
  except ValueError:
    return jsonify(error="page and size must be int"), 400

  page = max(page, 1)
  size = max(min(size, MAX_SIZE), 1)

  flt = BOOKS
  
  # Đổi sang tìm kiếm gần đúng (in) thay vì so sánh tuyệt đối (==)
  a = request.args.get("author")
  if a:
    flt = [b for b in flt if a.lower() in b["author"].lower()]
    
  q = request.args.get("q")
  if q:
    flt = [b for b in flt if q.lower() in b["title"].lower()]

  total = len(flt)
  start = (page - 1) * size
  end = start + size
  items = flt[start:end]
  last = max((total + size - 1) // size, 1)

  def u(p):
    return f"/books?page={p}&size={size}"

  links = {
      "self": {"href": u(page)},
      "first": {"href": u(1)},
      "last": {"href": u(last)},
  }
  if page > 1:
    links["prev"] = {"href": u(page - 1)}
  if end < total:
    links["next"] = {"href": u(page + 1)}

  body = {
      "data": items,
      "pagination": {
          "page": page,
          "size": size,
          "total": total,
          "total_pages": last,
      },
      "_links": links,
  }

  resp = make_response(jsonify(body), 200)
  resp.headers["Cache-Control"] = "public, max-age=30"
  return resp


if __name__ == "__main__":
  app.run(host="127.0.0.1", port=5000, debug=True)