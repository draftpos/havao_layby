import frappe

def after_install():
    create_client_script()
    create_server_script()
    frappe.db.commit()


def create_client_script():
    if frappe.db.exists("Client Script", {"name": "Sales Order Receipt Download"}):
        return

    frappe.get_doc({
        "doctype": "Client Script",
        "name": "Sales Order Receipt Download",
        "dt": "Sales Order",
        "view": "Form",
        "enabled": 1,
        "module": "Havano Laybye",
        "script": r"""
frappe.ui.form.on("Sales Order", {
    on_submit(frm) {
        const doc = frm.doc;
        const itemList = (doc.items || []).map(item => ({
            ProductName: item.item_name || item.item_code,
            productid: item.item_code,
            Qty: item.qty,
            Price: item.rate,
            Amount: item.amount,
            tax_type: "VAT",
            tax_rate: "15.0",
            tax_amount: "0.0",
            remarks: item.item_name || item.item_code,
            "Item-custom_is_order_item_1": false,
            "Item-custom_is_order_item_2": false,
            "Item-custom_is_order_item_3": false,
            "Item-custom_is_order_item_4": false,
            "Item-custom_is_order_item_5": false,
            "Item-custom_is_order_item_6": false,
        }));

        const payload = {
            CompanyName: doc.company,
            CompanyEmail: "",
            CompanyAddressLine1: "",
            CompanyAddressLine2: "",
            Tel: "",
            City: "", State: "", postcode: "", contact: "",
            TIN: "", VATNo: "",
            "Order Number ": doc.name,
            KOT: doc.name.split("-").pop(),
            InvoiceDate: doc.transaction_date,
            CashierName: frappe.session.user,
            CustomerName: doc.customer_name,
            CustomerContact: doc.customer_name,
            CustomerTradeName: null,
            CustomerEmail: null,
            CustomerTIN: null,
            CustomerVAT: null,
            Customeraddress: null,
            itemlist: itemList,
            AmountTendered: String(doc.grand_total),
            Change: 0,
            Currency: doc.currency || "ZWL",
            Footer: "Thank you for your purchase!",
            MultiCurrencyDetails: [{ Key: doc.currency || "ZWL", Value: doc.grand_total }],
            ReceiptNo: null,
            CustomerRef: doc.po_no || "None",
            DiscAmt: String(doc.discount_amount || "0.0"),
            Subtotal: doc.net_total,
            GrandTotal: doc.grand_total,
            TaxType: "Standard VAT",
            PaymentMode: doc.custom_payment_mode || "Cash",
            ReceiptType: "default-receipt",
        };

        const blob = new Blob([JSON.stringify(payload)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${doc.name}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
});
"""
    }).insert(ignore_permissions=True)


def create_server_script():
    if frappe.db.exists("Server Script", {"name": "Sales Order Auto Payment Entry"}):
        return

    frappe.get_doc({
        "doctype": "Server Script",
        "name": "Sales Order Auto Payment Entry",
        "script_type": "DocType Event",
        "reference_doctype": "Sales Order",
        "doctype_event": "After Submit",
        "module": "Havano Laybye",
        "enabled": 1,
        "script": r"""
if not doc.custom_account_paid_to:
    frappe.throw("Please select an Account Paid To before submitting.")

if not doc.custom_amount_paid or doc.custom_amount_paid <= 0:
    frappe.throw("Please enter Amount Paid before submitting.")

company = doc.company
company_currency = frappe.db.get_value("Company", company, "default_currency")
receivable_account = frappe.db.get_value("Company", company, "default_receivable_account")

paid_to_account = doc.custom_account_paid_to
paid_to_currency = (
    doc.custom_account_currency
    or frappe.db.get_value("Account", paid_to_account, "account_currency")
    or company_currency
)

total_paid = doc.custom_amount_paid or 0
received_amount = (
    doc.custom_received_amount
    if paid_to_currency != company_currency
    else total_paid
)

references = [{
    "reference_doctype":  "Sales Order",
    "reference_name":     doc.name,
    "total_amount":       doc.grand_total or 0,
    "outstanding_amount": doc.grand_total or 0,
    "allocated_amount":   total_paid,
}]

pe = frappe.get_doc({
    "doctype":                    "Payment Entry",
    "payment_type":               "Receive",
    "party_type":                 "Customer",
    "party":                      doc.customer,
    "party_name":                 doc.customer,
    "company":                    company,
    "posting_date":               doc.transaction_date,
    "paid_from":                  receivable_account,
    "paid_to":                    paid_to_account,
    "paid_from_account_currency": company_currency,
    "paid_to_account_currency":   paid_to_currency,
    "source_exchange_rate":       doc.custom_exchange_rate or 1,
    "target_exchange_rate":       doc.custom_exchange_rate or 1,
    "paid_amount":                total_paid,
    "received_amount":            received_amount or total_paid,
    "mode_of_payment":            doc.custom_payment_method or "Cash",
    "reference_no":               doc.name,
    "reference_date":             doc.transaction_date,
    "remarks":                    "Payment via Sales Order " + doc.name,
    "references":                 references,
})

pe.insert(ignore_permissions=True)
pe.submit()

frappe.db.set_value("Sales Order", doc.name, "custom_payment_entry", pe.name)
frappe.msgprint("Payment Entry " + pe.name + " created successfully.", alert=True)
"""
    }).insert(ignore_permissions=True)
