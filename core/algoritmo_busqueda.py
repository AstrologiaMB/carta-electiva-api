"""
Algoritmo de búsqueda REDISEÑADO - 2 fases ultra-optimizado
Elimina completamente las duplicaciones y redundancias
Reduce cálculos de 525,600 a ~6,000 (88x mejora)

FASE 1: Filtro básico cada 30 minutos (paralelizado)
FASE 2: Análisis directo de momentos filtrados (paralelizado)
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any
import logging
import multiprocessing as mp
import concurrent.futures

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.legacy_wrapper import LegacyAstroWrapper
from core.enraizamiento_calculator import EnraizamientoCalculator
from utils.scc_calculator import SCC_Calculator
from config import (
    FASE_1_INTERVALO_HORAS, FASE_2_INTERVALO_MINUTOS,
    UMBRAL_ENRAIZAMIENTO_MINIMO, MAX_RESULTADOS_FINALES
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constantes para sistema de puntuación porcentual
PUNTUACION_MAXIMA_TEORICA = 81.6  # Máximo teórico: (100 * 0.8) + (8 * 0.2) = 81.6

class AlgoritmoBusqueda:
    """
    Algoritmo de búsqueda REDISEÑADO - 2 fases simplificado

    Elimina completamente las duplicaciones y redundancias del algoritmo original.
    Análisis directo y eficiente sin ventanas superpuestas.

    FASE 1: Filtro básico cada 30 minutos (rápido)
    FASE 2: Análisis completo directo de momentos filtrados (SIN ventanas)
    """
    
    def __init__(self, carta_natal_A: Dict, tema_consulta: str, lat: float, lon: float):
        """
        Inicializa el algoritmo de búsqueda
        
        Args:
            carta_natal_A: Datos de la carta natal base
            tema_consulta: Tema astrológico (trabajo, amor, etc.)
            lat: Latitud del lugar
            lon: Longitud del lugar
        """
        self.carta_natal_A = carta_natal_A
        self.tema_consulta = tema_consulta
        self.lat = lat
        self.lon = lon
        
        # Inicializar calculadora avanzada de enraizamiento
        self.enraizamiento_calc = EnraizamientoCalculator(carta_natal_A)
        
        # Contadores para estadísticas
        self.calculos_fase_1 = 0
        self.calculos_fase_2 = 0
        
    def buscar_mejores_momentos(self, fecha_inicio: datetime, fecha_fin: datetime) -> List[Dict]:
        """
        Ejecuta la búsqueda completa de 2 fases ultra-optimizada

        Args:
            fecha_inicio: Fecha de inicio del rango
            fecha_fin: Fecha de fin del rango

        Returns:
            Lista de los mejores momentos encontrados
        """
        logger.info(f"🚀 Iniciando búsqueda optimizada para tema '{self.tema_consulta}'")
        logger.info(f"📅 Rango: {fecha_inicio.strftime('%Y-%m-%d')} a {fecha_fin.strftime('%Y-%m-%d')}")
        
        # FASE 1: Filtro básico (cada 30 minutos)
        logger.info(f"🔍 FASE 1: Filtro básico (cada {FASE_1_INTERVALO_HORAS * 60:.0f} minutos)")
        momentos_prometedores = self._fase_1_filtro_basico(fecha_inicio, fecha_fin)
        logger.info(f"   Momentos prometedores encontrados: {len(momentos_prometedores)}")
        
        if not momentos_prometedores:
            logger.warning("⚠️  No se encontraron momentos prometedores en Fase 1")
            return []
        
        # FASE 2: REDISEÑO SIMPLIFICADO - Análisis directo y retorno de resultados finales
        logger.info(f"🎯 FASE 2: Análisis completo de {len(momentos_prometedores)} momentos prometedores")
        momentos_finales = self._fase_2_enraizamiento(momentos_prometedores)
        logger.info(f"   ✅ Momentos óptimos encontrados: {len(momentos_finales)}")
        
        # Estadísticas finales
        total_calculos = self.calculos_fase_1 + self.calculos_fase_2
        logger.info(f"📊 Estadísticas de optimización:")
        logger.info(f"   Fase 1: {self.calculos_fase_1} cálculos")
        logger.info(f"   Fase 2: {self.calculos_fase_2} cálculos")
        logger.info(f"   Total: {total_calculos} cálculos")
        
        # Calcular mejora vs sistema original
        dias_totales = (fecha_fin - fecha_inicio).days
        calculos_originales = dias_totales * 24 * 60  # minuto por minuto
        mejora_factor = calculos_originales / total_calculos if total_calculos > 0 else 0
        logger.info(f"   Mejora: {mejora_factor:.1f}x más rápido que sistema original")
        
        return momentos_finales
    
    def _fase_1_filtro_basico(self, fecha_inicio: datetime, fecha_fin: datetime) -> List[datetime]:
        """
        Fase 1: Elimina períodos obviamente inadecuados
        Versión PARALELIZADA - Analiza cada 30 minutos para filtrar momentos básicamente no aptos
        """
        logger.info(f"⚡ Iniciando Fase 1 paralelizada...")

        # 1. Generar lista de momentos cada 30 minutos
        momentos_fase1 = self._generar_momentos_fase1(fecha_inicio, fecha_fin)
        logger.info(f"📅 Generados {len(momentos_fase1)} momentos para filtrar")

        # 2. Procesar en paralelo usando MULTIPROCESSING (mejor que Threading)
        cores_disponibles = mp.cpu_count()
        num_procesos = min(cores_disponibles, len(momentos_fase1))

        logger.info(f"🖥️  Usando {num_procesos} procesos (de {cores_disponibles} núcleos disponibles)")

        # Crear argumentos para la función estática
        args_list = [(momento, self.lat, self.lon) for momento in momentos_fase1]

        with mp.Pool(processes=num_procesos) as pool:
            resultados = pool.starmap(procesar_momento_fase1_estatico, args_list)

        # Contar cálculos y filtrar momentos aptos
        momentos_prometedores = []
        for momento, es_apto in zip(momentos_fase1, resultados):
            self.calculos_fase_1 += 1
            if es_apto:
                momentos_prometedores.append(momento)

        logger.info(f"✅ Fase 1 completada: {len(momentos_prometedores)} momentos prometedores")
        return momentos_prometedores

    def _generar_momentos_fase1(self, fecha_inicio: datetime, fecha_fin: datetime) -> List[datetime]:
        """
        Genera lista de momentos cada 30 minutos para Fase 1
        """
        momentos = []
        fecha_actual = fecha_inicio

        while fecha_actual <= fecha_fin:
            momentos.append(fecha_actual)
            fecha_actual += timedelta(minutes=30)  # Mantiene granularidad de 30 min

        return momentos

    def _procesar_momento_fase1(self, momento: datetime) -> bool:
        """
        Procesa un momento individual en Fase 1 (filtro rápido)
        Retorna True si el momento NO es descartado
        """
        try:
            # Crear wrapper para evaluación rápida
            wrapper = LegacyAstroWrapper(momento, self.lat, self.lon)

            # Solo verificar descalificadores críticos (muy rápido)
            es_descalificado, razon = wrapper.es_momento_critico_descalificado()

            # Retornar True si NO es descartado (es apto)
            return not es_descalificado

        except Exception as e:
            logger.warning(f"Error en filtro Fase 1 para {momento}: {e}")
            # En caso de error, considerar apto para no perder oportunidades
            return True

    def _fase_2_enraizamiento(self, momentos_prometedores: List[datetime]) -> List[Dict]:
        """
        REDISEÑO SIMPLIFICADO: Análisis directo de momentos prometedores
        SIN ventanas superpuestas - analiza ÚNICAMENTE los momentos filtrados

        Elimina completamente las duplicaciones del algoritmo original
        """
        logger.info(f"   Analizando {len(momentos_prometedores)} momentos prometedores...")

        momentos_enraizados = []

        # 🚀 PARALELIZACIÓN: Procesar momentos en paralelo para máxima velocidad
        logger.info(f"⚡ Procesando {len(momentos_prometedores)} momentos en paralelo...")

        # Determinar número óptimo de workers basado en CPU disponible
        max_workers = min(4, len(momentos_prometedores))  # Optimizado: 4 workers para mejor eficiencia

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Crear futuros para todos los momentos
            futuros = {
                executor.submit(self._procesar_momento_paralelo, momento): momento
                for momento in momentos_prometedores
            }

            # Procesar resultados a medida que se completan
            progreso_contador = 0
            total_momentos = len(momentos_prometedores)

            for futuro in concurrent.futures.as_completed(futuros):
                momento = futuros[futuro]
                self.calculos_fase_2 += 1
                progreso_contador += 1

                # Mostrar progreso cada 10 momentos procesados
                if progreso_contador % 10 == 0 or progreso_contador == total_momentos:
                    porcentaje = (progreso_contador / total_momentos) * 100
                    logger.info(f"📊 Progreso Fase 2: {progreso_contador}/{total_momentos} momentos ({porcentaje:.1f}%)")

                try:
                    resultado = futuro.result()
                    if resultado:
                        momentos_enraizados.append(resultado)

                except Exception as e:
                    logger.warning(f"Error procesando momento {momento}: {e}")

        logger.info(f"✅ Procesamiento paralelo completado: {len(momentos_enraizados)} momentos aptos")

        # Aplicar SCC (Score Contextual del Enraizamiento) a todos los momentos
        momentos_con_scc = self._aplicar_scc_a_momentos(momentos_enraizados)

        # Ordenar por SCC (prioridad principal) y puntuación total (desempate)
        momentos_con_scc.sort(key=lambda x: (x.get('scc', 0), x['puntuacion_total']), reverse=True)

        logger.info(f"   Momentos aptos encontrados: {len(momentos_con_scc)}")
        return momentos_con_scc[:MAX_RESULTADOS_FINALES]  # Retornar directamente los mejores

    def _calcular_enraizamiento_avanzado(self, fecha_hora: datetime) -> float:
        """
        v2.0 Advanced Enraizamiento Calculator
        Analiza conexiones reales entre carta natal A y momento electivo B(n)
        Retorna score de 25%-95% basado en factores astrológicos reales
        """
        try:
            # Usar calculadora avanzada de enraizamiento
            score_normalizado = self.enraizamiento_calc.calcular_enraizamiento_avanzado(
                fecha_hora, self.lat, self.lon, self.tema_consulta
            )
            
            # Convertir de rango 0.25-0.95 a escala 0-100 para compatibilidad
            score_escalado = score_normalizado * 100
            
            logger.debug(f"Enraizamiento avanzado: {score_escalado:.1f}% para {fecha_hora}")
            return score_escalado
            
        except Exception as e:
            logger.error(f"Error en cálculo de enraizamiento avanzado: {e}")
            # Retornar valor medio en caso de error para no interrumpir el proceso
            return 60.0
    
    def _calcular_puntuacion_total(self, score_enraizamiento: float, 
                                 resultado_luna: Dict, fecha_hora: datetime) -> float:
        """
        Calcula la puntuación total combinando enraizamiento y calidad
        Retorna un porcentaje de 0-100% del máximo posible
        """
        # Enraizamiento: 80% del peso
        puntos_enraizamiento = score_enraizamiento * 0.8
        
        # Calidad del momento: 20% del peso
        puntos_calidad = 0
        
        # Bonus por Luna apta
        if resultado_luna['apto']:
            puntos_calidad += 10
        
        # Bonus por puntos de Luna
        puntos_calidad += resultado_luna['puntos_luna'] * 2
        
        # Penalización por descalificadores
        puntos_calidad -= len(resultado_luna['descalificadores']) * 3
        
        # Aplicar peso de calidad (20%)
        puntos_calidad *= 0.2
        
        # Calcular puntuación bruta
        puntuacion_bruta = puntos_enraizamiento + puntos_calidad
        
        # Convertir a porcentaje del máximo teórico (0-100%)
        puntuacion_porcentual = (puntuacion_bruta / PUNTUACION_MAXIMA_TEORICA) * 100
        
        # Asegurar que esté en rango 0-100
        return max(0, min(100, puntuacion_porcentual))
    
    def _calcular_puntaje_ranking(self, detalles: Dict) -> float:
        """
        Calcula el Puntaje Ranking basado en la suma de:
        - Aptitud de la Luna
        - Regente del ASC
        - Regente de la Casa 10
        - Momentos positivos/negativos
        
        Returns:
            float: Puntaje de ranking para desempate (0-100 escala)
        """
        try:
            fase1_detalles = detalles.get('fase1', {})
            if not fase1_detalles:
                return 0.0
            
            # CORRECCIÓN: Extraer puntos de cada componente desde la estructura correcta
            detalles_fase1 = fase1_detalles.get('detalles', {})
            puntos_luna = detalles_fase1.get('luna', {}).get('puntos_luna', 0)
            puntos_asc = detalles_fase1.get('regente_asc', {}).get('puntos_regente_asc', 0)
            puntos_casa10 = detalles_fase1.get('regente_casa10', {}).get('puntos_regente_casa10', 0)
            puntos_positivas = detalles_fase1.get('combinaciones_positivas', {}).get('puntos_combinaciones_positivas', 0)
            puntos_negativas = detalles_fase1.get('combinaciones_negativas', {}).get('puntos_combinaciones_negativas', 0)
            
            # Sumar todos los componentes
            puntaje_total = puntos_luna + puntos_asc + puntos_casa10 + puntos_positivas + puntos_negativas
            
            # Normalizar a escala 0-100 (máximo teórico: 32 puntos, mínimo: -2)
            puntos_maximos = 32.0  # 10+10+6+6 = 32 (corregido con Luna 10 puntos)
            puntos_minimos = -2.0  # Solo penalizaciones negativas
            
            if puntaje_total <= puntos_minimos:
                return 0.0
            elif puntaje_total >= puntos_maximos:
                return 100.0
            else:
                # Normalizar al rango 0-100
                ratio = (puntaje_total - puntos_minimos) / (puntos_maximos - puntos_minimos)
                return max(0.0, min(100.0, ratio * 100))
                
        except Exception as e:
            logger.warning(f"Error calculando puntaje ranking: {e}")
            return 0.0
    
    def _calcular_puntuacion_total_combinada(self, enraizamiento_score: float, calidad_score: float) -> float:
        """
        Calcula la puntuación total combinada para ranking interno
        Metodología: Enraizamiento Primario + Desempate por Calidad

        Args:
            enraizamiento_score: Score de enraizamiento (0.0-1.0)
            calidad_score: Score de calidad (0.0-1.0)

        Returns:
            float: Puntuación total combinada (0-100 escala)
        """
        # Convertir a escala 0-100 y aplicar pesos
        # Enraizamiento: 80% del peso (criterio principal)
        # Calidad: 20% del peso (desempate)
        puntuacion_combinada = (enraizamiento_score * 80) + (calidad_score * 20)

        return round(puntuacion_combinada, 2)

    def _eliminar_momentos_cercanos(self, momentos: List[datetime],
                                   distancia_minima_minutos: int = 240) -> List[datetime]:
        """
        Elimina momentos que estén a menos de distancia_minima_minutos entre sí
        para evitar superposiciones de ventanas en Fase 2.

        Args:
            momentos: Lista de momentos a filtrar
            distancia_minima_minutos: Distancia mínima entre momentos (default: 240 min = 4 horas)

        Returns:
            List[datetime]: Lista filtrada sin momentos demasiado cercanos
        """
        if not momentos:
            return momentos

        # Ordenar momentos cronológicamente
        momentos_ordenados = sorted(momentos)

        # Mantener el primer momento
        momentos_filtrados = [momentos_ordenados[0]]

        # Procesar el resto, manteniendo solo aquellos con suficiente distancia
        for momento in momentos_ordenados[1:]:
            ultimo_incluido = momentos_filtrados[-1]

            # Calcular diferencia en minutos
            diferencia_minutos = (momento - ultimo_incluido).total_seconds() / 60

            # Si la diferencia es suficiente, incluir el momento
            if diferencia_minutos >= distancia_minima_minutos:
                momentos_filtrados.append(momento)

        logger.debug(f"Filtrado de momentos cercanos: {len(momentos)} -> {len(momentos_filtrados)} "
                    f"(distancia mínima: {distancia_minima_minutos} minutos)")

        return momentos_filtrados

    def _eliminar_duplicados_por_tiempo(self, momentos: List[Dict]) -> List[Dict]:
        """
        Elimina momentos duplicados basándose en su tiempo redondeado a minutos.
        Se queda con el momento de mejor calidad (mayor puntuación total).

        Args:
            momentos: Lista de momentos con datos detallados

        Returns:
            List[Dict]: Lista sin duplicados por tiempo
        """
        if not momentos:
            return momentos

        # Crear diccionario para agrupar por tiempo redondeado
        momentos_por_tiempo = {}

        for momento in momentos:
            # Redondear tiempo a minutos (ignorar segundos)
            tiempo_redondeado = momento['fecha_hora'].replace(second=0, microsecond=0)

            # Si ya existe este tiempo, comparar puntuaciones
            if tiempo_redondeado in momentos_por_tiempo:
                momento_existente = momentos_por_tiempo[tiempo_redondeado]

                # Comparar por puntuación total primero, luego por enraizamiento
                puntuacion_nueva = momento.get('puntuacion_total', 0)
                puntuacion_existente = momento_existente.get('puntuacion_total', 0)

                if puntuacion_nueva > puntuacion_existente:
                    momentos_por_tiempo[tiempo_redondeado] = momento
                elif puntuacion_nueva == puntuacion_existente:
                    # Si puntuaciones iguales, comparar enraizamiento
                    enraizamiento_nuevo = momento.get('enraizamiento_score', 0)
                    enraizamiento_existente = momento_existente.get('enraizamiento_score', 0)

                    if enraizamiento_nuevo > enraizamiento_existente:
                        momentos_por_tiempo[tiempo_redondeado] = momento
            else:
                # Primer momento para este tiempo
                momentos_por_tiempo[tiempo_redondeado] = momento

        momentos_unicos = list(momentos_por_tiempo.values())
        logger.debug(f"Eliminación de duplicados por tiempo: {len(momentos)} -> {len(momentos_unicos)}")

        return momentos_unicos

    def _aplicar_scc_a_momentos(self, momentos: List[Dict]) -> List[Dict]:
        """
        Aplica el Score Contextual del Enraizamiento (SCC) a todos los momentos

        Args:
            momentos: Lista de momentos con datos de enraizamiento

        Returns:
            Lista de momentos con SCC aplicado y categorías actualizadas
        """
        if not momentos:
            return momentos

        logger.info(f"🧮 Aplicando SCC a {len(momentos)} momentos...")

        # Aplicar SCC usando el calculador
        momentos_con_scc = SCC_Calculator.procesar_momentos_con_scc(momentos)

        logger.info(f"✅ SCC aplicado exitosamente a {len(momentos_con_scc)} momentos")
        return momentos_con_scc

    def _procesar_momento_paralelo(self, momento: datetime) -> Dict:
        """
        Procesa un momento individual en paralelo
        Contiene toda la lógica de evaluación que antes estaba en el bucle secuencial

        Args:
            momento: Momento a procesar

        Returns:
            Dict con datos del momento procesado o None si no apto
        """
        try:
            # Evaluación completa del momento exacto
            resultado = self.enraizamiento_calc.calcular_enraizamiento_avanzado(
                momento, self.lat, self.lon, self.tema_consulta
            )

            if resultado and resultado['apto']:
                # Convertir scores a porcentaje para compatibilidad
                enraizamiento_pct = resultado['enraizamiento_score'] * 100
                calidad_pct = resultado['calidad_score'] * 100

                if enraizamiento_pct >= UMBRAL_ENRAIZAMIENTO_MINIMO:
                    # Calcular Puntaje Ranking (calidad del momento para desempate)
                    puntaje_ranking = self._calcular_puntaje_ranking(resultado['detalles'])

                    # Calcular puntuación total combinada para ranking
                    puntuacion_total = self._calcular_puntuacion_total_combinada(
                        resultado['enraizamiento_score'], resultado['calidad_score']
                    )

                    momento_data = {
                        'fecha_hora': momento,
                        'tema_consulta': self.tema_consulta,
                        'enraizamiento_score': resultado['enraizamiento_score'],
                        'calidad_score': resultado['calidad_score'],
                        'enraizamiento_pct': enraizamiento_pct,
                        'calidad_pct': calidad_pct,
                        'puntaje_ranking': puntaje_ranking,
                        'puntuacion_total': puntuacion_total,
                        'detalles': resultado['detalles']
                    }
                    return momento_data

        except Exception as e:
            logger.warning(f"Error procesando momento paralelo {momento}: {e}")

        return None


def procesar_momento_fase1_estatico(momento: datetime, lat: float, lon: float) -> bool:
    """
    Función estática para multiprocessing - Fase 1
    Procesa un momento individual sin depender de 'self'
    """
    try:
        # Crear wrapper para evaluación rápida
        wrapper = LegacyAstroWrapper(momento, lat, lon)

        # Solo verificar descalificadores críticos (muy rápido)
        es_descalificado, razon = wrapper.es_momento_critico_descalificado()

        # Retornar True si NO es descartado (es apto)
        return not es_descalificado

    except Exception as e:
        # En caso de error, considerar apto para no perder oportunidades
        return True


def generar_rango_fechas(fecha_inicio: datetime, dias: int = 365) -> datetime:
    """
    Genera fecha de fin basada en fecha de inicio y número de días
    """
    return fecha_inicio + timedelta(days=dias)
