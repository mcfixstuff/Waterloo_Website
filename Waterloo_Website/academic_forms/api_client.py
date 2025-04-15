import requests

API_BASE_URL = "http://localhost:7070/api"

def get_all_forms(email=None, status=None, form_type=None):
    """Fetch all forms with optional filtering"""
    response = requests.get(f"{API_BASE_URL}/forms")
    if response.status_code == 200:
        forms = response.json().get('forms', [])
        
        # Apply filtering in Python since the API doesn't support query parameters
        if email:
            forms = [form for form in forms if form.get('email') == email]
        if status:
            forms = [form for form in forms if form.get('status') == status]
        if form_type:
            forms = [form for form in forms if form.get('form_type') == int(form_type)]
            
        return forms
    return []

def get_all_non_draft_forms(email=None, form_type=None):
    """Fetch only forms with 'under_review' status."""
    response = requests.get(f"{API_BASE_URL}/forms")
    if response.status_code == 200:
        forms = response.json().get('forms', [])
        
        # Filter to only include forms with 'under_review' status
        filtered_forms = [
            form for form in forms
            if form.get('status') == 'under_review'
        ]
        
        # Apply additional filtering if provided
        if email:
            filtered_forms = [form for form in filtered_forms if form.get('email') == email]
        if form_type:
            filtered_forms = [form for form in filtered_forms if form.get('form_type') == int(form_type)]
        
        return filtered_forms
    return []

def get_form(form_id):
    """Get a specific form by ID"""
    response = requests.get(f"{API_BASE_URL}/forms/{form_id}")
    if response.status_code == 200:
        return response.json().get('form')
    return None

def submit_form(email, form_type, form_data, signature_file=None, status="draft"):
    """Submit a new form"""
    # Handle signature file if provided
    if signature_file:
        import base64
        file_content = signature_file.read()
        signature_base64 = base64.b64encode(file_content).decode('utf-8')
        form_data["signature"] = signature_base64
    
    payload = {
        "email": email,
        "form_type": form_type,
        "form_data": form_data,  # This should match the API's expected field name
        "status": status
    }
    
    response = requests.post(
        f"{API_BASE_URL}/forms",
        json=payload
    )
    
    if response.status_code == 201:
        return response.json()
    return None

def update_form(form_id, form_data=None, status=None):
    """Update an existing form"""
    payload = {}
    if form_data:
        payload['form_data'] = form_data  # This should match the API's expected field name
    if status:
        payload['status'] = status
        
    response = requests.put(
        f"{API_BASE_URL}/forms/{form_id}",
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()
    return None

def delete_form(form_id):
    """Delete a form"""
    response = requests.delete(f"{API_BASE_URL}/forms/{form_id}")
    if response.status_code == 200:
        return response.json()
    return None