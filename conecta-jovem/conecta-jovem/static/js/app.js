(function () {
  // menu mobile
  var b = document.querySelector('.burger'), m = document.getElementById('menu');
  if (b && m) b.addEventListener('click', function () {
    var aberto = m.classList.toggle('aberto');
    b.setAttribute('aria-expanded', aberto);
  });
  // confirmação antes de excluir/cancelar
  document.querySelectorAll('form[data-confirmar]').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      if (!window.confirm(f.dataset.confirmar)) e.preventDefault();
    });
  });
  // feedback visual ao enviar formulários (evita duplo clique)
  document.querySelectorAll('form').forEach(function (f) {
    f.addEventListener('submit', function (e) {
      if (e.defaultPrevented) return;
      var btn = f.querySelector('button[type=submit]');
      if (btn) { setTimeout(function () { btn.disabled = true; btn.textContent = 'Enviando...'; }, 0); }
    });
  });
  // filtros de oportunidades: aplica ao trocar seleção
  document.querySelectorAll('form.filtros select').forEach(function (s) {
    s.addEventListener('change', function () { s.form.submit(); });
  });
  // mensagens somem sozinhas
  setTimeout(function () {
    document.querySelectorAll('.flash.sucesso').forEach(function (el) { el.style.display = 'none'; });
  }, 6000);
})();
