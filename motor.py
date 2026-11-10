"""Motor de recomendación que el estudiante debe completar.

Se proporcionan carga, validaciones y funciones auxiliares. Complete únicamente
los cuatro bloques señalados. Las puntuaciones de similitud no son probabilidades.
Este ejercicio no entrena un modelo supervisado: representa textos mediante
TF-IDF y actualiza un perfil con una regla explícita.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import normalize


def cargar_catalogo(ruta: Path) -> pd.DataFrame:
    """Carga y valida el CSV proporcionado, sin modificar su orden."""
    recursos = pd.read_csv(ruta, dtype=str, keep_default_na=False)
    columnas = ["id", "titulo", "descripcion", "etiquetas"]
    faltantes = set(columnas) - set(recursos.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas: {', '.join(sorted(faltantes))}.")
    if recursos.empty:
        raise ValueError("El catálogo no contiene recursos.")
    for columna in columnas:
        recursos[columna] = recursos[columna].str.strip()
        if (recursos[columna] == "").any():
            raise ValueError(f"La columna {columna} contiene valores vacíos.")
    if recursos["id"].duplicated().any():
        raise ValueError("Los identificadores de recursos deben ser únicos.")
    return recursos.reset_index(drop=True)


def cargar_perfiles(ruta: Path) -> dict:
    """Los intereses vacíos son válidos y se usan en la prueba T4."""
    with ruta.open(encoding="utf-8") as archivo:
        perfiles = json.load(archivo)
    if not isinstance(perfiles, dict) or not perfiles:
        raise ValueError("Se requiere un objeto JSON con perfiles de usuario.")
    for usuario_id, datos in perfiles.items():
        if not isinstance(usuario_id, str) or not usuario_id.strip():
            raise ValueError("Hay un identificador de usuario inválido.")
        if not isinstance(datos, dict):
            raise ValueError(f"El perfil {usuario_id} debe ser un objeto.")
        for campo in ("nombre", "intereses"):
            if not isinstance(datos.get(campo), str):
                raise ValueError(f"El campo {campo} de {usuario_id} debe ser texto.")
    return perfiles


def construir_indice(recursos: pd.DataFrame) -> tuple:
    """El vocabulario se aprende una vez y únicamente a partir de etiquetas."""
    vectorizador = TfidfVectorizer()
    matriz = vectorizador.fit_transform(recursos["etiquetas"]).toarray()
    return vectorizador, matriz


def crear_perfil(intereses: str, vectorizador: TfidfVectorizer) -> np.ndarray:
    """Devuelve un vector de una dimensión con el vocabulario del catálogo."""
    # TODO 1 (completado): se usa transform (no fit_transform) para proyectar los
    # intereses en el mismo vocabulario e IDF aprendidos del catálogo. Los términos
    # desconocidos se ignoran, por lo que un texto vacío o fuera del vocabulario
    # produce un vector de ceros. Se devuelve una copia 1D independiente por usuario.
    texto = intereses if isinstance(intereses, str) else ""
    vector = vectorizador.transform([texto]).toarray()[0]
    return np.asarray(vector, dtype=float).copy()


def calcular_puntuaciones(perfil: np.ndarray, matriz: np.ndarray) -> np.ndarray:
    """Devuelve una puntuación por fila del catálogo, en el mismo orden."""
    # TODO 2 (completado): cosine_similarity espera matrices 2D, por eso el perfil
    # se envuelve en una lista. El resultado (1 x n) se reduce a 1D. Con un perfil
    # nulo scikit-learn devuelve ceros (no divide por cero), así que no se requiere
    # un caso especial; nan_to_num es solo una salvaguarda.
    perfil_2d = np.asarray(perfil, dtype=float).reshape(1, -1)
    puntuaciones = cosine_similarity(perfil_2d, matriz)[0]
    return np.nan_to_num(puntuaciones, nan=0.0)


def recomendar(
    perfil: np.ndarray,
    recursos: pd.DataFrame,
    matriz: np.ndarray,
    vectorizador: TfidfVectorizer,
    top_k: int = 3,
) -> list[dict]:
    """Devuelve hasta top_k resultados positivos usando construir_resultado."""
    # TODO 3 (completado): se calculan las puntuaciones de los 12 candidatos, se
    # descartan las que no son positivas y se ordena por (-puntuación, id), es decir,
    # descendente por similitud y ascendente por id en caso de empate. Las
    # puntuaciones se conservan sin redondear; solo se redondean al mostrarlas.
    puntuaciones = calcular_puntuaciones(perfil, matriz)
    candidatos = [
        (float(puntuacion), str(recursos.iloc[indice]["id"]), indice)
        for indice, puntuacion in enumerate(puntuaciones)
        if puntuacion > 0
    ]
    candidatos.sort(key=lambda c: (-c[0], c[1]))
    return [
        construir_resultado(indice, puntuacion, perfil, recursos, matriz, vectorizador)
        for puntuacion, _, indice in candidatos[:top_k]
    ]


def actualizar_perfil(perfil: np.ndarray, vector_recurso: np.ndarray) -> np.ndarray:
    """Actualiza el perfil cuando el usuario pulsa Me interesa sobre un recurso."""
    # TODO 4 (completado): mezcla convexa con alpha = 0.6 (peso de la interacción
    # reciente) y normalización L2 para que el perfil mantenga norma 1 tras
    # actualizaciones sucesivas. Se devuelve un vector nuevo; no se modifica el
    # perfil recibido. Si la mezcla fuese nula, normalize devuelve ceros.
    alpha = 0.6
    mezcla = (1 - alpha) * np.asarray(perfil, dtype=float) + alpha * np.asarray(
        vector_recurso, dtype=float
    )
    return normalize([mezcla])[0]


def obtener_indice(recursos: pd.DataFrame, recurso_id: str) -> int:
    """Valida el identificador antes de modificar un perfil."""
    coincidencias = recursos.index[recursos["id"] == recurso_id].tolist()
    if not coincidencias:
        raise ValueError(f"No existe el recurso {recurso_id}.")
    return int(coincidencias[0])


def explicar_coincidencias(
    perfil: np.ndarray,
    vector_recurso: np.ndarray,
    vectorizador: TfidfVectorizer,
) -> str:
    """La explicación se limita a términos compartidos con peso positivo."""
    vocabulario = vectorizador.get_feature_names_out()
    mascara = (np.asarray(perfil) > 0) & (np.asarray(vector_recurso) > 0)
    terminos = vocabulario[mascara].tolist()
    if not terminos:
        return "No hay términos compartidos con peso positivo."
    return "Términos compartidos: " + ", ".join(terminos) + "."


def construir_resultado(
    indice: int,
    puntuacion: float,
    perfil: np.ndarray,
    recursos: pd.DataFrame,
    matriz: np.ndarray,
    vectorizador: TfidfVectorizer,
) -> dict:
    """Función auxiliar para usar dentro de recomendar."""
    recurso = recursos.iloc[indice]
    return {
        "id": str(recurso["id"]),
        "titulo": str(recurso["titulo"]),
        "puntuacion": float(puntuacion),
        "explicacion": explicar_coincidencias(perfil, matriz[indice], vectorizador),
    }


def describir_perfil(perfil: np.ndarray, vectorizador: TfidfVectorizer) -> dict:
    """Representación legible del estado; no cambia el vector utilizado."""
    vocabulario = vectorizador.get_feature_names_out()
    pares = [(str(termino), float(peso)) for termino, peso in zip(vocabulario, perfil)
             if peso > 0]
    pares.sort(key=lambda par: (-par[1], par[0]))
    return {termino: round(peso, 6) for termino, peso in pares}
