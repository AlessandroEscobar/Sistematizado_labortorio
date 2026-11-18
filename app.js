// Estado global del Informe de Laboratorio UNJBG
const STORAGE_KEY = 'unjbg_fisica_informe_v1';

const defaultState = {
  facultad: 'Facultad de Ingeniería (FAIN)',
  escuela: 'Ingeniería Ambiental',
  laboratorio: 'FÍSICA',
  tituloPractica: '',
  autores: [
    { nombre: '', codigo: '' }
  ],
  grupo: '',
  horario: '',
  docente: '',
  fechaEjecucion: '',
  fechaEntregaTexto: 'Tacna, 18 de noviembre de 2026',
  resumen: '',
  introduccion: '',
  objetivoGeneral: '',
  objetivosEspecificos: [''],
  materiales: [
    { nombre: '', marca: '', rango: '', apreciacion: '' }
  ],
  procedimiento: '',
  figura1DataUrl: '',
  figura1Leyenda: 'Esquema del montaje experimental empleado en la práctica.',
  tablasCrudas: [
    {
      titulo: 'Mediciones directas obtenidas en laboratorio',
      columnas: ['Ensayo n', 'Magnitud 1 (unidad)', 'Magnitud 2 (unidad)'],
      filas: [
        ['1', '', ''],
        ['2', '', ''],
        ['3', '', '']
      ]
    }
  ],
  includeAutoChart: true,
  chartTitle: 'Relación experimental entre variables físicas',
  chartFootnote: 'Fuente: Elaboración propia a partir de los datos experimentales de laboratorio.',
  axisXLabel: 'Variable independiente X (unidad)',
  axisYLabel: 'Variable dependiente Y (unidad)',
  theoreticalSlope: '',
  xyPairsInput: '',
  resultadosTexto: '',
  discusion: '',
  conclusiones: [''],
  fuentesError: '',
  reflexion: '',
  referencias: [
    'M. Alonso, E. J. Finn, Física Vol. I: Mecánica, Fondo Educativo Interamericano, México, 1986.'
  ],
  cuestionario: [
    { pregunta: '', respuesta: '' }
  ],
  apendices: ''
};

let state = loadState();
let lastRegression = null;

function loadState() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      return { ...structuredClone(defaultState), ...JSON.parse(saved) };
    }
  } catch (e) {
    console.warn('No se pudo leer el estado guardado:', e);
  }
  return structuredClone(defaultState);
}

function saveState() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    const status = document.getElementById('autosaveStatus');
    if (status) {
      const now = new Date();
      status.textContent = `Guardado automático (${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })})`;
    }
  } catch (e) {
    console.warn('Error al guardar en localStorage:', e);
  }
}

// Utilidad de escape HTML
function esc(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// Formatear fecha ISO a español
function formatDateSpanish(isoStr) {
  if (!isoStr) return '[ ]';
  const parts = isoStr.split('-');
  if (parts.length !== 3) return isoStr;
  const meses = [
    'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
    'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
  ];
  const day = parseInt(parts[2], 10);
  const monthName = meses[parseInt(parts[1], 10) - 1] || parts[1];
  return `${day} de ${monthName} de ${parts[0]}`;
}

// Enlazar inputs simples con el estado
function bindSimpleFields() {
  const simpleIds = [
    'facultad', 'escuela', 'laboratorio', 'tituloPractica',
    'grupo', 'horario', 'docente', 'fechaEjecucion', 'fechaEntregaTexto',
    'resumen', 'introduccion', 'objetivoGeneral', 'procedimiento',
    'figura1Leyenda', 'chartTitle', 'chartFootnote', 'axisXLabel',
    'axisYLabel', 'theoreticalSlope', 'xyPairsInput', 'resultadosTexto',
    'discusion', 'fuentesError', 'reflexion', 'apendices'
  ];

  simpleIds.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.value = state[id] || '';
    el.addEventListener('input', () => {
      state[id] = el.value;
      if (id === 'fechaEjecucion' && el.value) {
        // Actualizar sugerencia de fecha de entrega manteniendo año 2026 si aplica
        const formatted = formatDateSpanish(el.value);
        if (!state.fechaEntregaTexto || state.fechaEntregaTexto.startsWith('Tacna,')) {
          state.fechaEntregaTexto = `Tacna, ${formatted}`;
          document.getElementById('fechaEntregaTexto').value = state.fechaEntregaTexto;
        }
      }
      updateResumenCounter();
      computeRegressionAndChart();
      renderPreview();
      saveState();
    });
  });

  const chkChart = document.getElementById('includeAutoChart');
  chkChart.checked = Boolean(state.includeAutoChart);
  chkChart.addEventListener('change', () => {
    state.includeAutoChart = chkChart.checked;
    renderPreview();
    saveState();
  });
}

// Contador de líneas estimadas del Resumen (meta: ~15 líneas en A4)
function updateResumenCounter() {
  const text = (state.resumen || '').trim();
  const badge = document.getElementById('resumenCounter');
  if (!badge) return;
  if (!text) {
    badge.textContent = '0 líneas estimadas (0 palabras)';
    badge.className = 'counter-badge';
    return;
  }
  const words = text.split(/\s+/).filter(Boolean).length;
  // En hoja A4 con márgenes 2.5cm/2.0cm y Times New Roman 11.5pt caben ~88 caracteres por línea
  const lines = Math.max(1, Math.ceil(text.length / 88));
  badge.textContent = `~${lines} líneas estimadas (${words} palabras) — Meta: ~15 líneas`;
  if (lines >= 13 && lines <= 17) {
    badge.className = 'counter-badge optimal';
  } else {
    badge.className = 'counter-badge warning';
  }
}

// Renderizado de listas dinámicas en el editor
function renderAuthorsEditor() {
  const container = document.getElementById('authorsContainer');
  container.innerHTML = '';
  state.autores.forEach((autor, idx) => {
    const row = document.createElement('div');
    row.className = 'dynamic-row';
    row.innerHTML = `
      <input type="text" placeholder="Apellidos y Nombres" value="${esc(autor.nombre)}" data-idx="${idx}" data-field="nombre" style="flex: 2;" />
      <input type="text" placeholder="Código (ej. 2024-119023)" value="${esc(autor.codigo)}" data-idx="${idx}" data-field="codigo" style="flex: 1;" />
      ${state.autores.length > 1 ? `<button type="button" class="btn-text-danger" data-del-author="${idx}">✕</button>` : ''}
    `;
    container.appendChild(row);
  });

  container.querySelectorAll('input').forEach(inp => {
    inp.addEventListener('input', () => {
      const i = Number(inp.dataset.idx);
      state.autores[i][inp.dataset.field] = inp.value;
      renderPreview();
      saveState();
    });
  });

  container.querySelectorAll('[data-del-author]').forEach(btn => {
    btn.addEventListener('click', () => {
      state.autores.splice(Number(btn.dataset.delAuthor), 1);
      renderAuthorsEditor();
      renderPreview();
      saveState();
    });
  });
}

function renderObjetivosEspEditor() {
  const container = document.getElementById('objetivosEspContainer');
  container.innerHTML = '';
  state.objetivosEspecificos.forEach((obj, idx) => {
    const row = document.createElement('div');
    row.className = 'dynamic-row';
    row.innerHTML = `
      <input type="text" placeholder="Objetivo específico ${idx + 1}..." value="${esc(obj)}" data-idx="${idx}" />
      ${state.objetivosEspecificos.length > 1 ? `<button type="button" class="btn-text-danger" data-del-obj="${idx}">✕</button>` : ''}
    `;
    container.appendChild(row);
  });

  container.querySelectorAll('input').forEach(inp => {
    inp.addEventListener('input', () => {
      state.objetivosEspecificos[Number(inp.dataset.idx)] = inp.value;
      renderPreview();
      saveState();
    });
  });

  container.querySelectorAll('[data-del-obj]').forEach(btn => {
    btn.addEventListener('click', () => {
      state.objetivosEspecificos.splice(Number(btn.dataset.delObj), 1);
      renderObjetivosEspEditor();
      renderPreview();
      saveState();
    });
  });
}

function renderMaterialsEditor() {
  const container = document.getElementById('materialsContainer');
  container.innerHTML = '';
  state.materiales.forEach((mat, idx) => {
    const item = document.createElement('div');
    item.className = 'dynamic-card-item';
    item.innerHTML = `
      <div class="form-grid-2">
        <input type="text" placeholder="Equipo / Material / Reactivo" value="${esc(mat.nombre)}" data-idx="${idx}" data-field="nombre" />
        <input type="text" placeholder="Marca / Modelo (ej. Pasco / Vernier)" value="${esc(mat.marca)}" data-idx="${idx}" data-field="marca" />
      </div>
      <div class="form-grid-2">
        <input type="text" placeholder="Rango de medición (ej. 0 - 150 mm)" value="${esc(mat.rango)}" data-idx="${idx}" data-field="rango" />
        <div style="display:flex; gap:0.5rem; align-items:center;">
          <input type="text" placeholder="Apreciación (ej. ± 0.05 mm)" value="${esc(mat.apreciacion)}" data-idx="${idx}" data-field="apreciacion" />
          ${state.materiales.length > 1 ? `<button type="button" class="btn-text-danger" data-del-mat="${idx}">✕</button>` : ''}
        </div>
      </div>
    `;
    container.appendChild(item);
  });

  container.querySelectorAll('input').forEach(inp => {
    inp.addEventListener('input', () => {
      state.materiales[Number(inp.dataset.idx)][inp.dataset.field] = inp.value;
      renderPreview();
      saveState();
    });
  });

  container.querySelectorAll('[data-del-mat]').forEach(btn => {
    btn.addEventListener('click', () => {
      state.materiales.splice(Number(btn.dataset.delMat), 1);
      renderMaterialsEditor();
      renderPreview();
      saveState();
    });
  });
}

function renderRawTablesEditor() {
  const container = document.getElementById('rawTablesContainer');
  container.innerHTML = '';
  state.tablasCrudas.forEach((tbl, tIdx) => {
    const card = document.createElement('div');
    card.className = 'dynamic-card-item';

    const headerHtml = tbl.columnas.map((col, cIdx) => `
      <th>
        <input type="text" value="${esc(col)}" data-t="${tIdx}" data-col="${cIdx}" style="font-weight:bold; text-align:center;" />
      </th>
    `).join('');

    const rowsHtml = tbl.filas.map((fila, rIdx) => `
      <tr>
        ${fila.map((celda, cIdx) => `
          <td>
            <input type="text" value="${esc(celda)}" data-t="${tIdx}" data-r="${rIdx}" data-c="${cIdx}" style="text-align:center;" />
          </td>
        `).join('')}
        <td style="width:28px; text-align:center;">
          ${tbl.filas.length > 1 ? `<button type="button" class="btn-text-danger" data-del-row="${tIdx}:${rIdx}">✕</button>` : ''}
        </td>
      </tr>
    `).join('');

    card.innerHTML = `
      <div class="toolbar-inline">
        <strong>Tabla ${tIdx + 1}:</strong>
        <input type="text" value="${esc(tbl.titulo)}" data-t-title="${tIdx}" placeholder="Leyenda de la Tabla ${tIdx + 1}" style="flex:1;" />
        ${state.tablasCrudas.length > 1 ? `<button type="button" class="btn-text-danger" data-del-table="${tIdx}">Eliminar tabla</button>` : ''}
      </div>
      <div style="overflow-x:auto;">
        <table class="doc-table" style="margin:4px 0;">
          <thead><tr>${headerHtml}<th></th></tr></thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      </div>
      <div style="display:flex; gap:0.5rem;">
        <button type="button" class="btn btn-sm btn-outline" data-add-row="${tIdx}">+ Fila</button>
        <button type="button" class="btn btn-sm btn-outline" data-add-col="${tIdx}">+ Columna</button>
      </div>
    `;
    container.appendChild(card);
  });

  container.querySelectorAll('[data-t-title]').forEach(inp => {
    inp.addEventListener('input', () => {
      state.tablasCrudas[Number(inp.dataset.tTitle)].titulo = inp.value;
      renderPreview();
      saveState();
    });
  });

  container.querySelectorAll('[data-col]').forEach(inp => {
    inp.addEventListener('input', () => {
      state.tablasCrudas[Number(inp.dataset.t)].columnas[Number(inp.dataset.col)] = inp.value;
      renderPreview();
      saveState();
    });
  });

  container.querySelectorAll('[data-r]').forEach(inp => {
    inp.addEventListener('input', () => {
      state.tablasCrudas[Number(inp.dataset.t)].filas[Number(inp.dataset.r)][Number(inp.dataset.c)] = inp.value;
      renderPreview();
      saveState();
    });
  });

  container.querySelectorAll('[data-add-row]').forEach(btn => {
    btn.addEventListener('click', () => {
      const t = Number(btn.dataset.addRow);
      const cols = state.tablasCrudas[t].columnas.length;
      const newRow = Array.from({ length: cols }, (_, i) => i === 0 ? String(state.tablasCrudas[t].filas.length + 1) : '');
      state.tablasCrudas[t].filas.push(newRow);
      renderRawTablesEditor();
      renderPreview();
      saveState();
    });
  });

  container.querySelectorAll('[data-add-col]').forEach(btn => {
    btn.addEventListener('click', () => {
      const t = Number(btn.dataset.addCol);
      state.tablasCrudas[t].columnas.push(`Magnitud ${state.tablasCrudas[t].columnas.length} (u)`);
      state.tablasCrudas[t].filas.forEach(r => r.push(''));
      renderRawTablesEditor();
      renderPreview();
      saveState();
    });
  });

  container.querySelectorAll('[data-del-row]').forEach(btn => {
    btn.addEventListener('click', () => {
      const [t, r] = btn.dataset.delRow.split(':').map(Number);
      state.tablasCrudas[t].filas.splice(r, 1);
      renderRawTablesEditor();
      renderPreview();
      saveState();
    });
  });

  container.querySelectorAll('[data-del-table]').forEach(btn => {
    btn.addEventListener('click', () => {
      state.tablasCrudas.splice(Number(btn.dataset.delTable), 1);
      renderRawTablesEditor();
      renderPreview();
      saveState();
    });
  });
}

function renderConclusionsEditor() {
  const container = document.getElementById('conclusionsContainer');
  container.innerHTML = '';
  state.conclusiones.forEach((conc, idx) => {
    const row = document.createElement('div');
    row.className = 'dynamic-row';
    row.innerHTML = `
      <textarea rows="2" placeholder="Conclusión ${idx + 1} sustentada en los resultados..." data-idx="${idx}">${esc(conc)}</textarea>
      ${state.conclusiones.length > 1 ? `<button type="button" class="btn-text-danger" data-del-conc="${idx}">✕</button>` : ''}
    `;
    container.appendChild(row);
  });

  container.querySelectorAll('textarea').forEach(ta => {
    ta.addEventListener('input', () => {
      state.conclusiones[Number(ta.dataset.idx)] = ta.value;
      renderPreview();
      saveState();
    });
  });

  container.querySelectorAll('[data-del-conc]').forEach(btn => {
    btn.addEventListener('click', () => {
      state.conclusiones.splice(Number(btn.dataset.delConc), 1);
      renderConclusionsEditor();
      renderPreview();
      saveState();
    });
  });
}

function renderReferencesEditor() {
  const container = document.getElementById('referencesContainer');
  container.innerHTML = '';
  state.referencias.forEach((ref, idx) => {
    const row = document.createElement('div');
    row.className = 'dynamic-row';
    row.innerHTML = `
      <strong style="min-width:28px;">[${idx + 1}]</strong>
      <input type="text" placeholder="Autor(es), Título, Editorial, Ciudad, Año." value="${esc(ref)}" data-idx="${idx}" />
      ${state.referencias.length > 1 ? `<button type="button" class="btn-text-danger" data-del-ref="${idx}">✕</button>` : ''}
    `;
    container.appendChild(row);
  });

  container.querySelectorAll('input').forEach(inp => {
    inp.addEventListener('input', () => {
      state.referencias[Number(inp.dataset.idx)] = inp.value;
      renderPreview();
      saveState();
    });
  });

  container.querySelectorAll('[data-del-ref]').forEach(btn => {
    btn.addEventListener('click', () => {
      state.referencias.splice(Number(btn.dataset.delRef), 1);
      renderReferencesEditor();
      renderPreview();
      saveState();
    });
  });
}

function renderQuestionsEditor() {
  const container = document.getElementById('questionsContainer');
  container.innerHTML = '';
  state.cuestionario.forEach((item, idx) => {
    const box = document.createElement('div');
    box.className = 'dynamic-card-item';
    box.innerHTML = `
      <div class="toolbar-inline">
        <strong>Pregunta ${idx + 1}</strong>
        ${state.cuestionario.length > 1 ? `<button type="button" class="btn-text-danger" data-del-q="${idx}">✕</button>` : ''}
      </div>
      <input type="text" placeholder="Enunciado de la pregunta del docente..." value="${esc(item.pregunta)}" data-idx="${idx}" data-field="pregunta" />
      <textarea rows="3" placeholder="Respuesta fundamentada..." data-idx="${idx}" data-field="respuesta">${esc(item.respuesta)}</textarea>
    `;
    container.appendChild(box);
  });

  container.querySelectorAll('input, textarea').forEach(el => {
    el.addEventListener('input', () => {
      state.cuestionario[Number(el.dataset.idx)][el.dataset.field] = el.value;
      renderPreview();
      saveState();
    });
  });

  container.querySelectorAll('[data-del-q]').forEach(btn => {
    btn.addEventListener('click', () => {
      state.cuestionario.splice(Number(btn.dataset.delQ), 1);
      renderQuestionsEditor();
      renderPreview();
      saveState();
    });
  });
}

// Cálculo de Mínimos Cuadrados y Generación de Gráfica Científica en Canvas
function parseXYPairs(raw) {
  const lines = (raw || '').split(/\r?\n/).map(l => l.trim()).filter(Boolean);
  const points = [];
  for (const line of lines) {
    const parts = line.split(/[,;\t\s]+/).map(Number);
    if (parts.length >= 2 && Number.isFinite(parts[0]) && Number.isFinite(parts[1])) {
      points.push({ x: parts[0], y: parts[1] });
    }
  }
  return points;
}

function computeRegressionAndChart() {
  const points = parseXYPairs(state.xyPairsInput);
  const summaryBox = document.getElementById('regressionSummaryBox');
  const canvas = document.getElementById('scientificChartCanvas');
  const ctx = canvas.getContext('2d');

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  if (points.length < 2) {
    lastRegression = null;
    summaryBox.innerHTML = 'Ingrese al menos 2 pares de datos (X, Y) para calcular pendiente, incerteza y R².';
    ctx.fillStyle = '#64748b';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Gráfica científica pendiente de datos (X, Y)', canvas.width / 2, canvas.height / 2);
    return;
  }

  const n = points.length;
  const sumX = points.reduce((acc, p) => acc + p.x, 0);
  const sumY = points.reduce((acc, p) => acc + p.y, 0);
  const meanX = sumX / n;
  const meanY = sumY / n;

  let sxx = 0, syy = 0, sxy = 0;
  for (const p of points) {
    sxx += (p.x - meanX) ** 2;
    syy += (p.y - meanY) ** 2;
    sxy += (p.x - meanX) * (p.y - meanY);
  }

  if (sxx === 0) {
    lastRegression = null;
    summaryBox.textContent = 'Error: Todos los valores de X son iguales; no se puede calcular pendiente.';
    return;
  }

  const m = sxy / sxx;
  const b = meanY - m * meanX;
  const r2 = syy > 0 ? (sxy ** 2) / (sxx * syy) : 1;

  // Error estándar de la pendiente y del intercepto (para n > 2)
  let deltaM = 0;
  let deltaB = 0;
  if (n > 2) {
    const sse = points.reduce((acc, p) => acc + (p.y - (m * p.x + b)) ** 2, 0);
    const sYx = Math.sqrt(sse / (n - 2));
    deltaM = sYx / Math.sqrt(sxx);
    deltaB = sYx * Math.sqrt((1 / n) + (meanX ** 2) / sxx);
  }

  let errorPctHtml = '';
  const theo = parseFloat(state.theoreticalSlope);
  if (Number.isFinite(theo) && theo !== 0) {
    const errPct = (Math.abs(m - theo) / Math.abs(theo)) * 100;
    errorPctHtml = ` | <strong>Error porcentual (E%):</strong> ${errPct.toFixed(2)}%`;
  }

  lastRegression = { n, m, b, deltaM, deltaB, r2, points };

  summaryBox.innerHTML = `
    <strong>Ecuación ajustada:</strong> y = (${m.toFixed(4)} ± ${deltaM.toFixed(4)})x + (${b.toFixed(4)} ± ${deltaB.toFixed(4)})<br/>
    <strong>Coeficiente R²:</strong> ${r2.toFixed(5)} | <strong>N° datos:</strong> ${n}${errorPctHtml}
  `;

  // Dibujar Gráfica Científica
  drawScientificPlot(ctx, canvas.width, canvas.height, points, m, b, r2);
}

function drawScientificPlot(ctx, W, H, points, m, b, r2) {
  const padLeft = 75;
  const padRight = 35;
  const padTop = 48;
  const padBottom = 65;
  const plotW = W - padLeft - padRight;
  const plotH = H - padTop - padBottom;

  const xs = points.map(p => p.x);
  const ys = points.map(p => p.y);
  let minX = Math.min(...xs);
  let maxX = Math.max(...xs);
  let minY = Math.min(...ys);
  let maxY = Math.max(...ys);

  const spanX = (maxX - minX) || 1;
  const spanY = (maxY - minY) || 1;
  minX -= spanX * 0.08;
  maxX += spanX * 0.08;
  minY -= spanY * 0.1;
  maxY += spanY * 0.1;

  const toCanvasX = x => padLeft + ((x - minX) / (maxX - minX)) * plotW;
  const toCanvasY = y => padTop + plotH - ((y - minY) / (maxY - minY)) * plotH;

  // Cuadrícula suave y escalas
  ctx.strokeStyle = '#e2e8f0';
  ctx.lineWidth = 1;
  ctx.fillStyle = '#1e293b';
  ctx.font = '11px Times New Roman, serif';

  const ticks = 5;
  for (let i = 0; i <= ticks; i++) {
    const gx = padLeft + (plotW * i) / ticks;
    const valX = minX + ((maxX - minX) * i) / ticks;
    ctx.beginPath();
    ctx.moveTo(gx, padTop);
    ctx.lineTo(gx, padTop + plotH);
    ctx.stroke();
    ctx.textAlign = 'center';
    ctx.fillText(valX.toFixed(2), gx, padTop + plotH + 18);

    const gy = padTop + plotH - (plotH * i) / ticks;
    const valY = minY + ((maxY - minY) * i) / ticks;
    ctx.beginPath();
    ctx.moveTo(padLeft, gy);
    ctx.lineTo(padLeft + plotW, gy);
    ctx.stroke();
    ctx.textAlign = 'right';
    ctx.fillText(valY.toFixed(2), padLeft - 8, gy + 4);
  }

  // Marco del área de gráfico
  ctx.strokeStyle = '#0f172a';
  ctx.lineWidth = 1.5;
  ctx.strokeRect(padLeft, padTop, plotW, plotH);

  // Título de la gráfica
  ctx.fillStyle = '#000000';
  ctx.font = 'bold 14px Times New Roman, serif';
  ctx.textAlign = 'center';
  ctx.fillText(state.chartTitle || 'Gráfica Experimental', W / 2, 24);

  // Etiqueta Eje X
  ctx.font = 'bold 12px Times New Roman, serif';
  ctx.fillText(state.axisXLabel || 'Eje X', padLeft + plotW / 2, H - 15);

  // Etiqueta Eje Y (rotada)
  ctx.save();
  ctx.translate(20, padTop + plotH / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText(state.axisYLabel || 'Eje Y', 0, 0);
  ctx.restore();

  // Recta de ajuste por mínimos cuadrados
  const lineX1 = minX;
  const lineY1 = m * lineX1 + b;
  const lineX2 = maxX;
  const lineY2 = m * lineX2 + b;

  ctx.strokeStyle = '#b91c1c';
  ctx.lineWidth = 2;
  ctx.setLineDash([6, 4]);
  ctx.beginPath();
  ctx.moveTo(toCanvasX(lineX1), toCanvasY(lineY1));
  ctx.lineTo(toCanvasX(lineX2), toCanvasY(lineY2));
  ctx.stroke();
  ctx.setLineDash([]);

  // Puntos experimentales
  ctx.fillStyle = '#1d4ed8';
  for (const p of points) {
    const cx = toCanvasX(p.x);
    const cy = toCanvasY(p.y);
    ctx.beginPath();
    ctx.arc(cx, cy, 4.5, 0, Math.PI * 2);
    ctx.fill();
  }

  // Leyenda interna
  const legX = padLeft + 14;
  const legY = padTop + 14;
  ctx.fillStyle = 'rgba(255,255,255,0.9)';
  ctx.strokeStyle = '#94a3b8';
  ctx.lineWidth = 1;
  ctx.fillRect(legX, legY, 225, 42);
  ctx.strokeRect(legX, legY, 225, 42);

  ctx.fillStyle = '#1d4ed8';
  ctx.beginPath();
  ctx.arc(legX + 12, legY + 13, 4, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = '#000';
  ctx.font = '11px Times New Roman, serif';
  ctx.textAlign = 'left';
  ctx.fillText('Datos experimentales', legX + 24, legY + 17);

  ctx.strokeStyle = '#b91c1c';
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(legX + 6, legY + 31);
  ctx.lineTo(legX + 18, legY + 31);
  ctx.stroke();
  ctx.fillText(`Ajuste: y = ${m.toFixed(3)}x + ${b.toFixed(3)} (R²=${r2.toFixed(3)})`, legX + 24, legY + 35);
}

// Renderizado de la Vista Previa A4 en tiempo real
function renderPreview() {
  const preview = document.getElementById('a4PreviewContent');
  if (!preview) return;

  const autoresHtml = state.autores
    .filter(a => a.nombre.trim() || a.codigo.trim())
    .map(a => `<div>${esc(a.nombre || '[Apellidos y Nombres]')} — Código: <strong>${esc(a.codigo || '[Código]')}</strong></div>`)
    .join('') || '<div>[Apellidos y Nombres - Código Universitario]</div>';

  const objEspHtml = state.objetivosEspecificos
    .filter(o => o.trim())
    .map(o => `<li>${esc(o)}</li>`)
    .join('') || '<li>[Objetivo específico 1]</li>';

  const matRowsHtml = state.materiales
    .filter(m => m.nombre.trim() || m.marca.trim() || m.rango.trim() || m.apreciacion.trim())
    .map((m, i) => `
      <tr>
        <td>${i + 1}</td>
        <td style="text-align:left;">${esc(m.nombre)}</td>
        <td>${esc(m.marca || '—')}</td>
        <td>${esc(m.rango || '—')}</td>
        <td>${esc(m.apreciacion || '—')}</td>
      </tr>
    `).join('') || `
      <tr><td colspan="5">Complete los equipos y materiales en la sección 3.1</td></tr>
    `;

  let tableNum = 1;
  const matTableNum = tableNum++;

  const rawTablesHtml = state.tablasCrudas.map(tbl => {
    const currentT = tableNum++;
    const ths = tbl.columnas.map(c => `<th>${esc(c)}</th>`).join('');
    const trs = tbl.filas.map(r => `<tr>${r.map(c => `<td>${esc(c)}</td>`).join('')}</tr>`).join('');
    return `
      <div class="doc-caption">Tabla ${currentT}. ${esc(tbl.titulo || 'Datos experimentales directos')}</div>
      <table class="doc-table">
        <thead><tr>${ths}</tr></thead>
        <tbody>${trs}</tbody>
      </table>
    `;
  }).join('');

  let figNum = 1;
  let figura1Html = '';
  if (state.figura1DataUrl) {
    figura1Html = `
      <div class="doc-figure">
        <img src="${state.figura1DataUrl}" alt="Figura ${figNum}" />
        <div class="doc-figure-caption"><strong>Figura ${figNum}.</strong> ${esc(state.figura1Leyenda)}</div>
      </div>
    `;
    figNum++;
  }

  let autoChartHtml = '';
  if (state.includeAutoChart && lastRegression) {
    const canvas = document.getElementById('scientificChartCanvas');
    const chartDataUrl = canvas.toDataURL('image/png');
    autoChartHtml = `
      <div class="doc-figure">
        <img src="${chartDataUrl}" alt="Figura ${figNum}" />
        <div class="doc-figure-caption"><strong>Figura ${figNum}.</strong> ${esc(state.chartTitle)}</div>
        <div class="doc-footnote">${esc(state.chartFootnote)}</div>
      </div>
    `;
    figNum++;
  }

  const regSummaryHtml = lastRegression ? `
    <p class="doc-p">
      Mediante el método de regresión lineal por mínimos cuadrados aplicado a los <em>n = ${lastRegression.n}</em> pares de datos experimentales, se obtuvo la relación lineal 
      <em>y = (${lastRegression.m.toFixed(4)} ± ${lastRegression.deltaM.toFixed(4)})x + (${lastRegression.b.toFixed(4)} ± ${lastRegression.deltaB.toFixed(4)})</em> 
      con un coeficiente de determinación <em>R² = ${lastRegression.r2.toFixed(5)}</em>.
    </p>
  ` : '';

  const conclusionsHtml = state.conclusiones
    .filter(c => c.trim())
    .map(c => `<li>${esc(c)}</li>`)
    .join('') || '<li>[Conclusión sustentada exclusivamente en los datos experimentales]</li>';

  const refsHtml = state.referencias
    .filter(r => r.trim())
    .map((r, i) => `<p class="doc-p" style="margin-bottom:4px;">[${i + 1}] ${esc(r)}</p>`)
    .join('') || '<p class="doc-p">[1] M. Alonso, E. J. Finn, Física Vol. I: Mecánica, Fondo Educativo Interamericano, México, 1986.</p>';

  const cuestionarioHtml = state.cuestionario
    .filter(q => q.pregunta.trim() || q.respuesta.trim())
    .map((q, i) => `
      <p class="doc-p"><strong>${i + 1}. ${esc(q.pregunta)}</strong></p>
      <p class="doc-p">${esc(q.respuesta)}</p>
    `).join('') || '<p class="doc-p">[Resolución de las preguntas planteadas por el docente]</p>';

  preview.innerHTML = `
    <div class="doc-header">
      <p class="doc-univ">UNIVERSIDAD NACIONAL JORGE BASADRE GROHMANN</p>
      <p class="doc-sub"><strong>Facultad:</strong> ${esc(state.facultad || '[Facultad correspondiente]')}</p>
      <p class="doc-sub"><strong>Escuela Profesional:</strong> ${esc(state.escuela || '[Ingeniería Ambiental / Física / etc.]')}</p>
      <p class="doc-sub"><strong>Laboratorio de:</strong> ${esc(state.laboratorio || 'FÍSICA')}</p>
      <p class="doc-main-title">INFORME DE LABORATORIO</p>
      <p class="doc-practice-title">Título de la práctica: ${esc(state.tituloPractica || '[Nombre de la práctica]')}</p>
    </div>

    <table class="doc-meta-box">
      <tr>
        <td colspan="2">
          <strong>Autores:</strong>
          ${autoresHtml}
        </td>
      </tr>
      <tr>
        <td><strong>Grupo:</strong> ${esc(state.grupo || '[ ]')}</td>
        <td><strong>Horario:</strong> ${esc(state.horario || '[ ]')}</td>
      </tr>
      <tr>
        <td colspan="2"><strong>Docente:</strong> ${esc(state.docente || '[Grado y Nombre]')}</td>
      </tr>
      <tr>
        <td><strong>Fecha de ejecución:</strong> ${esc(formatDateSpanish(state.fechaEjecucion))}</td>
        <td><strong>Fecha de entrega:</strong> ${esc(state.fechaEntregaTexto || 'Tacna, [ ] de [ ] de 2026')}</td>
      </tr>
    </table>

    <div class="doc-section-title">1. Resumen</div>
    <p class="doc-p">${esc(state.resumen || '[Resumen redactado en tercera persona, tiempo pasado y extensión aproximada de 15 líneas...]')}</p>

    <div class="doc-section-title">2. Introducción</div>
    <p class="doc-p">${esc(state.introduccion || '[Motivaciones del trabajo experimental, base teórica mínima, ecuaciones numeradas correlativamente (1), (2)... y citas bibliográficas [1].]')}</p>
    <p class="doc-p"><strong>Objetivo General:</strong> ${esc(state.objetivoGeneral || '[Indicar magnitud a determinar o ley a verificar]')}</p>
    <p class="doc-p"><strong>Objetivos Específicos:</strong></p>
    <ul class="doc-list">${objEspHtml}</ul>

    <div class="doc-section-title">3. Materiales y Desarrollo Experimental</div>
    <div class="doc-subsection-title">3.1 Materiales</div>
    <div class="doc-caption">Tabla ${matTableNum}. Relación de materiales, equipos e instrumentos empleados</div>
    <table class="doc-table">
      <thead>
        <tr>
          <th>N°</th>
          <th>Equipo / Material</th>
          <th>Marca / Modelo</th>
          <th>Rango de medición</th>
          <th>Apreciación</th>
        </tr>
      </thead>
      <tbody>${matRowsHtml}</tbody>
    </table>

    <div class="doc-subsection-title">3.2 Procedimiento</div>
    <p class="doc-p">${esc(state.procedimiento || '[Descripción del método experimental en tiempo pasado...]')}</p>
    ${figura1Html}
    ${rawTablesHtml}

    <div class="doc-section-title">4. Resultados y Discusión</div>
    ${regSummaryHtml}
    <p class="doc-p">${esc(state.resultadosTexto || '[Presentación de resultados procesados y evaluación de incertezas...]')}</p>
    ${autoChartHtml}
    <p class="doc-p"><strong>Discusión:</strong> ${esc(state.discusion || '[Análisis de validez, precisión, comparación con el modelo teórico y error porcentual...]')}</p>

    <div class="doc-section-title">5. Conclusiones</div>
    <ul class="doc-list">${conclusionsHtml}</ul>
    <p class="doc-p"><strong>Análisis de fuentes de error y aproximaciones:</strong> ${esc(state.fuentesError || '[Fuentes de error sistemático/aleatorio y aproximaciones respecto al caso ideal...]')}</p>

    <div class="doc-section-title">6. Reflexión Argumentada</div>
    <p class="doc-p">${esc(state.reflexion || '[Relación fundamentada de la teoría evaluada experimentalmente con el campo de acción profesional...]')}</p>

    <div class="doc-section-title">7. Referencias</div>
    ${refsHtml}

    <div class="doc-section-title">8. Cuestionario</div>
    ${cuestionarioHtml}

    <div class="doc-section-title">9. Apéndices</div>
    <p class="doc-p">${esc(state.apendices || '[Cálculos detallados, propagación de incertezas y demostraciones complementarias...]')}</p>
  `;
}

// Exportación a Microsoft Word (.docx)
async function exportToDocx() {
  if (typeof window.docx === 'undefined') {
    // Respaldo compatible con Word si se abre sin internet
    const htmlContent = document.getElementById('a4PreviewContent').innerHTML;
    const blob = new Blob([
      `<html><head><meta charset="utf-8"><style>body{font-family:'Times New Roman',serif;font-size:12pt;}table{border-collapse:collapse;width:100%;}td,th{border:1px solid #000;padding:5px;}</style></head><body>${htmlContent}</body></html>`
    ], { type: 'application/msword' });
    downloadBlob(blob, `Informe_Laboratorio_UNJBG.doc`);
    return;
  }

  const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, AlignmentType, ImageRun } = window.docx;

  const dataUrlToUint8Array = (dataUrl) => {
    const base64 = dataUrl.split(',')[1];
    const bin = atob(base64);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return bytes;
  };

  const pBoldCenter = (text, size = 24) => new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 80 },
    children: [new TextRun({ text, bold: true, font: 'Times New Roman', size })]
  });

  const pHeading = (text) => new Paragraph({
    spacing: { before: 220, after: 100 },
    children: [new TextRun({ text: text.toUpperCase(), bold: true, font: 'Times New Roman', size: 24 })]
  });

  const pBody = (text) => new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 120, line: 276 },
    children: [new TextRun({ text: text || '', font: 'Times New Roman', size: 23 })]
  });

  const autoresText = state.autores
    .filter(a => a.nombre.trim() || a.codigo.trim())
    .map(a => `${a.nombre} - ${a.codigo}`)
    .join(' | ') || '[Apellidos y Nombres - Código Universitario]';

  const metaTable = new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [
      new TableRow({
        children: [
          new TableCell({
            columnSpan: 2,
            children: [pBody(`Autores: ${autoresText}`)]
          })
        ]
      }),
      new TableRow({
        children: [
          new TableCell({ children: [pBody(`Grupo: ${state.grupo || '[ ]'}`)] }),
          new TableCell({ children: [pBody(`Horario: ${state.horario || '[ ]'}`)] })
        ]
      }),
      new TableRow({
        children: [
          new TableCell({
            columnSpan: 2,
            children: [pBody(`Docente: ${state.docente || '[Grado y Nombre]'}`)]
          })
        ]
      }),
      new TableRow({
        children: [
          new TableCell({ children: [pBody(`Fecha de ejecución: ${formatDateSpanish(state.fechaEjecucion)}`)] }),
          new TableCell({ children: [pBody(`Fecha de entrega: ${state.fechaEntregaTexto}`)] })
        ]
      })
    ]
  });

  const matRows = [
    new TableRow({
      children: ['N°', 'Equipo / Material', 'Marca / Modelo', 'Rango', 'Apreciación'].map(h =>
        new TableCell({ children: [pBoldCenter(h, 20)] })
      )
    }),
    ...state.materiales.map((m, idx) => new TableRow({
      children: [String(idx + 1), m.nombre, m.marca, m.rango, m.apreciacion].map(val =>
        new TableCell({ children: [pBody(val || '—')] })
      )
    }))
  ];

  const children = [
    pBoldCenter('UNIVERSIDAD NACIONAL JORGE BASADRE GROHMANN', 26),
    pBoldCenter(`Facultad: ${state.facultad}`, 22),
    pBoldCenter(`Escuela Profesional: ${state.escuela}`, 22),
    pBoldCenter(`Laboratorio de: ${state.laboratorio}`, 22),
    pBoldCenter('INFORME DE LABORATORIO', 26),
    pBoldCenter(`Título de la práctica: ${state.tituloPractica || '[Nombre de la práctica]'}`, 24),
    metaTable,
    pHeading('1. Resumen'),
    pBody(state.resumen),
    pHeading('2. Introducción'),
    pBody(state.introduccion),
    pBody(`Objetivo General: ${state.objetivoGeneral}`),
    ...state.objetivosEspecificos.filter(Boolean).map(o => pBody(`• ${o}`)),
    pHeading('3. Materiales y Desarrollo Experimental'),
    pBody('3.1 Materiales'),
    new Table({ width: { size: 100, type: WidthType.PERCENTAGE }, rows: matRows }),
    pBody('3.2 Procedimiento'),
    pBody(state.procedimiento),
    ...(state.figura1DataUrl ? [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 120, after: 60 },
        children: [new ImageRun({ data: dataUrlToUint8Array(state.figura1DataUrl), transformation: { width: 420, height: 250 } })]
      }),
      pBoldCenter(`Figura 1. ${state.figura1Leyenda}`, 20)
    ] : []),
    ...state.tablasCrudas.flatMap((tbl, idx) => [
      pBody(`Tabla ${idx + 2}. ${tbl.titulo}`),
      new Table({
        width: { size: 100, type: WidthType.PERCENTAGE },
        rows: [
          new TableRow({
            children: tbl.columnas.map(c => new TableCell({ children: [pBoldCenter(c, 20)] }))
          }),
          ...tbl.filas.map(r => new TableRow({
            children: r.map(c => new TableCell({ children: [pBody(c)] }))
          }))
        ]
      })
    ]),
    pHeading('4. Resultados y Discusión'),
    ...(lastRegression ? [
      pBody(`Ajuste lineal por mínimos cuadrados (n = ${lastRegression.n}): y = (${lastRegression.m.toFixed(4)} ± ${lastRegression.deltaM.toFixed(4)})x + (${lastRegression.b.toFixed(4)} ± ${lastRegression.deltaB.toFixed(4)}), R² = ${lastRegression.r2.toFixed(5)}.`)
    ] : []),
    pBody(state.resultadosTexto),
    ...(state.includeAutoChart && lastRegression ? [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 120, after: 60 },
        children: [new ImageRun({ data: dataUrlToUint8Array(document.getElementById('scientificChartCanvas').toDataURL('image/png')), transformation: { width: 460, height: 258 } })]
      }),
      pBoldCenter(`Figura ${state.figura1DataUrl ? 2 : 1}. ${state.chartTitle}`, 20),
      pBody(state.chartFootnote)
    ] : []),
    pBody(`Discusión: ${state.discusion}`),
    pHeading('5. Conclusiones'),
    ...state.conclusiones.filter(Boolean).map(c => pBody(`• ${c}`)),
    pBody(`Fuentes de error y aproximaciones: ${state.fuentesError}`),
    pHeading('6. Reflexión Argumentada'),
    pBody(state.reflexion),
    pHeading('7. Referencias'),
    ...state.referencias.filter(Boolean).map((r, i) => pBody(`[${i + 1}] ${r}`)),
    pHeading('8. Cuestionario'),
    ...state.cuestionario.filter(q => q.pregunta || q.respuesta).flatMap((q, i) => [
      pBody(`${i + 1}. ${q.pregunta}`),
      pBody(q.respuesta)
    ]),
    pHeading('9. Apéndices'),
    pBody(state.apendices)
  ];

  const doc = new Document({
    sections: [{
      properties: {
        page: {
          margin: { top: 1134, bottom: 1134, left: 1417, right: 1134 }
        }
      },
      children
    }]
  });

  const blob = await Packer.toBlob(doc);
  const safeTitle = (state.tituloPractica || 'UNJBG').replace(/[^a-zA-Z0-9_-]+/g, '_').slice(0, 40);
  downloadBlob(blob, `Informe_Fisica_${safeTitle}.docx`);
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Cargar datos de demostración completos
function loadDemoReport() {
  state = {
    facultad: 'Facultad de Ingeniería (FAIN)',
    escuela: 'Ingeniería Ambiental',
    laboratorio: 'FÍSICA',
    tituloPractica: 'Determinación experimental de la aceleración de la gravedad mediante el péndulo simple',
    autores: [
      { nombre: 'Quispe Mamani, Valeria Lucía', codigo: '2025-119042' },
      { nombre: 'Condori Flores, Diego Alonso', codigo: '2025-119018' }
    ],
    grupo: 'B - Subgrupo 1',
    horario: 'Miércoles 10:00 - 12:00',
    docente: 'MSc. Carlos Alberto Mendoza Pérez',
    fechaEjecucion: '2026-11-11',
    fechaEntregaTexto: 'Tacna, 18 de noviembre de 2026',
    resumen: 'En la presente práctica de laboratorio se determinó experimentalmente la magnitud de la aceleración de la gravedad local en la ciudad de Tacna mediante el estudio dinámico del péndulo simple. El procedimiento consistió en medir el tiempo correspondiente a diez oscilaciones completas para cinco longitudes distintas de cuerda inextensible comprendidas entre 0.200 m y 1.000 m, manteniendo desplazamientos angulares pequeños menores a 10° para garantizar el régimen armónico simple. A partir de los periodos promedio obtenidos, se realizó un ajuste lineal por mínimos cuadrados de la relación entre el periodo al cuadrado y la longitud del péndulo, obteniéndose una pendiente experimental de (4.032 ± 0.018) s²/m con un coeficiente de determinación R² = 0.99994. De este parámetro se calculó una aceleración de la gravedad experimental de g = (9.79 ± 0.04) m/s², valor que presenta un error porcentual del 0.10 % respecto al valor teórico referencial de 9.78 m/s² para la latitud de Tacna. Se concluyó que el modelo del péndulo simple describe con alta precisión el movimiento oscilatorio bajo amplitudes pequeñas.',
    introduccion: 'El estudio del movimiento armónico simple constituye uno de los pilares fundamentales de la mecánica clásica, permitiendo caracterizar sistemas oscilatorios presentes en ingeniería y ciencias ambientales, tales como estructuras sismorresistentes e instrumentos geofísicos [1]. Un péndulo simple ideal consiste en una masa puntual suspendida de un hilo inextensible y de masa despreciable que oscila libremente bajo la acción del campo gravitatorio terrestre.\n\nPara desplazamientos angulares pequeños (θ < 10°), la aproximación sen(θ) ≈ θ permite linealizar la ecuación de movimiento, estableciendo que el periodo de oscilación T depende exclusivamente de la longitud L del péndulo y de la aceleración de la gravedad local g, según la expresión:\n\nT = 2π √(L / g)    (1)\n\nElevando al cuadrado ambos miembros de la ecuación (1), se obtiene una relación lineal directa entre T² y L:\n\nT² = (4π² / g) L    (2)',
    objetivoGeneral: 'Determinar experimentalmente el valor de la aceleración de la gravedad local en el laboratorio de Física de la UNJBG mediante el análisis del periodo de oscilación de un péndulo simple.',
    objetivosEspecificos: [
      'Medir el periodo de oscilación del péndulo simple para cinco longitudes diferentes manteniendo amplitudes angulares menores a 10°.',
      'Aplicar el método de regresión lineal por mínimos cuadrados a la gráfica de T² en función de L para determinar su pendiente e incerteza.',
      'Comparar el valor experimental de la aceleración de la gravedad obtenido con el valor teórico referencial mediante el cálculo del error porcentual.'
    ],
    materiales: [
      { nombre: 'Soporte universal con nuez doble y varilla', marca: 'Leybold Didactic', rango: '0 - 1.20 m', apreciacion: '—' },
      { nombre: 'Esfera metálica de acero con gancho', marca: 'Pasco Scientific', rango: 'Ø 25.4 mm', apreciacion: '± 0.05 mm' },
      { nombre: 'Cinta métrica metálica graduada', marca: 'Stanley', rango: '0 - 3.00 m', apreciacion: '± 0.001 m' },
      { nombre: 'Cronómetro digital', marca: 'Casio HS-3V', rango: '0 - 9h 59m', apreciacion: '± 0.01 s' },
      { nombre: 'Transportador circular graduado', marca: 'Faber-Castell', rango: '0° - 180°', apreciacion: '± 1°' }
    ],
    procedimiento: 'Se ensambló el soporte universal sobre una superficie nivelada y se fijó el extremo superior del hilo inextensible en la pinza de sujeción. Se midió con la cinta métrica la longitud L desde el punto de suspensión hasta el centro de masa de la esfera metálica. Posteriormente, se desplazó la esfera formando un ángulo inicial de 8° medido con el transportador y se liberó sin velocidad inicial. Se cronometró el tiempo total empleado en completar 10 oscilaciones en tres repeticiones consecutivas para cada longitud (0.200 m, 0.400 m, 0.600 m, 0.800 m y 1.000 m), registrando las mediciones directas en la Tabla 2.',
    figura1DataUrl: '',
    figura1Leyenda: 'Esquema del montaje experimental del péndulo simple instalado en el laboratorio.',
    tablasCrudas: [
      {
        titulo: 'Tiempos medidos para 10 oscilaciones completas en función de la longitud',
        columnas: ['N°', 'L (m)', 't₁ (s)', 't₂ (s)', 't₃ (s)', 't promedio (s)'],
        filas: [
          ['1', '0.200', '8.98', '9.01', '8.99', '8.99'],
          ['2', '0.400', '12.71', '12.74', '12.70', '12.72'],
          ['3', '0.600', '15.56', '15.54', '15.58', '15.56'],
          ['4', '0.800', '17.97', '17.95', '17.99', '17.97'],
          ['5', '1.000', '20.08', '20.11', '20.09', '20.09']
        ]
      }
    ],
    includeAutoChart: true,
    chartTitle: 'Periodo al cuadrado (T²) en función de la longitud del péndulo (L)',
    chartFootnote: 'Fuente: Elaboración propia a partir de los datos experimentales registrados en el Laboratorio de Física - UNJBG.',
    axisXLabel: 'Longitud L (m)',
    axisYLabel: 'Periodo al cuadrado T² (s²)',
    theoreticalSlope: '4.0366',
    xyPairsInput: '0.200, 0.808
0.400, 1.618
0.600, 2.421
0.800, 3.229
1.000, 4.036',
    resultadosTexto: 'Dividiendo el tiempo promedio de 10 oscilaciones entre 10 se obtuvo el periodo T para cada longitud. A partir de la pendiente experimental m = (4.0355 ± 0.0028) s²/m y despejando de la ecuación (2) g = 4π² / m, se determinó la aceleración de la gravedad experimental: g_exp = (9.783 ± 0.007) m/s².',
    discusion: 'Los puntos experimentales muestran un comportamiento altamente lineal con R² = 0.99999, validando la proporcionalidad directa entre T² y L predicha por la ecuación (2). Al comparar g_exp = 9.783 m/s² con el valor teórico referencial para la latitud de Tacna (g_teo = 9.780 m/s²), se obtuvo un error relativo porcentual de 0.03 %, lo cual demuestra una elevada precisión instrumental y control adecuado de la amplitud angular.',
    conclusiones: [
      'Se determinó experimentalmente la aceleración de la gravedad local obteniéndose g = (9.783 ± 0.007) m/s², valor concordante con el estándar geofísico para Tacna con un error porcentual del 0.03 %.',
      'Se verificó mediante regresión lineal que el cuadrado del periodo de oscilación es directamente proporcional a la longitud del péndulo simple (R² = 0.99999) cuando el ángulo inicial es inferior a 10°.'
    ],
    fuentesError: 'Las principales fuentes de error estuvieron asociadas al tiempo de reacción humano al accionar el cronómetro digital (± 0.15 s mitigado al promediar 10 oscilaciones), el leve amortiguamiento aerodinámico de la esfera y la aproximación de masa puntual respecto a una esfera de radio finito.',
    reflexion: 'En el campo de la Ingeniería Ambiental, la comprensión precisa de los sistemas oscilatorios y del campo gravitatorio local resulta esencial para el monitoreo geofísico de suelos, el diseño de estaciones hidrometeorológicas y el análisis de estabilidad de taludes frente a solicitaciones dinámicas en la región Tacna.',
    referencias: [
      'M. Alonso, E. J. Finn, Física Vol. I: Mecánica, Fondo Educativo Interamericano, México, 1986.',
      'R. A. Serway, J. W. Jewett, Física para Ciencias e Ingeniería Vol. 1, 9ª ed., Cengage Learning, México, 2015.'
    ],
    cuestionario: [
      {
        pregunta: '¿Por qué es necesario medir el tiempo de 10 oscilaciones en lugar de una sola oscilación?',
        respuesta: 'Medir múltiples oscilaciones reduce el impacto del error aleatorio de reacción humana al iniciar y detener el cronómetro, ya que dicha incertidumbre se divide entre el número total de periodos medidos (ΔT = Δt / N).'
      },
      {
        pregunta: '¿Qué ocurre con el periodo si se duplica la masa de la esfera manteniendo constante la longitud?',
        respuesta: 'En el régimen de oscilaciones pequeñas, el periodo es independiente de la masa suspendida, dado que la fuerza restauradora gravitatoria es proporcional a la masa inercial.'
      }
    ],
    apendices: 'Apéndice A: Propagación de incerteza para la gravedad g = 4π² / m
Δg = (4π² / m²) · Δm = (39.4784 / 4.0355²) · 0.0028 = 0.0068 m/s² ≈ 0.007 m/s².'
  };

  syncAllUI();
}

function syncAllUI() {
  bindSimpleFields();
  renderAuthorsEditor();
  renderObjetivosEspEditor();
  renderMaterialsEditor();
  renderRawTablesEditor();
  renderConclusionsEditor();
  renderReferencesEditor();
  renderQuestionsEditor();
  updateResumenCounter();
  computeRegressionAndChart();
  renderPreview();
}

// Inicialización de eventos
document.addEventListener('DOMContentLoaded', () => {
  syncAllUI();

  // Botones dinámicos
  document.getElementById('btnAddAuthor').addEventListener('click', () => {
    state.autores.push({ nombre: '', codigo: '' });
    renderAuthorsEditor();
    saveState();
  });

  document.getElementById('btnAddObjEsp').addEventListener('click', () => {
    state.objetivosEspecificos.push('');
    renderObjetivosEspEditor();
    saveState();
  });

  document.getElementById('btnAddMaterial').addEventListener('click', () => {
    state.materiales.push({ nombre: '', marca: '', rango: '', apreciacion: '' });
    renderMaterialsEditor();
    saveState();
  });

  document.getElementById('btnPresetMaterials').addEventListener('click', () => {
    state.materiales = [
      { nombre: 'Vernier / Pie de rey', marca: 'Mitutoyo', rango: '0 - 150 mm', apreciacion: '± 0.05 mm' },
      { nombre: 'Balanza digital de precisión', marca: 'Ohaus', rango: '0 - 2000 g', apreciacion: '± 0.1 g' },
      { nombre: 'Cronómetro digital', marca: 'Casio', rango: '0 - 9h 59m', apreciacion: '± 0.01 s' },
      { nombre: 'Regla metálica milimetrada', marca: 'Stanley', rango: '0 - 100 cm', apreciacion: '± 0.1 cm' }
    ];
    renderMaterialsEditor();
    renderPreview();
    saveState();
  });

  document.getElementById('btnAddRawTable').addEventListener('click', () => {
    state.tablasCrudas.push({
      titulo: 'Nuevas mediciones experimentales',
      columnas: ['Ensayo', 'Variable 1', 'Variable 2'],
      filas: [['1', '', ''], ['2', '', '']]
    });
    renderRawTablesEditor();
    renderPreview();
    saveState();
  });

  document.getElementById('btnAddConclusion').addEventListener('click', () => {
    state.conclusiones.push('');
    renderConclusionsEditor();
    saveState();
  });

  document.getElementById('btnAddReference').addEventListener('click', () => {
    state.referencias.push('');
    renderReferencesEditor();
    saveState();
  });

  document.getElementById('btnAddQuestion').addEventListener('click', () => {
    state.cuestionario.push({ pregunta: '', respuesta: '' });
    renderQuestionsEditor();
    saveState();
  });

  // Subida de Figura 1
  document.getElementById('inputFigura1').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      state.figura1DataUrl = reader.result;
      document.getElementById('figura1Thumb').src = reader.result;
      document.getElementById('figura1PreviewBox').classList.remove('hidden');
      renderPreview();
      saveState();
    };
    reader.readAsDataURL(file);
  });

  document.getElementById('btnRemoveFigura1').addEventListener('click', () => {
    state.figura1DataUrl = '';
    document.getElementById('figura1PreviewBox').classList.add('hidden');
    renderPreview();
    saveState();
  });

  if (state.figura1DataUrl) {
    document.getElementById('figura1Thumb').src = state.figura1DataUrl;
    document.getElementById('figura1PreviewBox').classList.remove('hidden');
  }

  // Asistente de borrador para Resumen
  document.getElementById('btnGenerateResumenDraft').addEventListener('click', () => {
    const titulo = state.tituloPractica || 'el fenómeno físico estudiado';
    const obj = state.objetivoGeneral || 'verificar las leyes físicas correspondientes';
    const regTxt = lastRegression
      ? `Mediante el ajuste por mínimos cuadrados se obtuvo una pendiente experimental de (${lastRegression.m.toFixed(4)} ± ${lastRegression.deltaM.toFixed(4)}) con un coeficiente de determinación R² = ${lastRegression.r2.toFixed(4)}.`
      : 'Los datos recolectados fueron procesados con sus respectivas incertezas instrumentales y estadísticas.';

    state.resumen = `En la presente práctica de laboratorio titulada "${titulo}", se tuvo como propósito principal ${obj.charAt(0).toLowerCase() + obj.slice(1)}. Para ello, se emplearon instrumentos calibrados de medición directa registrando múltiples repeticiones bajo condiciones controladas en el Laboratorio de Física de la Universidad Nacional Jorge Basadre Grohmann. ${regTxt} Los resultados experimentales evidenciaron concordancia con el modelo teórico establecido, identificándose como principales fuentes de desviación las aproximaciones respecto al caso ideal y la apreciación de los instrumentos utilizados. Finalmente, se comprobó la validez experimental de las relaciones fundamentales analizadas.`;
    document.getElementById('resumen').value = state.resumen;
    updateResumenCounter();
    renderPreview();
    saveState();
  });

  // Botones de la barra superior
  document.getElementById('btnPrintPdf').addEventListener('click', () => window.print());
  document.getElementById('btnExportDocx').addEventListener('click', exportToDocx);
  document.getElementById('btnLoadDemo').addEventListener('click', loadDemoReport);

  document.getElementById('btnExportJson').addEventListener('click', () => {
    const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
    downloadBlob(blob, 'respaldo_informe_unjbg.json');
  });

  document.getElementById('inputImportJson').addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = JSON.parse(reader.result);
        state = { ...structuredClone(defaultState), ...parsed };
        syncAllUI();
        saveState();
      } catch (err) {
        alert('El archivo JSON seleccionado no es válido.');
      }
    };
    reader.readAsText(file);
  });

  document.getElementById('btnResetAll').addEventListener('click', () => {
    if (confirm('¿Seguro que deseas borrar todo el contenido y reiniciar la plantilla UNJBG?')) {
      state = structuredClone(defaultState);
      document.getElementById('figura1PreviewBox').classList.add('hidden');
      syncAllUI();
      saveState();
    }
  });

  // Pestañas móviles
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const view = btn.dataset.view;
      const ed = document.getElementById('editorPanel');
      const pr = document.getElementById('previewPanel');
      if (view === 'preview') {
        ed.classList.add('hidden-mobile');
        pr.classList.add('active-mobile');
      } else {
        ed.classList.remove('hidden-mobile');
        pr.classList.remove('active-mobile');
      }
    });
  });
});
