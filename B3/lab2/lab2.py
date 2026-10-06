import logging
import uuid
from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException

app = Flask(__name__)

class ProblemError(Exception):
    def __init__(self, status, title, detail=None, type_path=None, **extra):
        super().__init__()
        self.status = status
        self.title = title
        self.detail = detail
        self.type_path = type_path
        self.extra = extra

def create_problem_response(status, title, detail=None, type_path=None, **extra):
    body = {
        "type": f"https://api.example.com/probs/{type_path}" if type_path else "about:blank",
        "title": title,
        "status": status,
        "instance": request.path,
        "trace_id": str(uuid.uuid4())
    }
    
    if detail:
        body["detail"] = detail
        
    body.update(extra)

    response = jsonify(body)
    response.status_code = status
    response.headers['Content-Type'] = 'application/problem+json'
    return response


@app.errorhandler(ProblemError)
def handle_problem_error(e):
    return create_problem_response(e.status, e.title, e.detail, e.type_path, **e.extra)

@app.errorhandler(HTTPException)
def handle_http_exception(e):
    return create_problem_response(
        status=e.code,
        title=e.name,
        detail=e.description
    )

@app.errorhandler(Exception)
def handle_unhandled_exception(e):
    logging.error("Unhandled Exception: %s", str(e), exc_info=True) 
    
    return create_problem_response(
        status=500,
        title="Internal Server Error",
        detail="An unexpected server error occurred."
    )

@app.route('/resources/<int:id>', methods=['GET'])
def get_resource(id):
    raise ProblemError(
        status=404,
        title="Resource Not Found",
        detail=f"Resource {id} does not exist.",
        type_path="resource-not-found",
        resource_id=id
    )

@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    if id == 9999: 
        raise ProblemError(
            status=404,
            title="User not found",
            type_path="user-not-found",
            resource_id=id
        )
    return jsonify({"id": id, "name": "John Doe"})

@app.route('/crash', methods=['GET'])
def trigger_crash():
    return str(1 / 0)

if __name__ == '__main__':
    app.run(debug=True)