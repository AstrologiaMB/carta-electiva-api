"""
Sistema de Score Contextual del Enraizamiento (SCC)
=========================================

Este módulo implementa el SCC: un score único que combina calidad absoluta
y relativa del enraizamiento para evitar sesgos y proporcionar contexto preciso.
"""

import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime

class SCC_Calculator:
    """
    Calculadora del Score Contextual del Enraizamiento (SCC)

    El SCC combina:
    - Calidad Absoluta: vs rango teórico (-6 a +10)
    - Calidad Relativa: vs valores encontrados en el período
    """

    # Rango teórico del enraizamiento
    ENRAIZAMIENTO_MIN = -6.0
    ENRAIZAMIENTO_MAX = 10.0
    ENRAIZAMIENTO_RANGO = ENRAIZAMIENTO_MAX - ENRAIZAMIENTO_MIN

    # Pesos para el cálculo híbrido
    PESO_ABSOLUTO = 0.8
    PESO_RELATIVO = 0.2

    # Umbral mínimo para evitar sesgos
    UMBRAL_MINIMO_RECOMENDABLE = 40.0

    @classmethod
    def calcular_scc(cls, enraizamiento_puntos: float,
                    valores_referencia: List[float] = None) -> Dict:
        """
        Calcula el Score Contextual del Enraizamiento (SCC)

        Args:
            enraizamiento_puntos: Puntos absolutos de enraizamiento (-6 a +10)
            valores_referencia: Lista de valores del período para contextualizar

        Returns:
            Dict con SCC y metadatos
        """
        # Calcular componente absoluto
        absoluto_pct = cls._calcular_componente_absoluto(enraizamiento_puntos)

        # Calcular componente relativo
        if valores_referencia and len(valores_referencia) > 1:
            relativo_pct = cls._calcular_componente_relativo(enraizamiento_puntos, valores_referencia)
        else:
            # Fallback: usar percentil aproximado basado en el valor absoluto
            relativo_pct = cls._estimar_percentil_aproximado(enraizamiento_puntos)

        # Calcular SCC final
        scc = (absoluto_pct * cls.PESO_ABSOLUTO) + (relativo_pct * cls.PESO_RELATIVO)

        # Determinar si es recomendable
        recomendable = scc >= cls.UMBRAL_MINIMO_RECOMENDABLE

        # Asignar categoría
        categoria = cls._asignar_categoria_scc(scc, recomendable)

        return {
            'scc': round(scc, 1),
            'absoluto_pct': round(absoluto_pct, 1),
            'relativo_pct': round(relativo_pct, 1),
            'recomendable': recomendable,
            'categoria': categoria,
            'motivo_no_recomendable': None if recomendable else cls._get_motivo_no_recomendable(scc, absoluto_pct)
        }

    @classmethod
    def _calcular_componente_absoluto(cls, puntos: float) -> float:
        """
        Calcula el componente absoluto vs rango teórico (-6 a +10)
        """
        if puntos <= cls.ENRAIZAMIENTO_MIN:
            return 0.0
        elif puntos >= cls.ENRAIZAMIENTO_MAX:
            return 100.0
        else:
            # Normalización lineal al rango 0-100
            ratio = (puntos - cls.ENRAIZAMIENTO_MIN) / cls.ENRAIZAMIENTO_RANGO
            return ratio * 100.0

    @classmethod
    def _calcular_componente_relativo(cls, puntos: float, valores_referencia: List[float]) -> float:
        """
        Calcula el componente relativo vs valores del período
        """
        if not valores_referencia:
            return 50.0

        valores_ordenados = sorted(valores_referencia)
        n = len(valores_ordenados)

        # Encontrar percentil usando interpolación
        for i, valor in enumerate(valores_ordenados):
            if puntos <= valor:
                if i == 0:
                    return 0.0
                elif puntos == valor:
                    return (i / n) * 100.0
                else:
                    # Interpolación lineal
                    prev_valor = valores_ordenados[i-1]
                    if valor != prev_valor:
                        interpolacion = (puntos - prev_valor) / (valor - prev_valor)
                        return ((i-1 + interpolacion) / n) * 100.0
                    else:
                        return (i / n) * 100.0

        return 100.0

    @classmethod
    def _estimar_percentil_aproximado(cls, puntos: float) -> float:
        """
        Estima percentil aproximado cuando no hay datos de referencia
        Basado en distribución esperada del enraizamiento
        """
        if puntos >= 3:
            return 95.0
        elif puntos >= 2:
            return 85.0
        elif puntos >= 1:
            return 70.0
        elif puntos >= 0:
            return 50.0
        elif puntos >= -2:
            return 30.0
        else:
            return 10.0

    @classmethod
    def _asignar_categoria_scc(cls, scc: float, recomendable: bool) -> str:
        """
        Asigna categoría basada en SCC
        """
        if not recomendable:
            return "NO RECOMENDABLE"

        if scc >= 75:
            return "🌟 EXCEPCIONAL"
        elif scc >= 65:
            return "✅ SOBRE PROMEDIO"
        elif scc >= 50:
            return "⚪ PROMEDIO"
        elif scc >= 40:
            return "⚠️ DEBAJO PROMEDIO"
        else:
            return "❌ LIMITADO"

    @classmethod
    def _get_motivo_no_recomendable(cls, scc: float, absoluto_pct: float) -> str:
        """
        Determina el motivo por el cual no es recomendable
        """
        if absoluto_pct < 30:
            return "Enraizamiento absoluto muy bajo (<30%)"
        elif scc < cls.UMBRAL_MINIMO_RECOMENDABLE:
            return f"SCC por debajo del umbral mínimo ({scc:.1f}% < {cls.UMBRAL_MINIMO_RECOMENDABLE}%)"
        else:
            return "Calidad insuficiente"

    @classmethod
    def procesar_momentos_con_scc(cls, momentos: List[Dict]) -> List[Dict]:
        """
        Procesa una lista de momentos y agrega SCC a cada uno

        Args:
            momentos: Lista de diccionarios con datos de momentos

        Returns:
            Lista de momentos con SCC agregado
        """
        if not momentos:
            return momentos

        # Extraer valores de enraizamiento para referencia
        valores_enraizamiento = []
        for momento in momentos:
            # Intentar obtener enraizamiento puro de diferentes fuentes
            enraizamiento = cls._extraer_enraizamiento_puro(momento)
            valores_enraizamiento.append(enraizamiento)

        # Procesar cada momento
        momentos_con_scc = []
        for momento in momentos:
            enraizamiento_puntos = cls._extraer_enraizamiento_puro(momento)
            scc_data = cls.calcular_scc(enraizamiento_puntos, valores_enraizamiento)

            # Agregar SCC al momento
            momento_con_scc = momento.copy()
            momento_con_scc.update({
                'scc': scc_data['scc'],
                'scc_absoluto_pct': scc_data['absoluto_pct'],
                'scc_relativo_pct': scc_data['relativo_pct'],
                'scc_categoria': scc_data['categoria'],
                'scc_recomendable': scc_data['recomendable']
            })

            momentos_con_scc.append(momento_con_scc)

        return momentos_con_scc

    @classmethod
    def _extraer_enraizamiento_puro(cls, momento: Dict) -> float:
        """
        Extrae el valor de enraizamiento puro de un momento
        """
        # Intentar obtener de detalles.enraizamiento_puro.puntos_total
        detalles = momento.get('detalles', {})
        if detalles and 'enraizamiento_puro' in detalles:
            enraizamiento_data = detalles['enraizamiento_puro']
            if isinstance(enraizamiento_data, dict) and 'puntos_total' in enraizamiento_data:
                return float(enraizamiento_data['puntos_total'])

        # Fallback: intentar de enraizamiento_score
        if 'enraizamiento_score' in momento:
            # Si es un score 0-1, convertir aproximado a puntos
            score = momento['enraizamiento_score']
            if 0 <= score <= 1:
                # Aproximación: score 0.5 ≈ 2 puntos (promedio)
                return (score - 0.5) * 8  # Escala aproximada

        # Último fallback: 0
        return 0.0

    @classmethod
    def generar_reporte_scc(cls, momentos: List[Dict]) -> str:
        """
        Genera un reporte resumen del SCC aplicado
        """
        if not momentos:
            return "No hay momentos para reportar"

        total_momentos = len(momentos)
        recomendables = sum(1 for m in momentos if m.get('scc_recomendable', False))

        # Estadísticas de SCC
        scc_values = [m.get('scc', 0) for m in momentos]
        scc_promedio = np.mean(scc_values) if scc_values else 0
        scc_max = max(scc_values) if scc_values else 0
        scc_min = min(scc_values) if scc_values else 0

        # Distribución por categorías
        categorias = {}
        for momento in momentos:
            cat = momento.get('scc_categoria', 'SIN CATEGORÍA')
            categorias[cat] = categorias.get(cat, 0) + 1

        reporte = f"""
================================================================================
                    REPORTE SCC - SCORE CONTEXTUAL DEL ENRAIZAMIENTO
================================================================================

📊 RESUMEN GENERAL
Total momentos evaluados: {total_momentos}
Momentos recomendables: {recomendables} ({recomendables/total_momentos*100:.1f}%)
SCC promedio: {scc_promedio:.1f}%
SCC máximo: {scc_max:.1f}%
SCC mínimo: {scc_min:.1f}%

🏆 DISTRIBUCIÓN POR CATEGORÍAS SCC
"""

        for categoria, cantidad in sorted(categorias.items()):
            porcentaje = (cantidad / total_momentos) * 100
            reporte += f"{categoria}: {cantidad} momentos ({porcentaje:.1f}%)\n"

        # Top momentos por SCC
        momentos_ordenados = sorted(momentos, key=lambda x: x.get('scc', 0), reverse=True)
        reporte += "\n🌟 TOP 5 MOMENTOS POR SCC\n"
        for i, momento in enumerate(momentos_ordenados[:5], 1):
            fecha = momento.get('fecha_hora', 'N/A')
            if hasattr(fecha, 'strftime'):
                fecha_str = fecha.strftime('%Y-%m-%d %H:%M')
            else:
                fecha_str = str(fecha)
            scc = momento.get('scc', 0)
            cat = momento.get('scc_categoria', 'N/A')
            reporte += f"{i}. {fecha_str} - SCC: {scc:.1f}% ({cat})\n"

        reporte += "\n" + "="*80
        return reporte


# Funciones de conveniencia para uso directo
def calcular_scc_enraizamiento(enraizamiento_puntos: float,
                             valores_referencia: List[float] = None) -> Dict:
    """
    Función de conveniencia para calcular SCC
    """
    return SCC_Calculator.calcular_scc(enraizamiento_puntos, valores_referencia)


def procesar_momentos_scc(momentos: List[Dict]) -> List[Dict]:
    """
    Función de conveniencia para procesar momentos con SCC
    """
    return SCC_Calculator.procesar_momentos_con_scc(momentos)


if __name__ == "__main__":
    # Ejemplo de uso
    print("=== SISTEMA SCC - SCORE CONTEXTUAL DEL ENRAIZAMIENTO ===")

    # Ejemplos con diferentes valores
    ejemplos = [
        (3, "Mejor caso del período actual"),
        (2, "Caso promedio del período"),
        (1, "Caso bajo del período"),
        (-1, "Caso negativo"),
        (-3, "Caso muy negativo")
    ]

    print("\n📋 EJEMPLOS DE SCC:")
    valores_referencia = [1, 2, 2, 3, 3, 3]  # Simulando distribución del período

    for puntos, descripcion in ejemplos:
        scc_data = calcular_scc_enraizamiento(puntos, valores_referencia)
        print(f"{descripcion} ({puntos} pts):")
        print(f"  SCC: {scc_data['scc']:.1f}%")
        print(f"  Absoluto: {scc_data['absoluto_pct']:.1f}%, Relativo: {scc_data['relativo_pct']:.1f}%")
        print(f"  Categoría: {scc_data['categoria']}")
        print(f"  Recomendable: {'✅ SÍ' if scc_data['recomendable'] else '❌ NO'}")
        if not scc_data['recomendable']:
            print(f"  Motivo: {scc_data['motivo_no_recomendable']}")
        print()
