"""
Advanced Enraizamiento Calculator for v2.0
Analyzes real astrological connections between natal chart A and electiva moment B(n)
Generates variable scores from 25%-95% based on actual astrological factors
"""

import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Any
from functools import lru_cache

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from immanuel import charts
from immanuel.const import chart, dignities
from immanuel.classes.serialize import ToJSON
from legacy_astro.settings_astro import astro_avanzada_settings
from config.settings import ENRAIZAMIENTO_WEIGHTS, ORBE_CONJUNCION, ORBE_TRIGONO_SEXTIL, ORBE_CUADRATURA_OPOSICION

logger = logging.getLogger(__name__)

class EnraizamientoCalculator:
    """
    Calculadora avanzada de enraizamiento que analiza conexiones reales
    entre carta natal A y momento electivo B(n)
    """
    
    def __init__(self, datos_natales: Dict):
        """
        Inicializa el calculador con los datos natales base
        
        Args:
            datos_natales: Dict con datos de carta natal (formato legacy o nuevo)
        """
        self.datos_natales = datos_natales
        self._carta_natal_cache = None
        
        # Configurar immanuel
        astro_avanzada_settings()
        
        # Si ya tenemos los datos de carta calculados, usarlos directamente
        if self._es_formato_legacy(datos_natales):
            self._carta_natal_cache = datos_natales
            logger.debug("Usando datos de carta natal en formato legacy")
    
    def _es_formato_legacy(self, datos: Dict) -> bool:
        """
        Determina si los datos están en formato legacy (ya calculados) o nuevo (para calcular)
        """
        # Formato legacy tiene 'planetas', 'casas', 'asc_grados'
        # Formato nuevo tiene 'fecha_nacimiento', 'lat_nacimiento', 'lon_nacimiento'
        return 'planetas' in datos and 'casas' in datos and 'asc_grados' in datos
        
    @lru_cache(maxsize=1)
    def _get_carta_natal(self) -> Dict:
        """
        Obtiene y cachea la carta natal base (Carta A)
        Se calcula una sola vez por sesión para optimizar performance
        """
        if self._carta_natal_cache is not None:
            return self._carta_natal_cache
            
        try:
            fecha_nacimiento = self.datos_natales['fecha_nacimiento']
            lat = self.datos_natales['lat_nacimiento']
            lon = self.datos_natales['lon_nacimiento']
            
            # Crear carta natal usando immanuel
            subject = charts.Subject(fecha_nacimiento, lat, lon)
            natal = charts.Natal(subject)
            
            # Convertir a JSON para facilitar análisis
            carta_data = {
                'planetas': json.loads(json.dumps(natal.objects, cls=ToJSON, indent=4)),
                'casas': json.loads(json.dumps(natal.houses, cls=ToJSON, indent=4)),
                'aspectos': json.loads(json.dumps(natal.aspects, cls=ToJSON, indent=4)),
                'asc_grados': json.loads(json.dumps(natal.objects, cls=ToJSON))["3000001"]["longitude"]["raw"],
                'asc_signo': json.loads(json.dumps(natal.objects, cls=ToJSON))["3000001"]["sign"]["number"]
            }
            
            self._carta_natal_cache = carta_data
            logger.debug("Carta natal A calculada y cacheada")
            return carta_data
            
        except Exception as e:
            logger.error(f"Error calculando carta natal A: {e}")
            raise
    
    @lru_cache(maxsize=1000)
    def _get_carta_electiva_cached(self, momento_tuple: tuple) -> Dict:
        """
        Calcula la carta para el momento electivo B(n) con cache inteligente

        Args:
            momento_tuple: Tuple (timestamp, lat, lon) para cache hashable

        Returns:
            Dict con datos de la carta electiva
        """
        timestamp, lat, lon = momento_tuple
        momento_electivo = datetime.fromtimestamp(timestamp)

        try:
            # Crear carta electiva usando immanuel
            subject = charts.Subject(momento_electivo, lat, lon)
            natal = charts.Natal(subject)

            # Convertir a JSON para facilitar análisis
            carta_data = {
                'planetas': json.loads(json.dumps(natal.objects, cls=ToJSON, indent=4)),
                'casas': json.loads(json.dumps(natal.houses, cls=ToJSON, indent=4)),
                'aspectos': json.loads(json.dumps(natal.aspects, cls=ToJSON, indent=4)),
                'asc_grados': json.loads(json.dumps(natal.objects, cls=ToJSON))["3000001"]["longitude"]["raw"],
                'asc_signo': json.loads(json.dumps(natal.objects, cls=ToJSON))["3000001"]["sign"]["number"]
            }

            return carta_data

        except Exception as e:
            logger.error(f"Error calculando carta electiva B(n): {e}")
            raise

    def _get_carta_electiva(self, momento_electivo: datetime, lat: float, lon: float) -> Dict:
        """
        Wrapper para obtener carta electiva con cache

        Args:
            momento_electivo: Fecha y hora del momento electivo
            lat: Latitud del lugar
            lon: Longitud del lugar

        Returns:
            Dict con datos de la carta electiva
        """
        # Convertir a tuple hashable para cache
        momento_tuple = (momento_electivo.timestamp(), lat, lon)
        return self._get_carta_electiva_cached(momento_tuple)
    
    def calcular_enraizamiento_avanzado(self, momento_electivo: datetime, 
                                      lat: float, lon: float, tema_consulta: str) -> Dict:
        """
        Nueva metodología: Enraizamiento Primario + Desempate por Calidad
        
        Args:
            momento_electivo: Momento electivo a evaluar
            lat: Latitud del lugar
            lon: Longitud del lugar
            tema_consulta: Tema de la consulta (trabajo, amor, etc.)
            
        Returns:
            Dict: {
                'apto': bool,
                'enraizamiento_score': float,  # Score principal (0.0-1.0)
                'calidad_score': float,        # Score de desempate (0.0-1.0)
                'momento': datetime,
                'detalles': dict
            } o None si momento no apto
        """
        try:
            # FASE 1: EVALUACIÓN DE CALIDAD DEL MOMENTO (Filtros + Puntaje)
            resultado_fase1 = self._evaluar_fase1_calidad(momento_electivo, lat, lon)
            
            if not resultado_fase1['apto']:
                # Momento descartado por filtros
                return None
            
            # FASE 2: ENRAIZAMIENTO PURO (EL GRAN JUEZ)
            resultado_enraizamiento_puro = self._calcular_enraizamiento_puro_completo(momento_electivo, lat, lon)
            score_enraizamiento = resultado_enraizamiento_puro['score']

            # Preparar resultado
            resultado = {
                'apto': True,
                'enraizamiento_score': score_enraizamiento,
                'calidad_score': resultado_fase1['score_normalizado'],
                'momento': momento_electivo,
                'detalles': {
                    'fase1': resultado_fase1,
                    'enraizamiento_puro': resultado_enraizamiento_puro,  # Información completa del enraizamiento puro
                    'enraizamiento_puntos': resultado_fase1.get('enraizamiento_detalles', {}),
                    'tema_consulta': tema_consulta
                }
            }
            
            logger.debug(f"Momento evaluado: {momento_electivo} - "
                        f"Enraizamiento: {score_enraizamiento:.3f}, "
                        f"Calidad: {resultado_fase1['score_normalizado']:.3f}")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error en evaluación de momento: {e}")
            return None
    
    def _evaluar_fase1_calidad(self, momento_electivo: datetime, lat: float, lon: float) -> Dict:
        """
        Evalúa la calidad del momento usando filtros y puntajes de Fase 1
        
        Returns:
            Dict: {
                'apto': bool,
                'score_normalizado': float,
                'puntos_totales': float,
                'detalles': dict
            }
        """
        try:
            # VERIFICACIÓN CRÍTICA PREVIA: ASC B(n) en casa 8 o 12 de A = DESCARTE AUTOMÁTICO
            carta_A = self._get_carta_natal()
            carta_B = self._get_carta_electiva(momento_electivo, lat, lon)
            
            asc_moment = carta_B['asc_grados']
            casa_8 = self._asc_en_casa_natal(asc_moment, carta_A, 8)
            casa_12 = self._asc_en_casa_natal(asc_moment, carta_A, 12)
            
            if casa_8 or casa_12:
                logger.debug(f"Momento {momento_electivo} DESCARTADO en Fase 1: ASC en casa {'8' if casa_8 else '12'} natal")
                return {
                    'apto': False, 
                    'razon': f'ASC momento en casa {"8" if casa_8 else "12"} natal - DESCARTE AUTOMÁTICO'
                }
            
            from core.legacy_wrapper import LegacyAstroWrapper
            
            # Crear wrapper para momento electivo B(n)
            wrapper_B = LegacyAstroWrapper(momento_electivo, lat, lon)
            
            # 1. EVALUAR LUNA (Filtro + Puntos)
            eval_luna = wrapper_B.evaluar_luna_completo()
            if not eval_luna['apto']:
                return {'apto': False, 'razon': 'Luna no apta'}
            puntos_luna = eval_luna['puntos_luna']
            
            # 2. EVALUAR REGENTE ASC (Filtro + Puntos)
            eval_asc = wrapper_B.evaluar_regente_asc_completo()
            if not eval_asc['apto']:
                return {'apto': False, 'razon': 'Regente ASC no apto'}
            puntos_asc = eval_asc['puntos_regente_asc']
            
            # 3. EVALUAR REGENTE CASA 10 (Filtro + Puntos)
            eval_casa10 = wrapper_B.evaluar_regente_casa10_completo()
            if not eval_casa10['apto']:
                return {'apto': False, 'razon': 'Regente Casa 10 no apto'}
            puntos_casa10 = eval_casa10['puntos_regente_casa10']
            
            # 4. EVALUAR COMBINACIONES POSITIVAS (Solo puntos)
            eval_positivas = wrapper_B.evaluar_combinaciones_positivas()
            puntos_positivas = eval_positivas['puntos_combinaciones_positivas']
            
            # 5. EVALUAR COMBINACIONES NEGATIVAS (Solo puntos)
            eval_negativas = wrapper_B.evaluar_combinaciones_negativas(self.datos_natales)
            puntos_negativas = eval_negativas['puntos_combinaciones_negativas']
            
            # 6. CALCULAR PUNTOS TOTALES
            puntos_totales = (
                puntos_luna +           # Máximo 10 puntos (corregido con exclusiones mutuas)
                puntos_asc +            # Máximo 10 puntos
                puntos_casa10 +         # Máximo 6 puntos
                puntos_positivas +      # Máximo 6 puntos
                puntos_negativas        # Máximo -2 puntos (penalizaciones)
            )

            # 7. NORMALIZAR SCORE (0.0-1.0)
            puntos_maximos = 32.0  # 10+10+6+6 = 32 (corregido con exclusiones mutuas)
            puntos_minimos = -2.0  # Solo penalizaciones negativas (máximo -2)
            
            if puntos_totales <= puntos_minimos:
                score_normalizado = 0.0
            elif puntos_totales >= puntos_maximos:
                score_normalizado = 1.0
            else:
                # Normalizar al rango 0.0-1.0
                ratio = (puntos_totales - puntos_minimos) / (puntos_maximos - puntos_minimos)
                score_normalizado = max(0.0, min(1.0, ratio))
            
            return {
                'apto': True,
                'score_normalizado': score_normalizado,
                'puntos_totales': puntos_totales,
                'detalles': {
                    'luna': eval_luna,
                    'regente_asc': eval_asc,
                    'regente_casa10': eval_casa10,
                    'combinaciones_positivas': eval_positivas,
                    'combinaciones_negativas': eval_negativas,
                    'puntos_maximos': puntos_maximos,
                    'puntos_minimos': puntos_minimos
                }
            }
            
        except Exception as e:
            logger.error(f"Error en evaluación Fase 1: {e}")
            return {'apto': False, 'razon': f'Error: {e}'}
    
    def _calcular_enraizamiento_puro(self, momento_electivo: datetime, lat: float, lon: float) -> float:
        """
        Calcula el enraizamiento puro usando las 23 condiciones originales

        Returns:
            float: Score de enraizamiento (0.0-1.0)
        """
        try:
            from core.original_enraizamiento import OriginalEnraizamientoCalculator

            # Usar el calculador de enraizamiento original optimizado
            original_calc = OriginalEnraizamientoCalculator(self.datos_natales)
            resultado_original = original_calc.calcular_enraizamiento_original(
                momento_electivo, lat, lon
            )

            # Retornar score normalizado (0.0-1.0)
            return resultado_original['score']

        except Exception as e:
            logger.error(f"Error calculando enraizamiento puro: {e}")
            # Retornar valor neutro en caso de error
            return 0.5

    def _calcular_enraizamiento_puro_completo(self, momento_electivo: datetime, lat: float, lon: float) -> Dict:
        """
        Calcula el enraizamiento puro usando las 23 condiciones originales
        Retorna toda la información del resultado original

        Returns:
            Dict: Resultado completo incluyendo puntos_total, score, etc.
        """
        try:
            from core.original_enraizamiento import OriginalEnraizamientoCalculator

            # Usar el calculador de enraizamiento original optimizado
            original_calc = OriginalEnraizamientoCalculator(self.datos_natales)
            resultado_original = original_calc.calcular_enraizamiento_original(
                momento_electivo, lat, lon
            )

            # Retornar resultado completo
            return resultado_original

        except Exception as e:
            logger.error(f"Error calculando enraizamiento puro completo: {e}")
            # Retornar resultado neutro en caso de error
            return {
                'score': 0.5,
                'porcentaje': 50.0,
                'puntos_total': 0,
                'puntos_rojos': 0,
                'puntos_azules': 0,
                'condiciones_rojas': 0,
                'condiciones_azules': 0,
                'tabla_condiciones': [],
                'momento': momento_electivo,
                'error': str(e)
            }
    
    def _analizar_conexiones_principales(self, carta_A: Dict, carta_B: Dict, tema_consulta: str) -> Dict:
        """
        Analiza las conexiones principales entre las dos cartas
        
        Returns:
            Dict con todas las conexiones encontradas y sus puntuaciones
        """
        conexiones = {
            'asc_connections': [],
            'casa_tema_connections': [],
            'regente_connections': [],
            'aspectos_generales': [],
            'penalizaciones': []
        }
        
        # 1. Conexiones del ASC B(n) con planetas A
        conexiones['asc_connections'] = self._analizar_conexiones_asc(carta_A, carta_B)
        
        # 2. Conexiones de Casa Tema B(n) con planetas A
        casa_tema = self._get_casa_tema(tema_consulta)
        conexiones['casa_tema_connections'] = self._analizar_conexiones_casa_tema(
            carta_A, carta_B, casa_tema
        )
        
        # 3. Conexiones de regentes
        conexiones['regente_connections'] = self._analizar_conexiones_regentes(carta_A, carta_B)
        
        # 4. Aspectos generales importantes
        conexiones['aspectos_generales'] = self._analizar_aspectos_generales(carta_A, carta_B)
        
        # 5. Penalizaciones críticas
        conexiones['penalizaciones'] = self._analizar_penalizaciones(carta_A, carta_B)
        
        return conexiones
    
    def _analizar_conexiones_asc(self, carta_A: Dict, carta_B: Dict) -> List[Dict]:
        """
        Analiza conexiones del ASC B(n) con planetas importantes de A
        """
        conexiones = []
        asc_B_grados = carta_B['asc_grados']
        
        
        # Planetas importantes para conexiones ASC
        planetas_importantes = {
            '4000001': 'sol',      # Sol
            '4000002': 'luna',     # Luna  
            '4000004': 'venus',    # Venus
            '4000006': 'jupiter',  # Júpiter
            '3000001': 'asc'       # ASC de A
        }
        
        for planeta_id, planeta_nombre in planetas_importantes.items():
            if planeta_id in carta_A['planetas']:
                planeta_A_grados = carta_A['planetas'][planeta_id]['longitude']['raw']
                
                # Calcular aspecto
                aspecto = self._calcular_aspecto(asc_B_grados, planeta_A_grados)
                
                if aspecto:
                    peso = self._get_peso_conexion_asc(planeta_nombre, aspecto['tipo'])
                    if peso > 0:
                        conexiones.append({
                            'tipo': f'asc_{aspecto["tipo"]}_{planeta_nombre}_A',
                            'peso': peso,
                            'orbe': aspecto['orbe'],
                            'descripcion': f'ASC B(n) {aspecto["tipo"]} {planeta_nombre.upper()} A'
                        })
        
        return conexiones
    
    def _analizar_conexiones_casa_tema(self, carta_A: Dict, carta_B: Dict, casa_tema: int) -> List[Dict]:
        """
        Analiza conexiones de la Casa Tema B(n) con planetas A
        """
        conexiones = []
        
        # Obtener cúspide de casa tema en B(n)
        casa_id = str(2000000 + casa_tema)
        if casa_id not in carta_B['casas']:
            return conexiones
            
        casa_tema_grados = carta_B['casas'][casa_id]['longitude']['raw']
        
        # Planetas importantes para casa tema
        planetas_importantes = {
            '4000001': 'sol',      # Sol
            '4000002': 'luna',     # Luna
            '4000004': 'venus',    # Venus
            '4000006': 'jupiter'   # Júpiter
        }
        
        for planeta_id, planeta_nombre in planetas_importantes.items():
            if planeta_id in carta_A['planetas']:
                planeta_A_grados = carta_A['planetas'][planeta_id]['longitude']['raw']
                
                # Calcular aspecto
                aspecto = self._calcular_aspecto(casa_tema_grados, planeta_A_grados)
                
                if aspecto and aspecto['tipo'] == 'conjuncion':
                    peso = self._get_peso_conexion_casa_tema(planeta_nombre)
                    if peso > 0:
                        conexiones.append({
                            'tipo': f'casa_tema_conjuncion_{planeta_nombre}_A',
                            'peso': peso,
                            'orbe': aspecto['orbe'],
                            'descripcion': f'Casa {casa_tema} B(n) conjunción {planeta_nombre.upper()} A'
                        })
        
        return conexiones
    
    def _analizar_conexiones_regentes(self, carta_A: Dict, carta_B: Dict) -> List[Dict]:
        """
        Analiza conexiones de regentes importantes
        """
        conexiones = []
        
        # Obtener regente ASC B(n)
        asc_signo_B = carta_B['asc_signo']
        regente_asc_B = dignities.TRADITIONAL_RULERSHIPS[asc_signo_B]
        
        if str(regente_asc_B) in carta_B['planetas']:
            regente_B_grados = carta_B['planetas'][str(regente_asc_B)]['longitude']['raw']
            
            # Analizar aspectos con planetas A
            planetas_A = ['4000001', '4000002', '4000004', '4000006']  # Sol, Luna, Venus, Júpiter
            
            for planeta_id in planetas_A:
                if planeta_id in carta_A['planetas']:
                    planeta_A_grados = carta_A['planetas'][planeta_id]['longitude']['raw']
                    
                    aspecto = self._calcular_aspecto(regente_B_grados, planeta_A_grados)
                    
                    if aspecto and aspecto['tipo'] == 'conjuncion':
                        conexiones.append({
                            'tipo': 'regente_asc_B_conjuncion_planetas_A',
                            'peso': ENRAIZAMIENTO_WEIGHTS.get('regente_asc_B_conjuncion_planetas_A', 6),
                            'orbe': aspecto['orbe'],
                            'descripcion': f'Regente ASC B(n) conjunción planeta A'
                        })
        
        return conexiones
    
    def _analizar_aspectos_generales(self, carta_A: Dict, carta_B: Dict) -> List[Dict]:
        """
        Analiza aspectos generales importantes entre las cartas
        """
        conexiones = []
        
        # Aspectos armónicos ASC B(n) con planetas A
        asc_B_grados = carta_B['asc_grados']
        
        planetas_A = {
            '4000001': 'sol',
            '4000002': 'luna', 
            '4000004': 'venus',
            '4000006': 'jupiter'
        }
        
        for planeta_id, planeta_nombre in planetas_A.items():
            if planeta_id in carta_A['planetas']:
                planeta_A_grados = carta_A['planetas'][planeta_id]['longitude']['raw']
                
                aspecto = self._calcular_aspecto(asc_B_grados, planeta_A_grados)
                
                if aspecto and aspecto['tipo'] in ['trigono', 'sextil']:
                    peso = ENRAIZAMIENTO_WEIGHTS.get(f'asc_{aspecto["tipo"]}_planetas_A', 6)
                    conexiones.append({
                        'tipo': f'asc_{aspecto["tipo"]}_planetas_A',
                        'peso': peso,
                        'orbe': aspecto['orbe'],
                        'descripcion': f'ASC B(n) {aspecto["tipo"]} {planeta_nombre.upper()} A'
                    })
        
        return conexiones
    
    def _analizar_penalizaciones(self, carta_A: Dict, carta_B: Dict) -> List[Dict]:
        """
        Analiza penalizaciones críticas
        """
        penalizaciones = []
        asc_B_grados = carta_B['asc_grados']
        
        # Penalizaciones por conjunciones problemáticas
        planetas_problematicos = {
            '4000007': 'saturno',  # Saturno
            '4000005': 'marte'     # Marte
        }
        
        for planeta_id, planeta_nombre in planetas_problematicos.items():
            if planeta_id in carta_A['planetas']:
                planeta_A_grados = carta_A['planetas'][planeta_id]['longitude']['raw']
                
                aspecto = self._calcular_aspecto(asc_B_grados, planeta_A_grados)
                
                if aspecto and aspecto['tipo'] == 'conjuncion':
                    peso = ENRAIZAMIENTO_WEIGHTS.get(f'asc_conjuncion_{planeta_nombre}_A', -12)
                    penalizaciones.append({
                        'tipo': f'asc_conjuncion_{planeta_nombre}_A',
                        'peso': peso,
                        'orbe': aspecto['orbe'],
                        'descripcion': f'ASC B(n) conjunción {planeta_nombre.upper()} A (penalización)'
                    })
        
        return penalizaciones
    
    def _calcular_aspecto(self, grados1: float, grados2: float) -> Dict:
        """
        Calcula el aspecto entre dos posiciones planetarias
        
        Returns:
            Dict con tipo de aspecto y orbe, o None si no hay aspecto válido
        """
        # Calcular diferencia angular
        diff = abs(grados1 - grados2)
        if diff > 180:
            diff = 360 - diff
        
        # Definir aspectos y orbes
        aspectos = [
            ('conjuncion', 0, ORBE_CONJUNCION),
            ('sextil', 60, ORBE_TRIGONO_SEXTIL),
            ('cuadratura', 90, ORBE_CUADRATURA_OPOSICION),
            ('trigono', 120, ORBE_TRIGONO_SEXTIL),
            ('oposicion', 180, ORBE_CUADRATURA_OPOSICION)
        ]
        
        for nombre, angulo_exacto, orbe_maximo in aspectos:
            orbe = abs(diff - angulo_exacto)
            if orbe <= orbe_maximo:
                return {
                    'tipo': nombre,
                    'orbe': orbe,
                    'angulo_exacto': angulo_exacto
                }
        
        return None
    
    def _get_peso_conexion_asc(self, planeta: str, aspecto: str) -> int:
        """
        Obtiene el peso para conexiones ASC según planeta y aspecto
        """
        key = f'asc_{aspecto}_{planeta}_A'
        return ENRAIZAMIENTO_WEIGHTS.get(key, 0)
    
    def _get_peso_conexion_casa_tema(self, planeta: str) -> int:
        """
        Obtiene el peso para conexiones Casa Tema
        """
        key = f'casa_tema_conjuncion_{planeta}_A'
        return ENRAIZAMIENTO_WEIGHTS.get(key, 0)
    
    def _get_casa_tema(self, tema_consulta: str) -> int:
        """
        Obtiene el número de casa según el tema de consulta
        """
        temas_casas = {
            'trabajo': 10,
            'carrera': 10,
            'profesion': 10,
            'amor': 7,
            'pareja': 7,
            'matrimonio': 7,
            'dinero': 2,
            'finanzas': 2,
            'salud': 6,
            'viajes': 9,
            'estudios': 9,
            'hogar': 4,
            'familia': 4
        }
        
        return temas_casas.get(tema_consulta.lower(), 1)  # Default Casa 1
    
    def _calcular_score_final(self, conexiones: Dict) -> float:
        """
        Calcula el score final basado en todas las conexiones
        """
        score_total = 0
        
        # Sumar todas las conexiones positivas
        for categoria in ['asc_connections', 'casa_tema_connections', 
                         'regente_connections', 'aspectos_generales']:
            for conexion in conexiones[categoria]:
                score_total += conexion['peso']
        
        # Restar penalizaciones
        for penalizacion in conexiones['penalizaciones']:
            score_total += penalizacion['peso']  # Ya son negativos
        
        # Normalizar a rango 0.25-0.95
        # Score base: 0 puntos = 25%, Score alto: 100+ puntos = 95%
        score_normalizado = 0.25 + (score_total / 100.0) * 0.70
        
        return max(0.25, min(0.95, score_normalizado))
    
    def _asc_en_casa_natal(self, asc_grados: float, carta_A: Dict, numero_casa: int) -> bool:
        """
        Determina si el ASC B(n) está en una casa específica de la carta natal A
        Método auxiliar para verificación de descarte automático
        """
        try:
            # Obtener información de la casa desde casas
            casa_id = str(2000000 + numero_casa)
            if casa_id not in carta_A['casas']:
                logger.debug(f"Casa {numero_casa} no encontrada en carta natal")
                return False
            
            casa_info = carta_A['casas'][casa_id]
            house_start_degree = casa_info['longitude']['raw']
            
            # Calcular siguiente casa para obtener el rango
            siguiente_casa_num = (numero_casa % 12) + 1
            siguiente_casa_id = str(2000000 + siguiente_casa_num)
            
            if siguiente_casa_id in carta_A['casas']:
                house_end_degree = carta_A['casas'][siguiente_casa_id]['longitude']['raw']
            else:
                # Fallback: asumir 30 grados
                house_end_degree = (house_start_degree + 30) % 360
            
            # Verificar si ASC está en el rango de la casa
            if house_start_degree <= house_end_degree:
                # Casa no cruza 0°
                return house_start_degree <= asc_grados <= house_end_degree
            else:
                # Casa cruza 0° (ej: casa empieza en 330° y termina en 30°)
                return asc_grados >= house_start_degree or asc_grados <= house_end_degree
                
        except Exception as e:
            logger.debug(f"Error verificando ASC en casa {numero_casa}: {e}")
            return False
