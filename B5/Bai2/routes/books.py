from flask import Blueprint, request, jsonify
from sqlalchemy import select, func, tuple_
import base64
import json
from models import db, Book

bp = Blueprint("books", __name__, url_prefix="/api/v1/books")

SORT_MAPPING = {
    "id": Book.id,
    "price": Book.price_vnd,
    "title": Book.title,
    "created_at": Book.created_at
}

def parse_multi_sort(raw_sort):
    """
    Xử lý multi-key sort dạng: ?sort=-price,title hoặc ?sort=price,-created_at[cite: 23, 26]
    """
    if not raw_sort:
        return [Book.id.desc()], [("id", True)], "-id"
    
    cols = []
    sort_meta = []
    for s in raw_sort.split(","):
        desc = s.startswith("-")
        key = s.lstrip("-")
        if key not in SORT_MAPPING:
            return None, None, None
        col = SORT_MAPPING[key]
        cols.append(col.desc() if desc else col.asc())
        sort_meta.append((key, desc))
    
    if "id" not in [k for k, _ in sort_meta]:
        primary_desc = sort_meta[0][1]
        cols.append(Book.id.desc() if primary_desc else Book.id.asc())
        
    return cols, sort_meta, raw_sort

def encode_cursor(data):
    return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip("=")

def decode_cursor(token):
    if not token:
        return None
    pad = "=" * (-len(token) % 4)
    return json.loads(base64.urlsafe_b64decode(token + pad))

@bp.get("")
def list_books():
    strategy = request.args.get("strategy", "cursor") 
    genre = request.args.get("genre")
    sort_raw = request.args.get("sort", "-id")
    limit = min(request.args.get("limit", 20, type=int), 100)

    cols, sort_meta, normalized_sort = parse_multi_sort(sort_raw)
    if cols is None:
        return jsonify({"error": "bad_sort", "message": "Invalid sort column provided"}), 400

    q = select(Book).order_by(*cols)

    if genre:
        q = q.where(Book.genre == genre)

    if strategy == "offset":
        offset_val = request.args.get("offset", 0, type=int)
        
        count_stmt = select(func.count(Book.id))
        if genre:
            count_stmt = count_stmt.where(Book.genre == genre)
        total = db.session.scalar(count_stmt)

        rows = db.session.scalars(q.offset(offset_val).limit(limit)).all()
        
        return jsonify({
            "data": [b.to_dict() for b in rows],
            "pagination": {
                "strategy": "offset",
                "offset": offset_val,
                "limit": limit,
                "total": total,
                "has_next": offset_val + limit < total
            }
        })

    elif strategy == "cursor":
        cursor_raw = request.args.get("cursor")
        if cursor_raw:
            try:
                c_data = decode_cursor(cursor_raw)
                if c_data.get("sort") != normalized_sort:
                    return jsonify({"error": "cursor_mismatch", "message": "Sort criteria changed, cursor is invalid"}), 400
                
                last_val = c_data.get("v")
                last_id = c_data.get("i")
                
                if last_id is not None:
                    primary_key_name = sort_meta[0][0]
                    desc_flag = sort_meta[0][1]
                    p_col = SORT_MAPPING[primary_key_name]
                    
                    op = "<" if desc_flag else ">"
                    if primary_key_name == "id":
                        condition = (Book.id < last_id) if desc_flag else (Book.id > last_id)
                        q = q.where(condition)
                    else:

                        op_tuple = tuple_(p_col, Book.id).op(op)
                        q = q.where(op_tuple((last_val, last_id)))
            except Exception:
                return jsonify({"error": "invalid_cursor", "message": "Malformed cursor token"}), 400

        rows = db.session.scalars(q.limit(limit + 1)).all()
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        next_cursor = None
        if rows and has_more:
            last_item = rows[-1]
            primary_key_name = sort_meta[0][0]
            val_to_store = getattr(last_item, primary_key_name)
            if hasattr(val_to_store, "isoformat"):
                val_to_store = val_to_store.isoformat()
                
            next_cursor = encode_cursor({
                "sort": normalized_sort,
                "v": val_to_store,
                "i": last_item.id
            })

        return jsonify({
            "data": [b.to_dict() for b in rows],
            "pagination": {
                "strategy": "cursor",
                "next_cursor": next_cursor,
                "has_more": has_more,
                "limit": limit
            }
        })
    else:
        return jsonify({"error": "invalid_strategy", "message": "Strategy must be 'offset' or 'cursor'"}), 400