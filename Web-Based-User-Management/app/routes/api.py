from flask import Blueprint, request, jsonify
from app.models import AcademicRequests, User
from app.extensions.db import db
from datetime import datetime

api = Blueprint("api", __name__)

# API to get all forms
@api.route("/api/forms", methods=["GET"])
def get_all_forms():
    forms = AcademicRequests.query.all()
    result = []
    for form in forms:
        result.append({
            "id": form.id,
            "email": form.email,
            "form_type": form.form_type,
            "data": form.data,
            "status": form.status,
            "created_at": form.created_at.strftime("%Y-%m-%d %H:%M:%S") if form.created_at else None
        })
    return jsonify({"forms": result}), 200

# API to get a specific form
@api.route("/api/forms/<int:form_id>", methods=["GET"])
def get_form(form_id):
    form = AcademicRequests.query.get(form_id)
    if not form:
        return jsonify({"error": "Form not found"}), 404
    
    result = {
        "id": form.id,
        "email": form.email,
        "form_type": form.form_type,
        "data": form.data,
        "status": form.status,
        "created_at": form.created_at.strftime("%Y-%m-%d %H:%M:%S") if form.created_at else None
    }
    return jsonify({"form": result}), 200

# API to submit a new form
@api.route("/api/forms", methods=["POST"])
def submit_form():
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    required_fields = ["email", "form_type", "form_data"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Create a new form request
    new_form = AcademicRequests(
        email=data["email"],
        form_type=data["form_type"],
        data=data["form_data"],
        status=data.get("status", "draft"),
        created_at=datetime.now()
    )
    
    # Add and commit to database
    db.session.add(new_form)
    db.session.commit()
    
    return jsonify({
        "message": "Form submitted successfully",
        "form_id": new_form.id
    }), 201

# API to update a form
@api.route("/api/forms/<int:form_id>", methods=["PUT", "PATCH"])
def update_form(form_id):
    form = AcademicRequests.query.get(form_id)
    if not form:
        return jsonify({"error": "Form not found"}), 404
    
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Update fields if provided
    if "email" in data:
        form.email = data["email"]
    if "form_type" in data:
        form.form_type = data["form_type"]
    if "form_data" in data:
        form.data = data["form_data"]
    if "status" in data:
        form.status = data["status"]
    
    db.session.commit()
    
    return jsonify({
        "message": "Form updated successfully",
        "form_id": form.id
    }), 200

# API to delete a form
@api.route("/api/forms/<int:form_id>", methods=["DELETE"])
def delete_form(form_id):
    form = AcademicRequests.query.get(form_id)
    if not form:
        return jsonify({"error": "Form not found"}), 404
    
    db.session.delete(form)
    db.session.commit()
    
    return jsonify({
        "message": "Form deleted successfully"
    }), 200

# API to get all users
@api.route("/api/users", methods=["GET"])
def get_all_users():
    users = User.query.all()
    result = []
    for user in users:
        result.append({
            "user_id": user.user_id,
            "email": user.email,
            "display_name": user.display_name,
            "role": user.role,
            "status": user.status
        })
    return jsonify({"users": result}), 200

# API to get a specific user
@api.route("/api/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    result = {
        "user_id": user.user_id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "status": user.status
    }
    return jsonify({"user": result}), 200

# API to create a new user
@api.route("/api/users", methods=["POST"])
def create_user():
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    required_fields = ["email", "display_name"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=data["email"]).first()
    if existing_user:
        return jsonify({"error": "User with this email already exists"}), 400
    
    # Create new user
    new_user = User(
        email=data["email"],
        display_name=data["display_name"],
        role=data.get("role", "User"),
        status=data.get("status", "active")
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        "message": "User created successfully",
        "user_id": new_user.user_id
    }), 201

# API to update a user
@api.route("/api/users/<int:user_id>", methods=["PUT", "PATCH"])
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Update fields if provided
    if "email" in data:
        user.email = data["email"]
    if "display_name" in data:
        user.display_name = data["display_name"]
    if "role" in data:
        user.role = data["role"]
    if "status" in data:
        user.status = data["status"]
    
    db.session.commit()
    
    return jsonify({
        "message": "User updated successfully",
        "user_id": user.user_id
    }), 200

# API to delete a user
@api.route("/api/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        "message": "User deleted successfully"
    }), 200