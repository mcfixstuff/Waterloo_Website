# Generated by Django 5.1.6 on 2025-03-01 21:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("admin_panel", "0003_user_signature_image"),
    ]

    operations = [
        migrations.CreateModel(
            name="FERPAForm",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("student_name", models.CharField(max_length=255)),
                ("university_division", models.CharField(max_length=50)),
                ("peoplesoft_id", models.CharField(max_length=20)),
                ("offices", models.JSONField(default=list)),
                ("info_categories", models.JSONField(default=list)),
                ("release_to", models.CharField(max_length=255)),
                (
                    "additional_individuals",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("purposes", models.JSONField(default=list)),
                ("password", models.CharField(max_length=10)),
                ("form_date", models.DateField()),
                (
                    "other_office_text",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "other_info_text",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "other_purpose_text",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("pending", "Pending Approval"),
                            ("approved", "Approved"),
                            ("returned", "Returned for Revision"),
                        ],
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("review_comments", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "reviewer",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reviewed_ferpa_forms",
                        to="admin_panel.user",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ferpa_forms",
                        to="admin_panel.user",
                    ),
                ),
            ],
        ),
    ]
