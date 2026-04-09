from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models


ROLE_EMPLOYEE = "Employee"
ROLE_APPROVER = "Approver"
ROLE_HR = "HR"
ROLE_NAMES = (ROLE_EMPLOYEE, ROLE_APPROVER, ROLE_HR)


class User(AbstractUser):
    business_unit = models.CharField(max_length=120, blank=True)
    weekly_contracted_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("37.50"))
    approver = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="direct_reports",
    )

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return self.get_full_name() or self.username

    def has_role(self, role_name):
        return self.groups.filter(name=role_name).exists()

    @property
    def is_employee_role(self):
        return self.has_role(ROLE_EMPLOYEE)

    @property
    def is_approver_role(self):
        return self.has_role(ROLE_APPROVER)

    @property
    def is_hr_role(self):
        return self.has_role(ROLE_HR)

    @property
    def role_names(self):
        return list(self.groups.filter(name__in=ROLE_NAMES).values_list("name", flat=True))

    @property
    def assigned_activity_codes(self):
        from apps.activities.models import ActivityCode

        return ActivityCode.objects.filter(user_assignments__user=self).distinct().order_by("code")
