from flask import Blueprint, render_template, request, session, redirect, url_for
from fpdf import FPDF
import os
from datetime import datetime

# Create a Flask Blueprint for the Approval System
approval_bp = Blueprint("approval", __name__, template_folder="../templates", static_folder="../static")

# Ensure directories exist
PDF_FOLDER = "app/static/pdfs/"
SIGNATURE_FOLDER = "app/static/signatures/"
if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)
if not os.path.exists(SIGNATURE_FOLDER):
    os.makedirs(SIGNATURE_FOLDER)

@approval_bp.route("/form_submit/thesis", methods=["GET", "POST"])
def form_submit_thesis():
    if request.method == "POST":
        first_name = session.get("first_name", "Unknown")
        middle_initial = session.get("middle_initial", "")
        last_name = session.get("last_name", "Unknown")
        uh_id = session.get("uh_id", "Unknown")
        student_email = session.get("student_email", "Unknown")
        degree = request.form["degree"]
        program = request.form["program"]
        defense_date = request.form["defense_date"]
        graduation_date = request.form["graduation_date"]
        thesis_title = request.form["thesis_title"]
        date = datetime.now().strftime("%Y-%m-%d")

        full_name = f"{first_name} {middle_initial} {last_name}".strip()

        # Handle signature upload
        signature_path = None
        if "signature" in request.files:
            signature = request.files["signature"]
            if signature.filename != "":
                signature_path = os.path.join(SIGNATURE_FOLDER, f"{uh_id}_signature.png")
                signature.save(signature_path)

        # Generate PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, "Written Thesis Approval Form", ln=True, align="C")
        pdf.ln(10)
        pdf.cell(200, 10, f"Student Name: {full_name}", ln=True)
        pdf.cell(200, 10, f"UH ID: {uh_id}", ln=True)
        pdf.cell(200, 10, f"Student Email: {student_email}", ln=True)
        pdf.cell(200, 10, f"Degree: {degree}", ln=True)
        pdf.cell(200, 10, f"Program: {program}", ln=True)
        pdf.cell(200, 10, f"Defense Date: {defense_date}", ln=True)
        pdf.cell(200, 10, f"Anticipated Graduation Date: {graduation_date}", ln=True)
        pdf.cell(200, 10, f"Thesis Title: {thesis_title}", ln=True)
        pdf.cell(200, 10, f"Submission Date: {date}", ln=True)

        # Add signature if uploaded
        if signature_path:
            pdf.image(signature_path, x=10, y=pdf.get_y() + 10, w=40, h=20)

        # Save PDF
        pdf_path = os.path.join(PDF_FOLDER, f"{uh_id}_thesis_approval.pdf")
        pdf.output(pdf_path)

        return f"Form submitted! <a href='/{pdf_path}'>Download PDF</a>"

    return render_template("form_submit_thesis.html")

@approval_bp.route("/form_submit/drop", methods=["GET", "POST"])
def form_submit_drop():
    return render_template("form_submit_drop.html")
