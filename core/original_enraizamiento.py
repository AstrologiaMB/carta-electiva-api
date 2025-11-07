"""
Original Enraizamiento Calculator - Respecting the Spirit of the Original Code
Implements the exact 23-condition logic from enraizar_a_bn.py with current orb settings
Focuses purely on Carta A (natal) ↔ Carta B(n) (electiva moment) connections
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
from config.settings import ORBE_CONJUNCION, ORBE_TRIGONO_SEXTIL

logger = logging.getLogger(__name__)

class OriginalEnraizamientoCalculator:
    """
    Calculadora que implementa las 23 condiciones originales de enraizamiento
    Mantiene el espíritu del código original con orbes actuales
    """
    
    def __init__(self, datos_natales: Dict):
        """
        Inicializa el calculador con los datos natales base (Carta A)
        
        Args:
            datos_natales: Dict con datos de carta natal
        """
        self.datos_natales = datos_natales
        self._carta_natal_cache = None
        
        # Configurar immanuel
        astro_avanzada_settings()
        
        # Si ya tenemos los datos de carta calculados, usarlos directamente
        if self._es_formato_legacy(datos_natales):
            self._carta_natal_cache = datos_natales
            logger.debug("Usando datos de carta natal A en formato legacy")
    
    def _es_formato_legacy(self, datos: Dict) -> bool:
        """Determina si los datos están en formato legacy (ya calculados)"""
        return 'planetas' in datos and 'casas' in datos and 'asc_grados' in datos
        
    @lru_cache(maxsize=1)
    def _get_carta_natal(self) -> Dict:
        """Obtiene y cachea la carta natal base (Carta A)"""
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
                'asc_signo': json.loads(json.dumps(natal.objects, cls=ToJSON))["3000001"]["sign"]["number"],
                '_houses': natal._houses  # Para análisis de casas
            }
            
            self._carta_natal_cache = carta_data
            logger.debug("Carta natal A calculada y cacheada para enraizamiento original")
            return carta_data
            
        except Exception as e:
            logger.error(f"Error calculando carta natal A: {e}")
            raise
    
    def _get_carta_electiva(self, momento_electivo: datetime, lat: float, lon: float) -> Dict:
        """Calcula la carta para el momento electivo B(n)"""
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
                'asc_signo': json.loads(json.dumps(natal.objects, cls=ToJSON))["3000001"]["sign"]["number"],
                '_houses': natal._houses  # Para análisis de casas
            }
            
            return carta_data
            
        except Exception as e:
            logger.error(f"Error calculando carta electiva B(n): {e}")
            raise
    
    def calcular_enraizamiento_original(self, momento_electivo: datetime, 
                                      lat: float, lon: float) -> Dict:
        """
        Calcula el enraizamiento usando las 23 condiciones originales
        Mantiene el espíritu del código original con orbes actuales
        
        Args:
            momento_electivo: Momento electivo a evaluar
            lat: Latitud del lugar
            lon: Longitud del lugar
            
        Returns:
            Dict con score, detalles y tabla de condiciones, o None si momento descartado
        """
        try:
            # Obtener cartas
            carta_A = self._get_carta_natal()
            carta_B = self._get_carta_electiva(momento_electivo, lat, lon)
            
            # VERIFICACIÓN CRÍTICA: ASC B(n) en casa 8 o 12 de A = DESCARTE AUTOMÁTICO
            asc_moment = carta_B['asc_grados']
            casa_8 = self._asc_en_casa(asc_moment, carta_A, 8)
            casa_12 = self._asc_en_casa(asc_moment, carta_A, 12)
            
            if casa_8 or casa_12:
                logger.debug(f"Momento {momento_electivo} DESCARTADO: ASC en casa {'8' if casa_8 else '12'} natal")
                return {
                    'descartado': True,
                    'razon': f'ASC momento en casa {"8" if casa_8 else "12"} natal',
                    'momento': momento_electivo,
                    'score': 0.0,
                    'porcentaje': 0.0
                }
            
            # Ejecutar las 23 condiciones originales
            tabla_condiciones = self._ejecutar_23_condiciones(carta_A, carta_B)
            
            # Calcular puntuación final
            puntos_rojos = sum(item['Punto'] for item in tabla_condiciones if item.get('Color') == 'Rojo')
            puntos_azules = sum(item['Punto'] for item in tabla_condiciones if item.get('Color') == 'Azul')
            total_puntos = puntos_rojos + puntos_azules
            
            # Normalizar a porcentaje usando relación lineal pura
            # Rango teórico: -6 (peor caso) a +10 (mejor caso) puntos
            # Fórmula lineal: y = 6.25x + 37.5
            # -6 puntos → 0%, 0 puntos → 37.5%, +10 puntos → 100%
            min_puntos_teoricos = -6.0
            max_puntos_teoricos = 10.0
            pendiente = 100.0 / (max_puntos_teoricos - min_puntos_teoricos)  # 6.25
            intercepto = -pendiente * min_puntos_teoricos  # 37.5

            porcentaje = pendiente * total_puntos + intercepto
            porcentaje = max(0, min(100, porcentaje))
            
            # Convertir a rango 0.0-1.0 para integración
            score_normalizado = porcentaje / 100.0
            
            resultado = {
                'score': score_normalizado,
                'porcentaje': porcentaje,
                'puntos_total': total_puntos,
                'puntos_rojos': puntos_rojos,
                'puntos_azules': puntos_azules,
                'condiciones_rojas': sum(1 for item in tabla_condiciones if item.get('Color') == 'Rojo'),
                'condiciones_azules': sum(1 for item in tabla_condiciones if item.get('Color') == 'Azul'),
                'tabla_condiciones': tabla_condiciones,
                'momento': momento_electivo
            }
            
            logger.debug(f"Enraizamiento original: {porcentaje:.1f}% "
                        f"(Rojos:{puntos_rojos}, Azules:{puntos_azules}) para {momento_electivo}")
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error en cálculo de enraizamiento original: {e}")
            # Retornar valor neutro en caso de error
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
    
    def _ejecutar_23_condiciones(self, carta_A: Dict, carta_B: Dict) -> List[Dict]:
        """
        Ejecuta las 23 condiciones originales exactas
        Mantiene la lógica original con orbes actuales
        """
        tabla = []
        
        # Obtener posiciones de la carta natal (A)
        asc_natal = carta_A['asc_grados']
        sat_natal = carta_A['planetas']['4000007']['longitude']['raw']  # Saturno
        marte_natal = carta_A['planetas']['4000005']['longitude']['raw']  # Marte
        jup_natal = carta_A['planetas']['4000006']['longitude']['raw']  # Júpiter
        sol_natal = carta_A['planetas']['4000001']['longitude']['raw']  # Sol
        luna_natal = carta_A['planetas']['4000002']['longitude']['raw']  # Luna
        ven_natal = carta_A['planetas']['4000004']['longitude']['raw']  # Venus
        
        # Obtener posiciones de la carta del momento (B(n))
        asc_moment = carta_B['asc_grados']
        
        # Aspectos y colores (como en el original)
        conjuncion = 0.0
        trigono = 120.0
        sextil = 60.0
        azul = "Azul"
        rojo = "Rojo"
        vacio = "Ninguno"
        
        # CONDICIONES ROJAS (PENALIZACIONES)
        
        # Condición 1: ASC B(n) conjunct Saturno A
        resultado = self._aspect(asc_moment, sat_natal, conjuncion, ORBE_CONJUNCION)
        color = rojo if resultado else vacio
        punto = -2 if resultado else 0
        tabla.append({
            "cond_num": 1,
            "Condicion": "Si el ASC de la carta B(n) coincide con el grado de Saturno de la carta natal A",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        # Condición 2: ASC B(n) conjunct Marte A
        resultado = self._aspect(asc_moment, marte_natal, conjuncion, ORBE_CONJUNCION)
        color = rojo if resultado else vacio
        punto = -2 if resultado else 0
        tabla.append({
            "cond_num": 2,
            "Condicion": "ASC de la carta B(n) coincide con el grado de Marte de la carta natal A",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        # Condición 3: ASC B(n) en casa 6 A
        resultado = self._asc_en_casa(asc_moment, carta_A, 6)
        color = rojo if resultado else vacio
        punto = -2 if resultado else 0
        tabla.append({
            "cond_num": 3,
            "Condicion": "ASC de la carta B(n) está en la casa 6 de la carta natal A",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        # Condición 4: ASC B(n) en casa 8 o 12 A
        casa_8 = self._asc_en_casa(asc_moment, carta_A, 8)
        casa_12 = self._asc_en_casa(asc_moment, carta_A, 12)
        resultado = casa_8 or casa_12
        color = rojo if resultado else vacio
        punto = -2 if resultado else 0
        tabla.append({
            "cond_num": 4,
            "Condicion": "ASC de la carta B(n) está en la casa 8 o 12 de la carta natal A",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        # CONDICIONES AZULES (BONIFICACIONES)
        
        # Condiciones 5-7: ASC B(n) aspectos con ASC A
        resultado = self._aspect(asc_moment, asc_natal, conjuncion, ORBE_CONJUNCION)
        color = azul if resultado else vacio
        punto = 2 if resultado else 0
        tabla.append({
            "cond_num": 5,
            "Condicion": "ASC de la carta B(n) está conjunto al ASC de la carta natal A",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        resultado = self._aspect(asc_moment, asc_natal, trigono, ORBE_TRIGONO_SEXTIL)
        color = azul if resultado else vacio
        punto = 1 if resultado else 0
        tabla.append({
            "cond_num": 6,
            "Condicion": "ASC de la carta B(n) está en trígono al ASC de la carta natal A",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        resultado = self._aspect(asc_moment, asc_natal, sextil, ORBE_TRIGONO_SEXTIL)
        color = azul if resultado else vacio
        punto = 1 if resultado else 0
        tabla.append({
            "cond_num": 7,
            "Condicion": "ASC de la carta B(n) está en sextil al ASC de la carta natal A",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        # Condiciones 8-10: ASC B(n) aspectos con Sol A
        resultado = self._aspect(asc_moment, sol_natal, conjuncion, ORBE_CONJUNCION)
        color = azul if resultado else vacio
        punto = 1 if resultado else 0
        tabla.append({
            "cond_num": 8,
            "Condicion": "ASC de la carta B(n) está conjunto al Sol de la carta natal A",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        resultado = self._aspect(asc_moment, sol_natal, trigono, ORBE_TRIGONO_SEXTIL)
        color = azul if resultado else vacio
        punto = 1 if resultado else 0
        tabla.append({
            "cond_num": 9,
            "Condicion": "ASC de la carta B(n) está en trígono al Sol de la carta natal A",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        resultado = self._aspect(asc_moment, sol_natal, sextil, ORBE_TRIGONO_SEXTIL)
        color = azul if resultado else vacio
        punto = 1 if resultado else 0
        tabla.append({
            "cond_num": 10,
            "Condicion": "ASC de la carta B(n) está en sextil al Sol de la carta natal A",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        # Condiciones 11-13: ASC B(n) aspectos con Luna A
        resultado = self._aspect(asc_moment, luna_natal, conjuncion, ORBE_CONJUNCION)
        color = azul if resultado else vacio
        punto = 1 if resultado else 0
        tabla.append({
            "cond_num": 11,
            "Condicion": "ASC de la carta B(n) está conjunto a la Luna de la carta natal A",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        resultado = self._aspect(asc_moment, luna_natal, trigono, ORBE_TRIGONO_SEXTIL)
        color = azul if resultado else vacio
        punto = 1 if resultado else 0
        tabla.append({
            "cond_num": 12,
            "Condicion": "ASC de la carta B(n) está en trígono a la Luna de la carta natal A",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        resultado = self._aspect(asc_moment, luna_natal, sextil, ORBE_TRIGONO_SEXTIL)
        color = azul if resultado else vacio
        punto = 1 if resultado else 0
        tabla.append({
            "cond_num": 13,
            "Condicion": "ASC de la carta B(n) está en sextil a la Luna de la carta natal A",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        # Condiciones 14-16: ASC B(n) aspectos con Venus A
        resultado = self._aspect(asc_moment, ven_natal, conjuncion, ORBE_CONJUNCION)
        color = azul if resultado else vacio
        punto = 1 if resultado else 0
        tabla.append({
            "cond_num": 14,
            "Condicion": "ASC de la carta B(n) está conjunto a Venus de la carta natal A",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        resultado = self._aspect(asc_moment, ven_natal, trigono, ORBE_TRIGONO_SEXTIL)
        color = azul if resultado else vacio
        punto = 1 if resultado else 0
        tabla.append({
            "cond_num": 15,
            "Condicion": "ASC de la carta B(n) está en trígono a Venus de la carta natal A",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        resultado = self._aspect(asc_moment, ven_natal, sextil, ORBE_TRIGONO_SEXTIL)
        color = azul if resultado else vacio
        punto = 1 if resultado else 0
        tabla.append({
            "cond_num": 16,
            "Condicion": "ASC de la carta B(n) está en sextil a Venus de la carta natal A",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        # Condiciones 17-19: ASC B(n) aspectos con Júpiter A
        resultado = self._aspect(asc_moment, jup_natal, conjuncion, ORBE_CONJUNCION)
        color = azul if resultado else vacio
        punto = 1 if resultado else 0
        tabla.append({
            "cond_num": 17,
            "Condicion": "ASC de la carta B(n) está conjunto a Júpiter de la carta natal A",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        resultado = self._aspect(asc_moment, jup_natal, trigono, ORBE_TRIGONO_SEXTIL)
        color = azul if resultado else vacio
        punto = 1 if resultado else 0
        tabla.append({
            "cond_num": 18,
            "Condicion": "ASC de la carta B(n) está en trígono a Júpiter de la carta natal A",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        resultado = self._aspect(asc_moment, jup_natal, sextil, ORBE_TRIGONO_SEXTIL)
        color = azul if resultado else vacio
        punto = 1 if resultado else 0
        tabla.append({
            "cond_num": 19,
            "Condicion": "ASC de la carta B(n) está en sextil a Júpiter de la carta natal A",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        # Condiciones 20-23: Casa 10 B(n) conjunciones con planetas A
        house_10_cusp = self._get_house_cusp(carta_B, 10)
        
        resultado = self._aspect(house_10_cusp, jup_natal, conjuncion, ORBE_CONJUNCION)
        color = azul if resultado else vacio
        punto = 1 if resultado else 0
        tabla.append({
            "cond_num": 20,
            "Condicion": "Cúspide de la casa 10 del momento está conjunta a Júpiter natal",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        resultado = self._aspect(house_10_cusp, ven_natal, conjuncion, ORBE_CONJUNCION)
        color = azul if resultado else vacio
        punto = 1 if resultado else 0
        tabla.append({
            "cond_num": 21,
            "Condicion": "Cúspide de la casa 10 del momento está conjunta a Venus natal",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        resultado = self._aspect(house_10_cusp, sol_natal, conjuncion, ORBE_CONJUNCION)
        color = azul if resultado else vacio
        punto = 1 if resultado else 0
        tabla.append({
            "cond_num": 22,
            "Condicion": "Cúspide de la casa 10 del momento está conjunta al Sol natal",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        resultado = self._aspect(house_10_cusp, luna_natal, conjuncion, ORBE_CONJUNCION)
        color = azul if resultado else vacio
        punto = 1 if resultado else 0
        tabla.append({
            "cond_num": 23,
            "Condicion": "Cúspide de la casa 10 del momento está conjunta a la Luna natal",
            "Resultado": resultado,
            "Color": color,
            "Punto": punto,
        })
        
        return tabla
    
    def _aspect(self, degree1: float, degree2: float, aspecto_grados: float, orb: float) -> bool:
        """
        Calcula si existe un aspecto entre dos posiciones
        Usa la lógica original con orbes actuales
        """
        # Convertir a float para mantener decimales
        degree1 = float(degree1)
        degree2 = float(degree2)
        
        # Calcular diferencia manteniendo decimales
        diferencia = abs(degree1 - degree2) % 360
        diferencia = min(diferencia, 360 - diferencia)
        
        # Verificar si está dentro del orbe del aspecto
        return abs(diferencia - aspecto_grados) <= orb
    
    def _asc_en_casa(self, asc_grados: float, carta_A: Dict, numero_casa: int) -> bool:
        """
        Determina si el ASC B(n) está en una casa específica de la carta A
        """
        try:
            # Obtener información de la casa desde _houses
            # Manejar tanto formato legacy (int) como immanuel (chart constants)
            house_key = None
            
            if '_houses' not in carta_A:
                logger.debug(f"No hay _houses en carta_A, usando fallback")
                return False
                
            # Intentar con chart constants primero (formato immanuel)
            try:
                house_key = getattr(chart, f'HOUSE{numero_casa}')
                house_info = carta_A['_houses'][house_key]
            except (AttributeError, KeyError):
                # Fallback a formato legacy (número directo)
                try:
                    house_info = carta_A['_houses'][numero_casa]
                except KeyError:
                    logger.debug(f"Casa {numero_casa} no encontrada en _houses")
                    return False
            
            # Extraer información de la casa
            if isinstance(house_info, dict):
                # Formato legacy: {'lon': x, 'size': y}
                house_start_degree = house_info.get('lon', 0)
                house_size = house_info.get('size', 30)
            else:
                # Formato immanuel: objeto con atributos
                house_start_degree = getattr(house_info, 'lon', 0)
                house_size = getattr(house_info, 'size', 30)
            
            house_end_degree = house_start_degree + house_size
            
            # Verificar si ASC está en el rango de la casa
            if house_end_degree <= 360:
                # Casa no cruza 0°
                return house_start_degree <= asc_grados <= house_end_degree
            else:
                # Casa cruza 0° (ej: 330° + 30° = 360°, entonces va de 330° a 0°)
                house_end_degree = house_end_degree % 360
                return asc_grados >= house_start_degree or asc_grados <= house_end_degree
                
        except Exception as e:
            logger.debug(f"Error verificando ASC en casa {numero_casa}: {e}")
            return False
    
    def _get_house_cusp(self, carta: Dict, numero_casa: int) -> float:
        """
        Obtiene la cúspide de una casa específica
        """
        try:
            # Manejar tanto formato legacy como immanuel
            if '_houses' not in carta:
                logger.debug(f"No hay _houses en carta, usando fallback")
                return 0.0
                
            # Intentar con chart constants primero (formato immanuel)
            try:
                house_key = getattr(chart, f'HOUSE{numero_casa}')
                house_info = carta['_houses'][house_key]
            except (AttributeError, KeyError):
                # Fallback a formato legacy (número directo)
                try:
                    house_info = carta['_houses'][numero_casa]
                except KeyError:
                    logger.debug(f"Casa {numero_casa} no encontrada en _houses")
                    return 0.0
            
            # Extraer longitud de la casa
            if isinstance(house_info, dict):
                # Formato legacy: {'lon': x}
                return house_info.get('lon', 0.0)
            else:
                # Formato immanuel: objeto con atributos
                return getattr(house_info, 'lon', 0.0)
                
        except Exception as e:
            logger.debug(f"Error obteniendo cúspide casa {numero_casa}: {e}")
            return 0.0
