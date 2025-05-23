# Generated by Django 5.1.6 on 2025-03-03 17:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("admin_panel", "0004_ferpaform"),
    ]

    operations = [
        migrations.CreateModel(
            name="TexasResidencyAffidavit",
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
                ("county_name", models.CharField(max_length=100)),
                ("appeared_name", models.CharField(max_length=255)),
                ("full_name", models.CharField(max_length=255)),
                ("age", models.PositiveIntegerField()),
                ("graduated_check", models.BooleanField(default=False)),
                ("resided_check", models.BooleanField(default=False)),
                ("permanent_resident_check", models.BooleanField(default=False)),
                ("college_name", models.CharField(max_length=255)),
                ("day_of_month", models.PositiveIntegerField()),
                ("month", models.CharField(max_length=20)),
                ("year", models.PositiveIntegerField()),
                ("student_id", models.CharField(max_length=50)),
                ("student_dob", models.DateField()),
                ("notary_day", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "notary_month",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                ("notary_year", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "notary_name",
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
                        related_name="reviewed_affidavits",
                        to="admin_panel.user",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="texas_residency_affidavits",
                        to="admin_panel.user",
                    ),
                ),
            ],
        ),
    ]
