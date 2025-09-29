document.addEventListener('DOMContentLoaded', () => {
  const header = document.querySelector('.site-header');
  if (!header) return;

  // Try obvious: <a class="brand">...</a>
  let a = header.querySelector('a.brand');

  // Fallback: any header link whose text contains "Bee Planet Connection"
  if (!a) {
    for (const el of header.querySelectorAll('a')) {
      if ((el.textContent || '').trim().toLowerCase().includes('bee planet connection')) { a = el; break; }
    }
  }

  if (!a) return;

  a.href = '/';
  a.innerHTML = '<img src="/img/logo/logo-256.png" alt="Bee Planet Connection" style="height:84px;width:auto;display:block">';
});
