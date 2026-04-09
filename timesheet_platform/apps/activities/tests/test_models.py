from decimal import Decimal

from apps.activities.models import ActivityCode
from testsupport.factories import BaseAppTestCase


class ActivityCodeModelTests(BaseAppTestCase):
    def test_system_controlled_activity_defaults_fixed_hours_to_zero(self):
        code = ActivityCode.objects.create(
            code="BANK_001",
            name="Bank Holiday",
            category=ActivityCode.CATEGORY_BANK_HOLIDAY,
            billing_type_default=ActivityCode.BILLING_NON_BILLABLE,
            is_system_controlled_hours=True,
        )

        self.assertEqual(code.fixed_hours, Decimal("0.00"))
