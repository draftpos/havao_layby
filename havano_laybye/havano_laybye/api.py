import frappe
from frappe.utils import flt, nowdate


@frappe.whitelist()
def get_account_info(account, transaction_date=None):
    company = frappe.defaults.get_global_default("company")
    company_currency = frappe.db.get_value("Company", company, "default_currency")
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


@frappe.whitelist()
def post_payment(sales_order, paid_amount, payment_method, account,
                 payment_date=None, exchange_rate=1, received_amount=None, remarks=None):
    paid_amount     = flt(paid_amount)
    exchange_rate   = flt(exchange_rate) or 1
    received_amount = flt(received_amount) if received_amount else paid_amount

    if paid_amount <= 0:
        frappe.throw("Paid amount must be greater than zero.")

    so = frappe.get_doc("Sales Order", sales_order)

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
        "posting_date":               payment_date or nowdate(),
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
        "reference_date":             payment_date or nowdate(),
        "remarks":                    remarks or f"Laybye payment for {sales_order}",
        "custom_sales_order":         sales_order,
    })
    pe.insert(ignore_permissions=True)
    pe.submit()

    current_paid = flt(frappe.db.get_value("Sales Order", sales_order, "custom_laybye_total_paid"))
    new_paid     = flt(current_paid + paid_amount, 2)
    new_balance  = flt(flt(so.grand_total) - new_paid, 2)

    frappe.db.set_value("Sales Order", sales_order, {
        "custom_laybye_total_paid": new_paid,
        "custom_laybye_balance":    new_balance,
    })
    frappe.db.commit()

    return {"pe_name": pe.name, "total_paid": new_paid, "balance": new_balance}
