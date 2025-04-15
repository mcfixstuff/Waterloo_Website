from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from . import api_client
from django.contrib.auth import get_user_model


from admin_panel.models import User 




#latex 

import os
import tempfile
import subprocess
from django.http import FileResponse, HttpResponse
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import date as date_filter
from . import api_client


def new_special_circumstance_form(request):
    if "access_token" not in request.session:
        return redirect("login")

    email = request.session.get("user_email")
    if not email:
        return redirect("login")
    
    # Get the user object to access signature
    user = get_object_or_404(User, email=email)
        
    if request.method == 'POST':
        form_data = {
            'student_name': request.POST.get('student_name'),
            'student_id': request.POST.get('student_id'),
            'degree': request.POST.get('degree'),
            'graduation_date': request.POST.get('graduation_date'),
            'special_request_option': request.POST.get('special_request_option'),
            'other_option_detail': request.POST.get('other_option_detail', ''),
            'justification': request.POST.get('justification'),
            'date': request.POST.get('date')
        }
        
        # Check if user has a signature in the database
        if user.signature_image:
            # Use signature from database
            import base64
            
            # Get the signature file content
            signature_file = user.signature_image
            signature_file.open()
            file_content = signature_file.read()
            signature_file.close()
                
            # Convert to base64 for API
            signature_base64 = base64.b64encode(file_content).decode('utf-8')
            form_data["signature"] = signature_base64
        
        status = 'under_review' if 'submit' in request.POST else 'draft'
        
        result = api_client.submit_form(
            email=email,
            form_type=1,  # 1 for Special Circumstance
            form_data=form_data,
            status=status
        )
        
        if result:
            messages.success(request, "Form saved successfully")
            return redirect('Applications')
        else:
            messages.error(request, "Error saving form")
    
    # Pass user object to template for signature display
    return render(request, 'academic_forms/special_circumstance_form.html', {'user': user})

def new_course_drop_form(request):
    if "access_token" not in request.session:
        return redirect("login")

    email = request.session.get("user_email")
    if not email:
        return redirect("login")
    
    # Get the user object to access signature
    user = get_object_or_404(User, email=email)
        
    if request.method == 'POST':
        form_data = {
            'student_name': request.POST.get('student_name'),
            'student_id': request.POST.get('student_id'),
            'semester': request.POST.get('semester'),
            'year': request.POST.get('year'),
            'subject': request.POST.get('subject'),
            'catalog_number': request.POST.get('catalog_number'),
            'class_number': request.POST.get('class_number'),
            'date': request.POST.get('date')
        }
        
        # Check if user has a signature in the database
        if user.signature_image:
            # Use signature from database
            import base64
            
            # Get the signature file content
            signature_file = user.signature_image
            signature_file.open()
            file_content = signature_file.read()
            signature_file.close()
                
            # Convert to base64 for API
            signature_base64 = base64.b64encode(file_content).decode('utf-8')
            form_data["signature"] = signature_base64
        
        status = 'under_review' if 'submit' in request.POST else 'draft'
        
        result = api_client.submit_form(
            email=email,
            form_type=2,  # 2 for Course Drop
            form_data=form_data,
            status=status
        )
        
        if result:
            messages.success(request, "Form saved successfully")
            return redirect('Applications')
        else:
            messages.error(request, "Error saving form")
    
    # Pass user object to template for signature display
    return render(request, 'academic_forms/course_drop_form.html', {'user': user})

def edit_form(request, form_id):
    if "access_token" not in request.session:
        return redirect("login")
    
    email = request.session.get("user_email")
    if not email:
        return redirect("login")
    
    # Get the user object to access signature
    user = get_object_or_404(User, email=email)
        
    form = api_client.get_form(form_id)
    if not form:
        messages.error(request, "Form not found")
        return redirect('Applications')
    
    # Process form submission for update
    if request.method == "POST":
        # Determine form type and gather form data accordingly
        if form['form_type'] == 1:  # Special Circumstance
            form_data = {
                "student_name": request.POST.get("student_name"),
                "student_id": request.POST.get("student_id"),
                "degree": request.POST.get("degree"),
                "graduation_date": request.POST.get("graduation_date"),
                "special_request_option": request.POST.get("special_request_option"),
                "other_option_detail": request.POST.get("other_option_detail", ""),
                "justification": request.POST.get("justification"),
                "date": request.POST.get("date"),
            }
        elif form['form_type'] == 2:  # Course Drop
            form_data = {
                'student_name': request.POST.get('student_name'),
                'student_id': request.POST.get('student_id'),
                'semester': request.POST.get('semester'),
                'year': request.POST.get('year'),
                'subject': request.POST.get('subject'),
                'catalog_number': request.POST.get('catalog_number'),
                'class_number': request.POST.get('class_number'),
                'date': request.POST.get('date')
            }
        else:
            messages.error(request, "Unknown form type")
            return redirect('Applications')

        # For edit forms, prioritize preserving the original signature if it exists
        if "signature" in form.get('data', {}):
            form_data["signature"] = form['data']['signature']
        # If no signature in form or user wants to update with current signature
        elif user.signature_image and request.POST.get('use_existing_signature') == 'true':
            # Use signature from database
            import base64
            
            # Get the signature file content
            signature_file = user.signature_image
            signature_file.open()
            file_content = signature_file.read()
            signature_file.close()
                
            # Convert to base64 for API
            signature_base64 = base64.b64encode(file_content).decode('utf-8')
            form_data["signature"] = signature_base64

        # Check if "submit" or "save" button was pressed
        status = "under_review" if 'submit' in request.POST else "draft"

        # Update the form
        response = api_client.update_form(form_id, form_data=form_data, status=status)

        if response:
            messages.success(request, "Form updated successfully.")
        else:
            messages.error(request, "Failed to update the form.")

        return redirect("Applications")
    
    # Determine which template to use based on form type
    template = 'academic_forms/special_circumstance_form.html' if form['form_type'] == 1 else 'academic_forms/course_drop_form.html'
    return render(request, template, {'form': form, 'is_edit': True, 'user': user})



def delete_form(request, form_id):
    if "access_token" not in request.session:
        return redirect("login")
        
    result = api_client.delete_form(form_id)
    if result:
        messages.success(request, "Form deleted successfully")
    else:
        messages.error(request, "Error deleting form")
        
    return redirect('Applications')

def view_form(request, form_id):
    if "access_token" not in request.session:
        return redirect("login")
    
    # Get the form data from the API
    form = api_client.get_form(form_id)
    if not form:
        messages.error(request, "Form not found")
        return redirect('Applications')
    
    # Render the template with just the form data from API
    return render(request, 'academic_forms/view_form.html', {'form': form})



def approve_form(request, form_id):
    """Approve a form by updating its status to 'approved'"""
    if "access_token" not in request.session:
        return redirect("login")
    
    email = request.session.get("user_email")
    if not email:
        return redirect("login")
    
    # Update the form status to 'approved'
    result = api_client.update_form(form_id, status="approved")
    
    if result:
        messages.success(request, "Form approved successfully")
    else:
        messages.error(request, "Error approving form")
    
    # Redirect back to the applications list
    return redirect('ApplicationApprovals')

def return_form(request, form_id):
    """Return a form by updating its status to 'returned'"""
    if "access_token" not in request.session:
        return redirect("login")
    
    email = request.session.get("user_email")
    if not email:
        return redirect("login")
    
    # Update the form status to 'returned'
    result = api_client.update_form(form_id, status="rejected")
    
    if result:
        messages.success(request, "Form returned successfully")
    else:
        messages.error(request, "Error returning form")
    
    # Redirect back to the applications list
    return redirect('ApplicationApprovals')


def generate_form_pdf(request, form_id):
    """
    Generate a PDF for academic forms (Special Circumstance or Course Drop)
    
    Args:
        request: The HTTP request
        form_id: The ID of the form to generate a PDF for
        
    Returns:
        A FileResponse with the generated PDF or an error response
    """
    # Check authentication
    if "access_token" not in request.session:
        return redirect("login")

    # Get the form from the API
    form = api_client.get_form(form_id)
    if not form:
        return HttpResponse("Form not found", status=404)
    
    # Determine which template to use based on form type
    if form['form_type'] == 1:  # Special Circumstance
        template_filename = 'special_circumstance_template.tex'
        
        # Create context for special circumstance form
        context = {
            'student_name': form['data'].get('student_name', ''),
            'student_id': form['data'].get('student_id', ''),
            'degree': form['data'].get('degree', ''),
            'graduation_date': form['data'].get('graduation_date', ''),
            'special_request_option': form['data'].get('special_request_option', ''),
            'other_option_detail': form['data'].get('other_option_detail', ''),
            'justification': form['data'].get('justification', '').replace('\n', '\\\\'),  # LaTeX line breaks
            'form_date': form['data'].get('date', ''),
            'status': form.get('status', 'unknown'),
        }
        
    elif form['form_type'] == 2:  # Course Drop
        template_filename = 'course_drop_template.tex'
        
        # Create context for course drop form
        context = {
            'student_name': form['data'].get('student_name', ''),
            'student_id': form['data'].get('student_id', ''),
            'semester': form['data'].get('semester', ''),
            'year': form['data'].get('year', ''),
            'subject': form['data'].get('subject', ''),
            'catalog_number': form['data'].get('catalog_number', ''),
            'class_number': form['data'].get('class_number', ''),
            'form_date': form['data'].get('date', ''),
            'status': form.get('status', 'unknown'),
        }
    else:
        return HttpResponse("Unsupported form type", status=400)
    
    # Add status text and colors for the PDF
    if form.get('status') == 'draft':
        context['status_text'] = 'Draft'
        context['status_color'] = 'gray!30'
    elif form.get('status') == 'under_review':
        context['status_text'] = 'Pending Approval'
        context['status_color'] = 'yellow!30'
    elif form.get('status') == 'approved':
        context['status_text'] = 'Approved'
        context['status_color'] = 'green!30'
    elif form.get('status') == 'rejected':
        context['status_text'] = 'Returned for Revision'
        context['status_color'] = 'red!30'
    else:
        context['status_text'] = form.get('status', 'Unknown')
        context['status_color'] = 'blue!20'
    
    # Handle signature
    if form['data'].get('signature'):
        # Create a temporary file for the signature image
        signature_base64 = form['data'].get('signature')
        context['has_signature'] = True
    else:
        context['has_signature'] = False
    
    # Get the LaTeX template file
    tex_template_path = os.path.join(settings.LATEX_TEMPLATE_DIR, template_filename)
    if not os.path.exists(tex_template_path):
        return HttpResponse(f"Template not found: {template_filename}", status=404)

    # Read the LaTeX template
    with open(tex_template_path, "r", encoding="utf-8") as f:
        tex_template = f.read()

    # Replace all placeholders in the template
    for key, value in context.items():
        tex_template = tex_template.replace(f"<<{key}>>", str(value))
        tex_template = tex_template.replace(f"<< {key} >>", str(value))

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write the rendered LaTeX source to a file
        tex_file_path = os.path.join(tmpdir, "form.tex")
        with open(tex_file_path, "w", encoding="utf-8") as f:
            f.write(tex_template)

        # If there's a signature, decode and save it
        if context.get('has_signature'):
            import base64
            signature_data = base64.b64decode(signature_base64)
            signature_path = os.path.join(tmpdir, "signature.png")
            with open(signature_path, "wb") as f:
                f.write(signature_data)

        # Run pdflatex to compile the .tex file
        try:
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "form.tex"],
                cwd=tmpdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
        except subprocess.CalledProcessError as e:
            error_output = e.stderr.decode() + "\n" + e.stdout.decode()
            return HttpResponse(f"LaTeX compile error:\n\n{error_output}", status=500)

        pdf_path = os.path.join(tmpdir, "form.pdf")
        
        # Set a useful filename for the download
        form_type_name = "Special_Circumstance" if form['form_type'] == 1 else "Course_Drop"
        filename = f"{form_type_name}_Form_{form_id}.pdf"
        
        response = FileResponse(open(pdf_path, "rb"), content_type="application/pdf")
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
