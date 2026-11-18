# Generador de Informes de Laboratorio de Física — UNJBG

Aplicación web abierta y gratuita diseñada para los estudiantes de la **Universidad Nacional Jorge Basadre Grohmann (UNJBG — Tacna, Perú)** que permite redactar, calcular incertezas, graficar datos experimentales y exportar **Informes de Laboratorio de Física** siguiendo estrictamente la estructura académica institucional.

## Características Principales

- **Encabezado Institucional UNJBG:** Campos configurables para Facultad, Escuela Profesional, Laboratorio de Física, Título de la práctica, lista dinámica de Autores con Código Universitario, Grupo, Horario, Docente, Fecha de ejecución y Fecha de entrega (`Tacna, [día] de [mes] de 2026`).
- **Estructura Completa de 9 Secciones:**
  1. **Resumen:** Contador inteligente de palabras y líneas estimadas en formato A4 (alerta visual alrededor de las ~15 líneas reglamentarias) y asistente de redacción en tercera persona y tiempo pasado.
  2. **Introducción:** Base teórica, ecuaciones numeradas correlativamente `(1), (2)...`, citas `[1]` y gestor de **Objetivos Generales y Específicos**.
  3. **Materiales y Desarrollo Experimental:**
     - **3.1 Materiales:** Tabla estructurada con instrumento/material, marca, rango de medición y apreciación.
     - **3.2 Procedimiento:** Redacción en tiempo pasado, carga de esquema experimental (**Figura 1** con leyenda) y constructor de tablas de datos crudos.
  4. **Resultados y Discusión:**
     - Módulo integrado de **Regresión Lineal por Mínimos Cuadrados** ($y = mx + b$), cálculo de pendiente con incerteza ($m \pm \Delta m$), coeficiente $R^2$, desviación estándar y error porcentual ($E\%$).
     - **Generador Automático de Gráficas Científicas:** Crea gráficos con título, ejes con unidades, escalas, puntos experimentales, recta de ajuste y nota al pie.
  5. **Conclusiones:** Sustentación de objetivos, análisis de fuentes de error y aproximaciones al caso ideal.
  6. **Reflexión Argumentada:** Vinculación del fenómeno físico con el campo de acción profesional de la Escuela correspondiente.
  7. **Referencias:** Gestor bibliográfico numerado `[1]`, `[2]`... bajo formato normado.
  8. **Cuestionario:** Editor de preguntas del docente y respuestas desarrolladas.
  9. **Apéndices:** Cálculos detallados y propagación de incertezas.
- **Exportación Múltiple:**
  - **PDF / Impresión A4:** Vista previa en tiempo real y exportación directa a PDF mediante impresión limpia (`@media print`).
  - **Microsoft Word (`.docx`):** Exportación directa a documento `.docx` editable con portada, tablas formateadas y gráficas incrustadas.
  - **Respaldo Colaborativo (`.json`):** Guarda y comparte el avance del informe con tus compañeros de grupo.

## Estructura del Repositorio

```text
unjbg-informe-fisica/
├── .github/
│   └── workflows/
│       └── deploy-pages.yml   # Despliegue automático en GitHub Pages
├── index.html                 # Interfaz del editor y vista previa A4
├── styles.css                 # Diseño responsivo y hoja de estilos de impresión A4
├── app.js                     # Lógica de cálculos físicos, gráficas y exportación DOCX/PDF
├── README.md                  # Documentación del proyecto
├── LICENSE                    # Licencia MIT
└── .gitignore                 # Exclusiones de Git
```

## Cómo publicar este software en GitHub Pages

1. Crea un nuevo repositorio público en [GitHub](https://github.com/new) (por ejemplo, `unjbg-informe-fisica`).
2. Sube todos los archivos de esta carpeta a la rama `main`.
3. En tu repositorio de GitHub, ve a **Settings → Pages**.
4. En **Build and deployment → Source**, selecciona **GitHub Actions** (o **Deploy from a branch** -> `main` / `/ (root)`).
5. En menos de un minuto tendrás tu aplicación funcionando en línea en `https://<tu-usuario>.github.io/unjbg-informe-fisica/`.

## Uso Local

No requiere instalación de servidores ni dependencias externas. Simplemente abre el archivo `index.html` en cualquier navegador moderno (Chrome, Edge, Firefox, Brave).
