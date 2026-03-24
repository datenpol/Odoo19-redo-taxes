# codexplayground Baseline

Date: `2026-03-12`

Environment: `https://codexplayground.odoo19.at/odoo`

API access used: Odoo 19 `JSON-2`

Version: `19.0+e`

## Module and company snapshot

Installed modules relevant to this project:

- `account`
- `l10n_at`
- `l10n_at_reports`

Not installed:

- `l10n_us`

Company counts:

- `San Francisco` accounts: `53`
- `AT Company` accounts: `240`
- `San Francisco` taxes: `4`
- `AT Company` taxes: `53`
- `San Francisco` journal entries and invoices: `35`

Product linkage snapshot:

- products with sale tax `1`: `51`
- products with purchase tax `2`: `58`
- products with Austrian sale tax `19`: `51`
- products with Austrian purchase tax `47`: `58`

This matters because many products already carry both the generic `San Francisco` taxes and the Austrian `AT Company` taxes at the same time.

## Company and identity baseline

### Company records

| Company ID | Name | Country | Currency | VAT | Default sale tax | Default purchase tax |
| --- | --- | --- | --- | --- | --- | --- |
| `1` | `My Company (San Francisco)` | `Austria` | `USD` | empty | `1 / 15%` | `2 / 15%` |
| `3` | `AT Company` | `Austria` | `EUR` | `ATU12345675` | `19 / 20% Ust` | `47 / 20% Vst` |

Lock dates on company `1`:

- `fiscalyear_lock_date`: empty
- `tax_lock_date`: empty
- `sale_lock_date`: empty
- `purchase_lock_date`: empty

### Partner records

| Partner ID | Name | Street | ZIP | City | Country | State | VAT | Phone | Email | Website |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `1` | `My Company (San Francisco)` | `8000 Marina Blvd, Suite 300` | `94005` | `Brisbane` | `Austria` | `California (US)` | empty | `+1 555-555-5556` | `info@yourcompany.com` | `http://www.example.com` |
| `44` | `AT Company` | `Sternwartestraße` | `6020` | `Innsbruck` | `Austria` | empty | `ATU12345675` | `+43 512 321 54 76` | `info@company.atexample.com` | `http://www.atexample.com` |

### Bank record on company partner `1`

| Bank record ID | Account number | Allow outgoing payments |
| --- | --- | --- |
| `2` | `BANK134567890` | `true` |

## Currency baseline

| Currency ID | Code | Symbol | Full name | Unit label | Subunit label | Position |
| --- | --- | --- | --- | --- | --- | --- |
| `1` | `USD` | `$` | `United States dollar` | `Dollars` | `Cents` | `before` |
| `126` | `EUR` | `€` | `Euro` | `Euros` | `Cents` | `after` |

Currency rates on company `1`:

| Currency ID | Rate date | Rate | Company rate | Inverse company rate |
| --- | --- | --- | --- | --- |
| `1` | `2010-01-01` | `1.0` | `1.0` | `1.0` |
| `126` | `2010-01-01` | `1.2834` | `1.2834` | `0.7791803023219572` |

## San Francisco tax baseline

### Current tax groups on company `1`

| Group ID | Name | Country | Payable account | Receivable account |
| --- | --- | --- | --- | --- |
| `1` | `Tax 15%` | `United States` | `22 / 252000 Tax Payable` | `10 / 132000 Tax Receivable` |
| `2` | `Tax 0%` | `United States` | `22 / 252000 Tax Payable` | `10 / 132000 Tax Receivable` |

### Current taxes on company `1`

| Tax ID | Type | Name | Amount | Country | Group | Description | Invoice label |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `1` | `sale` | `15%` | `15` | `United States` | `Tax 15%` | empty | empty |
| `2` | `purchase` | `15%` | `15` | `United States` | `Tax 15%` | empty | empty |
| `3` | `sale` | `0% Exports` | `0` | `United States` | `Tax 0%` | empty | empty |
| `4` | `purchase` | `0% Imports` | `0` | `United States` | `Tax 0%` | empty | empty |

### Current repartition behavior on company `1`

| Tax ID | Tax name | Document | Line type | Account | Tags |
| --- | --- | --- | --- | --- | --- |
| `1` | `15%` | `invoice` | `base` | empty | none |
| `1` | `15%` | `invoice` | `tax` | `21 / 251000 Tax Received` | none |
| `1` | `15%` | `refund` | `base` | empty | none |
| `1` | `15%` | `refund` | `tax` | `21 / 251000 Tax Received` | none |
| `2` | `15%` | `invoice` | `base` | empty | none |
| `2` | `15%` | `invoice` | `tax` | `9 / 131000 Tax Paid` | none |
| `2` | `15%` | `refund` | `base` | empty | none |
| `2` | `15%` | `refund` | `tax` | `9 / 131000 Tax Paid` | none |
| `3` | `0% Exports` | `invoice` | `base` | empty | none |
| `3` | `0% Exports` | `invoice` | `tax` | empty | none |
| `3` | `0% Exports` | `refund` | `base` | empty | none |
| `3` | `0% Exports` | `refund` | `tax` | empty | none |
| `4` | `0% Imports` | `invoice` | `base` | empty | none |
| `4` | `0% Imports` | `invoice` | `tax` | empty | none |
| `4` | `0% Imports` | `refund` | `base` | empty | none |
| `4` | `0% Imports` | `refund` | `tax` | empty | none |

## Austrian reference taxes already present in the same database

These are the main reference records for the mapping spec.

### Reference tax groups

| Group ID | Name | Payable account | Receivable account |
| --- | --- | --- | --- |
| `3` | `0%` | `193 / Allocation account for tax authorities` | `193 / Allocation account for tax authorities` |
| `4` | `10%` | `193 / Allocation account for tax authorities` | `193 / Allocation account for tax authorities` |
| `5` | `12%` | `193 / Allocation account for tax authorities` | `193 / Allocation account for tax authorities` |
| `6` | `13%` | `193 / Allocation account for tax authorities` | `193 / Allocation account for tax authorities` |
| `7` | `19%` | `193 / Allocation account for tax authorities` | `193 / Allocation account for tax authorities` |
| `8` | `20%` | `193 / Allocation account for tax authorities` | `193 / Allocation account for tax authorities` |

### Reference taxes

| Tax ID | Type | Name | Description | Invoice label | Group |
| --- | --- | --- | --- | --- | --- |
| `13` | `sale` | `0% Ust EX art6` | `UST_015 Export 0% (§ 6 Abs. 1 Z 2 bis 6)` | `0%` | `0%` |
| `19` | `sale` | `20% Ust` | `UST_022 Normal tax rate 20%` | `20%` | `20%` |
| `47` | `purchase` | `20% Vst` | `VST_060 Normal tax rate 20%` | `20%` | `20%` |
| `60` | `purchase` | `0% Vst` | `VST_071 IGE 0%` | `VST_071 IGE 0% (Art. 6 Abs. 2)` | `0%` |

### Reference repartition lines for likely report-aware mapping

| Tax | Document | Line type | Account | Tags |
| --- | --- | --- | --- | --- |
| `20% Ust` | `invoice` | `base` | empty | `1043,1054` |
| `20% Ust` | `invoice` | `tax` | `183 / VAT 20%` | `1055` |
| `20% Vst` | `invoice` | `base` | empty | none |
| `20% Vst` | `invoice` | `tax` | `148 / Input tax 20%` | `1084` |
| `0% Ust EX art6` | `invoice` | `base` | empty | `1043,1048` |
| `0% Ust EX art6` | `invoice` | `tax` | `186 / VAT, other` | none |
| `0% Vst` | `invoice` | `base` | empty | none |
| `0% Vst` | `invoice` | `tax` | `151 / Other tax 13%` | `1087` |

## Journal baseline on company `1`

| Journal ID | Name | Code | Type | Default account |
| --- | --- | --- | --- | --- |
| `1` | `Sales` | `RE` | `sale` | `26 / 400000 Product Sales` |
| `2` | `Purchases` | `RECHN` | `purchase` | `32 / 600000 Expenses` |
| `3` | `Miscellaneous Operations` | `SONST` | `general` | empty |
| `4` | `Exchange Difference` | `WECHS` | `general` | empty |
| `5` | `Cash Basis Taxes` | `CABA` | `general` | empty |
| `6` | `Bank` | `BNK1` | `bank` | `45 / 101401 Bank` |
| `7` | `Bestandsbewertung` | `STJ` | `general` | empty |
| `15` | `Kassensystem` | `POSS` | `general` | empty |
| `16` | `Bargeld (Möbelhaus)` | `CSH1` | `cash` | `291 / 101501 Bargeld (Möbelhaus)` |
| `17` | `Bargeld (Kleidergeschäft)` | `CSH2` | `cash` | `292 / 101502 Bargeld (Kleidergeschäft)` |
| `18` | `Bargeld (Bäckerei)` | `CSH3` | `cash` | `293 / 101503 Bargeld (Bäckerei)` |
| `19` | `Tax Returns` | `TAX` | `general` | empty |
| `21` | `Journal Loan Demo` | `LOAN` | `general` | empty |

## Chart of accounts baseline on company `1`

The Austrian reference chart on company `3` is much larger and mostly code-less. That is the reason the draft mapping spec preserves `San Francisco` account codes for now and focuses on names first.

### Current `San Francisco` account inventory

| Account ID | Code | Name | Type | Posted lines |
| --- | --- | --- | --- | --- |
| `1` | `101000` | `Current Assets` | `asset_current` | `0` |
| `43` | `101300` | `Account Receivable (PoS)` | `asset_receivable` | `4` |
| `45` | `101401` | `Bank` | `asset_cash` | `11` |
| `46` | `101402` | `Bank Suspense Account` | `asset_current` | `9` |
| `48` | `101403` | `Ausstehende Eingänge` | `asset_current` | `0` |
| `49` | `101404` | `Ausstehende Zahlungen` | `asset_current` | `0` |
| `291` | `101501` | `Bargeld (Möbelhaus)` | `asset_cash` | `3` |
| `292` | `101502` | `Bargeld (Kleidergeschäft)` | `asset_cash` | `0` |
| `293` | `101503` | `Bargeld (Bäckerei)` | `asset_cash` | `0` |
| `47` | `101701` | `Liquidity Transfer` | `asset_current` | `0` |
| `2` | `110100` | `Stock Valuation` | `asset_current` | `0` |
| `3` | `110400` | `Cost of Production` | `asset_current` | `0` |
| `4` | `110500` | `Work in Progress` | `asset_current` | `0` |
| `5` | `121000` | `Account Receivable` | `asset_receivable` | `16` |
| `6` | `121100` | `Products to receive` | `asset_current` | `0` |
| `7` | `122000` | `Owner's Current Account` | `asset_receivable` | `0` |
| `8` | `128000` | `Prepaid Expenses` | `asset_current` | `0` |
| `9` | `131000` | `Tax Paid` | `asset_current` | `0` |
| `10` | `132000` | `Tax Receivable` | `asset_receivable` | `0` |
| `11` | `141000` | `Prepayments` | `asset_prepayments` | `0` |
| `12` | `151000` | `Fixed Asset` | `asset_fixed` | `0` |
| `13` | `191000` | `Non-current assets` | `asset_non_current` | `0` |
| `14` | `201000` | `Current Liabilities` | `liability_current` | `0` |
| `44` | `201100` | `Credit Card` | `liability_credit_card` | `0` |
| `15` | `211000` | `Account Payable` | `liability_payable` | `5` |
| `16` | `211100` | `Bills to receive` | `liability_current` | `0` |
| `17` | `212000` | `Deferred Revenue` | `liability_current` | `0` |
| `18` | `230000` | `Salary Payable` | `liability_current` | `0` |
| `19` | `230100` | `Employee Payroll Taxes` | `liability_current` | `0` |
| `20` | `230200` | `Employer Payroll Taxes` | `liability_current` | `0` |
| `21` | `251000` | `Tax Received` | `liability_current` | `3` |
| `22` | `252000` | `Tax Payable` | `liability_payable` | `0` |
| `23` | `291000` | `Non-current Liabilities` | `liability_non_current` | `0` |
| `24` | `301000` | `Capital` | `equity` | `0` |
| `25` | `302000` | `Dividends` | `equity` | `0` |
| `26` | `400000` | `Product Sales` | `income` | `23` |
| `27` | `441000` | `Foreign Exchange Gain` | `income` | `0` |
| `28` | `442000` | `Cash Difference Gain` | `income` | `1` |
| `29` | `443000` | `Cash Discount Loss` | `expense` | `0` |
| `30` | `450000` | `Other Income` | `income_other` | `0` |
| `31` | `500000` | `Cost of Goods Sold` | `expense_direct_cost` | `0` |
| `32` | `600000` | `Expenses` | `expense` | `6` |
| `33` | `610000` | `Stock Variation` | `expense` | `0` |
| `34` | `611000` | `Purchase of Equipments` | `expense` | `0` |
| `35` | `612000` | `Rent` | `expense` | `0` |
| `36` | `620000` | `Bank Fees` | `expense` | `0` |
| `37` | `630000` | `Salary Expenses` | `expense` | `0` |
| `38` | `641000` | `Foreign Exchange Loss` | `expense` | `0` |
| `39` | `642000` | `Cash Difference Loss` | `expense` | `0` |
| `40` | `643000` | `Cash Discount Gain` | `income` | `0` |
| `41` | `961000` | `RD Expenses` | `expense` | `0` |
| `42` | `962000` | `Sales Expenses` | `expense` | `0` |
| `50` | `999999` | `Undistributed Profits/Losses` | `equity_unaffected` | `0` |

### Core Austrian reference accounts already available on company `3`

| Account ID | Name | Type |
| --- | --- | --- |
| `148` | `Input tax 20%` | `asset_current` |
| `183` | `VAT 20%` | `liability_current` |
| `193` | `Allocation account for tax authorities` | `liability_payable` |
| `284` | `Bank` | `asset_cash` |
| `285` | `Bank Suspense Account` | `asset_current` |
| `288` | `Liquidity Transfer` | `asset_current` |
| `289` | `Outstanding Receipts` | `asset_current` |
| `290` | `Outstanding Payments` | `asset_current` |

## Translation behavior on `AT Company`

This database already has active German UI translations:

- `res.users/context_get` for the API user returns `lang = de_DE`
- `res.lang` contains active `German / Deutsch` as `de_DE`

When the same Austrian reference records are read with `context.lang = de_DE`, Odoo returns German display values. That means the patcher can write:

- a canonical base value
- a `de_DE` translation for the actual user-facing Austrian-German UI

This behavior is central to the production-ready design because the user requirement is not just Austrian-looking records, but Austrian-German display text in the UI.

### Verified examples from live Odoo reads

| Record type | Reference ID | Base value | `de_DE` value |
| --- | --- | --- | --- |
| Journal | `8` | `Sales` | `Verkauf` |
| Journal | `14` | `Inventory Valuation` | `Bestandsbewertung` |
| Account | `130` | `Trade receivables, domestic` | `Forderungen aus Lieferungen und Leistungen Inland` |
| Account | `148` | `Input tax 20%` | `Vorsteuern 20%` |
| Account | `183` | `VAT 20%` | `Umsatzsteuer 20%` |
| Account | `202` | `Revenue 20%` | `Brutto-Umsatzerlöse im Inland (20%)` |
| Tax | `19` description | `UST_022 Normal tax rate 20%` | `UST_022 Normalsteuersatz 20%` |
| Tax | `47` description | `VST_060 Normal tax rate 20%` | `VST_060 Normalsteuersatz 20%` |

One nuance matters for implementation:

- tax descriptions come back as HTML in base reads, for example `<div>UST_022 Normal tax rate 20%</div>`
- the same field comes back as plain translated text in `de_DE` reads

The machine-readable reference harvest used for the translation-aware mapping spec is stored in `data/at-company-reference-values-2026-03-12.json`.

## Main baseline observations

- `San Francisco` already has country `Austria`, but the company partner still has `California (US)` as state and a US phone number.
- Company currency is still `USD`, while the Austrian reference company uses `EUR`.
- `San Francisco` still runs on US-flavored tax records underneath:
  - tax country is `United States`
  - tax groups are `Tax 15%` and `Tax 0%`
  - repartition tags are empty
- `San Francisco` has live posted entries on a small subset of accounts, so a cosmetic in-place rename strategy is viable.
- The Austrian reference chart in the same database is large and mostly code-less, which makes direct one-to-one code cloning unattractive for a fast safe patch.
- The cash journals and cash accounts show that the seed data is already slightly mixed and app-driven. The mapping spec should normalize that instead of pretending the source is clean.
