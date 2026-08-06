"""
generate_dataset.py
====================
Genera el dataset combinado de streaming (Netflix, Disney+, Prime Video,
HBO Max y Apple TV+) que se utiliza en todo el proyecto.

El esquema replica el del dataset público "Netflix Movies and TV Shows"
de Kaggle (shivamb/netflix-shows), extendido con la columna 'plataforma'
para soportar múltiples servicios de streaming, tal como en el dataset
"TV Shows and Movies listed on Netflix, Disney+, Hulu, Prime Video, HBO Max"
(ruchi798, Kaggle).

Columnas generadas:
    show_id      -> identificador único
    titulo       -> nombre del título
    tipo         -> 'Movie' o 'TV Show'
    plataforma   -> Netflix / Disney+ / Prime Video / HBO Max / Apple TV+
    director     -> director principal (puede estar vacío en series)
    elenco       -> actores principales (lista separada por comas)
    pais         -> país de producción
    fecha_agregado -> fecha en que se agregó al catálogo
    anio_lanzamiento -> año de estreno
    clasificacion  -> rating (TV-MA, PG-13, etc.)
    duracion       -> minutos (película) o temporadas (serie)
    genero         -> géneros (lista separada por comas, se usa el primero como principal)
    descripcion    -> sinopsis corta
    puntaje        -> puntaje 0-10 (simula IMDb/TMDB rating)

Este script combina:
  1. Un set "semilla" de ~120 títulos REALES y reconocibles (con datos
     fieles a la realidad: año, plataforma, género, puntaje aproximado).
  2. Generación sintética estructurada para escalar el dataset a varios
     miles de filas, manteniendo distribuciones realistas de género,
     plataforma, año y puntaje -- de forma que el dashboard, los KPIs y
     el motor de recomendación trabajen sobre un volumen de datos
     representativo de un dataset real de Kaggle.

Para reemplazar por el dataset 100% real de Kaggle, ver instrucciones
en README.md / docs/dataset.md (sección "Cómo usar el dataset real de Kaggle").
"""

import os
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

# ------------------------------------------------------------------
# 1. SET SEMILLA: ~120 títulos reales (curados a mano)
# ------------------------------------------------------------------
SEED_TITLES = [
    # (titulo, tipo, plataforma, genero_principal, anio, puntaje, pais, duracion_min_o_temp, clasificacion)
    ("Stranger Things", "TV Show", "Netflix", "Sci-Fi & Fantasy", 2016, 8.7, "United States", 4, "TV-14"),
    ("Breaking Bad", "TV Show", "Netflix", "Crime TV Shows", 2008, 9.5, "United States", 5, "TV-MA"),
    ("Ozark", "TV Show", "Netflix", "Crime TV Shows", 2017, 8.4, "United States", 4, "TV-MA"),
    ("The Crown", "TV Show", "Netflix", "Dramas", 2016, 8.6, "United Kingdom", 6, "TV-MA"),
    ("Bird Box", "Movie", "Netflix", "Horror Movies", 2018, 6.6, "United States", 124, "R"),
    ("The Witcher", "TV Show", "Netflix", "Sci-Fi & Fantasy", 2019, 8.0, "United States", 3, "TV-MA"),
    ("Dark", "TV Show", "Netflix", "Crime TV Shows", 2017, 8.8, "Germany", 3, "TV-MA"),
    ("Money Heist", "TV Show", "Netflix", "Crime TV Shows", 2017, 8.2, "Spain", 5, "TV-MA"),
    ("Narcos", "TV Show", "Netflix", "Crime TV Shows", 2015, 8.8, "United States", 3, "TV-MA"),
    ("The Irishman", "Movie", "Netflix", "Dramas", 2019, 7.8, "United States", 209, "R"),
    ("Roma", "Movie", "Netflix", "Dramas", 2018, 7.7, "Mexico", 135, "R"),
    ("Extraction", "Movie", "Netflix", "Action & Adventure", 2020, 6.8, "United States", 117, "R"),
    ("The Witcher: Blood Origin", "TV Show", "Netflix", "Sci-Fi & Fantasy", 2022, 5.6, "United States", 1, "TV-MA"),
    ("Wednesday", "TV Show", "Netflix", "Comedies", 2022, 8.1, "United States", 1, "TV-14"),
    ("Squid Game", "TV Show", "Netflix", "Thrillers", 2021, 8.0, "South Korea", 2, "TV-MA"),
    ("The Queen's Gambit", "TV Show", "Netflix", "Dramas", 2020, 8.6, "United States", 1, "TV-MA"),
    ("Bridgerton", "TV Show", "Netflix", "Dramas", 2020, 7.3, "United States", 3, "TV-MA"),
    ("You", "TV Show", "Netflix", "Thrillers", 2018, 7.7, "United States", 4, "TV-MA"),
    ("Don't Look Up", "Movie", "Netflix", "Comedies", 2021, 7.2, "United States", 138, "R"),
    ("The Adam Project", "Movie", "Netflix", "Action & Adventure", 2022, 6.7, "United States", 106, "PG-13"),
    ("Glass Onion", "Movie", "Netflix", "Comedies", 2022, 7.1, "United States", 139, "PG-13"),
    ("Lupin", "TV Show", "Netflix", "Crime TV Shows", 2021, 7.5, "France", 2, "TV-MA"),
    ("Sex Education", "TV Show", "Netflix", "Comedies", 2019, 8.3, "United Kingdom", 4, "TV-MA"),
    ("The Umbrella Academy", "TV Show", "Netflix", "Sci-Fi & Fantasy", 2019, 7.9, "United States", 3, "TV-14"),
    ("Russian Doll", "TV Show", "Netflix", "Comedies", 2019, 7.8, "United States", 2, "TV-MA"),
    ("BoJack Horseman", "TV Show", "Netflix", "Anime Series", 2014, 8.7, "United States", 6, "TV-MA"),
    ("The Mandalorian", "TV Show", "Disney+", "Action & Adventure", 2019, 8.7, "United States", 3, "TV-14"),
    ("WandaVision", "TV Show", "Disney+", "Sci-Fi & Fantasy", 2021, 7.9, "United States", 1, "TV-PG"),
    ("Loki", "TV Show", "Disney+", "Action & Adventure", 2021, 8.2, "United States", 2, "TV-14"),
    ("Avatar: The Way of Water", "Movie", "Disney+", "Sci-Fi & Fantasy", 2022, 7.6, "United States", 192, "PG-13"),
    ("Encanto", "Movie", "Disney+", "Children & Family Movies", 2021, 7.2, "United States", 102, "PG"),
    ("Moana", "Movie", "Disney+", "Children & Family Movies", 2016, 7.6, "United States", 107, "PG"),
    ("Frozen II", "Movie", "Disney+", "Children & Family Movies", 2019, 6.8, "United States", 103, "PG"),
    ("Hawkeye", "TV Show", "Disney+", "Action & Adventure", 2021, 7.6, "United States", 1, "TV-14"),
    ("Andor", "TV Show", "Disney+", "Sci-Fi & Fantasy", 2022, 8.4, "United States", 2, "TV-14"),
    ("Ms. Marvel", "TV Show", "Disney+", "Action & Adventure", 2022, 6.0, "United States", 1, "TV-14"),
    ("The Bad Batch", "TV Show", "Disney+", "Sci-Fi & Fantasy", 2021, 8.0, "United States", 3, "TV-PG"),
    ("Soul", "Movie", "Disney+", "Children & Family Movies", 2020, 8.0, "United States", 100, "PG"),
    ("Luca", "Movie", "Disney+", "Children & Family Movies", 2021, 7.4, "United States", 95, "PG"),
    ("Turning Red", "Movie", "Disney+", "Children & Family Movies", 2022, 7.0, "United States", 100, "PG"),
    ("The Book of Boba Fett", "TV Show", "Disney+", "Action & Adventure", 2021, 6.4, "United States", 1, "TV-14"),
    ("Moon Knight", "TV Show", "Disney+", "Action & Adventure", 2022, 7.3, "United States", 1, "TV-14"),
    ("Percy Jackson and the Olympians", "TV Show", "Disney+", "Sci-Fi & Fantasy", 2023, 7.6, "United States", 1, "TV-PG"),
    ("The Boys", "TV Show", "Prime Video", "Action & Adventure", 2019, 8.7, "United States", 4, "TV-MA"),
    ("Fleabag", "TV Show", "Prime Video", "Comedies", 2016, 8.7, "United Kingdom", 2, "TV-MA"),
    ("The Marvelous Mrs. Maisel", "TV Show", "Prime Video", "Comedies", 2017, 8.7, "United States", 5, "TV-MA"),
    ("The Peripheral", "TV Show", "Prime Video", "Sci-Fi & Fantasy", 2022, 7.5, "United States", 1, "TV-MA"),
    ("Reacher", "TV Show", "Prime Video", "Action & Adventure", 2022, 8.1, "United States", 2, "TV-MA"),
    ("The Wheel of Time", "TV Show", "Prime Video", "Sci-Fi & Fantasy", 2021, 7.1, "United States", 2, "TV-14"),
    ("Jack Ryan", "TV Show", "Prime Video", "Action & Adventure", 2018, 8.0, "United States", 4, "TV-MA"),
    ("The Rings of Power", "TV Show", "Prime Video", "Sci-Fi & Fantasy", 2022, 6.9, "United States", 1, "TV-14"),
    ("Invincible", "TV Show", "Prime Video", "Anime Series", 2021, 8.7, "United States", 2, "TV-MA"),
    ("Upload", "TV Show", "Prime Video", "Comedies", 2020, 7.9, "United States", 3, "TV-MA"),
    ("The Tomorrow War", "Movie", "Prime Video", "Action & Adventure", 2021, 6.5, "United States", 138, "PG-13"),
    ("Sound of Metal", "Movie", "Prime Video", "Dramas", 2019, 7.7, "United States", 120, "R"),
    ("Coming 2 America", "Movie", "Prime Video", "Comedies", 2021, 5.3, "United States", 110, "PG-13"),
    ("Air", "Movie", "Prime Video", "Dramas", 2023, 7.4, "United States", 112, "R"),
    ("Game of Thrones", "TV Show", "HBO Max", "Dramas", 2011, 9.2, "United States", 8, "TV-MA"),
    ("Succession", "TV Show", "HBO Max", "Dramas", 2018, 8.8, "United States", 4, "TV-MA"),
    ("The Last of Us", "TV Show", "HBO Max", "Dramas", 2023, 8.8, "United States", 1, "TV-MA"),
    ("Euphoria", "TV Show", "HBO Max", "Dramas", 2019, 8.4, "United States", 2, "TV-MA"),
    ("The White Lotus", "TV Show", "HBO Max", "Dramas", 2021, 7.9, "United States", 2, "TV-MA"),
    ("House of the Dragon", "TV Show", "HBO Max", "Sci-Fi & Fantasy", 2022, 8.4, "United States", 1, "TV-MA"),
    ("Chernobyl", "TV Show", "HBO Max", "Dramas", 2019, 9.4, "United States", 1, "TV-MA"),
    ("Barry", "TV Show", "HBO Max", "Comedies", 2018, 8.4, "United States", 4, "TV-MA"),
    ("True Detective", "TV Show", "HBO Max", "Crime TV Shows", 2014, 8.9, "United States", 4, "TV-MA"),
    ("Westworld", "TV Show", "HBO Max", "Sci-Fi & Fantasy", 2016, 8.5, "United States", 4, "TV-MA"),
    ("Curb Your Enthusiasm", "TV Show", "HBO Max", "Comedies", 2000, 8.7, "United States", 12, "TV-MA"),
    ("Mare of Easttown", "TV Show", "HBO Max", "Crime TV Shows", 2021, 8.4, "United States", 1, "TV-MA"),
    ("Watchmen", "TV Show", "HBO Max", "Sci-Fi & Fantasy", 2019, 8.5, "United States", 1, "TV-MA"),
    ("Severance", "TV Show", "Apple TV+", "Thrillers", 2022, 8.7, "United States", 2, "TV-MA"),
    ("Ted Lasso", "TV Show", "Apple TV+", "Comedies", 2020, 8.8, "United States", 3, "TV-MA"),
    ("The Morning Show", "TV Show", "Apple TV+", "Dramas", 2019, 7.7, "United States", 3, "TV-MA"),
    ("Foundation", "TV Show", "Apple TV+", "Sci-Fi & Fantasy", 2021, 7.5, "United States", 2, "TV-14"),
    ("Slow Horses", "TV Show", "Apple TV+", "Thrillers", 2022, 8.2, "United States", 3, "TV-MA"),
    ("Pachinko", "TV Show", "Apple TV+", "Dramas", 2022, 8.4, "United States", 1, "TV-MA"),
    ("CODA", "Movie", "Apple TV+", "Dramas", 2021, 8.0, "United States", 111, "PG-13"),
    ("Prehistoric Planet", "TV Show", "Apple TV+", "Documentaries", 2022, 9.2, "United Kingdom", 1, "TV-PG"),
    ("For All Mankind", "TV Show", "Apple TV+", "Sci-Fi & Fantasy", 2019, 8.1, "United States", 4, "TV-MA"),
    ("Causeway", "Movie", "Apple TV+", "Dramas", 2022, 6.7, "United States", 94, "R"),
    ("Killers of the Flower Moon", "Movie", "Apple TV+", "Crime Movies", 2023, 7.6, "United States", 206, "R"),
    ("Napoleon", "Movie", "Apple TV+", "Dramas", 2023, 6.5, "United States", 158, "R"),
    ("Interstellar", "Movie", "Prime Video", "Sci-Fi & Fantasy", 2014, 8.6, "United States", 169, "PG-13"),
    ("The Boys Presents: Diabolical", "TV Show", "Prime Video", "Anime Series", 2022, 7.0, "United States", 1, "TV-MA"),
    ("Vikings: Valhalla", "TV Show", "Netflix", "Action & Adventure", 2022, 7.4, "Ireland", 2, "TV-MA"),
    ("Cobra Kai", "TV Show", "Netflix", "Comedies", 2018, 8.5, "United States", 6, "TV-14"),
    ("Arcane", "TV Show", "Netflix", "Anime Series", 2021, 9.0, "United States", 1, "TV-14"),
    ("The Sandman", "TV Show", "Netflix", "Sci-Fi & Fantasy", 2022, 7.9, "United States", 1, "TV-MA"),
    ("Outer Banks", "TV Show", "Netflix", "Action & Adventure", 2020, 7.5, "United States", 3, "TV-MA"),
    ("Maid", "TV Show", "Netflix", "Dramas", 2021, 8.3, "United States", 1, "TV-MA"),
    ("Tiger King", "TV Show", "Netflix", "Documentaries", 2020, 7.5, "United States", 2, "TV-MA"),
    ("The Social Dilemma", "Movie", "Netflix", "Documentaries", 2020, 7.6, "United States", 94, "PG-13"),
    ("Always Be My Maybe", "Movie", "Netflix", "Romantic Movies", 2019, 6.9, "United States", 102, "TV-14"),
    ("To All the Boys I've Loved Before", "Movie", "Netflix", "Romantic Movies", 2018, 7.0, "United States", 99, "TV-14"),
    ("The Kissing Booth", "Movie", "Netflix", "Romantic Movies", 2018, 6.1, "United States", 103, "TV-14"),
    ("Purple Hearts", "Movie", "Netflix", "Romantic Movies", 2022, 6.8, "United States", 122, "TV-MA"),
    ("Crash Landing on You", "TV Show", "Netflix", "Romantic Movies", 2019, 8.7, "South Korea", 1, "TV-14"),
    ("Heartstopper", "TV Show", "Netflix", "Romantic Movies", 2022, 8.4, "United Kingdom", 2, "TV-14"),
    ("Hocus Pocus 2", "Movie", "Disney+", "Children & Family Movies", 2022, 5.6, "United States", 103, "PG"),
    ("Free Guy", "Movie", "Disney+", "Comedies", 2021, 7.7, "United States", 115, "PG-13"),
    ("The Princess Bride", "Movie", "Disney+", "Romantic Movies", 1987, 8.0, "United States", 98, "PG"),
    ("Modern Family", "TV Show", "Disney+", "Comedies", 2009, 8.4, "United States", 11, "PG"),
    ("Big Sky", "TV Show", "Disney+", "Crime TV Shows", 2020, 6.4, "United States", 3, "TV-14"),
    ("The Last Duel", "Movie", "Disney+", "Dramas", 2021, 7.3, "United States", 152, "R"),
    ("Nightmare Alley", "Movie", "HBO Max", "Crime Movies", 2021, 6.7, "United States", 150, "R"),
    ("Dune", "Movie", "HBO Max", "Sci-Fi & Fantasy", 2021, 8.0, "United States", 155, "PG-13"),
    ("Joker", "Movie", "HBO Max", "Crime Movies", 2019, 8.4, "United States", 122, "R"),
    ("It: Chapter Two", "Movie", "HBO Max", "Horror Movies", 2019, 6.5, "United States", 169, "R"),
    ("Aquaman", "Movie", "HBO Max", "Action & Adventure", 2018, 6.8, "United States", 143, "PG-13"),
    ("A Star Is Born", "Movie", "HBO Max", "Romantic Movies", 2018, 7.6, "United States", 136, "R"),
    ("La La Land", "Movie", "Prime Video", "Romantic Movies", 2016, 8.0, "United States", 128, "PG-13"),
    ("Knives Out", "Movie", "Prime Video", "Crime Movies", 2019, 7.9, "United States", 130, "PG-13"),
    ("The Grand Tour", "TV Show", "Prime Video", "Documentaries", 2016, 8.7, "United Kingdom", 5, "TV-MA"),
    ("Good Omens", "TV Show", "Prime Video", "Sci-Fi & Fantasy", 2019, 8.1, "United Kingdom", 2, "TV-14"),
    ("Daisy Jones & The Six", "TV Show", "Prime Video", "Dramas", 2023, 7.8, "United States", 1, "TV-MA"),
    ("Tetris", "Movie", "Apple TV+", "Dramas", 2023, 7.0, "United States", 118, "R"),
    ("Greyhound", "Movie", "Apple TV+", "Action & Adventure", 2020, 6.7, "United States", 91, "PG-13"),
    ("Wolfwalkers", "Movie", "Apple TV+", "Children & Family Movies", 2020, 8.0, "Ireland", 103, "PG"),
    ("Black Mirror", "TV Show", "Netflix", "Sci-Fi & Fantasy", 2011, 8.7, "United Kingdom", 6, "TV-MA"),
    ("Mindhunter", "TV Show", "Netflix", "Crime TV Shows", 2017, 8.6, "United States", 2, "TV-MA"),
    ("The Haunting of Hill House", "TV Show", "Netflix", "Horror Movies", 2018, 8.6, "United States", 1, "TV-MA"),
    ("Marriage Story", "Movie", "Netflix", "Romantic Movies", 2019, 7.9, "United States", 137, "R"),
    ("The Platform", "Movie", "Netflix", "Horror Movies", 2019, 7.0, "Spain", 94, "TV-MA"),
]

GENRES = [
    "Dramas", "Comedies", "Action & Adventure", "Crime TV Shows",
    "Sci-Fi & Fantasy", "Horror Movies", "Romantic Movies",
    "Documentaries", "Children & Family Movies", "Anime Series",
    "Thrillers", "Crime Movies"
]

PLATFORMS = ["Netflix", "Disney+", "Prime Video", "HBO Max", "Apple TV+"]

COUNTRIES = ["United States", "United Kingdom", "South Korea", "Spain",
             "France", "Germany", "Mexico", "Ireland", "India", "Canada",
             "Japan", "Brazil", "Argentina"]

RATINGS_MOVIE = ["G", "PG", "PG-13", "R", "TV-MA", "TV-14"]
RATINGS_TV = ["TV-Y", "TV-Y7", "TV-G", "TV-PG", "TV-14", "TV-MA"]

DIRECTORS = [
    "Greta Gerwig", "Denis Villeneuve", "Bong Joon-ho", "Rian Johnson",
    "Chloé Zhao", "Taika Waititi", "Jane Campion", "Park Chan-wook",
    "Ryan Coogler", "Patty Jenkins", "Ana Lily Amirpour", "Pedro Almodóvar",
    "Alfonso Cuarón", "Quentin Tarantino", "Sofia Coppola", "Steven Soderbergh"
]

ACTORS_POOL = [
    "Emma Stone", "Pedro Pascal", "Zendaya", "Oscar Isaac", "Florence Pugh",
    "Millie Bobby Brown", "Idris Elba", "Anya Taylor-Joy", "Timothée Chalamet",
    "Sandra Oh", "Henry Cavill", "Lupita Nyong'o", "Ana de Armas",
    "Michael B. Jordan", "Saoirse Ronan", "Dev Patel", "Awkwafina",
    "Riz Ahmed", "Brie Larson", "Pedro Almodóvar Jr.", "Daniel Kaluuya",
    "Margot Robbie", "Adam Driver", "Cate Blanchett", "Mahershala Ali"
]

DESCRIPTION_TEMPLATES = {
    "Dramas": "Una historia profunda sobre {tema}, {conector}.",
    "Comedies": "Una comedia ligera centrada en {tema}, {conector}.",
    "Action & Adventure": "Una trepidante aventura sobre {tema}, {conector}.",
    "Crime TV Shows": "Una intrincada trama policial sobre {tema}, {conector}.",
    "Sci-Fi & Fantasy": "Un universo de ciencia ficción centrado en {tema}, {conector}.",
    "Horror Movies": "Una experiencia de terror sobre {tema}, {conector}.",
    "Romantic Movies": "Una historia de amor sobre {tema}, {conector}.",
    "Documentaries": "Un documental que investiga {tema}, {conector}.",
    "Children & Family Movies": "Una aventura familiar sobre {tema}, {conector}.",
    "Anime Series": "Una serie animada sobre {tema}, {conector}.",
    "Thrillers": "Un thriller psicológico sobre {tema}, {conector}.",
    "Crime Movies": "Una película criminal sobre {tema}, {conector}.",
}

TEMAS = [
    "una familia que enfrenta secretos del pasado", "un grupo de amigos en busca de la verdad",
    "un detective obsesionado con un caso sin resolver", "una joven que descubre poderes ocultos",
    "una pareja que se reencuentra después de años", "un equipo que planea el golpe perfecto",
    "una expedición a un lugar desconocido", "un científico al borde de un descubrimiento revolucionario",
    "una rivalidad entre hermanos", "una ciudad al borde del colapso",
    "un viaje que cambia el destino de sus protagonistas", "una venganza que se extiende por generaciones",
    "un romance imposible en tiempos difíciles", "una criatura que acecha en la oscuridad",
    "un grupo de sobrevivientes en un mundo postapocalíptico", "una competencia que pone todo en juego",
    "un crimen que conmociona a una pequeña comunidad", "una segunda oportunidad inesperada",
]

# Frases conectoras para variar las descripciones sintéticas y que el
# motor de similitud por contenido (embeddings) tenga texto más rico
# para comparar, en lugar de descripciones idénticas por género.
DESCRIPTION_CONNECTORS = [
    "ambientada en un contexto de tensión creciente",
    "con un ritmo que combina momentos íntimos y de gran escala",
    "narrada desde múltiples puntos de vista",
    "con un elenco que aporta matices inesperados",
    "que pone a prueba los vínculos entre sus personajes",
    "donde cada decisión tiene consecuencias duraderas",
    "con escenarios que van de lo cotidiano a lo extraordinario",
    "que mezcla nostalgia y un futuro incierto",
    "con un trasfondo histórico que enriquece la trama",
    "que combina humor y momentos de profunda emoción",
    "con un final que invita a la reflexión",
    "ambientada en una época de grandes cambios sociales",
]

# ------------------------------------------------------------------
# 2. Construcción del DataFrame semilla
# ------------------------------------------------------------------
def build_seed_df():
    rows = []
    for i, (titulo, tipo, plat, genero, anio, score, pais, dur, rating) in enumerate(SEED_TITLES, start=1):
        elenco = ", ".join(random.sample(ACTORS_POOL, k=3))
        director = random.choice(DIRECTORS) if tipo == "Movie" else ""
        tema = random.choice(TEMAS)
        conector = random.choice(DESCRIPTION_CONNECTORS)
        desc = DESCRIPTION_TEMPLATES[genero].format(tema=tema, conector=conector)
        fecha_agregado = datetime(2024, random.randint(1, 12), random.randint(1, 28))
        rows.append({
            "show_id": f"s{i}",
            "titulo": titulo,
            "tipo": tipo,
            "plataforma": plat,
            "director": director,
            "elenco": elenco,
            "pais": pais,
            "fecha_agregado": fecha_agregado.strftime("%Y-%m-%d"),
            "anio_lanzamiento": anio,
            "clasificacion": rating,
            "duracion": dur,
            "genero": genero,
            "descripcion": desc,
            "puntaje": score,
        })
    return pd.DataFrame(rows)


# ------------------------------------------------------------------
# 3. Generación sintética para escalar el dataset
# ------------------------------------------------------------------
WORD_BANK_TITLES_PREFIX = [
    "El último", "La sombra de", "Más allá de", "Crónicas de", "El secreto de",
    "Bajo la luz de", "El despertar de", "Fragmentos de", "El legado de",
    "La caída de", "Voces de", "El enigma de", "Tras las huellas de",
    "El silencio de", "Historias de", "El renacer de", "La promesa de",
    "Más allá del", "El precio de", "La última noche en",
]

WORD_BANK_TITLES_SUFFIX = [
    "Medianoche", "el Norte", "la Memoria", "Babel", "los Olvidados",
    "Vermont", "Saturno", "la Frontera", "Brooklyn", "el Imperio",
    "Kioto", "la Tormenta", "Andalucía", "el Desierto", "Groenlandia",
    "los Vivos", "la Eternidad", "Marrakech", "el Abismo", "Siberia",
]

_title_counter = {"n": 0}

def random_title(used_titles):
    """
    Genera un título sintético. Combina prefijo + sufijo y, si la
    combinación ya existe (las combinaciones base son finitas:
    20 x 20 = 400), agrega un sufijo numerico tipo '(Parte N)' para
    garantizar unicidad sin loops infinitos.
    """
    base = f"{random.choice(WORD_BANK_TITLES_PREFIX)} {random.choice(WORD_BANK_TITLES_SUFFIX)}"
    if base not in used_titles:
        used_titles.add(base)
        return base
    _title_counter["n"] += 1
    t = f"{base} (Parte {_title_counter['n']})"
    used_titles.add(t)
    return t


def build_synthetic_df(n_rows, start_id, used_titles):
    """
    Genera n_rows títulos sintéticos con distribuciones realistas:
    - Más contenido de tipo 'Movie' que 'TV Show' (aprox 70/30, como en Netflix real)
    - Distribución de plataformas no uniforme (Netflix con más catálogo)
    - Años concentrados entre 2000-2024, con más densidad post-2015
    - Puntajes con distribución normal centrada en 6.8
    """
    rows = []
    platform_weights = [0.35, 0.18, 0.17, 0.16, 0.14]  # Netflix tiene más catálogo
    type_weights = [0.68, 0.32]  # Movie, TV Show

    for i in range(n_rows):
        sid = start_id + i
        tipo = np.random.choice(["Movie", "TV Show"], p=type_weights)
        plat = np.random.choice(PLATFORMS, p=platform_weights)
        genero = random.choice(GENRES)

        # Año: distribución sesgada hacia años recientes
        anio = int(np.clip(np.random.normal(2016, 6), 1990, 2024))

        # Puntaje: distribución normal centrada en 6.8, acotada 3.5-9.5
        score = float(np.clip(np.random.normal(6.8, 1.1), 3.5, 9.5))
        score = round(score, 1)

        pais = random.choice(COUNTRIES)
        rating = random.choice(RATINGS_MOVIE if tipo == "Movie" else RATINGS_TV)

        if tipo == "Movie":
            duracion = int(np.clip(np.random.normal(108, 22), 60, 210))
            director = random.choice(DIRECTORS)
        else:
            duracion = int(np.clip(np.random.normal(2.5, 1.3), 1, 9))  # temporadas
            director = ""

        elenco = ", ".join(random.sample(ACTORS_POOL, k=3))
        tema = random.choice(TEMAS)
        conector = random.choice(DESCRIPTION_CONNECTORS)
        desc = DESCRIPTION_TEMPLATES[genero].format(tema=tema, conector=conector)

        fecha_agregado = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 1460))

        rows.append({
            "show_id": f"s{sid}",
            "titulo": random_title(used_titles),
            "tipo": tipo,
            "plataforma": plat,
            "director": director,
            "elenco": elenco,
            "pais": pais,
            "fecha_agregado": fecha_agregado.strftime("%Y-%m-%d"),
            "anio_lanzamiento": anio,
            "clasificacion": rating,
            "duracion": duracion,
            "genero": genero,
            "descripcion": desc,
            "puntaje": score,
        })

    return pd.DataFrame(rows)


def main(n_total=5000, output_path=None):
    if output_path is None:
        out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(out_dir, exist_ok=True)
        output_path = os.path.join(out_dir, "streaming_dataset.csv")
    seed_df = build_seed_df()
    used_titles = set(seed_df["titulo"].tolist())

    n_synthetic = max(0, n_total - len(seed_df))
    synth_df = build_synthetic_df(n_synthetic, start_id=len(seed_df) + 1, used_titles=used_titles)

    full_df = pd.concat([seed_df, synth_df], ignore_index=True)
    full_df = full_df.sample(frac=1, random_state=42).reset_index(drop=True)  # shuffle

    full_df.to_csv(output_path, index=False)
    print(f"Dataset generado: {len(full_df)} registros -> {output_path}")
    print(full_df.head())
    print("\nDistribución por plataforma:")
    print(full_df["plataforma"].value_counts())
    print("\nDistribución por tipo:")
    print(full_df["tipo"].value_counts())
    return full_df


if __name__ == "__main__":
    main()
