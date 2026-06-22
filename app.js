/* ============================================================
   app.js
   ============================================================
   Lógica principal de la página StreamAI:
     1. Utilidades sobre el dataset (DATASET viene de dataset_embed.js)
     2. KPIs y estadísticas del hero
     3. Gráficos (Chart.js)
     4. Sistema de recomendación: filtros estructurados +
        similitud de contenido (TF-IDF + similitud de coseno,
        implementado en JS puro, equivalente a src/recommender.py)
     5. Navbar con resaltado de sección activa al scrollear

   El dataset (DATASET) es un array de objetos con las columnas:
     show_id, titulo, tipo ('Movie'|'TV Show'), plataforma, director,
     elenco, pais, fecha_agregado, anio_lanzamiento, clasificacion,
     duracion, genero, descripcion, puntaje
============================================================ */

// ============================================================
// 1. UTILIDADES SOBRE EL DATASET
// ============================================================

/** Traducción de tipo interno -> etiqueta visible */
const TIPO_LABEL = { "Movie": "Película", "TV Show": "Serie" };

/** Calcula el promedio de puntaje de un array de ítems */
function promedio(arr) {
  if (!arr.length) return 0;
  return (arr.reduce((a, b) => a + b.puntaje, 0) / arr.length);
}

/** Cuenta ocurrencias de un campo en un array de ítems */
function contarPor(arr, campo) {
  return arr.reduce((acc, item) => {
    acc[item[campo]] = (acc[item[campo]] || 0) + 1;
    return acc;
  }, {});
}

/** Devuelve la clave con el valor más alto de un objeto */
function maxKey(obj) {
  return Object.entries(obj).sort((a, b) => b[1] - a[1])[0][0];
}

// ============================================================
// 2. KPIs Y STATS DEL HERO
// ============================================================

function actualizarHeroStats() {
  document.getElementById('stat-total').textContent = DATASET.length;
  document.getElementById('stat-avg').textContent = promedio(DATASET).toFixed(1);
  const generos = new Set(DATASET.map(d => d.genero));
  document.getElementById('stat-genres').textContent = generos.size;

  // Plataformas con conteo real
  const platCounts = contarPor(DATASET, 'plataforma');
  const platformsGrid = document.getElementById('platforms-grid');
  const PLAT_CLASS = {
    "Netflix": "netflix", "Disney+": "disney", "Prime Video": "prime",
    "HBO Max": "hbo", "Apple TV+": "apple"
  };
  const order = ["Netflix", "Disney+", "Prime Video", "HBO Max", "Apple TV+"];

  platformsGrid.innerHTML = order.map(p => `
    <div class="platform-badge ${PLAT_CLASS[p]}">
      <div class="platform-dot"></div> ${p}
      <span class="platform-count">${platCounts[p] || 0}</span>
    </div>
  `).join('');
}

function renderKPIs() {
  const total = DATASET.length;
  const avg = promedio(DATASET);
  const xGenero = contarPor(DATASET, 'genero');
  const topGenero = maxKey(xGenero);

  // Plataforma con mejor promedio
  const plataformas = [...new Set(DATASET.map(d => d.plataforma))];
  let mejorPlat = '', mejorAvg = -1;
  plataformas.forEach(p => {
    const items = DATASET.filter(d => d.plataforma === p);
    const av = promedio(items);
    if (av > mejorAvg) { mejorAvg = av; mejorPlat = p; }
  });

  const nSeries = DATASET.filter(d => d.tipo === 'TV Show').length;
  const nPeliculas = DATASET.filter(d => d.tipo === 'Movie').length;

  document.getElementById('kpi-total').textContent = total;
  document.getElementById('kpi-total-sub').textContent = `${nSeries} series · ${nPeliculas} películas`;
  document.getElementById('kpi-avg').textContent = avg.toFixed(2);
  document.getElementById('kpi-genre').textContent = topGenero;
  document.getElementById('kpi-genre-sub').textContent = `${xGenero[topGenero]} títulos`;
  document.getElementById('kpi-platform').textContent = mejorPlat;
  document.getElementById('kpi-platform-sub').textContent = `Promedio: ${mejorAvg.toFixed(2)} ⭐`;
}

// ============================================================
// 3. GRÁFICOS (Chart.js)
// ============================================================

function renderCharts() {
  const COLORS = ['#E50914', '#0063E5', '#00A8E1', '#5822A0', '#A2AAAD', '#F5A623', '#7B2FBE', '#4ade80', '#00B4D8', '#f472b6', '#facc15', '#94a3b8'];

  // --- Gráfico 1: títulos por plataforma (doughnut) ---
  const platData = contarPor(DATASET, 'plataforma');
  new Chart(document.getElementById('chartPlatform'), {
    type: 'doughnut',
    data: {
      labels: Object.keys(platData),
      datasets: [{
        data: Object.values(platData),
        backgroundColor: COLORS,
        borderColor: '#13131A',
        borderWidth: 3,
        hoverOffset: 6
      }]
    },
    options: {
      plugins: {
        legend: { position: 'bottom', labels: { color: '#8888A8', font: { size: 11 }, padding: 14 } }
      },
      responsive: true
    }
  });

  // --- Gráfico 2: distribución por género (bar horizontal) ---
  const genData = contarPor(DATASET, 'genero');
  const sortedGen = Object.entries(genData).sort((a, b) => b[1] - a[1]);
  new Chart(document.getElementById('chartGenre'), {
    type: 'bar',
    data: {
      labels: sortedGen.map(e => e[0]),
      datasets: [{
        data: sortedGen.map(e => e[1]),
        backgroundColor: COLORS,
        borderRadius: 6,
        borderSkipped: false
      }]
    },
    options: {
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: '#8888A8', font: { size: 10 } }, grid: { color: '#2a2a45' } },
        y: { ticks: { color: '#F0F0F0', font: { size: 10 } }, grid: { display: false } }
      },
      responsive: true
    }
  });

  // --- Gráfico 3: evolución por año (line) ---
  const añoData = contarPor(DATASET, 'anio_lanzamiento');
  const sortedAño = Object.entries(añoData)
    .map(([k, v]) => [parseInt(k), v])
    .sort((a, b) => a[0] - b[0]);

  new Chart(document.getElementById('chartYear'), {
    type: 'line',
    data: {
      labels: sortedAño.map(e => e[0]),
      datasets: [{
        label: 'Títulos',
        data: sortedAño.map(e => e[1]),
        borderColor: '#7B2FBE',
        backgroundColor: 'rgba(123,47,190,0.12)',
        pointBackgroundColor: '#E50914',
        pointRadius: 3,
        tension: 0.35,
        fill: true
      }]
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: '#8888A8', font: { size: 10 } }, grid: { color: '#2a2a45' } },
        y: { ticks: { color: '#8888A8', font: { size: 10 } }, grid: { color: '#2a2a45' } }
      },
      responsive: true
    }
  });
}

// ============================================================
// 4. SISTEMA DE RECOMENDACIÓN
// ============================================================

/* ----------------------------------------------------------
   4.1 Motor de similitud de contenido (TF-IDF + coseno)
   ----------------------------------------------------------
   Implementación liviana de TF-IDF en JS puro, equivalente al
   enfoque usado en src/recommender.py (TfidfVectorizer +
   cosine_similarity de scikit-learn). Se vectoriza la
   concatenación de "descripcion" + "genero" (con más peso)
   para cada título, y se calcula la similitud de coseno entre
   vectores para encontrar contenido parecido.
---------------------------------------------------------- */

let TFIDF_VECTORS = null;
let VOCAB = null;

function tokenizar(texto) {
  return texto.toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '') // quitar acentos
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length > 2);
}

function construirEmbeddings() {
  // Corpus: descripción + género (repetido para dar más peso al género)
  const docs = DATASET.map(d => tokenizar(`${d.descripcion} ${d.genero} ${d.genero}`));

  // Vocabulario global
  const df = {}; // document frequency
  docs.forEach(tokens => {
    new Set(tokens).forEach(t => { df[t] = (df[t] || 0) + 1; });
  });

  VOCAB = Object.keys(df);
  const vocabIndex = {};
  VOCAB.forEach((w, i) => vocabIndex[w] = i);

  const N = docs.length;

  TFIDF_VECTORS = docs.map(tokens => {
    const tf = {};
    tokens.forEach(t => { tf[t] = (tf[t] || 0) + 1; });

    const vec = new Float32Array(VOCAB.length);
    Object.entries(tf).forEach(([term, freq]) => {
      const idf = Math.log((N + 1) / (df[term] + 1)) + 1;
      vec[vocabIndex[term]] = freq * idf;
    });

    // Normalizar (norma L2) para que el producto punto = similitud de coseno
    let norm = 0;
    for (let i = 0; i < vec.length; i++) norm += vec[i] * vec[i];
    norm = Math.sqrt(norm) || 1;
    for (let i = 0; i < vec.length; i++) vec[i] /= norm;

    return vec;
  });
}

function similitudCoseno(vecA, vecB) {
  let dot = 0;
  for (let i = 0; i < vecA.length; i++) dot += vecA[i] * vecB[i];
  return dot; // ambos vectores ya están normalizados -> dot = coseno
}

/**
 * Devuelve los `topN` títulos más similares a `titulo` (búsqueda
 * parcial, insensible a mayúsculas) según similitud de coseno sobre
 * los embeddings TF-IDF de descripción + género.
 */
function similares(titulo, topN = 5) {
  const idx = DATASET.findIndex(d => d.titulo.toLowerCase().includes(titulo.toLowerCase()));
  if (idx === -1) return null;

  const sims = TFIDF_VECTORS.map((v, i) => ({ i, sim: similitudCoseno(TFIDF_VECTORS[idx], v) }));
  sims.sort((a, b) => b.sim - a.sim);

  const top = sims.filter(s => s.i !== idx).slice(0, topN);
  return {
    referencia: DATASET[idx],
    resultados: top.map(s => ({ ...DATASET[s.i], similitud: s.sim }))
  };
}

/* ----------------------------------------------------------
   4.2 Filtrado estructurado
---------------------------------------------------------- */
function filtrarDataset({ genero = '', plataforma = '', tipo = '', puntajeMin = 0 } = {}) {
  let resultado = DATASET.filter(item => {
    if (genero && item.genero !== genero) return false;
    if (plataforma && item.plataforma !== plataforma) return false;
    if (tipo && item.tipo !== tipo) return false;
    if (item.puntaje < puntajeMin) return false;
    return true;
  });
  resultado.sort((a, b) => b.puntaje - a.puntaje);
  return resultado;
}

/* ----------------------------------------------------------
   4.3 Render de tarjetas de resultados
---------------------------------------------------------- */
function renderCard(item, extra = {}) {
  const simTag = extra.similitud != null
    ? `<span class="tag tag-sim">Similitud ${(extra.similitud * 100).toFixed(0)}%</span>`
    : '';
  return `
    <div class="content-card">
      <div class="content-card-header">
        <div class="content-title">${item.titulo}</div>
        <div class="content-score">⭐ ${item.puntaje.toFixed(1)}</div>
      </div>
      <div class="content-meta">
        <span class="tag tag-platform">${item.plataforma}</span>
        <span class="tag tag-genre">${item.genero}</span>
        <span class="tag tag-type">${TIPO_LABEL[item.tipo] || item.tipo}</span>
        <span class="tag tag-year">${item.anio_lanzamiento}</span>
        ${simTag}
      </div>
      <p class="content-desc">${item.descripcion}</p>
      <p class="content-extra">📍 ${item.pais} · 🎬 ${item.director || 'N/D'}</p>
    </div>
  `;
}

function filtrar() {
  const genero = document.getElementById('f-genre').value;
  const plataforma = document.getElementById('f-platform').value;
  const tipo = document.getElementById('f-type').value;
  const puntajeMin = parseFloat(document.getElementById('f-score').value) || 0;

  const resultados = filtrarDataset({ genero, plataforma, tipo, puntajeMin }).slice(0, 60);

  pintarResultados(resultados, resultados.length);
}

function resetFiltros() {
  document.getElementById('f-genre').value = '';
  document.getElementById('f-platform').value = '';
  document.getElementById('f-type').value = '';
  document.getElementById('f-score').value = '';
  document.getElementById('f-similar').value = '';
  filtrar();
}

function buscarSimilares() {
  const titulo = document.getElementById('f-similar').value.trim();
  if (!titulo) { filtrar(); return; }

  const res = similares(titulo, 12);
  const grid = document.getElementById('results-grid');
  const count = document.getElementById('results-count');

  if (!res) {
    grid.innerHTML = `<div class="no-results" style="grid-column:1/-1"><span>🔍</span>No encontramos "${titulo}" en el catálogo.</div>`;
    count.textContent = 'Sin resultados';
    return;
  }

  count.innerHTML = `Títulos similares a <strong>"${res.referencia.titulo}"</strong> (${res.resultados.length} resultados, motor TF-IDF)`;
  grid.innerHTML = res.resultados.map(r => renderCard(r, { similitud: r.similitud })).join('');
}

function pintarResultados(resultados, totalCount) {
  const grid = document.getElementById('results-grid');
  const count = document.getElementById('results-count');

  if (!resultados.length) {
    grid.innerHTML = `<div class="no-results" style="grid-column:1/-1"><span>🎭</span>No encontramos títulos con esos filtros. Probá con otras opciones.</div>`;
    count.textContent = 'Sin resultados';
  } else {
    grid.innerHTML = resultados.map(r => renderCard(r)).join('');
    count.textContent = `${totalCount} título${totalCount !== 1 ? 's' : ''} encontrado${totalCount !== 1 ? 's' : ''} (mostrando hasta 60)`;
  }
}

/** Llena el select de géneros dinámicamente desde el dataset */
function poblarFiltroGeneros() {
  const select = document.getElementById('f-genre');
  const generos = [...new Set(DATASET.map(d => d.genero))].sort();
  generos.forEach(g => {
    const opt = document.createElement('option');
    opt.value = g;
    opt.textContent = g;
    select.appendChild(opt);
  });
}

// ============================================================
// 5. NAVBAR · marcar link activo al scrollear
// ============================================================
function setActive(el) {
  document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
  el.classList.add('active');
}

function initNavObserver() {
  const sections = ['home', 'dashboard', 'recomendar'];
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.id;
        document.querySelectorAll('.nav-links a').forEach(a => {
          a.classList.toggle('active', a.getAttribute('href') === `#${id}`);
        });
      }
    });
  }, { threshold: 0.4 });

  sections.forEach(id => {
    const el = document.getElementById(id);
    if (el) observer.observe(el);
  });
}

// ============================================================
// INICIALIZACIÓN
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  // Construir embeddings TF-IDF (puede tardar un instante con 800 items)
  construirEmbeddings();

  actualizarHeroStats();
  renderKPIs();
  renderCharts();
  poblarFiltroGeneros();
  filtrar();
  initNavObserver();

  // Ocultar overlay de carga
  document.getElementById('loading-overlay').classList.add('hidden');
});
