"""Demo JSON files loaded by `load_demo_data` and the login-screen loader."""

from __future__ import annotations

import json

from django.apps import apps

CORE_DEMO_FIXTURES = (
    "user_data.json",
    "employee_info_data.json",
    "base_data.json",
    "work_info_data.json",
    "mail_log_data.json",
)

OPTIONAL_DEMO_FIXTURES = (
    ("attendance", "attendance_data.json"),
    ("leave", "leave_data.json"),
    ("asset", "asset_data.json"),
    ("recruitment", "recruitment_data.json"),
    ("onboarding", "onboarding_data.json"),
    ("offboarding", "offboarding_data.json"),
    ("pms", "pms_data.json"),
    ("pms", "pms_scenarios_data.json"),
    ("payroll", "payroll_scenarios_data.json"),
    ("payroll", "payroll_data.json"),
    ("payroll", "payroll_loanaccount_data.json"),
    ("project", "project_data.json"),
    ("project", "project_scenarios_data.json"),
    ("helpdesk", "helpdesk_scenarios_data.json"),
)

# Mail Automation / Tags UIs — existing JSON, previously side-loaded only.
# faq.json is skipped (invalid JSON); helpdesk expansion already seeds FAQs.
SIDE_DEMO_FIXTURES = (
    (None, "tags.json"),
    (None, "mail_templates.json"),
    ("horilla_automations", "mail_automations.json"),
)


def demo_fixture_files() -> list[str]:
    files = list(CORE_DEMO_FIXTURES)
    files += [f for app, f in OPTIONAL_DEMO_FIXTURES if apps.is_installed(app)]
    files += [
        f for app, f in SIDE_DEMO_FIXTURES if app is None or apps.is_installed(app)
    ]
    return files


def sanitize_demo_fixture_text(fixture_text: str) -> tuple[str, int]:
    """Remove fields retired from the current model schema.

    The packaged demo data is intentionally kept across product releases, so a
    fixture can occasionally outlive a model field.  Django's ``loaddata``
    aborts the entire file in that case; filtering only unknown fields retains
    the rest of the representative test data.
    """
    try:
        records = json.loads(fixture_text)
    except json.JSONDecodeError:
        return fixture_text, 0

    if not isinstance(records, list):
        return fixture_text, 0

    removed = 0
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("fields"), dict):
            continue

        try:
            model = apps.get_model(record["model"])
        except (KeyError, LookupError, ValueError):
            continue

        valid_names = set()
        for field in model._meta.get_fields():
            if field.auto_created and not field.concrete:
                continue
            valid_names.add(field.name)
            attname = getattr(field, "attname", None)
            if attname:
                valid_names.add(attname)

        fields = record["fields"]
        for name in tuple(fields):
            if name not in valid_names:
                fields.pop(name)
                removed += 1

    return json.dumps(records), removed
