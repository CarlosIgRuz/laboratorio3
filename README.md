# Laboratorio 3 — Aplicación inteligente adaptativa

## Identificación

- Integrante: Carlos Ignacio Ruz Aguilera (trabajo individual)
- Curso y sección: Ingeniería Web Avanzada — OII436-1
- URL del repositorio: https://github.com/CarlosIgRuz/laboratorio3
- Fecha: 9 de noviembre de 2026

## Objetivo y alcance

Recomendador de recursos de aprendizaje basado en contenido. Cada recurso y cada
perfil se representan con TF-IDF sobre la columna `etiquetas`, se comparan con la
similitud del coseno y el perfil del usuario activo se actualiza automáticamente
al registrar **Me interesa**. La implementación es por consola (sin Angular).

Se completaron únicamente los cuatro bloques TODO de `motor.py`; `app.py` y los
datos se conservan como fueron entregados.

## Preparación y ejecución

Versión de Python utilizada: **Python 3.13** (funciona con Python 3.10 o posterior).

```bash
cd laboratorio3
python -m venv .venv            # En Windows también: py -m venv .venv
```

Activación del entorno (comando utilizado: `source .venv/bin/activate`):

```bash
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
# Windows CMD
.venv\Scripts\activate.bat
```

Instalación de dependencias y comprobación:

```bash
python -m pip install -r requirements.txt
python -c "import sys; print(sys.executable)"   # debe apuntar a .venv
python app.py --comprobar
```

Ejecución:

```bash
python app.py --demo   # ejecuta T1–T4 y genera evidencias/
python app.py          # modo interactivo
```

`--comprobar` informa 12 recursos, 4 usuarios y una matriz TF-IDF de 12 × 17
(vocabulario: angular, api, componentes, consultas, datos, formularios, funciones,
graficos, http, interfaces, pandas, python, sql, tablas, validacion, variables, web).

`.gitignore` excluye `.venv/`, `__pycache__/`, `*.py[cod]`, `.DS_Store` y `node_modules/`.

### Reproducción desde una copia nueva

No se requieren instrucciones adicionales: basta con clonar, crear el entorno,
instalar `requirements.txt` y ejecutar `python app.py --demo`. El modo demo parte
siempre de los perfiles de `datos/perfiles.json`, por lo que las evidencias se
regeneran con los mismos valores.

## Catálogo y datos (Paso 1)

- `datos/recursos.csv` tiene las columnas `id`, `titulo`, `descripcion`, `etiquetas`
  y 12 recursos (R01–R12). **Solo `etiquetas`** interviene en el cálculo TF-IDF;
  `titulo` y `descripcion` se usan para presentar los resultados.
- `cargar_catalogo` lee todo como texto (`dtype=str`, `keep_default_na=False`),
  elimina espacios, **rechaza valores vacíos** en cualquiera de las cuatro columnas
  y **rechaza identificadores repetidos** con un `ValueError`; la aplicación muestra
  el error y termina sin calcular nada.
- `datos/perfiles.json` contiene u1 (`python datos pandas`), u2
  (`angular componentes interfaces`), u3 (intereses vacíos, permitido) y u4
  (`zzxyz123`, fuera del vocabulario).

## Implementación de `motor.py`

| Función | Implementación |
|---|---|
| `crear_perfil` | `vectorizador.transform([intereses]).toarray()[0]`: proyecta los intereses al espacio ya ajustado al catálogo, sin reajustar. Devuelve un vector 1D nuevo por usuario, por lo que u1 y u2 tienen estados independientes. |
| `calcular_puntuaciones` | `cosine_similarity([perfil], matriz)[0]`: una puntuación por recurso, en el orden de las filas. Con un perfil nulo devuelve 12 ceros. |
| `recomendar` | Filtra puntuaciones `> 0`, ordena con la clave `(-puntuación, id)` (descendente, desempate por id ascendente), toma hasta 3 y construye cada resultado con `construir_resultado`. Las puntuaciones no se redondean en el cálculo. |
| `actualizar_perfil` | `mezcla = 0.4 * perfil + 0.6 * recurso`, luego `normalize([mezcla])[0]` (norma L2 = 1). Devuelve un vector nuevo sin modificar el anterior. |

Un ID desconocido (por ejemplo `R99` en modo interactivo) produce
`No existe el recurso R99.` y el perfil y el historial quedan sin cambios, porque
`obtener_indice` falla antes de llamar a `actualizar_perfil`.

## Pruebas funcionales y evidencias

Resultados obtenidos con `python app.py --demo` (archivos en `evidencias/`).

| Caso | Entrada o interacción | Resultado esperado | Resultado observado | Estado |
|---|---|---|---|---|
| T1 | Recomendaciones iniciales para u1 y u2, sin interacciones. | Rankings distintos según intereses; hasta 3 resultados positivos, orden descendente, desempate por ID; R02 primero para u1 y R07 primero para u2. | **u1:** R02 (1.0000), R12 (0.4965), R03 (0.4326). **u2:** R07 (1.0000), R08 (0.5677), R09 (0.3087). Ambas listas tienen 3 resultados positivos en orden descendente. El desempate se verificó con el ranking completo de u1 tras valorar R04: R05 y R06 (0.4378) y R10 y R11 (0.1026) aparecen en orden de ID ascendente. | Cumple |
| T2 | u1 marca «Me interesa» en R04 (no estaba en su top 3) y se recalcula en la misma ejecución. | Cambia el vector de u1; se registra el evento; cambia la puntuación de al menos un recurso no valorado (R05); se conservan los 12 candidatos; R04 pasa al primer lugar. | Historial de u1: `{numero: 1, accion: Me interesa, recurso: R04}`. El perfil incorpora `api` y `web`. Nuevo ranking: R04 (0.8752), R02 (0.6880), R09 (0.4958). R05 sube de 0.0000 a 0.4378 y R09 de 0.0000 a 0.4958. Los 12 recursos tienen puntuación antes y después (CSV). | Cumple |
| T3 | Consultar u2 después de la interacción de u1. | El vector, el historial y las puntuaciones de u2 no cambian. | Perfil de u2 idéntico (`componentes 0.6575, interfaces 0.5647, angular 0.4988`), historial vacío, mismas puntuaciones y mismo ranking R07, R08, R09. Las 4 condiciones de `reporte_demo.json` son `true`. | Cumple |
| T4 | Recomendar para u3 (intereses vacíos) y u4 (`zzxyz123`). | Lista vacía y mensaje informativo para ambos; sin errores; ningún recurso con puntuación cero se presenta como relevante. | Ambos obtienen un vector nulo, 12 puntuaciones iguales a 0, lista `[]` y el mensaje «No hay coincidencias positivas. Declare intereses presentes en el catálogo.» La aplicación no falla. | Cumple |

**Interpretación.** T1 muestra que el mismo catálogo produce rankings diferentes
porque cambian los perfiles. T2 demuestra la adaptación: el evento modifica el
vector y, en consecuencia, las puntuaciones de recursos no valorados. T3 confirma
que el estado es independiente para cada usuario. T4 confirma que la aplicación no
inventa relevancia cuando no hay términos reconocidos.

### Comparación de la adaptación (u1, «Me interesa» en R04)

Perfil de u1 (pesos no nulos):

| Término | Antes | Después |
|---|---|---|
| pandas | 0.753247 | 0.376477 |
| datos | 0.465091 | 0.232455 |
| python | 0.465091 | 0.637116 |
| api | — | 0.446269 |
| web | — | 0.446269 |

Recomendaciones: **antes** R02, R12, R03 → **después** R04, R02, R09.

Puntuaciones de los mismos 12 candidatos (`evidencias/puntuaciones_antes_despues.csv`,
redondeadas a 4 decimales solo para mostrarlas):

| id | Etiquetas | Antes | Después | Diferencia |
|---|---|---|---|---|
| R01 | python variables funciones | 0.1861 | 0.2549 | +0.0688 |
| R02 | python datos pandas | 1.0000 | 0.6880 | −0.3120 |
| R03 | python datos graficos | 0.4326 | 0.4044 | −0.0282 |
| R04 *(valorado)* | python web api | 0.2510 | 0.8752 | +0.6241 |
| **R05** | web api http | 0.0000 | 0.4378 | **+0.4378** |
| R06 | web api validacion | 0.0000 | 0.4378 | +0.4378 |
| R07 | angular componentes interfaces | 0.0000 | 0.0000 | 0.0000 |
| R08 | angular formularios interfaces | 0.0000 | 0.0000 | 0.0000 |
| **R09** | angular web api | 0.0000 | 0.4958 | **+0.4958** |
| R10 | sql datos consultas | 0.2053 | 0.1026 | −0.1027 |
| R11 | sql datos tablas | 0.2053 | 0.1026 | −0.1027 |
| R12 | python sql datos | 0.4965 | 0.4642 | −0.0324 |

**Cambio en recursos no valorados (R05 y R09).** Antes de la interacción el perfil
de u1 solo tenía pesos en `python`, `datos` y `pandas`. R05 (`web api http`) y R09
(`angular web api`) no compartían ningún término con el perfil, así que su coseno
era exactamente 0. Al valorar R04 (`python web api`), la regla
`0.4·perfil + 0.6·R04` incorporó al perfil los términos `api` y `web`
(0.4463 cada uno tras normalizar). Ahora R05 y R09 comparten `api` y `web` con el
perfil: R05 sube a 0.4378 y R09 a 0.4958, con lo que R09 entra al top 3 aunque
nadie lo valoró. R09 supera a R05 porque `http` es un término exclusivo de R05 con
IDF alto que concentra peso de su vector, mientras que `angular` aparece en tres
recursos y pesa menos dentro de R09; así, la parte compartida (`api`, `web`) es
proporcionalmente mayor en R09.

Al mismo tiempo, recursos ligados a `datos`/`pandas`/`sql` bajan (R02, R10, R11)
porque el perfil normalizado redistribuyó su peso hacia `api`, `web` y `python`.
R07 y R08 siguen en 0 porque no comparten ningún término con el nuevo perfil. Este
cambio es evidencia de adaptación porque proviene únicamente de la actualización
automática del vector (no de cambiar los intereses del JSON ni de filtrar
candidatos): los 12 recursos son los mismos antes y después.

### Problemas detectados y acciones realizadas

- No se detectaron fallos: las cuatro pruebas cumplen y los resultados coinciden
  con lo indicado en la guía (u1: R02, R12, R03 → R04, R02, R09).
- Se verificó manualmente que un ID inexistente (`R99`) muestra un aviso y no
  modifica el perfil ni el historial.
- `cosine_similarity` con un vector nulo devuelve 0 en lugar de error o `NaN`;
  igualmente se añadió `np.nan_to_num` como salvaguarda.
- Observación: R04 sigue apareciendo en las recomendaciones después de valorarlo,
  porque el diseño del laboratorio conserva los 12 candidatos para comparar
  puntuaciones. En un sistema real convendría excluir recursos ya consumidos.

## Preguntas evaluadas

**1. ¿Qué información describe el contenido de los recursos y qué información constituye el perfil del usuario?**

El contenido de cada recurso está en `datos/recursos.csv`: `id`, `titulo`,
`descripcion` y `etiquetas`; solo `etiquetas` se vectoriza con TF-IDF y forma cada
fila de `matriz` (`construir_indice`). El perfil del usuario parte del campo
`intereses` de `datos/perfiles.json`, que `crear_perfil` convierte en un vector del
mismo vocabulario. Durante la ejecución, el perfil es el vector actual guardado en
`estado[usuario_id]` (app.py) junto con su historial `historial[usuario_id]`; los
intereses iniciales son solo el punto de partida.

**2. ¿Por qué se utiliza `fit_transform` sobre el catálogo y `transform` sobre los intereses? ¿Qué problema causaría ajustar un vectorizador por perfil?**

`fit_transform` aprende el vocabulario (17 términos) y los pesos IDF a partir de
todo el catálogo y los aplica a los recursos. `transform` reutiliza exactamente ese
vocabulario e IDF para los intereses, así que perfil y recursos quedan en el mismo
espacio de 17 dimensiones, con cada posición correspondiente al mismo término, y el
coseno puede compararlos. Si se ajustara un vectorizador por perfil, cada perfil
tendría su propio vocabulario (por ejemplo, 3 términos para u1) con otro orden y
otros pesos IDF calculados sobre un solo documento: los vectores tendrían
dimensiones distintas a la matriz (error en `cosine_similarity`) o, si coincidieran
en tamaño, las posiciones representarían términos diferentes y las puntuaciones no
tendrían sentido.

**3. ¿Por qué el mismo catálogo produce recomendaciones distintas para u1 y u2? ¿Una similitud de 0,80 es un 80 % de probabilidad de que el recurso guste?**

Porque la puntuación depende del perfil: u1 tiene pesos en `python`, `datos` y
`pandas`, y u2 en `angular`, `componentes` e `interfaces`. Cada uno coincide con
recursos distintos (u1 → R02, R12, R03; u2 → R07, R08, R09). No: 0,80 indica que
los vectores TF-IDF apuntan en direcciones parecidas, es decir, que comparten
términos con pesos proporcionales. Es una medida geométrica de coincidencia de
etiquetas, no una probabilidad calibrada; no se entrenó con datos de preferencias
reales ni mide la comprensión semántica o la calidad del recurso.

**4. ¿En qué se diferencia modificar manualmente los intereses iniciales de la adaptación implementada?**

Modificar los intereses iniciales es editar `perfiles.json` a mano: es una
configuración externa que se aplica al reiniciar y que no deja rastro de por qué
cambió. La adaptación implementada ocurre en tiempo de ejecución y sin
intervención: el **evento** es la acción «Me interesa» sobre un recurso (u1 → R04),
el **estado modificado** es el vector actual `estado["u1"]` (mezcla
0.4·perfil + 0.6·R04 normalizada) junto con el registro en `historial["u1"]`, y el
**efecto observable** son las nuevas puntuaciones de los 12 recursos y el nuevo
ranking en la misma sesión (R05 y R09 pasan de 0 a 0.4378 y 0.4958; R09 entra al
top 3). Los intereses del JSON no cambian.

**5. Relación con el ciclo MAPE-K.**

| Etapa | Elemento del programa |
|---|---|
| Monitorizar | Captura de la opción `m` / «Me interesa» y del ID en `interactivo`, y registro del evento en `historial[usuario_id]` dentro de `registrar_interes`. |
| Analizar | `obtener_indice` valida el ID y obtiene el vector del recurso valorado (`matriz[indice]`); `explicar_coincidencias` identifica los términos compartidos. |
| Planificar | `actualizar_perfil` decide el nuevo vector: mezcla con alpha = 0.6 y normalización L2. |
| Ejecutar | `registrar_interes` reemplaza `estado[usuario_id]` por el nuevo vector y `recomendar`/`calcular_puntuaciones` producen el nuevo ranking. |
| Conocimiento | El vectorizador y la `matriz` TF-IDF del catálogo, los perfiles (`estado`) y los historiales (`historial`) de cada usuario conservados en memoria. |

**6. Limitación y mejora propuesta.**

Limitación: el sistema solo aprende de retroalimentación positiva y solo de las
etiquetas. Un usuario no puede indicar que algo no le interesa, y el perfil puede
desplazarse fuertemente con un solo clic (alpha = 0.6 hizo que `pandas` bajara de
0.75 a 0.38), sin olvidar ni ponderar el tiempo. Además, sinónimos que no estén en
el vocabulario (por ejemplo «gráficos» vs «visualización») no se relacionan.

Mejora concreta: incorporar una acción «No me interesa» y usar una actualización
tipo Rocchio, `p' = normalize(a·p + b·media(positivos) − c·media(negativos))`, con
recorte de pesos negativos a 0. Requiere guardar en el historial la etiqueta de
cada interacción (positiva/negativa) y, opcionalmente, su fecha para aplicar un
decaimiento temporal. Los valores de `a`, `b`, `c` deberían ajustarse con datos
reales de interacción (por ejemplo, midiendo precisión@3 sobre clics posteriores)
en lugar de fijarse de forma didáctica.

## Archivos de la entrega

```
laboratorio3/
├── app.py
├── motor.py
├── datos/
│   ├── recursos.csv
│   └── perfiles.json
├── evidencias/
│   ├── reporte_demo.json
│   └── puntuaciones_antes_despues.csv
├── README.md
├── requirements.txt
└── .gitignore
```

No se incluyen `.venv`, `__pycache__` ni dependencias instaladas.
