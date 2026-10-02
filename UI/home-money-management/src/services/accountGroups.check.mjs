// Runnable check for the Accounts page grouping / health rules.
//   node src/services/accountGroups.check.mjs
// Fails loudly if the grouping, subtotal or badge rules that drive the page break.
import assert from 'node:assert/strict';
import {
  ACCOUNT_GROUPS,
  creditUtilization,
  filterAccounts,
  groupAccounts,
  groupKeyFor,
  healthBadge,
  netWorthContribution,
  normalizeType,
  sortAccounts,
} from './accountGroups.ts';

const account = (overrides) => ({
  id: 1,
  account_name: 'Main',
  account_type: 'Checking',
  bank: 'BBVA',
  total: 0,
  ...overrides,
});

// Page order is part of the spec: the five documented groups, then Other.
assert.deepEqual(
  ACCOUNT_GROUPS.map((group) => group.key),
  ['cash', 'savings', 'investments', 'credit', 'loans', 'other'],
);

// Type normalisation handles the "… Account" / "… Card" suffixes the API stores.
assert.equal(normalizeType('Savings Account'), 'Savings');
assert.equal(normalizeType('Credit Card'), 'Credit');

// Every documented type lands in one of the page groups.
assert.equal(groupKeyFor('Débito'), 'cash');
assert.equal(groupKeyFor('Checking Account'), 'cash');
assert.equal(groupKeyFor('Cash'), 'cash');
assert.equal(groupKeyFor('Savings'), 'savings');
assert.equal(groupKeyFor('Investment'), 'investments');
assert.equal(groupKeyFor('Retirement'), 'investments');
assert.equal(groupKeyFor('Crédito'), 'credit');
assert.equal(groupKeyFor('Credit Card'), 'credit');
assert.equal(groupKeyFor('Loan'), 'loans');
assert.equal(groupKeyFor('Mortgage'), 'loans');
assert.equal(groupKeyFor('Business'), 'other');
assert.equal(groupKeyFor(undefined), 'other');

// Net worth mirrors Account.net_worth_value, quirks included.
assert.equal(netWorthContribution(account({ total: 100 })), 100);
assert.equal(netWorthContribution(account({ account_type: 'Loan', total: 400 })), -400);
assert.equal(
  netWorthContribution(
    account({ account_type: 'Credit Card', total: 300, credit_limit: 1000 }),
  ),
  -700,
);
assert.equal(netWorthContribution(account({ account_type: 'Credit Card', total: 300 })), 0);

// Utilisation and health badges.
assert.equal(creditUtilization(account({ total: 1000 })), null);
assert.equal(
  creditUtilization(
    account({ account_type: 'Credit Card', total: 750, credit_limit: 1000 }),
  ),
  0.25,
);
assert.equal(creditUtilization(account({ account_type: 'Credit Card', total: 1000 })), null);
assert.deepEqual(
  healthBadge(account({ account_type: 'Credit Card', total: 750, credit_limit: 1000 })),
  { label: '25% used', tone: 'good' },
);
assert.deepEqual(
  healthBadge(account({ account_type: 'Credit Card', total: 450, credit_limit: 1000 })),
  { label: '55% used', tone: 'warn' },
);
assert.deepEqual(
  healthBadge(account({ account_type: 'Credit Card', total: 150, credit_limit: 1000 })),
  { label: '85% used', tone: 'bad' },
);
assert.deepEqual(healthBadge(account({ total: -20 })), { label: 'Overdrawn', tone: 'bad' });
assert.equal(healthBadge(account({ total: 20 })), null);

const accounts = [
  account({ id: 1, account_name: 'Checking', account_type: 'Checking', bank: 'BBVA', total: 100 }),
  account({
    id: 2,
    account_name: 'Credit',
    account_type: 'Credit Card',
    bank: 'BBVA',
    total: 300,
    credit_limit: 1000,
  }),
  account({ id: 3, account_name: 'Emergency', account_type: 'Savings', bank: 'Banorte', total: 50 }),
  account({
    id: 4,
    account_name: 'Card 2',
    account_type: 'Crédito',
    bank: 'Banorte',
    total: 1000,
    credit_limit: 1000,
  }),
];

// Grouping: fixed order, empty groups dropped, subtotal per group and per bank.
const groups = groupAccounts(accounts);
assert.deepEqual(
  groups.map((group) => group.key),
  ['cash', 'savings', 'credit'],
);
assert.equal(groups[0].subtotal, 100);
assert.equal(groups[1].subtotal, 50);
assert.equal(groups[2].subtotal, -700);
assert.deepEqual(
  groups[2].institutions.map((section) => section.bank),
  ['Banorte', 'BBVA'],
);
assert.equal(groups[2].institutions[0].subtotal, 0);
assert.equal(groups[2].institutions[1].subtotal, -700);
assert.deepEqual(groupAccounts([]), []);

// Search spans name / bank / type; the group filter narrows to one bucket.
assert.equal(filterAccounts(accounts, 'banorte').length, 2);
assert.equal(filterAccounts(accounts, 'card').length, 2); // matches name *and* type
assert.equal(filterAccounts(accounts, '', 'credit').length, 2);
assert.equal(filterAccounts(accounts, '', 'savings').length, 1);
assert.equal(filterAccounts(accounts, 'nothing').length, 0);
assert.equal(filterAccounts(accounts, '', 'all').length, 4);

// Sorting by name and by net worth contribution.
assert.deepEqual(
  sortAccounts(accounts, 'name').map((item) => item.account_name),
  ['Card 2', 'Checking', 'Credit', 'Emergency'],
);
assert.deepEqual(sortAccounts(accounts, '-networth').map((item) => item.id), [1, 3, 4, 2]);
assert.deepEqual(sortAccounts(accounts, 'bank').map((item) => item.id), [3, 4, 1, 2]);

console.log('accountGroups: all checks passed');
