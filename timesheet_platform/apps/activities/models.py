from decimal import Decimal

from django.conf import settings
from django.db import models


class ActivityCode(models.Model):
    CATEGORY_PROJECT = "project"
    CATEGORY_INTERNAL = "internal"
    CATEGORY_BANK_HOLIDAY = "bank_holiday"
    CATEGORY_ANNUAL_LEAVE = "annual_leave"
    CATEGORY_SICK_LEAVE = "sick_leave"
    CATEGORY_OTHER = "other"

    CATEGORY_CHOICES = (
        (CATEGORY_PROJECT, "Project"),
        (CATEGORY_INTERNAL, "Internal"),
        (CATEGORY_BANK_HOLIDAY, "Bank holiday"),
        (CATEGORY_ANNUAL_LEAVE, "Annual leave"),
        (CATEGORY_SICK_LEAVE, "Sick leave"),
        (CATEGORY_OTHER, "Other"),
    )

    BILLING_INTERNAL = "internal"
    BILLING_BILLABLE = "billable"
    BILLING_NON_BILLABLE = "non_billable"

    BILLING_CHOICES = (
        (BILLING_INTERNAL, "Internal"),
        (BILLING_BILLABLE, "Billable"),
        (BILLING_NON_BILLABLE, "Non-billable"),
    )

    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES)
    billing_type_default = models.CharField(max_length=20, choices=BILLING_CHOICES, blank=True)
    fixed_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    default_duration = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_system_controlled_hours = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        if self.fixed_hours is None and self.is_system_controlled_hours:
            self.fixed_hours = Decimal("0.00")
        super().save(*args, **kwargs)


class UserActivityAssignment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="activity_assignments")
    activity_code = models.ForeignKey(ActivityCode, on_delete=models.CASCADE, related_name="user_assignments")
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="activity_assignments_made",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "activity_code"], name="unique_user_activity_assignment"),
        ]
        ordering = ["user", "activity_code"]

    def __str__(self):
        return f"{self.user} -> {self.activity_code}"
