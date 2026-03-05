import frappe
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class SalesOrderLaybye(Document):
    def validate(self):
        _sync_laybye_totals(self)
    def on_cancel(self):
        _cancel_laybye_payment_entries(self)


def on_validate(doc, method=None):
    _sync_laybye_totals(doc)


def _sync_laybye_totals(so):
    if not hasattr(so, "custom_laybye_payments"):
        return
    total_paid = sum(flt(r.paid_amount) for r in (so.custom_laybye_payments or []))
    so.custom_laybye_total_paid = flt(total_paid, 2)
    so.custom_laybye_balance    = flt(flt(so.grand_total) - total_paid, 2)


def _cancel_laybye_payment_entries(so):
    if not hasattr(so, "custom_laybye_payments"):
        return
    for row in (so.custom_laybye_payments or []):
        pe_name = row.get("payment_entry")
        if pe_name and frappe.db.exists("Payment Entry", pe_name):
            pe = frappe.get_doc("Payment Entry", pe_name)
            if pe.docstatus == 1:
                pe.cancel()


@frappe.whitelist()
def post_laybye_payment(sales_order, row_name, paid_amount, payment_method,
                        account, exchange_rate=1, received_amount=None, remarks=None):
    paid_amount     = flt(paid_amount)
    exchange_rate   = flt(exchange_rate) or 1
    received_amount = flt(received_amount) if received_amount else paid_amount

    if paid_amount <= 0:
        frappe.throw("Paid amount must be greater than zero.")

    so  = frappe.get_doc("Sales Order", sales_order)
    row = next((r for r in so.custom_laybye_payments if r.name == row_name), None)
    if not row:
        frappe.throw(f"Row {row_name} not found on {sales_order}.")
    if row.payment_entry:
        frappe.throw(f"Row already has Payment Entry {row.payment_entry}. Cancel it first.")

    company          = frappe.defaults.get_global_default("company")
    company_currency = frappe.db.get_value("Company", company, "default_currency")
    receivable_acct  = frappe.db.get_value("Company", company, "default_receivable_account")
    acct_currency    = frappe.db.get_value("Account", account, "account_currency") or company_currency
    is_multi         = acct_currency != company_currency

    pe = frappe.get_doc({
        "doctype":                    "Payment Entry",
        "payment_type":               "Receive",
        "party_type":                 "Customer",
        "party":                      so.customer,
        "party_name":                 so.customer_name or so.customer,
        "company":                    company,
        "posting_date":               row.payment_date or nowdate(),
        "paid_from":                  receivable_acct,
        "paid_to":                    account,
        "paid_from_account_currency": company_currency,
        "paid_to_account_currency":   acct_currency,
        "source_exchange_rate":       exchange_rate,
        "target_exchange_rate":       exchange_rate,
        "paid_amount":                paid_amount,
        "received_amount":            received_amount if is_multi else paid_amount,
        "mode_of_payment":            payment_method or "Cash",
        "reference_no":               sales_order,
        "reference_date":             row.payment_date or nowdate(),
        "remarks":                    remarks or f"Laybye payment for {sales_order}",
        "custom_sales_order":         sales_order,
    })
    pe.insert(ignore_permissions=True)
    pe.submit()

    frappe.db.set_value("Laybye Payment Item", row_name, "payment_entry", pe.name, update_modified=False)

    so.reload()
    _sync_laybye_totals(so)
    so.save(ignore_permissions=True)

    frappe.msgprint(f"Payment Entry <b>{pe.name}</b> created.", alert=True)
    return pe.name


@frappe.whitelist()
def get_account_currency_and_rate(account, transaction_date=None):
    company_currency = frappe.db.get_value(
        "Company", frappe.defaults.get_global_default("company"), "default_currency"
    )
    acct_currency = frappe.db.get_value("Account", account, "account_currency") or company_currency
    if acct_currency == company_currency:
        return {"account_currency": acct_currency, "exchange_rate": 1}
    from erpnext.setup.utils import get_exchange_rate
    rate = get_exchange_rate(
        transaction_date=transaction_date or nowdate(),
        from_currency=acct_currency,
        to_currency=company_currency,
    ) or 1
    return {"account_currency": acct_currency, "exchange_rate": rate}
