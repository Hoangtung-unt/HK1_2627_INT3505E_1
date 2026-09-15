from flask import Flask, jsonify, request
app = Flask(__name__)
BOOKS = [
    {"id": 1, "title" : "book 1", "author": "author 1"},
    {"id": 2, "title" : "book 2", "author": "author 2"},
    {"id": 3, "title" : "book 3", "author": "author 3"},
    {"id": 4, "title" : "book 4", "author": "author 4"},
    {"id": 5, "title" : "book 5", "author": "author 5"},
    {"id": 6, "title" : "book 6", "author": "author 6"}
]
_next = len(BOOKS) + 1
def find(bid):
    for book in BOOKS:
        if book["id"] == bid:
            return book
    return None
@app.route("/books", methods = ["GET"])
def list_books():
    limit = int(request.args.get("limit", 20))
    if len(BOOKS) < limit:
        return jsonify({"error": "Limit exceeds the number of books"}), 400
    return jsonify(BOOKS[:limit]), 200
@app.route("/book/<int:bid>", methods = ["GET"])
def get_book(bid):
    book = find(bid)
    if not book:
        return jsonify({"error": "not found"}), 404
    return jsonify(book), 200
@app.route("/books", methods = ["POST"])
def create_book():
    global _next
    args = request.get_json(silent = True) or {}
    title = args.get("title")
    author = args.get("author")
    if not title or not author:
        return jsonify({"error": "need title + author"}), 400
    book = {"id": _next, "title": title, "author": author}
    BOOKS.append(book)
    _next += 1
    return jsonify(book), 201, {"Location":f"/book/{book['id']}"}
@app.route("/book/<int:bid>", methods = ["PUT", "DELETE"])
def modify_book(bid):
    book = find(bid)
    if not book:
        return jsonify({"error": "not found"}), 404
    if request.method == "PUT":
        book.update(request.get_json(silent = True) or {})
        return jsonify(book), 200
    BOOKS.remove(book)
    return "", 204
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)