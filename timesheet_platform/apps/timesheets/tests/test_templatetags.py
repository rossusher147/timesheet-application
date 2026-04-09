from decimal import Decimal
from types import SimpleNamespace

from apps.timesheets.templatetags.timesheet_extras import get_item, get_item_total
from testsupport.factories import BaseAppTestCase


class TimesheetTemplateTagTests(BaseAppTestCase):
    def test_get_item_returns_default_empty_list(self):
        self.assertEqual(get_item({}, "missing"), [])

    def test_get_item_total_sums_entry_durations(self):
        mapping = {
            "monday": [
                SimpleNamespace(duration=Decimal("3.75")),
                SimpleNamespace(duration=Decimal("3.75")),
            ]
        }

        self.assertEqual(get_item_total(mapping, "monday"), Decimal("7.50"))
