from flask import Flash, jsonify,make_response,Request
app=Flash(__name__)
BOOKS = []
_next_id = 1
@app.get("/books")
def list_books():
    return jsonify({
        "data": BOOKS,
        "total": len(BOOKS)
    }), 200
@app.get("/books/<int:bid>")
def get_book(bid):
    book = next((b for b in BOOKS if b["id"] == bid), None)
    if not book:
        return jsonify(error="not found"), 404
    resp = make_response(jsonify(book))