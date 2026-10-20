// Lee docs/data/precios.json y docs/data/alertas-evaluadas.json (espejo que
// genera el workflow) y dibuja comparativa, evolución y alertas.
const fmt = new Intl.NumberFormat("es-AR", { style: "currency", currency: "GBP" });

async function cargarJson(ruta) {
  const r = await fetch(ruta);
  if (!r.ok) throw new Error(ruta + " → HTTP " + r.status);
  return r.json();
}

function ultimoPunto(prod) { return prod.precios[prod.precios.length - 1]; }

function variacion(prod) {
  if (prod.precios.length < 2) return null;
  const a = prod.precios[prod.precios.length - 2].precio;
  const b = ultimoPunto(prod).precio;
  return a === 0 ? null : ((b - a) / a) * 100;
}

function minimo(prod) {
  return Math.min(...prod.precios.map((p) => p.precio));
}

// ---------- alertas ----------
async function renderAlertas() {
  const caja = document.getElementById("lista-alertas");
  try {
    const datos = await cargarJson("data/alertas-evaluadas.json");
    caja.textContent = "";
    if (!datos.alertas.length) {
      const p = document.createElement("p");
      p.className = "alerta-vacia";
      p.textContent =
        "Sin alertas: ningún producto bajó más del umbral configurado en " +
        "reglas/alertas.json desde la medición anterior. Cuando ocurra, la " +
        "alerta aparece acá en la próxima corrida del workflow.";
      caja.appendChild(p);
      return;
    }
    for (const a of datos.alertas) {
      const div = document.createElement("div");
      div.className = "alerta";
      div.innerHTML =
        "<strong>▼ " + a.bajada_pct + "%</strong> " + a.titulo +
        " — bajó de " + fmt.format(a.precio_anterior) + " a " +
        fmt.format(a.precio_actual) + " (umbral: " + a.umbral + "%)";
      caja.appendChild(div);
    }
  } catch {
    caja.innerHTML = '<p class="estado">No se pudieron cargar las alertas.</p>';
  }
}

// ---------- ticker ----------
function renderTicker(datos) {
  const pista = document.getElementById("ticker-pista");
  if (!pista) return;
  const items = Object.entries(datos.productos).map(([id, p]) => {
    const v = variacion(p);
    const vari = v === null ? "" :
      ' <i class="' + (v < 0 ? "v-baja" : v > 0 ? "v-sube" : "") + '">' +
      (v > 0 ? "▲" : v < 0 ? "▼" : "=") + Math.abs(v).toFixed(1) + "%</i>";
    return "<span>" + p.titulo.replace(/&/g, "&amp;").replace(/</g, "&lt;") +
      "<strong>" + fmt.format(ultimoPunto(p).precio) + "</strong>" + vari + "</span>";
  });
  // duplicado para el bucle continuo
  pista.innerHTML = items.join("") + items.join("");
}

// ---------- tabla ----------
function renderTabla(datos) {
  const caja = document.getElementById("tabla-precios");
  const productos = Object.entries(datos.productos)
    .map(([id, p]) => ({ id, ...p }))
    .sort((a, b) => ultimoPunto(a).precio - ultimoPunto(b).precio);

  const tabla = document.createElement("table");
  tabla.innerHTML =
    "<thead><tr><th>Producto</th><th class='num'>Precio</th>" +
    "<th class='num'>Variación</th><th class='num'>Mínimo</th>" +
    "<th class='num'>Puntos</th></tr></thead>";
  const cuerpo = document.createElement("tbody");
  for (const p of productos) {
    const v = variacion(p);
    const celdaV = v === null ? "—" : (v > 0 ? "+" : "") + v.toFixed(1) + "%";
    const color = v === null ? "" : v < 0 ? "color:#57d98f" : v > 0 ? "color:#ff8f7a" : "";
    const tr = document.createElement("tr");
    tr.innerHTML =
      '<td><a href="' + p.url + '">' + p.titulo + "</a></td>" +
      '<td class="num">' + fmt.format(ultimoPunto(p).precio) + "</td>" +
      '<td class="num" style="' + color + '">' + celdaV + "</td>" +
      '<td class="num">' + fmt.format(minimo(p)) + "</td>" +
      '<td class="num">' + p.precios.length + "</td>";
    cuerpo.appendChild(tr);
  }
  tabla.appendChild(cuerpo);
  caja.textContent = "";
  caja.appendChild(tabla);
}

// ---------- gráfico ----------
const select = document.getElementById("producto");
const canvas = document.getElementById("grafico");
const vacio = document.getElementById("grafico-vacio");

function dibujar(puntos) {
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth, h = 260;
  canvas.width = w * dpr; canvas.height = h * dpr;
  ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, w, h);
  if (!puntos || puntos.length === 0) { vacio.hidden = false; return; }
  vacio.hidden = true;

  const margen = { i: 52, d: 14, a: 18, b: 30 };
  const xs = puntos.map((_, i) => i);
  const ys = puntos.map((p) => p.precio);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const pad = (maxY - minY) * 0.15 || maxY * 0.05 || 1;
  const yMin = minY - pad, yMax = maxY + pad;
  const X = (i) => margen.i + (xs.length === 1 ? (w - margen.i - margen.d) / 2
    : (i / (xs.length - 1)) * (w - margen.i - margen.d));
  const Y = (v) => margen.a + (1 - (v - yMin) / (yMax - yMin)) * (h - margen.a - margen.b);

  // ejes y grilla
  ctx.strokeStyle = "#2c291f"; ctx.fillStyle = "#a89f88";
  ctx.font = "11px 'IBM Plex Mono', monospace"; ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const v = yMin + ((yMax - yMin) * i) / 4;
    const y = Y(v);
    ctx.beginPath(); ctx.moveTo(margen.i, y); ctx.lineTo(w - margen.d, y); ctx.stroke();
    ctx.fillText(fmt.format(v), 4, y + 4);
  }

  // línea
  ctx.strokeStyle = "#e8b04b"; ctx.lineWidth = 2; ctx.beginPath();
  xs.forEach((i, k) => (k === 0 ? ctx.moveTo(X(i), Y(ys[k])) : ctx.lineTo(X(i), Y(ys[k]))));
  ctx.stroke();

  // puntos
  ctx.fillStyle = "#e8b04b";
  xs.forEach((i, k) => { ctx.beginPath(); ctx.arc(X(i), Y(ys[k]), 3.2, 0, 7); ctx.fill(); });

  // etiquetas de fecha (primera y última)
  ctx.fillStyle = "#a89f88";
  const f = (ts) => ts.slice(0, 10);
  ctx.fillText(f(puntos[0].ts), margen.i, h - 8);
  if (puntos.length > 1) {
    const ult = f(puntos[puntos.length - 1].ts);
    ctx.fillText(ult, w - margen.d - ctx.measureText(ult).width, h - 8);
  }
}

async function init() {
  renderAlertas();
  try {
    const datos = await cargarJson("data/precios.json");
    renderTicker(datos);
    renderTabla(datos);
    select.textContent = "";
    for (const [id, p] of Object.entries(datos.productos)) {
      const op = document.createElement("option");
      op.value = id; op.textContent = p.titulo;
      select.appendChild(op);
    }
    const pintar = () => dibujar(datos.productos[select.value]?.precios);
    select.addEventListener("change", pintar);
    window.addEventListener("resize", pintar);
    pintar();
  } catch {
    select.innerHTML = "<option>Error al cargar datos</option>";
    document.getElementById("tabla-precios").innerHTML =
      '<p class="estado">No se pudo cargar data/precios.json. ' +
      "Corré <code>python -m scraper.main</code> para generarlo.</p>";
  }
}
init();
