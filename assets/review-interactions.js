function sizeDiagram(canvas, scale) {
  const svg = canvas.querySelector('svg');
  const box = svg.viewBox.baseVal;
  svg.dataset.scale = scale;
  svg.style.width = `${box.width * scale}px`;
  svg.style.height = `${box.height * scale}px`;
}
function fitCanvas(canvas) {
  if (!canvas.clientWidth) return;
  canvas.dataset.fit = 'true';
  sizeDiagram(canvas, canvas.clientWidth / canvas.querySelector('svg').viewBox.baseVal.width);
}
function fit(button) { fitCanvas(button.closest('.chain').querySelector('.canvas')); }
function zoom(button, delta) {
  const canvas = button.closest('.chain').querySelector('.canvas');
  canvas.dataset.fit = 'false';
  sizeDiagram(canvas, Math.max(.05, Math.min(4, Number(canvas.querySelector('svg').dataset.scale || 1) + delta)));
}
function filterFiles(query) {
  document.querySelectorAll('#inventory tr[data-file]').forEach(row => row.hidden = !row.dataset.file.includes(query.toLowerCase()));
}
document.querySelectorAll('.canvas').forEach(canvas => {
  canvas.style.cursor = 'grab';
  let drag = null, suppressClick = false;
  canvas.addEventListener('pointerdown', event => {
    suppressClick = false;
    // 代码链接交由浏览器处理，不能捕获其指针，否则IDEA跳转会被拖动逻辑吞掉。
    if (event.target.closest('a, button, input, select, textarea')) return;
    if (event.button !== 0 || event.pointerType === 'touch') return;
    drag = {id:event.pointerId, x:event.clientX, y:event.clientY, left:canvas.scrollLeft, top:canvas.scrollTop, moved:false};
  });
  canvas.addEventListener('pointermove', event => {
    if (!drag) return;
    const dx = event.clientX - drag.x, dy = event.clientY - drag.y;
    if (!drag.moved && Math.hypot(dx, dy) < 5) return;
    drag.moved = true;
    canvas.setPointerCapture(event.pointerId);
    canvas.style.cursor = 'grabbing';
    event.preventDefault();
    canvas.scrollLeft = drag.left - dx;
    canvas.scrollTop = drag.top - dy;
  });
  const stop = () => {
    if (!drag) return;
    suppressClick = drag.moved;
    if (canvas.hasPointerCapture(drag.id)) canvas.releasePointerCapture(drag.id);
    drag = null;
    canvas.style.cursor = 'grab';
  };
  canvas.addEventListener('pointerup', stop);
  canvas.addEventListener('pointercancel', stop);
  canvas.addEventListener('pointerleave', () => { if (drag && !drag.moved) stop(); });
  canvas.addEventListener('dragstart', event => event.preventDefault());
  canvas.addEventListener('click', event => {
    if (event.target.closest('a')) { suppressClick = false; return; }
    if (suppressClick) { event.preventDefault(); event.stopPropagation(); suppressClick = false; }
  }, true);
  canvas.style.userSelect = 'none';
  canvas.dataset.fit = 'true';
  new ResizeObserver(() => { if (canvas.dataset.fit === 'true') fitCanvas(canvas); }).observe(canvas);
  canvas.closest('.chain').addEventListener('toggle', () => {
    if (canvas.dataset.fit === 'true') requestAnimationFrame(() => fitCanvas(canvas));
  });
  fitCanvas(canvas);
});

const sidebarToggle = document.querySelector('.sidebar-toggle');
if (sidebarToggle) sidebarToggle.onclick = () => {
  const collapsed = document.body.classList.toggle('sidebar-collapsed');
  sidebarToggle.textContent = collapsed ? '☰' : '收起目录';
  sidebarToggle.setAttribute('aria-expanded', String(!collapsed));
};
document.querySelectorAll('.nav-list a').forEach(a => a.addEventListener('click', () => {
  const target = document.getElementById(a.getAttribute('href').slice(1));
  if (target) target.open = true;
  document.querySelectorAll('.nav-list a').forEach(link => link.classList.toggle('active', link === a));
}));
