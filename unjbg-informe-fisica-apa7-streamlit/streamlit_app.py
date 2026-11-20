import io
import json
import math
from datetime import date, datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Inches, Pt

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS (VISTA PREVIA APA 7)
# ==============================================================================
st.set_page_config(
    page_title="Generador de Informe de Física — UNJBG (APA 7)",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .unjbg-banner {
        background: linear-gradient(135deg, #8b1e24, #631217);
        color: white;
        padding: 1.1rem 1.4rem;
        border-radius: 10px;
        border-bottom: 4px solid #c59b27;
        margin-bottom: 1rem;
    }
    .unjbg-banner h1 {
        margin: 0;
        font-size: 1.42rem;
        color: #ffffff;
    }
    .unjbg-banner p {
        margin: 0.25rem 0 0 0;
        font-size: 0.9rem;
        opacity: 0.92;
    }
    .norma-box {
        background-color: #fffbeb;
        border-left: 4px solid #c59b27;
        padding: 0.7rem 0.95rem;
        border-radius: 0 6px 6px 0;
        font-size: 0.88rem;
        color: #451a03;
        margin-bottom: 0.8rem;
    }
    .apa-badge {
        display: inline-block;
        background-color: #1e3a8a;
        color: #ffffff;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 0.2rem 0.55rem;
        border-radius: 4px;
        margin-bottom: 0.4rem;
    }
    .a4-preview {
        background-color: #ffffff;
        color: #000000;
        padding: 2.54cm;
        border: 1px solid #cbd5e1;
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        border-radius: 4px;
    }
    .apa-p {
        text-align: justify;
        text-indent: 1.27cm;
        margin-top: 0;
        margin-bottom: 0.6rem;
    }
    .apa-p-noindent {
        text-align: justify;
        text-indent: 0;
        margin-top: 0;
        margin-bottom: 0.6rem;
    }
    .apa-h1 {
        text-align: center;
        font-weight: bold;
        margin-top: 1.2rem;
        margin-bottom: 0.5rem;
        color: #000000;
    }
    .apa-h2 {
        text-align: left;
        font-weight: bold;
        margin-top: 1rem;
        margin-bottom: 0.4rem;
        color: #000000;
    }
    .apa-ref {
        padding-left: 1.27cm;
        text-indent: -1.27cm;
        text-align: left;
        margin-bottom: 0.5rem;
    }
    .apa-table {
        width: 100%;
        border-collapse: collapse;
        margin: 0.4rem 0 0.4rem 0;
        font-size: 0.92rem;
    }
    .apa-table th {
        border-top: 1.5px solid #000000;
        border-bottom: 1px solid #000000;
        border-left: none;
        border-right: none;
        padding: 6px 8px;
        text-align: center;
        font-weight: bold;
        background-color: transparent;
    }
    .apa-table td {
        border: none;
        padding: 5px 8px;
        text-align: center;
    }
    .apa-table tbody tr:last-child td {
        border-bottom: 1.5px solid #000000;
    }
    .meta-table {
        width: 100%;
        border-collapse: collapse;
        margin: 0.8rem 0 1.2rem 0;
        font-size: 0.95rem;
    }
    .meta-table td {
        border: 1px solid #000000;
        padding: 6px 10px;
        text-align: left;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# UTILIDADES Y DATOS POR DEFECTO
# ==============================================================================
MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]


def fecha_a_espanol(f) -> str:
    if isinstance(f, str):
        return f
    if isinstance(f, (date, datetime)):
        return f"{f.day} de {MESES_ES[f.month - 1]} de {f.year}"
    return "[ ]"


def get_default_data() -> dict:
    return {
        "apa_fuente": "Times New Roman",
        "apa_interlineado": 2.0,
        "apa_sangria": True,
        "facultad": "Facultad de Ingeniería (FAIN)",
        "escuela": "Ingeniería Ambiental",
        "laboratorio": "FÍSICA",
        "titulo_practica": "",
        "autores_df": [
            {"Apellidos y Nombres": "", "Código Universitario": ""}
        ],
        "grupo": "",
        "horario": "",
        "docente": "",
        "fecha_ejecucion": "2026-11-11",
        "fecha_entrega": "Tacna, 18 de noviembre de 2026",
        "resumen": "",
        "introduccion": "",
        "objetivo_general": "",
        "objetivos_especificos": "",
        "materiales_df": [
            {"Equipo / Material / Reactivo": "", "Marca / Modelo": "", "Rango de medición": "", "Apreciación": ""}
        ],
        "procedimiento": "",
        "figura1_titulo": "Esquema del dispositivo experimental empleado en la práctica",
        "figura1_nota": "Elaboración propia a partir del montaje realizado en el Laboratorio de Física - UNJBG.",
        "tabla_cruda_titulo": "Mediciones directas obtenidas en el laboratorio",
        "tabla_cruda_nota": "Elaboración propia a partir de las lecturas instrumentales directas.",
        "datos_crudos_df": [
            {"Ensayo n": "1", "Magnitud 1 (unidad)": "", "Magnitud 2 (unidad)": ""},
            {"Ensayo n": "2", "Magnitud 1 (unidad)": "", "Magnitud 2 (unidad)": ""},
            {"Ensayo n": "3", "Magnitud 1 (unidad)": "", "Magnitud 2 (unidad)": ""},
        ],
        "incluir_grafica": True,
        "grafica_titulo": "Relación experimental entre variables físicas",
        "grafica_eje_x": "Variable independiente X (unidad)",
        "grafica_eje_y": "Variable dependiente Y (unidad)",
        "grafica_nota": "Elaboración propia a partir de los datos experimentales procesados en el laboratorio.",
        "pendiente_teorica": "",
        "pares_xy_df": [
            {"X": 0.20, "Y": 0.81},
            {"X": 0.40, "Y": 1.62},
            {"X": 0.60, "Y": 2.41},
            {"X": 0.80, "Y": 3.23},
            {"X": 1.00, "Y": 4.04},
        ],
        "resultados_texto": "",
        "discusion": "",
        "conclusiones": "",
        "fuentes_error": "",
        "reflexion": "",
        "referencias_apa": [
            "Alonso, M., & Finn, E. J. (1986). Física Vol. I: Mecánica. Fondo Educativo Interamericano."
        ],
        "cuestionario_df": [
            {"Pregunta": "", "Respuesta fundamentada": ""}
        ],
        "apendices": "",
    }


def get_demo_data() -> dict:
    return {
        "apa_fuente": "Times New Roman",
        "apa_interlineado": 2.0,
        "apa_sangria": True,
        "facultad": "Facultad de Ingeniería (FAIN)",
        "escuela": "Ingeniería Ambiental",
        "laboratorio": "FÍSICA",
        "titulo_practica": "Determinación experimental de la aceleración de la gravedad mediante el péndulo simple",
        "autores_df": [
            {"Apellidos y Nombres": "Quispe Mamani, Valeria Lucía", "Código Universitario": "2025-119042"},
            {"Apellidos y Nombres": "Condori Flores, Diego Alonso", "Código Universitario": "2025-119018"},
        ],
        "grupo": "B - Subgrupo 1",
        "horario": "Miércoles 10:00 - 12:00",
        "docente": "MSc. Carlos Alberto Mendoza Pérez",
        "fecha_ejecucion": "2026-11-11",
        "fecha_entrega": "Tacna, 18 de noviembre de 2026",
        "resumen": (
            "En la presente práctica de laboratorio se determinó experimentalmente la magnitud de la aceleración de la gravedad "
            "local en la ciudad de Tacna mediante el estudio dinámico del péndulo simple. El procedimiento consistió en medir el "
            "tiempo correspondiente a diez oscilaciones completas para cinco longitudes distintas de cuerda inextensible comprendidas "
            "entre 0.200 m y 1.000 m, manteniendo desplazamientos angulares pequeños menores a 10° para garantizar el régimen armónico "
            "simple. A partir de los periodos promedio obtenidos, se realizó un ajuste lineal por mínimos cuadrados de la relación "
            "entre el periodo al cuadrado y la longitud del péndulo, obteniéndose una pendiente experimental de (4.0355 ± 0.0028) s²/m "
            "con un coeficiente de determinación R² = 0.99999. De este parámetro se calculó una aceleración de la gravedad experimental "
            "de g = (9.783 ± 0.007) m/s², valor que presenta un error porcentual del 0.03 % respecto al valor teórico referencial de "
            "9.780 m/s² para la latitud de Tacna. Se concluyó que el modelo del péndulo simple describe con alta precisión el movimiento "
            "oscilatorio bajo amplitudes pequeñas."
        ),
        "introduccion": (
            "El estudio del movimiento armónico simple constituye uno de los pilares fundamentales de la mecánica clásica, "
            "permitiendo caracterizar sistemas oscilatorios presentes en ingeniería y ciencias ambientales, tales como estaciones "
            "geofísicas y estructuras sismorresistentes (Alonso & Finn, 1986). Un péndulo simple ideal consiste en una masa puntual "
            "suspendida de un hilo inextensible y de masa despreciable que oscila libremente bajo la acción del campo gravitatorio "
            "terrestre (Serway & Jewett, 2015).\n\n"
            "Para desplazamientos angulares pequeños (θ < 10°), la aproximación sen(θ) ≈ θ permite linealizar la ecuación de "
            "movimiento, estableciendo que el periodo de oscilación T depende exclusivamente de la longitud L del péndulo y de la "
            "aceleración de la gravedad local g, según la expresión:\n\n"
            "T = 2π √(L / g)    (1)\n\n"
            "Elevando al cuadrado ambos miembros de la ecuación (1), se obtiene una relación lineal directa entre T² y L:\n\n"
            "T² = (4π² / g) L    (2)"
        ),
        "objetivo_general": (
            "Determinar experimentalmente el valor de la aceleración de la gravedad local en el Laboratorio de Física de la UNJBG "
            "mediante el análisis del periodo de oscilación de un péndulo simple."
        ),
        "objetivos_especificos": (
            "- Medir el periodo de oscilación del péndulo simple para cinco longitudes diferentes manteniendo amplitudes angulares menores a 10°.\n"
            "- Aplicar el método de regresión lineal por mínimos cuadrados a la gráfica de T² en función de L para determinar su pendiente e incerteza.\n"
            "- Comparar el valor experimental de la aceleración de la gravedad obtenido con el valor teórico referencial mediante el cálculo del error porcentual."
        ),
        "materiales_df": [
            {"Equipo / Material / Reactivo": "Soporte universal con nuez doble", "Marca / Modelo": "Leybold Didactic", "Rango de medición": "0 - 1.20 m", "Apreciación": "—"},
            {"Equipo / Material / Reactivo": "Esfera metálica de acero con gancho", "Marca / Modelo": "Pasco Scientific", "Rango de medición": "Ø 25.4 mm", "Apreciación": "± 0.05 mm"},
            {"Equipo / Material / Reactivo": "Cinta métrica metálica graduada", "Marca / Modelo": "Stanley", "Rango de medición": "0 - 3.00 m", "Apreciación": "± 0.001 m"},
            {"Equipo / Material / Reactivo": "Cronómetro digital", "Marca / Modelo": "Casio HS-3V", "Rango de medición": "0 - 9h 59m", "Apreciación": "± 0.01 s"},
            {"Equipo / Material / Reactivo": "Transportador circular graduado", "Marca / Modelo": "Faber-Castell", "Rango de medición": "0° - 180°", "Apreciación": "± 1°"},
        ],
        "procedimiento": (
            "Se ensambló el soporte universal sobre una superficie nivelada y se fijó el extremo superior del hilo inextensible en "
            "la pinza de sujeción. Se midió con la cinta métrica la longitud L desde el punto de suspensión hasta el centro de masa "
            "de la esfera metálica. Posteriormente, se desplazó la esfera formando un ángulo inicial de 8° medido con el transportador "
            "y se liberó sin velocidad inicial. Se cronometró el tiempo total empleado en completar 10 oscilaciones en tres repeticiones "
            "consecutivas para cada longitud (0.200 m, 0.400 m, 0.600 m, 0.800 m y 1.000 m), registrando las mediciones directas en la Tabla 2."
        ),
        "figura1_titulo": "Esquema del montaje experimental del péndulo simple instalado en el laboratorio",
        "figura1_nota": "Elaboración propia a partir del montaje experimental en el Laboratorio de Física - UNJBG.",
        "tabla_cruda_titulo": "Tiempos medidos para 10 oscilaciones completas en función de la longitud",
        "tabla_cruda_nota": "Elaboración propia a partir de mediciones cronometradas directamente en el laboratorio.",
        "datos_crudos_df": [
            {"Ensayo n": "1", "Longitud L (m)": "0.200", "t₁ (s)": "8.98", "t₂ (s)": "9.01", "t₃ (s)": "8.99"},
            {"Ensayo n": "2", "Longitud L (m)": "0.400", "t₁ (s)": "12.71", "t₂ (s)": "12.74", "t₃ (s)": "12.70"},
            {"Ensayo n": "3", "Longitud L (m)": "0.600", "t₁ (s)": "15.56", "t₂ (s)": "15.54", "t₃ (s)": "15.58"},
            {"Ensayo n": "4", "Longitud L (m)": "0.800", "t₁ (s)": "17.97", "t₂ (s)": "17.95", "t₃ (s)": "17.99"},
            {"Ensayo n": "5", "Longitud L (m)": "1.000", "t₁ (s)": "20.08", "t₂ (s)": "20.11", "t₃ (s)": "20.09"},
        ],
        "incluir_grafica": True,
        "grafica_titulo": "Periodo al cuadrado (T²) en función de la longitud del péndulo (L)",
        "grafica_eje_x": "Longitud L (m)",
        "grafica_eje_y": "Periodo al cuadrado T² (s²)",
        "grafica_nota": "Elaboración propia a partir de los datos experimentales registrados en el Laboratorio de Física - UNJBG.",
        "pendiente_teorica": "4.0366",
        "pares_xy_df": [
            {"X": 0.200, "Y": 0.808},
            {"X": 0.400, "Y": 1.618},
            {"X": 0.600, "Y": 2.421},
            {"X": 0.800, "Y": 3.229},
            {"X": 1.000, "Y": 4.036},
        ],
        "resultados_texto": (
            "Dividiendo el tiempo promedio de 10 oscilaciones entre 10 se obtuvo el periodo T para cada longitud. A partir de la "
            "pendiente experimental m = (4.0355 ± 0.0028) s²/m y despejando de la ecuación (2) g = 4π² / m, se determinó la "
            "aceleración de la gravedad experimental: g_exp = (9.783 ± 0.007) m/s²."
        ),
        "discusion": (
            "Los puntos experimentales muestran un comportamiento altamente lineal con R² = 0.99999, validando la proporcionalidad "
            "directa entre T² y L predicha por la ecuación (2). Al comparar g_exp = 9.783 m/s² con el valor teórico referencial para "
            "la latitud de Tacna (g_teo = 9.780 m/s²), se obtuvo un error relativo porcentual de 0.03 %, lo cual demuestra una elevada "
            "precisión instrumental y control adecuado de la amplitud angular."
        ),
        "conclusiones": (
            "1. Se determinó experimentalmente la aceleración de la gravedad local obteniéndose g = (9.783 ± 0.007) m/s², valor concordante con el estándar geofísico para Tacna con un error porcentual del 0.03 %.\n"
            "2. Se verificó mediante regresión lineal que el cuadrado del periodo de oscilación es directamente proporcional a la longitud del péndulo simple (R² = 0.99999) cuando el ángulo inicial es inferior a 10°."
        ),
        "fuentes_error": (
            "Las principales fuentes de error estuvieron asociadas al tiempo de reacción humano al accionar el cronómetro digital "
            "(± 0.15 s mitigado al promediar 10 oscilaciones), el leve amortiguamiento aerodinámico de la esfera y la aproximación "
            "de masa puntual respecto a una esfera de radio finito."
        ),
        "reflexion": (
            "En el campo de la Ingeniería Ambiental, la comprensión precisa de los sistemas oscilatorios y del campo gravitatorio "
            "local resulta esencial para el monitoreo geofísico de suelos, el diseño de estaciones hidrometeorológicas y el análisis "
            "de estabilidad de taludes frente a solicitaciones dinámicas en la región Tacna."
        ),
        "referencias_apa": [
            "Alonso, M., & Finn, E. J. (1986). Física Vol. I: Mecánica. Fondo Educativo Interamericano.",
            "Serway, R. A., & Jewett, J. W. (2015). Física para ciencias e ingeniería (9.ª ed., Vol. 1). Cengage Learning.",
            "Tipler, P. A., & Mosca, G. (2010). Física para la ciencia y la tecnología (6.ª ed., Vol. 1). Editorial Reverté.",
        ],
        "cuestionario_df": [
            {
                "Pregunta": "¿Por qué es necesario medir el tiempo de 10 oscilaciones en lugar de una sola oscilación?",
                "Respuesta fundamentada": "Medir múltiples oscilaciones reduce el impacto del error aleatorio de reacción humana al iniciar y detener el cronómetro, ya que dicha incertidumbre se divide entre el número total de periodos medidos (ΔT = Δt / N)."
            },
            {
                "Pregunta": "¿Qué ocurre con el periodo si se duplica la masa de la esfera manteniendo constante la longitud?",
                "Respuesta fundamentada": "En el régimen de oscilaciones pequeñas, el periodo es independiente de la masa suspendida, dado que la fuerza restauradora gravitatoria es proporcional a la masa inercial."
            },
        ],
        "apendices": (
            "Apéndice A: Propagación de incerteza para la gravedad g = 4π² / m\n"
            "Δg = (4π² / m²) · Δm = (39.4784 / 4.0355²) · 0.0028 = 0.0068 m/s² ≈ 0.007 m/s²."
        ),
    }


if "informe" not in st.session_state:
    st.session_state.informe = get_default_data()

data = st.session_state.informe


# ==============================================================================
# CÁLCULOS FÍSICOS Y GRÁFICA CIENTÍFICA
# ==============================================================================
def calcular_regresion(df_xy: pd.DataFrame):
    if df_xy is None or df_xy.empty:
        return None
    df_clean = df_xy.copy()
    df_clean["X"] = pd.to_numeric(df_clean["X"], errors="coerce")
    df_clean["Y"] = pd.to_numeric(df_clean["Y"], errors="coerce")
    df_clean = df_clean.dropna(subset=["X", "Y"])
    n = len(df_clean)
    if n < 2:
        return None

    x = df_clean["X"].to_numpy(dtype=float)
    y = df_clean["Y"].to_numpy(dtype=float)
    mean_x = np.mean(x)
    mean_y = np.mean(y)
    sxx = np.sum((x - mean_x) ** 2)
    syy = np.sum((y - mean_y) ** 2)
    sxy = np.sum((x - mean_x) * (y - mean_y))

    if sxx == 0:
        return None

    m = sxy / sxx
    b = mean_y - m * mean_x
    r2 = (sxy ** 2) / (sxx * syy) if syy > 0 else 1.0

    if n > 2:
        sse = np.sum((y - (m * x + b)) ** 2)
        s_yx = math.sqrt(sse / (n - 2))
        delta_m = s_yx / math.sqrt(sxx)
        delta_b = s_yx * math.sqrt((1.0 / n) + (mean_x ** 2) / sxx)
    else:
        delta_m = 0.0
        delta_b = 0.0

    return {
        "n": n,
        "x": x,
        "y": y,
        "m": m,
        "b": b,
        "delta_m": delta_m,
        "delta_b": delta_b,
        "r2": r2,
    }


def generar_figura_matplotlib(reg: dict, eje_x: str, eje_y: str) -> io.BytesIO:
    # En APA 7 el número y título de la figura van fuera de la imagen (en el documento)
    fig, ax = plt.subplots(figsize=(7.2, 4.1), dpi=220)
    x = reg["x"]
    y = reg["y"]
    m = reg["m"]
    b = reg["b"]
    r2 = reg["r2"]

    ax.scatter(x, y, color="#1d4ed8", s=45, zorder=3, label="Datos experimentales")
    x_line = np.linspace(np.min(x), np.max(x), 100)
    y_line = m * x_line + b
    ax.plot(
        x_line,
        y_line,
        color="#b91c1c",
        linestyle="--",
        linewidth=1.8,
        zorder=2,
        label=f"Ajuste lineal: y = {m:.4f}x + {b:.4f} (R² = {r2:.5f})",
    )

    ax.set_xlabel(eje_x or "Eje X", fontsize=10, fontweight="bold", family="serif")
    ax.set_ylabel(eje_y or "Eje Y", fontsize=10, fontweight="bold", family="serif")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="best", fontsize=8.5, frameon=True)
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=220)
    plt.close(fig)
    buf.seek(0)
    return buf


# ==============================================================================
# UTILIDADES XML PARA WORD (.DOCX) EN FORMATO APA 7ª EDICIÓN
# ==============================================================================
def set_apa_table_borders(table):
    """Aplica bordes estilo APA 7: solo líneas horizontales superior, encabezado e inferior (sin verticales)."""
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        '  <w:top w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
        '  <w:bottom w:val="single" w:sz="12" w:space="0" w:color="000000"/>'
        '  <w:left w:val="none"/>'
        '  <w:right w:val="none"/>'
        '  <w:insideH w:val="none"/>'
        '  <w:insideV w:val="none"/>'
        '</w:tblBorders>'
    )
    tblPr.append(borders)

    # Borde inferior en la fila de encabezados (fila 0)
    if len(table.rows) > 0:
        for cell in table.rows[0].cells:
            tcPr = cell._tc.get_or_add_tcPr()
            tcBorders = parse_xml(
                f'<w:tcBorders {nsdecls("w")}>'
                '  <w:bottom w:val="single" w:sz="6" w:space="0" w:color="000000"/>'
                '</w:tcBorders>'
            )
            tcPr.append(tcBorders)


def add_page_number_header(section, font_name: str, font_pt: float):
    """Agrega el número de página en la esquina superior derecha según APA 7ª edición."""
    header = section.header
    p = header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run()
    run.font.name = font_name
    run.font.size = Pt(font_pt)

    fldChar1 = OxmlElement("w:fldChar")
    fldChar1.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.set(qn("xml:space"), "preserve")
    instrText.text = "PAGE"
    fldChar2 = OxmlElement("w:fldChar")
    fldChar2.set(qn("w:fldCharType"), "separate")
    fldChar3 = OxmlElement("w:fldChar")
    fldChar3.set(qn("w:fldCharType"), "end")

    r = run._r
    r.append(fldChar1)
    r.append(instrText)
    r.append(fldChar2)
    r.append(fldChar3)


def construir_docx_apa7(d: dict, reg: dict | None, fig1_bytes: bytes | None, chart_buf: io.BytesIO | None) -> bytes:
    doc = Document()

    font_name = d.get("apa_fuente", "Times New Roman")
    font_pt = 12.0 if font_name == "Times New Roman" else 11.0
    line_spacing = float(d.get("apa_interlineado", 2.0))
    use_indent = bool(d.get("apa_sangria", True))

    # Márgenes APA 7: 2.54 cm (1 pulgada) en todos los lados
    for section in doc.sections:
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)
        section.top_margin = Cm(2.54)
        section.bottom_margin = Cm(2.54)
        section.left_margin = Cm(2.54)
        section.right_margin = Cm(2.54)
        add_page_number_header(section, font_name, font_pt)

    style_normal = doc.styles["Normal"]
    style_normal.font.name = font_name
    style_normal.font.size = Pt(font_pt)

    def add_center_bold(text: str, size: float = font_pt, underline: bool = False):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(text)
        run.bold = True
        run.underline = underline
        run.font.name = font_name
        run.font.size = Pt(size)
        return p

    def add_apa_level1(text: str):
        """Título Nivel 1 APA 7: Centrado, Negrita."""
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = line_spacing
        run = p.add_run(text)
        run.bold = True
        run.font.name = font_name
        run.font.size = Pt(font_pt)
        return p

    def add_apa_level2(text: str):
        """Título Nivel 2 APA 7: Alineado a la izquierda, Negrita."""
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = line_spacing
        run = p.add_run(text)
        run.bold = True
        run.font.name = font_name
        run.font.size = Pt(font_pt)
        return p

    def add_apa_body(text: str, bold_prefix: str = "", force_noindent: bool = False):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = line_spacing
        p.paragraph_format.space_after = Pt(6)
        if use_indent and not force_noindent:
            p.paragraph_format.first_line_indent = Cm(1.27)
        if bold_prefix:
            r_pre = p.add_run(bold_prefix)
            r_pre.bold = True
            r_pre.font.name = font_name
            r_pre.font.size = Pt(font_pt)
        run = p.add_run(text or "")
        run.font.name = font_name
        run.font.size = Pt(font_pt)
        return p

    def add_apa_caption_and_title(label_bold: str, title_italic: str):
        """Encabezado APA 7 para Tablas y Figuras: Tabla X (negrita) + Título (cursiva)."""
        p1 = doc.add_paragraph()
        p1.paragraph_format.space_before = Pt(10)
        p1.paragraph_format.space_after = Pt(2)
        p1.paragraph_format.keep_with_next = True
        r1 = p1.add_run(label_bold)
        r1.bold = True
        r1.font.name = font_name
        r1.font.size = Pt(font_pt)

        p2 = doc.add_paragraph()
        p2.paragraph_format.space_after = Pt(4)
        p2.paragraph_format.keep_with_next = True
        r2 = p2.add_run(title_italic)
        r2.italic = True
        r2.font.name = font_name
        r2.font.size = Pt(font_pt)

    def add_apa_note(note_text: str):
        """Nota al pie APA 7 debajo de tablas y figuras: Nota. en cursiva."""
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(10)
        p.paragraph_format.line_spacing = 1.15
        r_lbl = p.add_run("Nota. ")
        r_lbl.italic = True
        r_lbl.font.name = font_name
        r_lbl.font.size = Pt(font_pt - 1)
        r_txt = p.add_run(note_text)
        r_txt.font.name = font_name
        r_txt.font.size = Pt(font_pt - 1)

    # Encabezado Institucional UNJBG
    add_center_bold("UNIVERSIDAD NACIONAL JORGE BASADRE GROHMANN", font_pt + 2)
    add_center_bold(f"Facultad: {d['facultad']}", font_pt)
    add_center_bold(f"Escuela Profesional: {d['escuela']}", font_pt)
    add_center_bold(f"Laboratorio de: {d['laboratorio']}", font_pt)
    add_center_bold("INFORME DE LABORATORIO", font_pt + 1, underline=True)
    add_center_bold(f"Título de la práctica: {d['titulo_practica'] or '[Nombre de la práctica]'}", font_pt)

    autores_list = [
        f"{row.get('Apellidos y Nombres', '').strip()} - {row.get('Código Universitario', '').strip()}"
        for row in d["autores_df"]
        if str(row.get("Apellidos y Nombres", "")).strip() or str(row.get("Código Universitario", "")).strip()
    ]
    autores_str = "\n".join(autores_list) if autores_list else "[Apellidos y Nombres - Código Universitario]"

    meta_tbl = doc.add_table(rows=4, cols=2)
    meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_tbl.style = "Table Grid"
    c0 = meta_tbl.cell(0, 0).merge(meta_tbl.cell(0, 1))
    c0.text = f"Autores:\n{autores_str}"
    meta_tbl.cell(1, 0).text = f"Grupo: {d['grupo'] or '[ ]'}"
    meta_tbl.cell(1, 1).text = f"Horario: {d['horario'] or '[ ]'}"
    c2 = meta_tbl.cell(2, 0).merge(meta_tbl.cell(2, 1))
    c2.text = f"Docente: {d['docente'] or '[Grado y Nombre]'}"
    meta_tbl.cell(3, 0).text = f"Fecha de ejecución: {fecha_a_espanol(d['fecha_ejecucion'])}"
    meta_tbl.cell(3, 1).text = f"Fecha de entrega: {d['fecha_entrega']}"

    # 1. Resumen (sin sangría en primera línea según APA 7)
    add_apa_level1("1. Resumen")
    add_apa_body(d["resumen"], force_noindent=True)

    # 2. Introducción
    add_apa_level1("2. Introducción")
    for para in (d["introduccion"] or "").split("\n\n"):
        if para.strip():
            add_apa_body(para.strip())
    add_apa_body(d["objetivo_general"], bold_prefix="Objetivo General: ")
    add_apa_body(d["objetivos_especificos"], bold_prefix="Objetivos Específicos:\n", force_noindent=True)

    # 3. Materiales y Desarrollo Experimental
    add_apa_level1("3. Materiales y Desarrollo Experimental")
    add_apa_level2("3.1 Materiales")

    mat_rows = [r for r in d["materiales_df"] if any(str(v).strip() for v in r.values())]
    if mat_rows:
        add_apa_caption_and_title("Tabla 1", "Relación de materiales, equipos e instrumentos empleados")
        cols = list(mat_rows[0].keys())
        t_mat = doc.add_table(rows=1 + len(mat_rows), cols=len(cols))
        t_mat.alignment = WD_TABLE_ALIGNMENT.CENTER
        for j, col_name in enumerate(cols):
            cell_p = t_mat.cell(0, j).paragraphs[0]
            cell_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = cell_p.add_run(str(col_name))
            r.bold = True
            r.font.name = font_name
            r.font.size = Pt(font_pt - 1)
        for i, row in enumerate(mat_rows):
            for j, col_name in enumerate(cols):
                cell_p = t_mat.cell(i + 1, j).paragraphs[0]
                cell_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = cell_p.add_run(str(row.get(col_name, "")))
                r.font.name = font_name
                r.font.size = Pt(font_pt - 1)
        set_apa_table_borders(t_mat)
        add_apa_note("Especificaciones técnicas verificadas en los instrumentos del Laboratorio de Física - UNJBG.")

    add_apa_level2("3.2 Procedimiento")
    add_apa_body(d["procedimiento"])

    fig_counter = 1
    if fig1_bytes:
        add_apa_caption_and_title(f"Figura {fig_counter}", d["figura1_titulo"])
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.add_run().add_picture(io.BytesIO(fig1_bytes), width=Inches(4.5))
        add_apa_note(d["figura1_nota"])
        fig_counter += 1

    raw_rows = [r for r in d["datos_crudos_df"] if any(str(v).strip() for v in r.values())]
    if raw_rows:
        add_apa_caption_and_title("Tabla 2", d["tabla_cruda_titulo"])
        cols_r = list(raw_rows[0].keys())
        t_raw = doc.add_table(rows=1 + len(raw_rows), cols=len(cols_r))
        t_raw.alignment = WD_TABLE_ALIGNMENT.CENTER
        for j, c_name in enumerate(cols_r):
            cell_p = t_raw.cell(0, j).paragraphs[0]
            cell_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = cell_p.add_run(str(c_name))
            r.bold = True
            r.font.name = font_name
            r.font.size = Pt(font_pt - 1)
        for i, row in enumerate(raw_rows):
            for j, c_name in enumerate(cols_r):
                cell_p = t_raw.cell(i + 1, j).paragraphs[0]
                cell_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = cell_p.add_run(str(row.get(c_name, "")))
                r.font.name = font_name
                r.font.size = Pt(font_pt - 1)
        set_apa_table_borders(t_raw)
        add_apa_note(d["tabla_cruda_nota"])

    # 4. Resultados y Discusión
    add_apa_level1("4. Resultados y Discusión")
    if reg:
        add_apa_body(
            f"Mediante el ajuste lineal por mínimos cuadrados aplicado a n = {reg['n']} pares de datos experimentales, "
            f"se obtuvo la ecuación y = ({reg['m']:.4f} ± {reg['delta_m']:.4f})x + ({reg['b']:.4f} ± {reg['delta_b']:.4f}), "
            f"con un coeficiente de determinación R² = {reg['r2']:.5f}."
        )
    add_apa_body(d["resultados_texto"])

    if chart_buf and d["incluir_grafica"]:
        chart_buf.seek(0)
        add_apa_caption_and_title(f"Figura {fig_counter}", d["grafica_titulo"])
        p_ch = doc.add_paragraph()
        p_ch.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_ch.add_run().add_picture(chart_buf, width=Inches(5.2))
        add_apa_note(d["grafica_nota"])

    add_apa_body(d["discusion"], bold_prefix="Discusión: ")

    # 5. Conclusiones
    add_apa_level1("5. Conclusiones")
    add_apa_body(d["conclusiones"], force_noindent=True)
    add_apa_body(d["fuentes_error"], bold_prefix="Análisis de fuentes de error y aproximaciones: ")

    # 6. Reflexión Argumentada
    add_apa_level1("6. Reflexión Argumentada")
    add_apa_body(d["reflexion"])

    # 7. Referencias (APA 7: orden alfabético y sangría francesa de 1.27 cm)
    add_apa_level1("7. Referencias")
    refs_sorted = sorted([r.strip() for r in d["referencias_apa"] if r.strip()], key=lambda s: s.lower())
    for ref in refs_sorted:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_ref.paragraph_format.line_spacing = line_spacing
        p_ref.paragraph_format.space_after = Pt(6)
        p_ref.paragraph_format.left_indent = Cm(1.27)
        p_ref.paragraph_format.first_line_indent = Cm(-1.27)
        run = p_ref.add_run(ref)
        run.font.name = font_name
        run.font.size = Pt(font_pt)

    # 8. Cuestionario
    add_apa_level1("8. Cuestionario")
    for idx, item in enumerate(d["cuestionario_df"], start=1):
        preg = str(item.get("Pregunta", "")).strip()
        resp = str(item.get("Respuesta fundamentada", "")).strip()
        if preg or resp:
            add_apa_body(preg, bold_prefix=f"{idx}. ", force_noindent=True)
            add_apa_body(resp)

    # 9. Apéndices
    add_apa_level1("9. Apéndices")
    add_apa_body(d["apendices"], force_noindent=True)

    out = io.BytesIO()
    doc.save(out)
    out.seek(0)
    return out.getvalue()


# ==============================================================================
# BARRA LATERAL (CONFIGURACIÓN APA 7 Y ACCIONES RÁPIDAS)
# ==============================================================================
with st.sidebar:
    st.markdown("### 🏛️ UNJBG — Física (APA 7)")
    st.caption("Normas APA 7ª Edición integradas")

    if st.button("📋 Cargar Informe de Ejemplo (APA 7)", use_container_width=True):
        st.session_state.informe = get_demo_data()
        st.rerun()

    if st.button("🗑️ Limpiar Todo el Formulario", use_container_width=True):
        st.session_state.informe = get_default_data()
        st.rerun()

    st.divider()
    st.markdown("### 📐 Ajustes de Estilo APA 7")
    data["apa_fuente"] = st.selectbox(
        "Tipografía APA 7",
        options=["Times New Roman", "Arial", "Calibri"],
        index=["Times New Roman", "Arial", "Calibri"].index(data.get("apa_fuente", "Times New Roman")),
    )
    data["apa_interlineado"] = st.selectbox(
        "Interlineado",
        options=[2.0, 1.5],
        format_func=lambda x: "Doble (2.0 — Estándar APA 7)" if x == 2.0 else "1.5 líneas",
        index=0 if data.get("apa_interlineado", 2.0) == 2.0 else 1,
    )
    data["apa_sangria"] = st.checkbox(
        "Sangría de primera línea (1.27 cm)",
        value=data.get("apa_sangria", True),
    )

    st.divider()
    st.markdown("### 💾 Respaldo Colaborativo")
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    st.download_button(
        label="⬇️ Guardar avance (.json)",
        data=json_str.encode("utf-8"),
        file_name="respaldo_informe_unjbg_apa7.json",
        mime="application/json",
        use_container_width=True,
    )

    uploaded_json = st.file_uploader("⬆️ Cargar avance (.json)", type=["json"])
    if uploaded_json is not None:
        try:
            loaded = json.load(uploaded_json)
            base = get_default_data()
            base.update(loaded)
            st.session_state.informe = base
            st.success("Respaldo cargado correctamente.")
        except Exception as exc:
            st.error(f"Archivo JSON inválido: {exc}")

# ==============================================================================
# CABECERA PRINCIPAL
# ==============================================================================
st.markdown(
    """
    <div class="unjbg-banner">
      <h1>Generador de Informe de Laboratorio de Física — UNJBG</h1>
      <p>Universidad Nacional Jorge Basadre Grohmann • Tacna • Estructura Institucional + Formato APA 7ª Edición</p>
    </div>
    """,
    unsafe_allow_html=True,
)

tabs = st.tabs([
    "0–1. Encabezado y Resumen",
    "2–3. Introducción y Experimento",
    "4. Resultados y Gráfica APA 7",
    "5–7. Conclusiones y Referencias APA 7",
    "8–9. Cuestionario y Apéndices",
    "📄 Vista Previa A4 y Word (.docx)",
])

# ------------------------------------------------------------------------------
# PESTAÑA 1: ENCABEZADO Y RESUMEN
# ------------------------------------------------------------------------------
with tabs[0]:
    st.subheader("Encabezado Institucional (UNJBG)")
    c1, c2 = st.columns(2)
    with c1:
        data["facultad"] = st.text_input("Facultad", value=data["facultad"])
        data["laboratorio"] = st.text_input("Laboratorio de", value=data["laboratorio"])
    with c2:
        data["escuela"] = st.text_input("Escuela Profesional", value=data["escuela"])
        data["titulo_practica"] = st.text_input(
            "Título de la práctica",
            value=data["titulo_practica"],
            placeholder="Ej. Determinación de la aceleración de la gravedad mediante péndulo simple",
        )

    st.markdown("**Autores (Apellidos y Nombres - Código Universitario)**")
    df_autores_edit = st.data_editor(
        pd.DataFrame(data["autores_df"]),
        num_rows="dynamic",
        use_container_width=True,
        key="editor_autores",
    )
    data["autores_df"] = df_autores_edit.fillna("").to_dict(orient="records")

    c3, c4, c5 = st.columns(3)
    with c3:
        data["grupo"] = st.text_input("Grupo", value=data["grupo"], placeholder="Ej. A / Subgrupo 2")
    with c4:
        data["horario"] = st.text_input("Horario", value=data["horario"], placeholder="Ej. Miércoles 10:00 - 12:00")
    with c5:
        data["docente"] = st.text_input("Docente (Grado y Nombre)", value=data["docente"], placeholder="Ej. MSc. Juan Pérez")

    c6, c7 = st.columns(2)
    with c6:
        try:
            default_dt = date.fromisoformat(str(data["fecha_ejecucion"]))
        except Exception:
            default_dt = date(2026, 11, 11)
        picked_date = st.date_input("Fecha de ejecución", value=default_dt)
        data["fecha_ejecucion"] = picked_date.isoformat()
    with c7:
        data["fecha_entrega"] = st.text_input(
            "Fecha de entrega (Tacna, [ ] de [ ] de 2026)",
            value=data["fecha_entrega"],
        )

    st.divider()
    st.subheader("1. Resumen")
    st.markdown(
        """
        <div class="norma-box">
        <strong>Norma UNJBG + APA 7:</strong> Redactado en un solo párrafo <em>sin sangría inicial</em>, en tercera persona,
        tiempo pasado y con una extensión aproximada de <strong>15 líneas</strong> (~150–250 palabras).
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_res_btn, col_res_info = st.columns([1, 2])
    with col_res_btn:
        if st.button("✨ Generar borrador desde mis datos"):
            tit = data["titulo_practica"] or "el fenómeno físico estudiado"
            obj = data["objetivo_general"] or "verificar las leyes físicas correspondientes"
            data["resumen"] = (
                f"En la presente práctica de laboratorio titulada \"{tit}\", se tuvo como propósito principal "
                f"{obj[0].lower() + obj[1:] if len(obj) > 1 else obj}. Para ello, se emplearon instrumentos calibrados "
                f"de medición directa registrando múltiples repeticiones bajo condiciones controladas en el Laboratorio de "
                f"Física de la Universidad Nacional Jorge Basadre Grohmann. Los datos recolectados fueron procesados mediante "
                f"ajuste lineal y propagación de incertezas, obteniéndose valores experimentales concordantes con el modelo "
                f"teórico establecido. Se identificaron como principales fuentes de desviación las aproximaciones respecto al "
                f"caso ideal y la apreciación instrumental, comprobándose finalmente la validez de las relaciones analizadas."
            )
            st.rerun()

    data["resumen"] = st.text_area("Texto del Resumen", value=data["resumen"], height=190)
    num_palabras = len(data["resumen"].split())
    lineas_est = math.ceil(len(data["resumen"]) / 85) if data["resumen"].strip() else 0
    with col_res_info:
        if 13 <= lineas_est <= 17:
            st.success(f"Extensión óptima: ~{lineas_est} líneas estimadas ({num_palabras} palabras). Meta: ~15 líneas.")
        else:
            st.info(f"Extensión actual: ~{lineas_est} líneas estimadas ({num_palabras} palabras). Meta: ~15 líneas.")

# ------------------------------------------------------------------------------
# PESTAÑA 2: INTRODUCCIÓN Y DESARROLLO EXPERIMENTAL
# ------------------------------------------------------------------------------
with tabs[1]:
    st.subheader("2. Introducción y Objetivos")
    st.markdown(
        """
        <div class="norma-box">
        <strong>Cita en el texto (APA 7):</strong> Utiliza el sistema autor-fecha, por ejemplo: <code>(Alonso & Finn, 1986)</code>
        o <code>Según Serway y Jewett (2015), ...</code>. Numera las ecuaciones correlativamente <code>(1)</code>, <code>(2)</code>...
        </div>
        """,
        unsafe_allow_html=True,
    )
    data["introduccion"] = st.text_area(
        "Motivación, Base Teórica y Ecuaciones Numeradas",
        value=data["introduccion"],
        height=180,
    )
    data["objetivo_general"] = st.text_area("Objetivo General", value=data["objetivo_general"], height=75)
    data["objetivos_especificos"] = st.text_area(
        "Objetivos Específicos",
        value=data["objetivos_especificos"],
        height=105,
    )

    st.divider()
    st.subheader("3. Materiales y Desarrollo Experimental")
    st.markdown("**3.1 Materiales (se renderiza automáticamente como Tabla 1 en estilo APA 7 sin líneas verticales)**")
    df_mat_edit = st.data_editor(
        pd.DataFrame(data["materiales_df"]),
        num_rows="dynamic",
        use_container_width=True,
        key="editor_materiales",
    )
    data["materiales_df"] = df_mat_edit.fillna("").to_dict(orient="records")

    st.markdown("**3.2 Procedimiento (redactado en tiempo pasado)**")
    data["procedimiento"] = st.text_area("Descripción del método experimental", value=data["procedimiento"], height=135)

    col_fig, col_ley = st.columns([1, 1])
    with col_fig:
        fig1_file = st.file_uploader("Subir esquema del dispositivo experimental (Figura 1)", type=["png", "jpg", "jpeg"])
        fig1_bytes = fig1_file.getvalue() if fig1_file is not None else None
        if fig1_bytes:
            st.image(fig1_bytes, caption="Vista previa Figura 1", width=250)
    with col_ley:
        data["figura1_titulo"] = st.text_input("Título descriptivo de la Figura 1 (en cursiva APA 7)", value=data["figura1_titulo"])
        data["figura1_nota"] = st.text_input("Nota al pie de la Figura 1", value=data["figura1_nota"])

    st.markdown("**Tabla 2: Datos directos tomados en el experimento (estilo APA 7)**")
    c_t1, c_t2 = st.columns(2)
    with c_t1:
        data["tabla_cruda_titulo"] = st.text_input("Título en cursiva de la Tabla 2", value=data["tabla_cruda_titulo"])
    with c_t2:
        data["tabla_cruda_nota"] = st.text_input("Nota al pie de la Tabla 2", value=data["tabla_cruda_nota"])

    df_raw_edit = st.data_editor(
        pd.DataFrame(data["datos_crudos_df"]),
        num_rows="dynamic",
        use_container_width=True,
        key="editor_datos_crudos",
    )
    data["datos_crudos_df"] = df_raw_edit.fillna("").to_dict(orient="records")

# ------------------------------------------------------------------------------
# PESTAÑA 3: RESULTADOS Y GRÁFICA APA 7
# ------------------------------------------------------------------------------
with tabs[2]:
    st.subheader("4. Resultados y Discusión")
    st.markdown(
        """
        <div class="norma-box">
        <strong>Gráficas en APA 7:</strong> El número (<strong>Figura X</strong>) y el <em>título descriptivo en cursiva</em> se
        ubican encima de la gráfica, mientras que la <em>Nota.</em> explicativa y fuente van debajo.
        </div>
        """,
        unsafe_allow_html=True,
    )

    data["incluir_grafica"] = st.checkbox("Incluir gráfica científica generada automáticamente", value=data["incluir_grafica"])

    cg1, cg2 = st.columns(2)
    with cg1:
        data["grafica_titulo"] = st.text_input("Título descriptivo de la Gráfica (APA 7)", value=data["grafica_titulo"])
        data["grafica_eje_x"] = st.text_input("Nombre del Eje X y Unidades", value=data["grafica_eje_x"])
    with cg2:
        data["grafica_nota"] = st.text_input("Nota al pie de la Gráfica (Nota.)", value=data["grafica_nota"])
        data["grafica_eje_y"] = st.text_input("Nombre del Eje Y y Unidades", value=data["grafica_eje_y"])

    data["pendiente_teorica"] = st.text_input(
        "Pendiente teórica de referencia (opcional, para calcular E%)",
        value=data["pendiente_teorica"],
        placeholder="Ej. 4.0366",
    )

    col_xy, col_plot = st.columns([1, 1.35])
    with col_xy:
        st.markdown("**Pares de datos procesados (X, Y)**")
        df_xy_edit = st.data_editor(
            pd.DataFrame(data["pares_xy_df"]),
            num_rows="dynamic",
            use_container_width=True,
            key="editor_pares_xy",
        )
        data["pares_xy_df"] = df_xy_edit.to_dict(orient="records")

    reg_res = calcular_regresion(df_xy_edit)
    chart_buffer = None

    with col_plot:
        if reg_res:
            err_msg = ""
            try:
                m_teo = float(data["pendiente_teorica"])
                if m_teo != 0:
                    err_pct = abs(reg_res["m"] - m_teo) / abs(m_teo) * 100.0
                    err_msg = f" | **Error porcentual (E%):** `{err_pct:.2f}%`"
            except Exception:
                pass

            st.success(
                f"**Ajuste por mínimos cuadrados (n = {reg_res['n']}):**\n\n"
                f"- Pendiente: `m = ({reg_res['m']:.4f} ± {reg_res['delta_m']:.4f})`\n"
                f"- Intercepto: `b = ({reg_res['b']:.4f} ± {reg_res['delta_b']:.4f})`\n"
                f"- Coeficiente de determinación: `R² = {reg_res['r2']:.5f}`{err_msg}"
            )
            chart_buffer = generar_figura_matplotlib(reg_res, data["grafica_eje_x"], data["grafica_eje_y"])
            st.markdown(f"**Figura {2 if fig1_bytes else 1}**\n\n*{data['grafica_titulo']}*")
            st.image(chart_buffer, use_container_width=True)
            st.caption(f"*Nota.* {data['grafica_nota']}")
        else:
            st.warning("Ingrese al menos 2 filas numéricas válidas en (X, Y) para calcular pendiente, incerteza y gráfica.")

    data["resultados_texto"] = st.text_area("Presentación de Resultados Procesados e Incertezas", value=data["resultados_texto"], height=125)
    data["discusion"] = st.text_area("Discusión de Resultados", value=data["discusion"], height=125)

# ------------------------------------------------------------------------------
# PESTAÑA 4: CONCLUSIONES, REFLEXIÓN Y REFERENCIAS APA 7
# ------------------------------------------------------------------------------
with tabs[3]:
    st.subheader("5. Conclusiones")
    data["conclusiones"] = st.text_area("Conclusiones Experimentales", value=data["conclusiones"], height=115)
    data["fuentes_error"] = st.text_area("Análisis de Fuentes de Error y Aproximaciones al Caso Ideal", value=data["fuentes_error"], height=95)

    st.divider()
    st.subheader("6. Reflexión Argumentada")
    data["reflexion"] = st.text_area("Relación con el campo de acción profesional", value=data["reflexion"], height=105)

    st.divider()
    st.subheader("7. Referencias (Formato APA 7ª Edición)")
    st.markdown(
        """
        <div class="norma-box">
        <strong>Reglas APA 7 para Referencias:</strong> Ordenadas alfabéticamente por el apellido del primer autor,
        con <strong>sangría francesa de 1.27 cm</strong> (0.5 in) y formato:
        <code>Apellido, N. (Año). <em>Título del libro en cursiva</em> (edición). Editorial.</code>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("➕ Asistente para construir referencia en APA 7ª Edición"):
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            ref_autores = st.text_input("Autor(es) (ej. Alonso, M., & Finn, E. J.)", key="apa_aut")
            ref_titulo = st.text_input("Título de la obra o artículo", key="apa_tit")
        with r_col2:
            ref_anio = st.text_input("Año (ej. 1986)", key="apa_anio")
            ref_editorial = st.text_input("Editorial / Revista / URL", key="apa_ed")

        if st.button("Agregar referencia formateada a la lista"):
            if ref_autores.strip() and ref_titulo.strip():
                anio_txt = ref_anio.strip() if ref_anio.strip() else "s. f."
                ed_txt = f" {ref_editorial.strip()}." if ref_editorial.strip() else ""
                nueva_ref = f"{ref_autores.strip()} ({anio_txt}). {ref_titulo.strip()}.{ed_txt}"
                data["referencias_apa"].append(nueva_ref)
                st.rerun()
            else:
                st.warning("Completa al menos Autor(es) y Título.")

    df_refs_edit = st.data_editor(
        pd.DataFrame({"Referencia bibliográfica (APA 7)": data["referencias_apa"]}),
        num_rows="dynamic",
        use_container_width=True,
        key="editor_refs_apa",
    )
    data["referencias_apa"] = [
        str(x).strip() for x in df_refs_edit["Referencia bibliográfica (APA 7)"].fillna("").tolist() if str(x).strip()
    ]

# ------------------------------------------------------------------------------
# PESTAÑA 5: CUESTIONARIO Y APÉNDICES
# ------------------------------------------------------------------------------
with tabs[4]:
    st.subheader("8. Cuestionario")
    df_q_edit = st.data_editor(
        pd.DataFrame(data["cuestionario_df"]),
        num_rows="dynamic",
        use_container_width=True,
        key="editor_cuestionario",
    )
    data["cuestionario_df"] = df_q_edit.fillna("").to_dict(orient="records")

    st.divider()
    st.subheader("9. Apéndices")
    data["apendices"] = st.text_area("Cálculos detallados y propagación de incertezas", value=data["apendices"], height=130)

# ------------------------------------------------------------------------------
# PESTAÑA 6: VISTA PREVIA A4 Y EXPORTACIÓN WORD (.DOCX)
# ------------------------------------------------------------------------------
with tabs[5]:
    st.subheader("Exportar Informe Oficial UNJBG en Formato APA 7ª Edición")
    docx_bytes = construir_docx_apa7(data, reg_res, fig1_bytes, chart_buffer)
    safe_name = "".join(c if c.isalnum() else "_" for c in (data["titulo_practica"] or "UNJBG"))[:35]

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.download_button(
            label="📥 Descargar Word (.docx) con Formato APA 7",
            data=docx_bytes,
            file_name=f"Informe_Fisica_APA7_{safe_name}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True,
        )
    with col_d2:
        st.info(
            "El archivo `.docx` incluye márgenes APA 7 (2.54 cm), numeración de página superior derecha, "
            "sangría de primera línea (1.27 cm), tablas APA sin bordes verticales y sangría francesa en Referencias."
        )

    st.divider()
    st.subheader("Vista Previa del Documento (APA 7ª Edición)")

    font_css = f"'{data['apa_fuente']}', Times, serif"
    line_css = str(data["apa_interlineado"])
    p_class = "apa-p" if data["apa_sangria"] else "apa-p-noindent"

    autores_html = "<br>".join(
        f"{r.get('Apellidos y Nombres', '')} - <strong>{r.get('Código Universitario', '')}</strong>"
        for r in data["autores_df"]
        if str(r.get("Apellidos y Nombres", "")).strip() or str(r.get("Código Universitario", "")).strip()
    ) or "[Apellidos y Nombres - Código Universitario]"

    mat_df_prev = pd.DataFrame(data["materiales_df"])
    mat_html = mat_df_prev.to_html(index=False, classes="apa-table", border=0) if not mat_df_prev.empty else ""

    raw_df_prev = pd.DataFrame(data["datos_crudos_df"])
    raw_html = raw_df_prev.to_html(index=False, classes="apa-table", border=0) if not raw_df_prev.empty else ""

    refs_sorted_prev = sorted(data["referencias_apa"], key=lambda s: s.lower())
    refs_html = "".join(f'<div class="apa-ref">{r}</div>' for r in refs_sorted_prev)

    q_html = "".join(
        f'<p class="apa-p-noindent"><strong>{i}. {r.get("Pregunta", "")}</strong></p>'
        f'<p class="{p_class}">{r.get("Respuesta fundamentada", "")}</p>'
        for i, r in enumerate(data["cuestionario_df"], start=1)
        if str(r.get("Pregunta", "")).strip() or str(r.get("Respuesta fundamentada", "")).strip()
    )

    intro_paragraphs = "".join(
        f'<p class="{p_class}">{p.strip()}</p>'
        for p in (data["introduccion"] or "").split("\n\n")
        if p.strip()
    )

    preview_html = f"""
    <div class="a4-preview" style="font-family: {font_css}; line-height: {line_css}; font-size: 12pt;">
      <div style="text-align:right; font-size:10pt; margin-bottom:0.5rem;">1</div>
      <div style="text-align:center; border-bottom:2px solid #000; padding-bottom:10px; margin-bottom:14px; line-height:1.35;">
        <div style="font-size:13.5pt; font-weight:bold;">UNIVERSIDAD NACIONAL JORGE BASADRE GROHMANN</div>
        <div><strong>Facultad:</strong> {data['facultad']}</div>
        <div><strong>Escuela Profesional:</strong> {data['escuela']}</div>
        <div><strong>Laboratorio de:</strong> {data['laboratorio']}</div>
        <div style="font-size:13pt; font-weight:bold; margin:8px 0 4px 0; text-decoration:underline;">INFORME DE LABORATORIO</div>
        <div><strong>Título de la práctica:</strong> {data['titulo_practica'] or '[Nombre de la práctica]'}</div>
      </div>

      <table class="meta-table" style="line-height:1.35;">
        <tr><td colspan="2"><strong>Autores:</strong><br>{autores_html}</td></tr>
        <tr>
          <td><strong>Grupo:</strong> {data['grupo'] or '[ ]'}</td>
          <td><strong>Horario:</strong> {data['horario'] or '[ ]'}</td>
        </tr>
        <tr><td colspan="2"><strong>Docente:</strong> {data['docente'] or '[Grado y Nombre]'}</td></tr>
        <tr>
          <td><strong>Fecha de ejecución:</strong> {fecha_a_espanol(data['fecha_ejecucion'])}</td>
          <td><strong>Fecha de entrega:</strong> {data['fecha_entrega']}</td>
        </tr>
      </table>

      <div class="apa-h1">1. Resumen</div>
      <p class="apa-p-noindent">{data['resumen']}</p>

      <div class="apa-h1">2. Introducción</div>
      {intro_paragraphs}
      <p class="{p_class}"><strong>Objetivo General:</strong> {data['objetivo_general']}</p>
      <p class="apa-p-noindent"><strong>Objetivos Específicos:</strong><br>{data['objetivos_especificos'].replace(chr(10), '<br>')}</p>

      <div class="apa-h1">3. Materiales y Desarrollo Experimental</div>
      <div class="apa-h2">3.1 Materiales</div>
      <div style="line-height:1.35; margin-top:0.5rem;">
        <div><strong>Tabla 1</strong></div>
        <div><em>Relación de materiales, equipos e instrumentos empleados</em></div>
      </div>
      {mat_html}
      <div style="font-size:10pt; line-height:1.3; margin-bottom:0.8rem;"><em>Nota.</em> Especificaciones técnicas de los equipos del Laboratorio de Física - UNJBG.</div>

      <div class="apa-h2">3.2 Procedimiento</div>
      <p class="{p_class}">{data['procedimiento']}</p>

      <div style="line-height:1.35; margin-top:0.5rem;">
        <div><strong>Tabla 2</strong></div>
        <div><em>{data['tabla_cruda_titulo']}</em></div>
      </div>
      {raw_html}
      <div style="font-size:10pt; line-height:1.3; margin-bottom:0.8rem;"><em>Nota.</em> {data['tabla_cruda_nota']}</div>

      <div class="apa-h1">4. Resultados y Discusión</div>
      <p class="{p_class}">{data['resultados_texto']}</p>
      <p class="{p_class}"><strong>Discusión:</strong> {data['discusion']}</p>

      <div class="apa-h1">5. Conclusiones</div>
      <p class="apa-p-noindent">{data['conclusiones'].replace(chr(10), '<br>')}</p>
      <p class="{p_class}"><strong>Análisis de fuentes de error y aproximaciones:</strong> {data['fuentes_error']}</p>

      <div class="apa-h1">6. Reflexión Argumentada</div>
      <p class="{p_class}">{data['reflexion']}</p>

      <div class="apa-h1">7. Referencias</div>
      {refs_html}

      <div class="apa-h1">8. Cuestionario</div>
      {q_html}

      <div class="apa-h1">9. Apéndices</div>
      <p class="apa-p-noindent">{data['apendices'].replace(chr(10), '<br>')}</p>
    </div>
    """
    st.markdown(preview_html, unsafe_allow_html=True)
