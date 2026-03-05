### Havano Laybye





# Havano Laybye

A Frappe/ERPNext app that adds **Laybye (Layaway) payment functionality** to Sales Orders.

It allows a customer to place a Sales Order and pay a deposit upfront. A Payment Entry is automatically created on submission, and the outstanding balance is tracked directly on the Sales Order.

---

## What It Does

```
Customer places Sales Order ($500)
        ↓
Pays deposit ($200) at time of order
        ↓
Payment Entry auto-created → money goes into selected bank/cash account
        ↓
Balance Remaining = $300 (tracked on the Sales Order)
```

---

## Features

- 💰 **Amount Paid** field on Sales Order
- 📊 **Balance Remaining** field (Grand Total − Amount Paid)
- 🏦 **Account Paid To** — select any Bank or Cash account
- 💱 **Multi-currency support** — works with foreign currency accounts
  - Automatically fetches exchange rate
  - Shows Received Amount in foreign currency
  - Calculates Paid Amount in base currency
- 🧾 **Auto Payment Entry** created on Sales Order submit
- 📁 **Payment section** is collapsible on the Sales Order form

---

## Requirements

- ERPNext v15+
- Frappe v15+

---

## Installation

```bash
# Get the app
bench get-app https://github.com/draftpos/havano_laybye.git

# Install on your site
bench --site your-site.local install-app havano_laybye

# Run migrate to apply fixtures
bench --site your-site.local migrate
```

---

## How to Use

1. Create a new **Sales Order** as normal
2. Add your items
3. Scroll down to the **Payment** section
4. Select **Account Paid To** (Bank or Cash account)
5. Select **Payment Method** (Cash / Bank / Mobile Money)
6. If foreign currency account selected:
   - Enter **Received Amount** in foreign currency (e.g. USD)
   - Exchange rate auto-fetches
   - **Paid Amount** in base currency auto-calculates
7. If base currency account:
   - Just enter **Amount Paid**
8. **Submit** the Sales Order
9. A **Payment Entry** is automatically created and linked
10. **Balance Remaining** shows what the customer still owes

---

## Fields Added to Sales Order

| Field | Type | Description |
|---|---|---|
| Account Paid To | Link (Account) | Bank or Cash account to receive payment |
| Payment Method | Select | Cash, Bank, or Mobile Money |
| Amount Paid | Currency | Amount paid in base currency |
| Received Amount | Currency | Amount in foreign currency (multi-currency only) |
| Exchange Rate | Float | Auto-fetched exchange rate |
| Account Currency | Data | Currency of selected account (read only) |
| Balance Remaining | Currency | Grand Total minus Amount Paid |
| Payment Entry | Link | Auto-created Payment Entry reference |

---

## Uninstall

```bash
bench --site your-site.local uninstall-app havano_laybye
bench --site your-site.local migrate
```

---

## License

MIT

## Publisher

Fortune — fortunemakunya88@gmail.com
havano_laybye

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app havano_laybye
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/havano_laybye
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
