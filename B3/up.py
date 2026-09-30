from flask import Flask, request, jsonify

app = Flask(__name__)
posts_db = []
post_id_counter = 1

@app.route('/api/v1/posts', methods=['GET'])
def get_posts():
    return jsonify({
        "status": "success",
        "data": posts_db,
        "total": len(posts_db)
    }), 200

@app.route('/api/v1/posts', methods=['POST'])
def create_post():
    global post_id_counter
    data = request.get_json()
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({"error": "Thiếu title hoặc content"}), 400
        
    new_post = {
        "id": post_id_counter,
        "title": data.get('title'),
        "content": data.get('content'),
        "author_id": data.get('author_id')
    }
    posts_db.append(new_post)
    post_id_counter += 1
    return jsonify(new_post), 201

if __name__ == '__main__':
    app.run(debug=True, port=5000)