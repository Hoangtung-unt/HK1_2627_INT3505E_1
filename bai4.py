from flask import Flask, jsonify, request

app = Flask(__name__)
danh_sach_sach = [
    {"book_id": "1", "ten_sach": "Lap trinh Python"},
    {"book_id": "2", "ten_sach": "Mang may tinh"},
    {"book_id": "3", "ten_sach": "Toan roi rac"},
    {"book_id": "4", "ten_sach": "Co so du lieu"}
]
def tim_sach_theo_id(ma_sach):
    for sach in danh_sach_sach:
        if sach["book_id"] == ma_sach:
            return sach
    return None
@app.route("/books/<book_id>", methods=["GET"])
def get_book(book_id):
    sach = tim_sach_theo_id(book_id)
    if not sach:
        return jsonify({"loi": "Khong tim thay sach"}), 404
    return jsonify(sach), 200
@app.route("/books", methods=["GET"])
def get_list_book():
    # Lấy limit từ URL và ép sang số nguyên (int)
    limit = request.args.get("limit", 20)
    limit = int(limit)
    tu_khoa = request.args.get("word", "")
    tu_khoa = tu_khoa.strip().lower()
    ket_qua = []
    for sach in danh_sach_sach:
        ten = sach["ten_sach"].strip().lower()
        if tu_khoa in ten:
            ket_qua.append(sach)
    ket_qua = ket_qua[:limit]
    
    return jsonify({"danh_sach": ket_qua}), 200

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)