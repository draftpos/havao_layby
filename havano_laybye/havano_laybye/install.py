import frappe

FIELDS = [
    {"fieldname":"custom_laybye_section",         "fieldtype":"Section Break","label":"Laybye Payment",             "insert_after":"terms","collapsible":1},
    {"fieldname":"custom_laybye_date",            "fieldtype":"Date",         "label":"Payment Date",               "insert_after":"custom_laybye_section","default":"Today"},
    {"fieldname":"custom_laybye_method",          "fieldtype":"Select",       "label":"Payment Method",             "insert_after":"custom_laybye_date","options":"Cash\nBank\nMobile Money","default":"Cash"},
    {"fieldname":"custom_laybye_account",         "fieldtype":"Link",         "label":"Account Paid To",            "insert_after":"custom_laybye_method","options":"Account"},
    {"fieldname":"custom_laybye_account_currency","fieldtype":"Data",         "label":"Account Currency",           "insert_after":"custom_laybye_account","read_only":1,"print_hide":1},
    {"fieldname":"custom_laybye_col1",            "fieldtype":"Column Break",                                       "insert_after":"custom_laybye_account_currency"},
    {"fieldname":"custom_laybye_exchange_rate",   "fieldtype":"Float",        "label":"Exchange Rate",              "insert_after":"custom_laybye_col1","default":"1"},
    {"fieldname":"custom_laybye_paid_amount",     "fieldtype":"Currency",     "label":"Paid Amount",                "insert_after":"custom_laybye_exchange_rate"},
    {"fieldname":"custom_laybye_received_amount", "fieldtype":"Currency",     "label":"Received Amount (Foreign)",  "insert_after":"custom_laybye_paid_amount","options":"custom_laybye_account_currency"},
    {"fieldname":"custom_laybye_remarks",         "fieldtype":"Small Text",   "label":"Remarks",                   "insert_after":"custom_laybye_received_amount"},
    {"fieldname":"custom_laybye_post_btn",        "fieldtype":"Button",       "label":"Post Payment Entry",         "insert_after":"custom_laybye_remarks"},
    {"fieldname":"custom_laybye_totals_section",  "fieldtype":"Section Break","label":"",                          "insert_after":"custom_laybye_post_btn"},
    {"fieldname":"custom_laybye_balance_display", "fieldtype":"HTML",         "label":"Balance Display",            "insert_after":"custom_laybye_totals_section"},
    {"fieldname":"custom_laybye_col2",            "fieldtype":"Column Break",                                       "insert_after":"custom_laybye_balance_display"},
    {"fieldname":"custom_laybye_total_paid",      "fieldtype":"Currency",     "label":"Total Paid",                 "insert_after":"custom_laybye_col2","read_only":1},
    {"fieldname":"custom_laybye_balance",         "fieldtype":"Currency",     "label":"Balance Due",                "insert_after":"custom_laybye_total_paid","read_only":1},
]

def after_install():
    from frappe.custom.doctype.custom_field.custom_field import create_custom_field
    for cf in FIELDS:
        if not frappe.db.exists("Custom Field", {"dt": "Sales Order", "fieldname": cf["fieldname"]}):
            create_custom_field("Sales Order", cf)
            print(f"Created {cf['fieldname']}")
        else:
            print(f"Skipped {cf['fieldname']} (exists)")
    frappe.db.commit()
    print("Done.")
