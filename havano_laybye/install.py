import frappe

CUSTOM_FIELDS = [
    {"dt": "Sales Order", "fieldname": "custom_laybye_section",         "fieldtype": "Section Break", "label": "Laybye Payments",  "insert_after": "terms",                        "collapsible": 1},
    {"dt": "Sales Order", "fieldname": "custom_laybye_payments",        "fieldtype": "Table",         "label": "Laybye Payments",  "options": "Laybye Payment Item", "insert_after": "custom_laybye_section"},
    {"dt": "Sales Order", "fieldname": "custom_laybye_totals_section",  "fieldtype": "Section Break", "label": "",                 "insert_after": "custom_laybye_payments"},
    {"dt": "Sales Order", "fieldname": "custom_laybye_balance_display", "fieldtype": "HTML",          "label": "Balance Display",  "insert_after": "custom_laybye_totals_section"},
    {"dt": "Sales Order", "fieldname": "custom_laybye_col1",            "fieldtype": "Column Break",  "insert_after": "custom_laybye_balance_display"},
    {"dt": "Sales Order", "fieldname": "custom_laybye_total_paid",      "fieldtype": "Currency",      "label": "Total Paid",       "read_only": 1, "insert_after": "custom_laybye_col1"},
    {"dt": "Sales Order", "fieldname": "custom_laybye_balance",         "fieldtype": "Currency",      "label": "Balance Due",      "read_only": 1, "insert_after": "custom_laybye_total_paid"},
]

def after_install():
    _create_custom_fields()
    frappe.db.commit()
    print("Havano Laybye: custom fields installed.")

def _create_custom_fields():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_field
    for cf in CUSTOM_FIELDS:
        dt = cf.pop("dt")
        if frappe.db.exists("Custom Field", {"dt": dt, "fieldname": cf["fieldname"]}):
            cf["dt"] = dt
            continue
        create_custom_field(dt, cf)
        cf["dt"] = dt
        print(f"Created {cf['fieldname']} on {dt}")
