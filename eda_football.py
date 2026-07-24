"""
=============================================================================
 ANÁLISIS EXPLORATORIO DE DATOS (EDA) - FÚTBOL ARGENTINO (2008-2022)
=============================================================================
 Dataset     : futbolargentino.xlsx
 Columnas    : Jugadores, Posicion, Edad, Altura, Pie, Fichado,
               Equipo Anterior, Valor de mercado, Temporada, Club
 Temporadas  : 2008 – 2022  |  Registros: ~12.092 jugadores
=============================================================================
"""

# ─── ENCODING (Windows / CP1252 compatibility) ───────────────────────────────
import sys, io
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ─── IMPORTACIONES ──────────────────────────────────────────────────────────
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import seaborn as sns

warnings.filterwarnings("ignore")

# ─── CONFIGURACIÓN GLOBAL DE ESTILO ─────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "#0d1117",
    "axes.facecolor":   "#161b22",
    "axes.edgecolor":   "#30363d",
    "axes.labelcolor":  "#c9d1d9",
    "axes.titlecolor":  "#f0f6fc",
    "xtick.color":      "#8b949e",
    "ytick.color":      "#8b949e",
    "text.color":       "#c9d1d9",
    "grid.color":       "#21262d",
    "grid.linestyle":   "--",
    "grid.linewidth":   0.6,
    "font.family":      "DejaVu Sans",
    "figure.dpi":       130,
})

# Paleta de colores corporativa
AZUL    = "#58a6ff"
GOLD    = "#f0a500"
ROJO    = "#f85149"
VERDE   = "#3fb950"
NARANJA = "#ffa657"
PURPURA = "#bc8cff"
GRIS    = "#484f58"

# ═══════════════════════════════════════════════════════════════════════════
# MÓDULO 1 — CARGA, DIAGNÓSTICO Y LIMPIEZA
# ═══════════════════════════════════════════════════════════════════════════

def cargar_y_limpiar(filepath: str) -> pd.DataFrame:
    """
    Carga el dataset de fútbol argentino, realiza diagnóstico completo
    y aplica una estrategia de limpieza documentada.

    Decisiones de limpieza:
    - Duplicados exactos            → Eliminación (no aportan información).
    - 'Valor de mercado' = '-'      → Convertir a NaN. El guión '-' indica
                                      datos no disponibles (jugadores sin
                                      valuación pública). Se imputa con la
                                      MEDIANA por Posición para conservar el
                                      sesgo táctico-económico.
    - 'Altura' = '-'                → Idem: mediana por posición.
    - 'Pie' = '-' o NaN             → Se reemplaza por 'No especificado'
                                      (categoría válida para análisis).
    - 'Equipo Anterior' NaN         → Se reemplaza por 'Sin dato' (1.536
                                      casos = 12.7%; no eliminamos porque
                                      perderíamos demasiada info valiosa).
    - 'Edad' y 'Temporada'          → Conversión a int64.
    - 'Valor de mercado'            → Conversión a float64 (valores en €).
    """
    sep = "-" * 60

    print("\n" + "=" * 60)
    print("  MODULO 1 - DIAGNOSTICO Y LIMPIEZA")
    print("=" * 60)

    # ── 1.0 Carga ────────────────────────────────────────────────────────
    df = pd.read_excel(filepath, engine="openpyxl")
    print(f"\n  Archivo: {filepath}")
    print(f"  Forma inicial: {df.shape[0]} filas x {df.shape[1]} columnas")

    print(f"\n  Columnas y tipos originales:")
    for col in df.columns:
        print(f"    {col:<25} {df[col].dtype}")

    # ── 1.1 Duplicados ───────────────────────────────────────────────────
    n_dup = df.duplicated().sum()
    print(f"\n{sep}")
    print(f"  1.1 DUPLICADOS: {n_dup}")
    print(f"      -> Estrategia: eliminacion directa (drop_duplicates).")
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"      OK: {len(df)} filas tras eliminacion.")

    # ── 1.2 Valor de mercado ─────────────────────────────────────────────
    print(f"\n{sep}")
    print("  1.2 VALOR DE MERCADO")
    # '-' no es un número: reemplazamos por NaN
    df["Valor de mercado"] = df["Valor de mercado"].replace("-", np.nan)
    df["Valor de mercado"] = pd.to_numeric(df["Valor de mercado"], errors="coerce")
    n_nulos_vm = df["Valor de mercado"].isnull().sum()
    print(f"      Nulos tras conversion: {n_nulos_vm} ({n_nulos_vm/len(df)*100:.1f}%)")
    # Imputar con mediana por posicion (distribucion muy sesgada a la derecha)
    mediana_vm = df.groupby("Posicion")["Valor de mercado"].transform("median")
    df["Valor de mercado"] = df["Valor de mercado"].fillna(mediana_vm)
    df["Valor de mercado"] = df["Valor de mercado"].fillna(df["Valor de mercado"].median())
    print(f"      OK: Imputado con mediana por posicion.")

    # ── 1.3 Altura ───────────────────────────────────────────────────────
    print(f"\n{sep}")
    print("  1.3 ALTURA")
    df["Altura"] = df["Altura"].replace("-", np.nan)
    df["Altura"] = pd.to_numeric(df["Altura"], errors="coerce")
    n_nulos_alt = df["Altura"].isnull().sum()
    print(f"      Nulos tras conversion: {n_nulos_alt}")
    mediana_alt = df.groupby("Posicion")["Altura"].transform("median")
    df["Altura"] = df["Altura"].fillna(mediana_alt)
    df["Altura"] = df["Altura"].fillna(df["Altura"].median())
    print(f"      OK: Imputado con mediana por posicion.")

    # ── 1.4 Pie ──────────────────────────────────────────────────────────
    print(f"\n{sep}")
    print("  1.4 PIE DOMINANTE")
    df["Pie"] = df["Pie"].replace("-", "No especificado").fillna("No especificado")
    print(f"      Distribucion: {df['Pie'].value_counts().to_dict()}")

    # ── 1.5 Equipo Anterior ──────────────────────────────────────────────
    print(f"\n{sep}")
    print("  1.5 EQUIPO ANTERIOR")
    n_nulos_ea = df["Equipo Anterior"].isnull().sum()
    df["Equipo Anterior"] = df["Equipo Anterior"].fillna("Sin dato")
    print(f"      {n_nulos_ea} nulos -> reemplazados por 'Sin dato'.")

    # ── 1.6 Tipos finales ────────────────────────────────────────────────
    print(f"\n{sep}")
    print("  1.6 CONVERSION DE TIPOS")
    df["Edad"]      = pd.to_numeric(df["Edad"], errors="coerce").astype("Int64")
    df["Temporada"] = pd.to_numeric(df["Temporada"], errors="coerce").astype("Int64")
    print(f"      'Edad' y 'Temporada' -> Int64")

    # ── 1.7 Ingeniería de features adicionales ────────────────────────────
    # Zona táctica: agrupa las 16 posiciones en 4 zonas lógicas
    mapa_zona = {
        "Portero":               "Arqueros",
        "Defensa":               "Defensores",
        "Defensa central":       "Defensores",
        "Lateral izquierdo":     "Defensores",
        "Lateral derecho":       "Defensores",
        "Pivote":                "Mediocampistas",
        "Mediocentro":           "Mediocampistas",
        "Interior derecho":      "Mediocampistas",
        "Interior izquierdo":    "Mediocampistas",
        "Centrocampista":        "Mediocampistas",
        "Mediocentro ofensivo":  "Mediocampistas",
        "Mediapunta":            "Mediocampistas",
        "Extremo izquierdo":     "Delanteros",
        "Extremo derecho":       "Delanteros",
        "Delantero centro":      "Delanteros",
        "Delantero":             "Delanteros",
    }
    df["Zona"] = df["Posicion"].map(mapa_zona).fillna("Otros")

    # Valor en millones (para visualizaciones)
    df["Valor_M"] = df["Valor de mercado"] / 1_000_000

    # ── 1.8 Reporte final ────────────────────────────────────────────────
    print(f"\n{sep}")
    print(f"  FORMA FINAL: {df.shape[0]} filas x {df.shape[1]} columnas")
    print(f"  Nulos restantes: {df.isnull().sum().sum()}")
    print("=" * 60 + "\n")

    return df


# ═══════════════════════════════════════════════════════════════════════════
# MÓDULO 2 — RESUMEN ESTADÍSTICO TÁCTICO
# ═══════════════════════════════════════════════════════════════════════════

def resumen_tactico(df: pd.DataFrame) -> None:
    """
    Genera un resumen estadístico de las métricas disponibles agrupadas
    por zona táctica y posición específica.

    Métricas analizadas:
      - Valor de mercado (€): indicador de rendimiento percibido
      - Edad: composición etaria por rol táctico
      - Altura (m): perfil físico por posición

    Se incluye análisis por temporada para ver evolución del mercado.
    """
    print("\n" + "=" * 60)
    print("  MODULO 2 - RESUMEN ESTADISTICO TACTICO")
    print("=" * 60)

    metricas = ["Valor de mercado", "Edad", "Altura"]

    # ── Por zona táctica ─────────────────────────────────────────────────
    print("\n  2.1 Media por Zona Tactica:")
    resumen_zona = df.groupby("Zona")[metricas].agg(["mean", "median", "std"]).round(2)
    n_por_zona = df.groupby("Zona")["Jugadores"].count().rename("n")
    print(pd.concat([n_por_zona, resumen_zona], axis=1).to_string())

    # ── Por posición específica ───────────────────────────────────────────
    print("\n  2.2 Media por Posicion Especifica:")
    resumen_pos = (
        df.groupby("Posicion")
        .agg(
            n               = ("Jugadores", "count"),
            valor_promedio  = ("Valor de mercado", "mean"),
            valor_mediano   = ("Valor de mercado", "median"),
            edad_promedio   = ("Edad", "mean"),
            altura_promedio = ("Altura", "mean"),
        )
        .round(2)
        .sort_values("valor_mediano", ascending=False)
    )
    print(resumen_pos.to_string())

    # ── Evolución del valor de mercado por temporada ──────────────────────
    print("\n  2.3 Evolucion valor de mercado promedio por temporada:")
    evol = df.groupby("Temporada")["Valor de mercado"].agg(["mean","median","count"]).round(0)
    print(evol.to_string())

    # ── Top 10 jugadores más valiosos ────────────────────────────────────
    print("\n  2.4 Top 10 jugadores mas valiosos (pico de carrera):")
    top10 = (
        df.groupby("Jugadores")["Valor de mercado"]
        .max()
        .reset_index()
        .nlargest(10, "Valor de mercado")
    )
    top10["Valor de mercado"] = top10["Valor de mercado"].apply(lambda x: f"€{x/1e6:.2f}M")
    print(top10.to_string(index=False))

    print("\n" + "=" * 60 + "\n")


# ═══════════════════════════════════════════════════════════════════════════
# MÓDULO 3 — VISUALIZACIONES AVANZADAS
# ═══════════════════════════════════════════════════════════════════════════

# ─── Gráfico 1: Declive de los 30 años ──────────────────────────────────────

def grafico_declive_edad(df: pd.DataFrame) -> None:
    """
    Gráfico de líneas con banda de confianza que muestra cómo evoluciona
    el VALOR DE MERCADO (€) según la edad, desagregado por zona táctica.

    Insight esperado: el peak económico de cada zona es distinto.
    Los delanteros y extremos peakean más joven (23-26); los mediocampistas
    y defensores conservan valor más tiempo.

    Metodología: media del valor máximo histórico por jugador-edad,
    suavizada con media móvil de ventana 3.
    """
    print("  -> Generando Grafico 1: Declive de los 30 anos...")

    # Usar el valor máximo de cada jugador en cada edad (evita sesgo de multi-temporada)
    df_age = (
        df[df["Zona"].isin(["Arqueros", "Defensores", "Mediocampistas", "Delanteros"])]
        .copy()
    )

    colores_zona = {
        "Arqueros":       NARANJA,
        "Defensores":     AZUL,
        "Mediocampistas": PURPURA,
        "Delanteros":     VERDE,
    }

    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#161b22")

    for zona, color in colores_zona.items():
        sub = df_age[df_age["Zona"] == zona]
        grp = sub.groupby("Edad")["Valor de mercado"].agg(["mean", "std"]).reset_index()
        grp = grp[(grp["Edad"] >= 16) & (grp["Edad"] <= 38)]
        grp["smooth"] = grp["mean"].rolling(3, center=True, min_periods=1).mean()
        grp["std"]    = grp["std"].fillna(0)

        ax.plot(grp["Edad"], grp["smooth"] / 1e6,
                color=color, lw=2.8, label=zona, zorder=3)
        ax.fill_between(
            grp["Edad"],
            (grp["smooth"] - grp["std"]) / 1e6,
            (grp["smooth"] + grp["std"]) / 1e6,
            color=color, alpha=0.10
        )

    # Umbral de los 30
    ax.axvline(x=30, color=GOLD, lw=1.8, ls=":", alpha=0.85)
    ax.text(30.2, ax.get_ylim()[1] * 0.95, "Umbral\n30 anos",
            color=GOLD, fontsize=8.5, va="top", style="italic")

    # Zona de peak general
    ax.axvspan(23, 27, alpha=0.04, color=AZUL)
    ax.text(25, ax.get_ylim()[1] * 0.98, "Peak\nde mercado",
            color=AZUL, fontsize=8, ha="center", alpha=0.6)

    ax.set_title(
        "Declive de los 30 anos\nEvolución del Valor de Mercado (€M) por Edad y Zona Táctica",
        fontsize=15, fontweight="bold", color="#f0f6fc", pad=15
    )
    ax.set_xlabel("Edad del jugador", fontsize=11, labelpad=8)
    ax.set_ylabel("Valor de mercado promedio (Millones €)", fontsize=11, labelpad=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:.1f}M"))
    ax.legend(loc="upper right", framealpha=0.2, edgecolor="#30363d", fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(16, 38)

    plt.tight_layout(pad=2)
    plt.savefig("grafico1_declive_30.png", dpi=150, bbox_inches="tight",
                facecolor="#0d1117")
    print("     OK: Guardado como 'grafico1_declive_30.png'")
    plt.show()


# ─── Gráfico 2: Joyas Ocultas ────────────────────────────────────────────────

def grafico_joyas_ocultas(df: pd.DataFrame) -> None:
    """
    Scatter plot de Valor de Mercado (€) vs. Edad, coloreado por zona táctica.

    Clasifica en 4 cuadrantes respecto a las medianas:
      - Joven + Alto valor  → "Promesas de Oro"    (verde)
      - Joven + Bajo valor  → "Cantera en desarrollo" (azul)
      - Mayor + Alto valor  → "Veteranos Premium"  (dorado)
      - Mayor + Bajo valor  → "Fin de ciclo"       (gris)

    Anota automáticamente los 8 jugadores más valiosos siendo menores de
    25 años (mejor ROI de inversión).
    """
    print("  -> Generando Grafico 2: Joyas Ocultas (Promesas de Oro)...")

    # Un registro por jugador (pico de valor)
    df_peak = (
        df.loc[df.groupby("Jugadores")["Valor de mercado"].idxmax()]
        .copy()
        .reset_index(drop=True)
    )

    q_edad  = df_peak["Edad"].median()
    q_valor = df_peak["Valor de mercado"].median()

    def cuadrante(row):
        joven = row["Edad"] <= q_edad
        caro  = row["Valor de mercado"] >= q_valor
        if joven and caro:
            return "Promesa de Oro"
        elif joven and not caro:
            return "Cantera"
        elif not joven and caro:
            return "Veterano Premium"
        else:
            return "Fin de ciclo"

    df_peak["Cuadrante"] = df_peak.apply(cuadrante, axis=1)

    color_map = {
        "Promesa de Oro":    VERDE,
        "Cantera":           AZUL,
        "Veterano Premium":  GOLD,
        "Fin de ciclo":      GRIS,
    }
    size_map = {
        "Promesa de Oro":   45,
        "Cantera":          20,
        "Veterano Premium": 38,
        "Fin de ciclo":     15,
    }

    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#161b22")

    for cat, color in color_map.items():
        mask = df_peak["Cuadrante"] == cat
        ax.scatter(
            df_peak.loc[mask, "Edad"],
            df_peak.loc[mask, "Valor_M"],
            c=color, alpha=0.55,
            s=size_map[cat],
            label=f"{cat} (n={mask.sum()})",
            edgecolors="none", zorder=3
        )

    # Líneas de cuadrante
    ax.axvline(q_edad,  color="#30363d", lw=1.2, ls="--", alpha=0.8)
    ax.axhline(q_valor/1e6, color="#30363d", lw=1.2, ls="--", alpha=0.8)

    # Top 8 promesas (menores de 25, mayor valor)
    promesas = df_peak[(df_peak["Cuadrante"] == "Promesa de Oro") &
                       (df_peak["Edad"] <= 25)].nlargest(8, "Valor de mercado")

    for _, row in promesas.iterrows():
        ax.annotate(
            row["Jugadores"].split()[-1],   # solo apellido para no saturar
            xy=(row["Edad"], row["Valor_M"]),
            xytext=(5, 5), textcoords="offset points",
            fontsize=7, color=VERDE, alpha=0.92,
            arrowprops=dict(arrowstyle="-", color=VERDE, alpha=0.35, lw=0.7),
        )

    # Etiquetas de cuadrantes
    ymax = df_peak["Valor_M"].quantile(0.98)
    ax.text(q_edad - 0.3, ymax * 0.93, "PROMESAS\nDE ORO",
            color=VERDE, fontsize=9, ha="right", fontweight="bold", alpha=0.55)
    ax.text(q_edad + 0.3, ymax * 0.93, "VETERANOS\nPREMIUM",
            color=GOLD,  fontsize=9, ha="left",  fontweight="bold", alpha=0.55)

    ax.set_ylim(bottom=-0.05)
    ax.set_title(
        "Joyas Ocultas del Mercado\nValor Pico (€M) vs. Edad — Fútbol Argentino 2008–2022",
        fontsize=15, fontweight="bold", color="#f0f6fc", pad=15
    )
    ax.set_xlabel("Edad del jugador (en su pico de valor)", fontsize=11, labelpad=8)
    ax.set_ylabel("Valor de mercado pico (Millones €)", fontsize=11, labelpad=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"€{x:.1f}M"))
    ax.legend(loc="upper right", framealpha=0.2, edgecolor="#30363d", fontsize=9.5)
    ax.grid(True, alpha=0.25)

    plt.tight_layout(pad=2)
    plt.savefig("grafico2_joyas_ocultas.png", dpi=150, bbox_inches="tight",
                facecolor="#0d1117")
    print("     OK: Guardado como 'grafico2_joyas_ocultas.png'")
    plt.show()


# ─── Gráfico 3: Matriz de Atributos ─────────────────────────────────────────

def grafico_matriz_atributos(df: pd.DataFrame) -> None:
    """
    Dado que el dataset no contiene atributos técnicos individuales (velocidad,
    pases, etc.), este gráfico presenta un ANÁLISIS MULTIDIMENSIONAL basado en
    las variables disponibles:

    - Heatmap 3.A: Valor de mercado promedio por Posición × Temporada
      (evolución económica de cada rol a lo largo de los años).
    - Heatmap 3.B: Correlación entre variables numéricas clave:
      Valor de mercado, Edad, Altura y Temporada.

    Este enfoque maximiza la información extraíble del dataset real.
    """
    print("  -> Generando Grafico 3: Matriz de Atributos (Heatmap doble)...")

    fig, axes = plt.subplots(1, 2, figsize=(18, 8))
    fig.patch.set_facecolor("#0d1117")
    for ax in axes:
        ax.set_facecolor("#0d1117")

    # ── 3.A: Valor promedio por Posición × Temporada ──────────────────────
    ax1 = axes[0]

    pivot = (
        df.pivot_table(
            index="Posicion",
            columns="Temporada",
            values="Valor de mercado",
            aggfunc="median"
        ) / 1_000_000
    )
    # Ordenar posiciones por valor global descendente
    pivot = pivot.loc[pivot.mean(axis=1).sort_values(ascending=False).index]

    cmap_pivot = sns.light_palette(AZUL, as_cmap=True)
    sns.heatmap(
        pivot,
        ax=ax1,
        cmap=cmap_pivot,
        annot=True,
        fmt=".1f",
        linewidths=0.4,
        linecolor="#0d1117",
        annot_kws={"size": 7},
        cbar_kws={"label": "Valor mediano (€M)", "shrink": 0.7},
    )
    ax1.set_title(
        "Valor de Mercado Mediano (€M)\npor Posicion y Temporada",
        fontsize=13, fontweight="bold", color="#f0f6fc", pad=12
    )
    ax1.set_xlabel("Temporada", fontsize=10)
    ax1.set_ylabel("Posicion", fontsize=10)
    ax1.tick_params(colors="#8b949e")
    cbar1 = ax1.collections[0].colorbar
    cbar1.ax.tick_params(colors="#8b949e")
    cbar1.ax.yaxis.label.set_color("#8b949e")

    # ── 3.B: Correlación entre variables numéricas ────────────────────────
    ax2 = axes[1]

    cols_num = ["Valor de mercado", "Edad", "Altura", "Temporada"]
    labels_bonitos = {
        "Valor de mercado": "Valor\nMercado (€)",
        "Edad":             "Edad",
        "Altura":           "Altura (m)",
        "Temporada":        "Temporada",
    }
    df_corr = df[cols_num].rename(columns=labels_bonitos)
    corr = df_corr.corr(method="pearson")

    mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
    cmap_div = sns.diverging_palette(10, 220, s=85, l=45, sep=10, as_cmap=True)

    sns.heatmap(
        corr,
        mask=mask,
        ax=ax2,
        cmap=cmap_div,
        center=0,
        annot=True,
        fmt=".3f",
        linewidths=0.5,
        linecolor="#0d1117",
        cbar_kws={"label": "Pearson r", "shrink": 0.7},
        annot_kws={"size": 14, "color": "#f0f6fc", "fontweight": "bold"},
        square=True,
        vmin=-1, vmax=1,
    )
    ax2.set_title(
        "Correlacion de Pearson\nEntre Variables Numericas",
        fontsize=13, fontweight="bold", color="#f0f6fc", pad=12
    )
    ax2.set_xticklabels(ax2.get_xticklabels(), rotation=20, ha="right", fontsize=11)
    ax2.set_yticklabels(ax2.get_yticklabels(), rotation=0, fontsize=11)
    cbar2 = ax2.collections[0].colorbar
    cbar2.ax.tick_params(colors="#8b949e")
    cbar2.ax.yaxis.label.set_color("#8b949e")

    plt.suptitle(
        "Matriz de Atributos — Fútbol Argentino 2008–2022",
        fontsize=16, fontweight="bold", color="#f0f6fc", y=1.02
    )
    plt.tight_layout(pad=2)
    plt.savefig("grafico3_matriz_atributos.png", dpi=150, bbox_inches="tight",
                facecolor="#0d1117")
    print("     OK: Guardado como 'grafico3_matriz_atributos.png'")
    plt.show()


# ═══════════════════════════════════════════════════════════════════════════
# BONUS: Gráfico 4 — Distribución por Pie Dominante
# ═══════════════════════════════════════════════════════════════════════════

def grafico_bonus_pie_zona(df: pd.DataFrame) -> None:
    """
    BONUS: Gráfico de barras apiladas (%) que muestra la distribución del
    pie dominante (derecho / izquierdo / ambidiestro) dentro de cada zona
    táctica.

    Insight: ¿Los zurdos están sobrerrepresentados en ciertas posiciones?
    (hipótesis clásica del fútbol: zurdos naturales en extremo izquierdo,
    pero también muy valorados en cualquier posición central).
    """
    print("  -> Generando Grafico 4 (BONUS): Pie Dominante por Zona...")

    zonas_orden = ["Arqueros", "Defensores", "Mediocampistas", "Delanteros"]
    pie_orden   = ["derecho", "izquierdo", "ambidiestro", "No especificado"]
    colores_pie = [AZUL, ROJO, VERDE, GRIS]

    df_pie = df[df["Zona"].isin(zonas_orden)].copy()

    # Tabla de contingencia normalizada
    tabla = (
        df_pie.groupby(["Zona", "Pie"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=zonas_orden, columns=pie_orden, fill_value=0)
    )
    tabla_pct = tabla.div(tabla.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(11, 6))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#161b22")

    bottom = np.zeros(len(zonas_orden))
    for i, (col, color) in enumerate(zip(pie_orden, colores_pie)):
        vals = tabla_pct[col].values
        bars = ax.bar(
            zonas_orden, vals, bottom=bottom,
            color=color, alpha=0.85, label=col.capitalize(), width=0.6
        )
        # Etiqueta dentro de la barra si es suficientemente grande
        for j, (bar, val) in enumerate(zip(bars, vals)):
            if val > 5:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bottom[j] + val / 2,
                    f"{val:.1f}%",
                    ha="center", va="center",
                    fontsize=9, color="white", fontweight="bold"
                )
        bottom += vals

    ax.set_title(
        "Distribución del Pie Dominante por Zona Táctica\nFútbol Argentino 2008–2022",
        fontsize=14, fontweight="bold", color="#f0f6fc", pad=15
    )
    ax.set_ylabel("Porcentaje de jugadores (%)", fontsize=11, labelpad=8)
    ax.set_xlabel("Zona táctica", fontsize=11, labelpad=8)
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax.legend(loc="upper right", framealpha=0.2, edgecolor="#30363d", fontsize=10)
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout(pad=2)
    plt.savefig("grafico4_pie_dominante.png", dpi=150, bbox_inches="tight",
                facecolor="#0d1117")
    print("     OK: Guardado como 'grafico4_pie_dominante.png'")
    plt.show()


# ═══════════════════════════════════════════════════════════════════════════
# MÓDULO 4 — PIPELINE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("\n" + "#" * 60)
    print("  EDA PROFESIONAL - FUTBOL ARGENTINO 2008-2022")
    print("  Cientifico de Datos Senior - Portafolio")
    print("#" * 60)

    DATASET = "futbolargentino.xlsx"

    # Modulo 1: Carga y limpieza
    df = cargar_y_limpiar(DATASET)

    # Modulo 2: Resumen estadistico
    resumen_tactico(df)

    # Modulo 3: Visualizaciones
    print("\n" + "=" * 60)
    print("  MODULO 3 - VISUALIZACIONES AVANZADAS")
    print("=" * 60 + "\n")

    grafico_declive_edad(df)
    grafico_joyas_ocultas(df)
    grafico_matriz_atributos(df)
    grafico_bonus_pie_zona(df)

    print("\n" + "#" * 60)
    print("  EDA COMPLETADO - 4 graficos guardados.")
    print("#" * 60 + "\n")

    return df


if __name__ == "__main__":
    df = main()
