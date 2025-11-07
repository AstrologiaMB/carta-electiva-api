"""
Sistema de Ranking por Cardinalidad - Enraizamiento
=========================================

Este módulo implementa el sistema de ranking A-E basado en el enraizamiento
astrológico, utilizando percentiles y umbrales estadísticamente válidos.

Ranking:
- A_Excelente: >50.0% (>85 percentil) - Primera opción
- B_Muy_Bueno: 45.0-50.0% (70-85%) - Muy recomendable
- C_Bueno: 43.8-45.0% (50-70%) - Aceptable
- D_Aceptable: 40.0-43.8% (30-50%) - Única opción si no hay mejores
- E_Regular: <40.0% (<30%) - Evitar si posible
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional

class RankingSystem:
    """
    Sistema de ranking por cardinalidad basado en enraizamiento.
    """

    # Umbrales del sistema de ranking
    UMBRALES_RANKING = {
        'A_Excelente': {'min': 50.0, 'percentil_min': 85, 'descripcion': 'Primera opción - Enraizamiento excepcional'},
        'B_Muy_Bueno': {'min': 45.0, 'max': 50.0, 'percentil_min': 70, 'percentil_max': 85, 'descripcion': 'Muy recomendable - Enraizamiento fuerte'},
        'C_Bueno': {'min': 43.8, 'max': 45.0, 'percentil_min': 50, 'percentil_max': 70, 'descripcion': 'Aceptable - Enraizamiento sólido'},
        'D_Aceptable': {'min': 40.0, 'max': 43.8, 'percentil_min': 30, 'percentil_max': 50, 'descripcion': 'Única opción si no hay mejores - Enraizamiento moderado'},
        'E_Regular': {'max': 40.0, 'percentil_max': 30, 'descripcion': 'Evitar si posible - Enraizamiento limitado'}
    }

    # Percentiles de referencia (basados en 20 datos)
    PERCENTILES_REFERENCIA = {
        10: 37.5,
        25: 40.0,
        50: 43.8,
        75: 50.0,
        90: 56.2
    }

    @staticmethod
    def calcular_percentil_valor(enraizamiento: float, valores_referencia: List[float]) -> float:
        """
        Calcula el percentil de un valor específico dentro de una distribución.

        Args:
            enraizamiento: Valor de enraizamiento a evaluar
            valores_referencia: Lista de valores para calcular percentiles

        Returns:
            Percentil del valor (0-100)
        """
        if not valores_referencia:
            return 50.0

        valores_ordenados = sorted(valores_referencia)
        n = len(valores_ordenados)

        # Encontrar posición
        for i, valor in enumerate(valores_ordenados):
            if enraizamiento <= valor:
                if i == 0:
                    return 0.0
                elif enraizamiento == valor:
                    return (i / n) * 100
                else:
                    # Interpolación lineal
                    prev_valor = valores_ordenados[i-1]
                    return ((i-1) + (enraizamiento - prev_valor) / (valor - prev_valor)) / n * 100

        return 100.0

    @classmethod
    def asignar_ranking(cls, enraizamiento: float, percentil: Optional[float] = None,
                       valores_referencia: Optional[List[float]] = None) -> Dict:
        """
        Asigna ranking A-E basado en enraizamiento y percentil.

        Args:
            enraizamiento: Valor de enraizamiento (%)
            percentil: Percentil del valor (opcional)
            valores_referencia: Lista de valores para calcular percentil (opcional)

        Returns:
            Dict con ranking, nivel, descripción y recomendación
        """
        # Calcular percentil si no se proporciona
        if percentil is None and valores_referencia:
            percentil = cls.calcular_percentil_valor(enraizamiento, valores_referencia)
        elif percentil is None:
            # Usar percentil aproximado basado en umbrales conocidos
            if enraizamiento >= 56.2:
                percentil = 95.0
            elif enraizamiento >= 50.0:
                percentil = 85.0
            elif enraizamiento >= 45.0:
                percentil = 75.0
            elif enraizamiento >= 43.8:
                percentil = 60.0
            elif enraizamiento >= 40.0:
                percentil = 40.0
            else:
                percentil = 20.0

        # Asignar ranking basado en enraizamiento y percentil
        if enraizamiento > 50.0:
            nivel = 'A_Excelente'
        elif 45.0 <= enraizamiento <= 50.0:
            nivel = 'B_Muy_Bueno'
        elif 43.8 <= enraizamiento < 45.0:
            nivel = 'C_Bueno'
        elif 40.0 <= enraizamiento < 43.8:
            nivel = 'D_Aceptable'
        else:
            nivel = 'E_Regular'

        umbral = cls.UMBRALES_RANKING[nivel]

        return {
            'ranking': nivel,
            'nivel': nivel.split('_')[1],
            'enraizamiento': enraizamiento,
            'percentil': round(percentil, 1),
            'descripcion': umbral['descripcion'],
            'calidad_relativa': cls._calcular_calidad_relativa(enraizamiento),
            'recomendacion': cls._generar_recomendacion(nivel, enraizamiento, percentil)
        }

    @staticmethod
    def _calcular_calidad_relativa(enraizamiento: float) -> str:
        """Calcula calidad relativa vs promedio (45.5%)"""
        promedio = 45.5
        diferencia = enraizamiento - promedio
        porcentaje = (diferencia / promedio) * 100

        if porcentaje > 10:
            return f"Muy Superior (+{porcentaje:.1f}% vs promedio)"
        elif porcentaje > 0:
            return f"Superior (+{porcentaje:.1f}% vs promedio)"
        elif porcentaje > -10:
            return f"Promedio ({porcentaje:+.1f}% vs promedio)"
        else:
            return f"Inferior ({porcentaje:+.1f}% vs promedio)"

    @staticmethod
    def _generar_recomendacion(nivel: str, enraizamiento: float, percentil: float) -> str:
        """Genera recomendación específica basada en nivel y métricas"""
        recomendaciones = {
            'A_Excelente': f"🌟 EXCELENTE ELECCIÓN - Enraizamiento {enraizamiento}% (P{percentil:.0f})",
            'B_Muy_Bueno': f"✅ MUY BUENA OPCIÓN - Enraizamiento {enraizamiento}% (P{percentil:.0f})",
            'C_Bueno': f"👍 BUENA OPCIÓN - Enraizamiento {enraizamiento}% (P{percentil:.0f})",
            'D_Aceptable': f"⚠️ ACEPTABLE - Enraizamiento {enraizamiento}% (P{percentil:.0f})",
            'E_Regular': f"❌ EVITAR SI POSIBLE - Enraizamiento {enraizamiento}% (P{percentil:.0f})"
        }
        return recomendaciones.get(nivel, f"Evaluación: {enraizamiento}% (P{percentil:.0f})")

    @classmethod
    def procesar_dataframe(cls, df: pd.DataFrame,
                          columna_enraizamiento: str = 'Enraizamiento (%)') -> pd.DataFrame:
        """
        Procesa un DataFrame y agrega columnas de ranking.

        Args:
            df: DataFrame con datos de momentos
            columna_enraizamiento: Nombre de la columna de enraizamiento

        Returns:
            DataFrame con columnas de ranking agregadas
        """
        if columna_enraizamiento not in df.columns:
            raise ValueError(f"Columna '{columna_enraizamiento}' no encontrada en DataFrame")

        # Obtener valores de referencia para calcular percentiles
        valores_referencia = df[columna_enraizamiento].tolist()

        # Aplicar ranking a cada fila
        rankings = []
        for _, row in df.iterrows():
            enraizamiento = row[columna_enraizamiento]
            ranking_info = cls.asignar_ranking(enraizamiento, valores_referencia=valores_referencia)
            rankings.append(ranking_info)

        # Crear DataFrame con rankings
        rankings_df = pd.DataFrame(rankings)

        # Combinar con DataFrame original
        df_resultado = pd.concat([df, rankings_df], axis=1)

        return df_resultado

    @classmethod
    def generar_reporte_ranking(cls, df_con_ranking: pd.DataFrame) -> str:
        """
        Genera un reporte resumen del ranking aplicado.

        Args:
            df_con_ranking: DataFrame con columnas de ranking

        Returns:
            String con reporte formateado
        """
        if 'ranking' not in df_con_ranking.columns:
            return "Error: DataFrame no contiene columna 'ranking'"

        # Contar por ranking
        conteo_ranking = df_con_ranking['ranking'].value_counts().sort_index()

        # Estadísticas generales
        total_momentos = len(df_con_ranking)
        enraizamiento_promedio = df_con_ranking['Enraizamiento (%)'].mean()

        # Generar reporte
        reporte = f"""
================================================================================
                    REPORTE DE RANKING - SISTEMA DE CARDINALIDAD
================================================================================

📊 RESUMEN GENERAL
Total momentos evaluados: {total_momentos}
Enraizamiento promedio: {enraizamiento_promedio:.1f}%

🏆 DISTRIBUCIÓN POR RANKING
"""

        for ranking, cantidad in conteo_ranking.items():
            porcentaje = (cantidad / total_momentos) * 100
            descripcion = cls.UMBRALES_RANKING[ranking]['descripcion']
            reporte += f"{ranking}: {cantidad} momentos ({porcentaje:.1f}%) - {descripcion}\n"

        # Mejores momentos
        mejores = df_con_ranking.nlargest(3, 'Enraizamiento (%)')
        reporte += "\n🌟 TOP 3 MOMENTOS RECOMENDADOS\n"
        for i, (_, row) in enumerate(mejores.iterrows(), 1):
            reporte += f"{i}. {row.get('Fecha y Hora', 'N/A')} - {row['Enraizamiento (%)']}% ({row['ranking']})\n"

        reporte += "\n" + "="*80

        return reporte


# Función de conveniencia para uso directo
def asignar_ranking_momento(enraizamiento: float,
                           valores_referencia: Optional[List[float]] = None) -> Dict:
    """
    Función de conveniencia para asignar ranking a un momento específico.

    Args:
        enraizamiento: Valor de enraizamiento (%)
        valores_referencia: Lista opcional de valores para calcular percentil

    Returns:
        Dict con información completa del ranking
    """
    return RankingSystem.asignar_ranking(enraizamiento, valores_referencia=valores_referencia)


if __name__ == "__main__":
    # Ejemplo de uso
    print("=== SISTEMA DE RANKING POR CARDINALIDAD ===")

    # Ejemplo con datos del archivo
    momentos_ejemplo = [56.2, 50.0, 43.8, 37.5]

    print("\n📋 EJEMPLOS DE RANKING:")
    for enraizamiento in momentos_ejemplo:
        ranking = asignar_ranking_momento(enraizamiento, momentos_ejemplo)
        print(f"Enraizamiento {enraizamiento}% → {ranking['ranking']} ({ranking['nivel']})")
        print(f"  └─ {ranking['descripcion']}")
        print(f"  └─ Percentil: {ranking['percentil']}%")
        print(f"  └─ {ranking['recomendacion']}\n")
