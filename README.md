# StreamAI: Recomendador de Contenido de Streaming

## Descripción del proyecto

StreamAI es una aplicación web desarrollada con el objetivo de analizar tendencias de contenido audiovisual en distintas plataformas de streaming y brindar recomendaciones personalizadas de películas y series mediante técnicas de análisis de datos y procesamiento de texto.

La plataforma integra información proveniente de Netflix, Disney+, Prime Video, HBO Max, Apple TV+. 

A partir de estos datos se desarrolló un dashboard interactivo y un motor de recomendación basado en similitud de contenido.

## Contenido

```
├── index.html            # Pagina Web
├── app.js                # Lógica: KPIs, gráficos, filtros y motor de similitud (TF-IDF)
├── dataset_embed.js      # Dataset (800 títulos) embebido como variable JS
├── README.md
├── LICENSE
├── docs/
│   ├── Presentacion_Proyecto.pdf
│   ├── Seguimiento.pdf
│   └── Flujo_n8n.pdf
└── scripts/
    └── generate_dataset.py
```
## Arquitectura del proyecto

Datasets Kaggle

        ↓
Limpieza y unificación (Python / Google Colab)

        ↓
Dataset final

        ↓
Dashboard Web (HTML + JS + Chart.js)

        ↓
Motor de recomendación (TF-IDF)

        ↓
Chatbot OpenAI + n8n

## Objetivos

### Objetivo general

Desarrollar una plataforma web que permita analizar el contenido disponible en múltiples servicios de streaming y recomendar títulos según las preferencias del usuario.

### Objetivos específicos
Integrar datasets de distintas plataformas.
Analizar géneros, popularidad y tendencias de consumo.
Construir indicadores y visualizaciones interactivas.
Implementar un sistema de recomendación basado en IA.
Integrar un chatbot mediante n8n y OpenAI.

## Demo del proyecto

🌐 Página Web:

https://seregrun-ops.github.io/tp-con-sorpreas/

Repositorio:

https://github.com/Seregrun-ops/tp-con-sorpreas

## Dataset

El archivo `dataset_embed.js` contiene una muestra de 800 títulos, con un esquema
equivalente al dataset público *"Netflix Movies and TV Shows"* de Kaggle,
extendido con la columna `plataforma` para cubrir los 5 servicios de
streaming. Columnas: `show_id`, `titulo`, `tipo`, `plataforma`, `director`,
`elenco`, `pais`, `fecha_agregado`, `anio_lanzamiento`, `clasificacion`,
`duracion`, `genero`, `descripcion`, `puntaje`.

Enlaces de Datasets:
https://www.kaggle.com/datasets/shivamb/netflix-show

https://www.kaggle.com/datasets/unanimad/disney-plus-shows

https://www.kaggle.com/datasets/shivamb/amazon-prime-movies-and-tv-shows

https://www.kaggle.com/datasets/dgoenrique/apple-tv-movies-and-tv-shows

https://www.kaggle.com/datasets/ruchi798/movies-on-netflix-prime-video-hulu-and-disney
