import base64
import json
from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, asc, or_, and_

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    total = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "status": self.status,
            "total": self.total
        }

def encode_cursor(sort_val, last_id):
    """Mã hóa giá trị sort và id thành chuỗi base64 an toàn."""
    cursor_data = json.dumps([sort_val, last_id])
    return base64.urlsafe_b64encode(cursor_data.encode('utf-8')).decode('utf-8')

def decode_cursor(cursor_str):
    """Giải mã cursor. Ném lỗi ValueError nếu cursor không hợp lệ."""
    try:
        decoded_bytes = base64.urlsafe_b64decode(cursor_str.encode('utf-8'))
        return json.loads(decoded_bytes.decode('utf-8'))
    except Exception:
        raise ValueError("Invalid cursor")

@app.route('/orders', methods=['GET'])
def get_orders():
    query = Order.query

    status = request.args.get('status')
    customer_id = request.args.get('customer_id', type=int)
    if status:
        query = query.filter(Order.status == status)
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)

    sort_param = request.args.get('sort', '-id')
    is_desc = sort_param.startswith('-')
    sort_field_name = sort_param.lstrip('-')
    
    sort_column = getattr(Order, sort_field_name, Order.id)

    cursor_str = request.args.get('cursor')
    if cursor_str:
        try:
            cursor_val, cursor_id = decode_cursor(cursor_str)
        except ValueError:
            return jsonify({"error": "Bad Request", "message": "Cursor không hợp lệ"}), 400
        
        if is_desc:
            query = query.filter(
                or_(
                    sort_column < cursor_val,
                    and_(sort_column == cursor_val, Order.id < cursor_id)
                )
            )
        else:
            query = query.filter(
                or_(
                    sort_column > cursor_val,
                    and_(sort_column == cursor_val, Order.id > cursor_id)
                )
            )

    if is_desc:
        query = query.order_by(desc(sort_column), desc(Order.id))
    else:
        query = query.order_by(asc(sort_column), asc(Order.id))

    limit = request.args.get('limit', 10, type=int)
    results = query.limit(limit + 1).all()

    has_next = len(results) > limit
    items = results[:limit]

    next_cursor = None
    if has_next and items:
        last_item = items[-1]
        last_sort_val = getattr(last_item, sort_field_name)
        next_cursor = encode_cursor(last_sort_val, last_item.id)

    fields_param = request.args.get('fields')
    fields = fields_param.split(',') if fields_param else None

    formatted_items = []
    for item in items:
        item_dict = item.to_dict()
        if fields:
            item_dict = {k: v for k, v in item_dict.items() if k in fields}
        formatted_items.append(item_dict)

    return jsonify({
        "data": formatted_items,
        "next_cursor": next_cursor
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        db.session.add_all([
            Order(customer_id=1, status='paid', total=150.0),
            Order(customer_id=2, status='pending', total=200.5),
            Order(customer_id=1, status='paid', total=99.9),
            Order(customer_id=3, status='paid', total=300.0),
        ])
        db.session.commit()
    app.run(port=5000)