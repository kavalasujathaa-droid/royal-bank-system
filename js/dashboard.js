document.addEventListener('DOMContentLoaded', () => {
  const usersEl = document.getElementById('users');
  const accountsEl = document.getElementById('accounts');
  const transactionsEl = document.getElementById('transactions');

  if (usersEl) {
    usersEl.textContent = '0';
  }
  if (accountsEl) {
    accountsEl.textContent = '0';
  }
  if (transactionsEl) {
    transactionsEl.textContent = '0';
  }
});
