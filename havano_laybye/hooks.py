app_name = "havano_laybye"
app_title = "Havano Laybye"
app_publisher = "Fortune"
app_description = "Laybye payments on Sales Orders"
app_email = "fortunemakunya88@gmail.com"
app_license = "mit"
fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [["dt", "=", "Sales Order"]]
    },
    {
        "doctype": "Client Script",
        "filters": [["name", "=", "Sales Order Payment and Balance"]]
    },
    {
        "doctype": "Server Script",
        "filters": [["name", "=", "Sales Order Auto Payment Entry"]]
    }
]
after_install = "havano_laybye.havano_laybye.install.after_install"
app_include_js = "/assets/havano_laybye/js/laybye.bundle.js"
