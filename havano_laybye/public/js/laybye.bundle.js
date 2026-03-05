// @ts-nocheck
// ═══════════════════════════════════════════════════════════════
//  HAVANO LAYBYE — Sales Order Laybye Payment Extension
// ═══════════════════════════════════════════════════════════════

frappe.ui.form.on("Sales Order", {

    refresh: function(frm) {
        laybye_setup_account_query(frm);
        laybye_toggle_currency(frm);
        laybye_refresh_display(frm);
        // Wire the Post button on every refresh
        setTimeout(function() {
            if (frm.fields_dict["custom_laybye_post_btn"] &&
                frm.fields_dict["custom_laybye_post_btn"].$input) {
                frm.fields_dict["custom_laybye_post_btn"].$input
                    .off("click.laybye")
                    .on("click.laybye", function() { laybye_post_payment(frm); });
            }
        }, 300);
    },

    onload: function(frm) {
        laybye_setup_account_query(frm);
        laybye_toggle_currency(frm);
        laybye_refresh_display(frm);
    },

    // Account selected → fetch currency + rate
    custom_laybye_account: function(frm) {
        if (!frm.doc.custom_laybye_account) {
            frm.set_value("custom_laybye_account_currency", "");
            frm.set_value("custom_laybye_exchange_rate", 1);
            laybye_toggle_currency(frm);
            return;
        }
        frappe.call({
            method: "havano_laybye.havano_laybye.api.get_account_info",
            args: {
                account: frm.doc.custom_laybye_account,
                transaction_date: frm.doc.custom_laybye_date || frappe.datetime.get_today()
            },
            callback: function(r) {
                if (!r.message) return;
                frm.set_value("custom_laybye_account_currency", r.message.account_currency);
                frm.set_value("custom_laybye_exchange_rate", r.message.exchange_rate);
                laybye_toggle_currency(frm);
                laybye_update_rate_desc(frm);
            }
        });
    },

    // Method changed → reset account, re-filter
    custom_laybye_method: function(frm) {
        frm.set_value("custom_laybye_account", "");
        frm.set_value("custom_laybye_account_currency", "");
        frm.set_value("custom_laybye_exchange_rate", 1);
        laybye_toggle_currency(frm);
        laybye_setup_account_query(frm);
    },

    // paid_amount (base) → derive received_amount (foreign)
    custom_laybye_paid_amount: function(frm) {
        if (frm._laybye_lock) return;
        frm._laybye_lock = true;
        let rate = flt_l(frm.doc.custom_laybye_exchange_rate) || 1;
        frm.doc.custom_laybye_received_amount = laybye_is_multi(frm)
            ? flt_l(frm.doc.custom_laybye_paid_amount / rate, 2)
            : frm.doc.custom_laybye_paid_amount;
        frm.refresh_field("custom_laybye_received_amount");
        frm._laybye_lock = false;
        laybye_refresh_display(frm);
    },

    // received_amount (foreign) → back-calculate paid_amount (base)
    custom_laybye_received_amount: function(frm) {
        if (frm._laybye_lock) return;
        if (!laybye_is_multi(frm)) return;
        frm._laybye_lock = true;
        let rate = flt_l(frm.doc.custom_laybye_exchange_rate) || 1;
        frm.doc.custom_laybye_paid_amount = flt_l(frm.doc.custom_laybye_received_amount * rate, 2);
        frm.refresh_field("custom_laybye_paid_amount");
        frm._laybye_lock = false;
        laybye_refresh_display(frm);
    },

    // exchange_rate changed → recalc received from paid
    custom_laybye_exchange_rate: function(frm) {
        if (!laybye_is_multi(frm)) return;
        let rate = flt_l(frm.doc.custom_laybye_exchange_rate) || 1;
        frm.doc.custom_laybye_received_amount = flt_l(frm.doc.custom_laybye_paid_amount / rate, 2);
        frm.refresh_field("custom_laybye_received_amount");
        laybye_update_rate_desc(frm);
    },

    grand_total:             function(frm) { laybye_refresh_display(frm); },
    custom_laybye_total_paid: function(frm) { laybye_refresh_display(frm); }

});

// ─────────────────────────────────────────────────────────────
//  POST PAYMENT
// ─────────────────────────────────────────────────────────────
function laybye_post_payment(frm) {
    if (frm.doc.docstatus !== 1) {
        frappe.msgprint(__("Please submit the Sales Order before posting a payment."));
        return;
    }
    if (!frm.doc.custom_laybye_account) {
        frappe.msgprint(__("Please select an Account."));
        return;
    }
    if (!flt_l(frm.doc.custom_laybye_paid_amount)) {
        frappe.msgprint(__("Please enter a Paid Amount."));
        return;
    }

    let is_multi = laybye_is_multi(frm);
    let cur_base = frappe.boot.sysdefaults.currency || "";
    let cur_acct = frm.doc.custom_laybye_account_currency || cur_base;
    let rate     = flt_l(frm.doc.custom_laybye_exchange_rate) || 1;
    let msg      = "Post <b>" + cur_base + " " + fmt(frm.doc.custom_laybye_paid_amount) + "</b>"
        + (is_multi ? " (" + cur_acct + " " + fmt(frm.doc.custom_laybye_received_amount) + " @ " + rate + ")" : "")
        + " via <b>" + frm.doc.custom_laybye_method + "</b>?";

    frappe.confirm(__(msg), function() {
        frappe.call({
            method: "havano_laybye.havano_laybye.api.post_payment",
            freeze: true,
            freeze_message: __("Creating Payment Entry..."),
            args: {
                sales_order:     frm.doc.name,
                paid_amount:     frm.doc.custom_laybye_paid_amount,
                payment_method:  frm.doc.custom_laybye_method,
                account:         frm.doc.custom_laybye_account,
                payment_date:    frm.doc.custom_laybye_date,
                exchange_rate:   frm.doc.custom_laybye_exchange_rate || 1,
                received_amount: frm.doc.custom_laybye_received_amount,
                remarks:         frm.doc.custom_laybye_remarks || ""
            },
            callback: function(r) {
                if (!r.message) return;
                frm.doc.custom_laybye_total_paid = r.message.total_paid;
                frm.doc.custom_laybye_balance    = r.message.balance;
                frm.refresh_field("custom_laybye_total_paid");
                frm.refresh_field("custom_laybye_balance");
                frm.set_value("custom_laybye_paid_amount", 0);
                frm.set_value("custom_laybye_received_amount", 0);
                frm.set_value("custom_laybye_remarks", "");
                laybye_refresh_display(frm);
                frappe.show_alert({
                    message: "Payment Entry " + r.message.pe_name + " created",
                    indicator: "green"
                });
            }
        });
    });
}

// ─────────────────────────────────────────────────────────────
//  ACCOUNT QUERY
// ─────────────────────────────────────────────────────────────
function laybye_setup_account_query(frm) {
    frm.set_query("custom_laybye_account", function() {
        return {
            filters: [
                ["Account", "account_type", "in", ["Bank", "Cash"]],
                ["Account", "is_group",     "=",  0],
                ["Account", "company",      "=",  frappe.defaults.get_default("company")]
            ]
        };
    });
}

// ─────────────────────────────────────────────────────────────
//  CURRENCY HELPERS
// ─────────────────────────────────────────────────────────────
function laybye_is_multi(frm) {
    let ac = frm.doc.custom_laybye_account_currency;
    return !!(ac && ac !== frappe.boot.sysdefaults.currency);
}

function laybye_toggle_currency(frm) {
    let multi = laybye_is_multi(frm);
    let base  = frappe.boot.sysdefaults.currency || "";
    let acct  = frm.doc.custom_laybye_account_currency || base;

    frm.set_df_property("custom_laybye_exchange_rate",   "hidden", multi ? 0 : 1);
    frm.set_df_property("custom_laybye_received_amount", "hidden", multi ? 0 : 1);
    frm.set_df_property("custom_laybye_paid_amount",     "label",  "Paid Amount (" + base + ")");
    frm.set_df_property("custom_laybye_received_amount", "label",  "Received Amount (" + acct + ")");
    frm.refresh_fields([
        "custom_laybye_exchange_rate",
        "custom_laybye_received_amount",
        "custom_laybye_paid_amount"
    ]);
}

function laybye_update_rate_desc(frm) {
    if (!laybye_is_multi(frm)) {
        frm.set_df_property("custom_laybye_exchange_rate", "description", "");
        frm.refresh_field("custom_laybye_exchange_rate");
        return;
    }
    let rate = flt_l(frm.doc.custom_laybye_exchange_rate, 4);
    frm.set_df_property("custom_laybye_exchange_rate", "description",
        "1 " + frm.doc.custom_laybye_account_currency +
        " = " + rate + " " + frappe.boot.sysdefaults.currency
    );
    frm.refresh_field("custom_laybye_exchange_rate");
}

// ─────────────────────────────────────────────────────────────
//  BALANCE DISPLAY
// ─────────────────────────────────────────────────────────────
function laybye_refresh_display(frm) {
    if (!frm.fields_dict["custom_laybye_balance_display"]) return;
    let grand = flt_l(frm.doc.grand_total);
    let paid  = flt_l(frm.doc.custom_laybye_total_paid);
    let bal   = flt_l(frm.doc.custom_laybye_balance);
    if (!paid && !bal) bal = grand;
    let pct   = grand ? Math.min(100, Math.round((paid / grand) * 100)) : 0;
    let col   = pct >= 100 ? "#28a745" : pct >= 50 ? "#ffc107" : "#dc3545";
    let cur   = frappe.boot.sysdefaults.currency || "";

    frm.fields_dict["custom_laybye_balance_display"].$wrapper.html(
        "<div style='margin:10px 0 6px;font-size:13px;font-weight:600;color:#333;'>Payment Summary</div>" +
        "<div style='display:flex;gap:14px;flex-wrap:wrap;margin-bottom:10px;'>" +
            "<div style='background:#f8f9fa;border-radius:6px;padding:10px 16px;min-width:120px;'>" +
                "<div style='font-size:10px;color:#888;text-transform:uppercase;'>Grand Total</div>" +
                "<div style='font-size:16px;font-weight:700;color:#333;'>" + cur + " " + fmt(grand) + "</div>" +
            "</div>" +
            "<div style='background:#e8f5e9;border-radius:6px;padding:10px 16px;min-width:120px;'>" +
                "<div style='font-size:10px;color:#888;text-transform:uppercase;'>Total Paid</div>" +
                "<div style='font-size:16px;font-weight:700;color:#28a745;'>" + cur + " " + fmt(paid) + "</div>" +
            "</div>" +
            "<div style='background:" + (bal > 0 ? "#fff3cd" : "#d4edda") + ";border-radius:6px;padding:10px 16px;min-width:120px;'>" +
                "<div style='font-size:10px;color:#888;text-transform:uppercase;'>Balance Due</div>" +
                "<div style='font-size:16px;font-weight:700;color:" + (bal > 0 ? "#856404" : "#155724") + ";'>" +
                    cur + " " + fmt(bal) +
                "</div>" +
            "</div>" +
        "</div>" +
        "<div style='background:#eee;border-radius:99px;height:7px;overflow:hidden;margin-bottom:3px;'>" +
            "<div style='background:" + col + ";width:" + pct + "%;height:100%;border-radius:99px;transition:width .4s;'></div>" +
        "</div>" +
        "<div style='font-size:11px;color:#888;margin-bottom:6px;'>" + pct + "% paid</div>"
    );
}

// ─────────────────────────────────────────────────────────────
//  UTILS
// ─────────────────────────────────────────────────────────────
function flt_l(v, p) {
    p = (p !== undefined) ? p : 9;
    return parseFloat((parseFloat(v) || 0).toFixed(p));
}
function fmt(n) {
    return Number(n).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
}
