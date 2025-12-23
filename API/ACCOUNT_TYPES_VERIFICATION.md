# Account Types and Balance Calculation Verification

## Account Type Categories

### Assets (Positive Net Worth Contribution)

These accounts represent money you **have**:

- **Savings** / **Savings Account**: Money in savings account
- **Checking**: Money in checking account  
- **Débito** / **Debit**: Debit card account balance
- **Efectivo** / **Cash**: Physical cash on hand
- **Investment**: Investment account value
- **Business**: Business account balance
- **Other**: Other asset accounts

**Net Worth Calculation**: `+total` (add balance to net worth)

### Liabilities (Negative Net Worth Contribution)

These accounts represent money you **owe**:

#### Credit Cards

- **Crédito** / **Credit Card** / **Credit**: Credit card accounts
  - `total` field = **Available Credit** (how much credit you still have)
  - `credit_limit` = Total credit limit
  - **Used Credit** = `credit_limit - total`
  - **Debt** = Used Credit = `credit_limit - total`
  
**Net Worth Calculation**: `-(credit_limit - total)` (subtract debt from net worth)

**Example**:

- Credit Limit: $42,000
- Available Credit (total): $5,209.60
- Used Credit: $42,000 - $5,209.60 = $36,790.40
- Net Worth Contribution: -$36,790.40 (subtracted from net worth)

#### Loans and Mortgages

- **Loan**: Personal loans, car loans, etc.
- **Mortgage**: Home mortgage

**Net Worth Calculation**: `-total` (subtract what you owe)

## Balance Update Logic

### For Regular Accounts (Assets)

- **Income Transaction**: `total += amount` (balance increases)
- **Expense Transaction**: `total -= amount` (balance decreases)

### For Credit Cards

- **Expense Transaction**: `total -= amount` (available credit decreases)
  - Example: Spend $100 → Available credit goes from $5,000 to $4,900
- **Income Transaction** (Payment): `total += amount` (available credit increases)
  - Example: Pay $500 → Available credit goes from $4,900 to $5,400

**Note**: The same logic applies because `total` represents available credit, which decreases when you spend and increases when you pay.

## Net Worth Formula

```
Net Worth = Sum of Assets - Sum of Liabilities

Where:
- Assets = Savings + Checking + Debit + Cash + Investment + Business + Other
- Liabilities = Credit Card Debt + Loans + Mortgages

Credit Card Debt = Credit Limit - Available Credit
```

## Verification Checklist

✅ **Total Balance Calculation**:

- Assets are added correctly
- Credit card debt is subtracted correctly
- Loans/Mortgages are subtracted correctly

✅ **Credit Card Balance Logic**:

- `total` represents available credit
- Used credit = `credit_limit - total`
- Debt = Used credit
- Net worth contribution = -debt

✅ **Transaction Updates**:

- Expenses reduce available credit (for credit cards)
- Income/payments increase available credit (for credit cards)
- Same logic works for all account types

✅ **Account Type Normalization**:

- "Savings Account" → "Savings"
- "Checking Account" → "Checking"
- "Credit Card" handled correctly
- All variants recognized

## Example Calculation

**Assets**:

- Savings: $10,000
- Checking: $5,000
- Cash: $500
- **Total Assets**: $15,500

**Liabilities**:

- Credit Card 1: Limit $42,000, Available $5,209.60 → Debt = $36,790.40
- Credit Card 2: Limit $10,000, Available $8,000 → Debt = $2,000
- Loan: $20,000
- **Total Liabilities**: $58,790.40

**Net Worth**: $15,500 - $58,790.40 = **-$43,290.40**

This correctly shows negative net worth when liabilities exceed assets.
