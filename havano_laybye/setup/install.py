import frappe

def after_install():
    create_custom_fields()
    create_payment_balance_client_script()
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


def create_custom_fields()
    create_payment_balance_client_script():
    fields = [
        {"dt": "Sales Order", "fieldname": "custom_payment_", "fieldtype": "Section Break", "label": "Payment Details", "insert_after": "taxes", "collapsible": 1},
        {"dt": "Sales Order", "fieldname": "custom_payment_entry", "fieldtype": "Link", "label": "Payment Entry", "options": "Payment Entry", "insert_after": "custom_payment_", "read_only": 1},
        {"dt": "Sales Order", "fieldname": "custom_account_paid_to", "fieldtype": "Link", "label": "Account Paid To", "options": "Account", "insert_after": "custom_payment_entry"},
        {"dt": "Sales Order", "fieldname": "custom_received_amount", "fieldtype": "Currency", "label": "Received Amount", "insert_after": "custom_account_paid_to"},
        {"dt": "Sales Order", "fieldname": "custom_payment_method", "fieldtype": "Select", "label": "Payment Method", "options": "Cash\nBank\nMobile Money", "insert_after": "custom_received_amount", "translatable": 1},
        {"dt": "Sales Order", "fieldname": "custom_column_break_qus6v", "fieldtype": "Column Break", "insert_after": "custom_payment_method"},
        {"dt": "Sales Order", "fieldname": "custom_balance_remaining", "fieldtype": "Currency", "label": "Balance Remaining", "insert_after": "custom_column_break_qus6v", "read_only": 1, "in_list_view": 1},
        {"dt": "Sales Order", "fieldname": "custom_account_currency", "fieldtype": "Data", "label": "Account Currency", "insert_after": "custom_balance_remaining", "read_only": 1, "print_hide": 1, "translatable": 1},
        {"dt": "Sales Order", "fieldname": "custom_amount_paid", "fieldtype": "Currency", "label": "Amount Paid", "insert_after": "custom_account_currency"},
        {"dt": "Sales Order", "fieldname": "custom_exchange_rate", "fieldtype": "Float", "label": "Exchange Rate", "insert_after": "custom_amount_paid", "default": "1"},
        {"dt": "Sales Order", "fieldname": "custom_column_break_9ds3v", "fieldtype": "Column Break", "insert_after": "packed_items"},
        {"dt": "Sales Order", "fieldname": "custom_column_break_lsrh0", "fieldtype": "Column Break", "insert_after": "custom_column_break_9ds3v"},
        {"dt": "Sales Order", "fieldname": "custom_payment_details", "fieldtype": "Currency", "label": "Payment Details", "insert_after": "custom_column_break_lsrh0"},
        {"dt": "Sales Order", "fieldname": "custom_column_break_xq6ey", "fieldtype": "Column Break", "insert_after": "custom_payment_details"},
        {"dt": "Sales Order", "fieldname": "custom_laybye_section", "fieldtype": "Section Break", "label": "Laybye Payments", "insert_after": "terms", "collapsible": 1},
        {"dt": "Sales Order", "fieldname": "custom_laybye_date", "fieldtype": "Date", "label": "Payment Date", "insert_after": "custom_laybye_section", "default": "Today"},
        {"dt": "Sales Order", "fieldname": "custom_laybye_method", "fieldtype": "Select", "label": "Payment Method", "options": "Cash\nBank\nMobile Money", "insert_after": "custom_laybye_date", "default": "Cash"},
        {"dt": "Sales Order", "fieldname": "custom_laybye_account", "fieldtype": "Link", "label": "Account Paid To", "options": "Account", "insert_after": "custom_laybye_method"},
        {"dt": "Sales Order", "fieldname": "custom_laybye_account_currency", "fieldtype": "Data", "label": "Account Currency", "insert_after": "custom_laybye_account", "read_only": 1, "print_hide": 1},
        {"dt": "Sales Order", "fieldname": "custom_laybye_payments", "fieldtype": "Table", "label": "Laybye Payments", "options": "Laybye Payment Item", "insert_after": "custom_laybye_account_currency"},
        {"dt": "Sales Order", "fieldname": "custom_laybye_totals_section", "fieldtype": "Section Break", "insert_after": "custom_laybye_payments"},
        {"dt": "Sales Order", "fieldname": "custom_laybye_balance_display", "fieldtype": "HTML", "label": "Balance Display", "insert_after": "custom_laybye_totals_section"},
        {"dt": "Sales Order", "fieldname": "custom_laybye_col2", "fieldtype": "Column Break", "insert_after": "custom_laybye_balance_display"},
        {"dt": "Sales Order", "fieldname": "custom_laybye_col1", "fieldtype": "Column Break", "insert_after": "custom_laybye_col2"},
        {"dt": "Sales Order", "fieldname": "custom_laybye_exchange_rate", "fieldtype": "Float", "label": "Exchange Rate", "insert_after": "custom_laybye_col1", "default": "1"},
        {"dt": "Sales Order", "fieldname": "custom_laybye_paid_amount", "fieldtype": "Currency", "label": "Paid Amount", "insert_after": "custom_laybye_exchange_rate"},
        {"dt": "Sales Order", "fieldname": "custom_laybye_received_amount", "fieldtype": "Currency", "label": "Received Amount (Foreign)", "options": "custom_laybye_account_currency", "insert_after": "custom_laybye_paid_amount"},
        {"dt": "Sales Order", "fieldname": "custom_laybye_remarks", "fieldtype": "Small Text", "label": "Remarks", "insert_after": "custom_laybye_received_amount"},
        {"dt": "Sales Order", "fieldname": "custom_laybye_post_btn", "fieldtype": "Button", "label": "Post Payment Entry", "insert_after": "custom_laybye_remarks"},
        {"dt": "Sales Order", "fieldname": "custom_laybye_total_paid", "fieldtype": "Currency", "label": "Total Paid", "insert_after": "custom_laybye_post_btn", "read_only": 1},
        {"dt": "Sales Order", "fieldname": "custom_laybye_balance", "fieldtype": "Currency", "label": "Balance Due", "insert_after": "custom_laybye_total_paid", "read_only": 1},
    ]

    for f in fields:
        if frappe.db.exists("Custom Field", {"dt": f["dt"], "fieldname": f["fieldname"]}):
            continue
        frappe.get_doc({
            "doctype": "Custom Field",
            **f
        }).insert(ignore_permissions=True)


def create_payment_balance_client_script():
    if frappe.db.exists("Client Script", {"name": "Sales Order Payment and Balance"}):
        return

    frappe.get_doc({
        "doctype": "Client Script",
        "name": "Sales Order Payment and Balance",
        "dt": "Sales Order",
        "view": "Form",
        "enabled": 1,
        "module": "Havano Laybye",
        "script": r"""
frappe.ui.form.on('Sales Order', {

    refresh: function(frm) {
        frm.trigger('set_account_query');
        if (frm.doc.custom_account_paid_to) {
            frm.trigger('custom_account_paid_to');
        } else {
            toggle_currency_fields(frm);
        }
        calculate_balance(frm);
    },

    custom_account_paid_to: function(frm) {
        if (!frm.doc.custom_account_paid_to) {
            frm.doc.custom_account_currency = '';
            frm.set_value('custom_exchange_rate', 1);
            toggle_currency_fields(frm);
            return;
        }
        frappe.db.get_value('Account', frm.doc.custom_account_paid_to, 'account_currency', function(r) {
            if (!r || !r.account_currency) return;
            let company_currency = frappe.boot.sysdefaults.currency;
            let acct_currency    = r.account_currency;

            frm.doc.custom_account_currency = acct_currency;
            frm.get_field('custom_account_currency') &&
                frm.get_field('custom_account_currency').set_input(acct_currency);
            frm.refresh_field('custom_account_currency');

            if (acct_currency !== company_currency) {
                frappe.call({
                    method: 'erpnext.setup.utils.get_exchange_rate',
                    args: {
                        transaction_date: frm.doc.transaction_date || frappe.datetime.get_today(),
                        from_currency:    acct_currency,
                        to_currency:      company_currency,
                        args:             'for_buying'
                    },
                    callback: function(res) {
                        frm.set_value('custom_exchange_rate', res.message || 1);
                        if (!res.message) frappe.msgprint(__('No exchange rate found. Please enter manually.'));
                        toggle_currency_fields(frm);
                    }
                });
            } else {
                frm.set_value('custom_exchange_rate', 1);
                toggle_currency_fields(frm);
            }
        });
        frm.trigger('set_account_query');
    },

    set_account_query: function(frm) {
        frm.set_query('custom_account_paid_to', function() {
            return {
                filters: [
                    ['Account', 'account_type', 'in', ['Bank', 'Cash']],
                    ['Account', 'is_group',     '=',  0],
                    ['Account', 'company',      '=',  frappe.defaults.get_default('company')]
                ]
            };
        });
    },

    custom_amount_paid: function(frm) {
        if (frm._paid_updating) return;
        frm._paid_updating = true;
        let rate = flt(frm.doc.custom_exchange_rate) || 1;
        if (is_multi_currency(frm)) {
            frm.doc.custom_received_amount = flt(frm.doc.custom_amount_paid / rate, 2);
            frm.refresh_field('custom_received_amount');
        }
        frm._paid_updating = false;
        update_rate_description(frm);
        calculate_balance(frm);
    },

    custom_received_amount: function(frm) {
        if (frm._paid_updating) return;
        if (!is_multi_currency(frm)) return;
        frm._paid_updating = true;
        let rate = flt(frm.doc.custom_exchange_rate) || 1;
        frm.doc.custom_amount_paid = flt(frm.doc.custom_received_amount * rate, 2);
        frm.refresh_field('custom_amount_paid');
        frm._paid_updating = false;
        update_rate_description(frm);
        calculate_balance(frm);
    },

    custom_exchange_rate: function(frm) {
        if (!is_multi_currency(frm)) return;
        let rate = flt(frm.doc.custom_exchange_rate) || 1;
        frm._paid_updating = true;
        frm.doc.custom_received_amount = flt(frm.doc.custom_amount_paid / rate, 2);
        frm.refresh_field('custom_received_amount');
        frm._paid_updating = false;
        update_rate_description(frm);
        calculate_balance(frm);
    },

    custom_payment_method: function(frm) {
        frm.set_value('custom_account_paid_to', '');
        frm.doc.custom_account_currency = '';
        frm.set_value('custom_exchange_rate', 1);
        toggle_currency_fields(frm);
        frm.trigger('set_account_query');
    }
});

function calculate_balance(frm) {
    let grand_total = flt(frm.doc.grand_total) || 0;
    let amount_paid = flt(frm.doc.custom_amount_paid) || 0;
    frm.doc.custom_balance_remaining = flt(grand_total - amount_paid, 2);
    frm.refresh_field('custom_balance_remaining');
}

function toggle_currency_fields(frm) {
    let multi            = is_multi_currency(frm);
    let company_currency = frappe.boot.sysdefaults.currency;
    let acct_currency    = frm.doc.custom_account_currency || company_currency;

    frm.set_df_property('custom_exchange_rate',   'hidden', multi ? 0 : 1);
    frm.set_df_property('custom_received_amount', 'hidden', multi ? 0 : 1);

    if (multi) {
        frm.set_df_property('custom_amount_paid', 'label', 'Paid Amount (' + company_currency + ')');
        frm.set_df_property('custom_received_amount', 'label', 'Received Amount (' + acct_currency + ')');
        frm.set_df_property('custom_exchange_rate', 'label', 'Target Exchange Rate');
        frm.set_df_property('custom_balance_remaining', 'label', 'Balance Remaining (' + company_currency + ')');
    } else {
        frm.set_df_property('custom_amount_paid', 'label', 'Amount Paid (' + acct_currency + ')');
        frm.set_df_property('custom_received_amount', 'label', 'Received Amount');
        frm.set_df_property('custom_exchange_rate', 'label', 'Exchange Rate');
        frm.set_df_property('custom_balance_remaining', 'label', 'Balance Remaining (' + acct_currency + ')');
    }

    update_rate_description(frm);
    frm.refresh_fields(['custom_amount_paid', 'custom_balance_remaining', 'custom_exchange_rate', 'custom_received_amount', 'custom_account_currency']);
}

function update_rate_description(frm) {
    if (!is_multi_currency(frm)) {
        frm.set_df_property('custom_exchange_rate', 'description', '');
        frm.refresh_field('custom_exchange_rate');
        return;
    }
    let rate             = flt(frm.doc.custom_exchange_rate, 4);
    let acct_currency    = frm.doc.custom_account_currency;
    let company_currency = frappe.boot.sysdefaults.currency;
    frm.set_df_property('custom_exchange_rate', 'description',
        '1 ' + acct_currency + ' = ' + rate + ' ' + company_currency
    );
    frm.refresh_field('custom_exchange_rate');
}

function is_multi_currency(frm) {
    let acct = frm.doc.custom_account_currency;
    return !!(acct && acct !== frappe.boot.sysdefaults.currency);
}

function flt(val, precision) {
    precision = (precision !== undefined) ? precision : 9;
    return parseFloat((parseFloat(val) || 0).toFixed(precision));
}
"""
    }).insert(ignore_permissions=True)
