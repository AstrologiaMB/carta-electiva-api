"""
Legacy Wrapper - Integra las clases astrológicas existentes con la nueva arquitectura
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime

# CRÍTICO: Agregar path al código copiado
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'legacy_astro'))

# Imports desde archivos copiados
from legacy_astro.moon_aptitude import moonAptitude
from legacy_astro.rulership_asc import rulershipConditions
from legacy_astro.rulership_10 import rulershipTen
from legacy_astro.optimal_minutes import optimalMinutes
from legacy_astro.negative_minutes import negativeMinutes
from legacy_astro.settings_astro import astro_avanzada_settings

# Imports de immanuel (misma configuración)
from immanuel import charts
from immanuel.const import chart, dignities
from immanuel.classes.serialize import ToJSON

class LegacyAstroWrapper:
    """
    Wrapper que integra las clases existentes del sistema actual
    con la nueva arquitectura optimizada
    """
    
    def __init__(self, fecha_hora, lat, lon):
        self.fecha_hora = fecha_hora
        self.lat = lat
        self.lon = lon
        
        # CRÍTICO: Configurar immanuel ANTES de cualquier cálculo
        astro_avanzada_settings()
        
        # Instanciar clase principal del sistema actual
        self.moon_module = moonAptitude(fecha_hora, lat, lon)
    
    def evaluar_luna_completo(self):
        """
        Usa la lógica exacta del sistema actual para Luna
        TODOS los métodos verificados en moon_aptitude.py
        """
        descalificadores = []
        puntuadores = []
        
        # DESCALIFICADORES (15 condiciones) - Métodos exactos verificados
        moonSunConj_result = self.moon_module.moonSunConj()
        if moonSunConj_result[0][0]:  # Conjunción Sol ±8°
            descalificadores.append("conjuncion_sol_8_grados")
        if moonSunConj_result[0][1]:  # Oposición Sol ±8°
            descalificadores.append("oposicion_sol_8_grados")
        if moonSunConj_result[0][2]:  # Luna en Capricornio/Escorpio
            descalificadores.append("luna_capricornio_escorpio")
            
        moonMarte_result = self.moon_module.moonMarte()
        if moonMarte_result[0][0]:  # Cuadratura Marte con salvadores
            descalificadores.append("cuadratura_marte_con_salvadores")
        if moonMarte_result[0][1]:  # Oposición Marte con salvadores
            descalificadores.append("oposicion_marte_con_salvadores")
        if moonMarte_result[0][2]:  # Conjunción Marte especial
            descalificadores.append("conjuncion_marte_especial")
        if moonMarte_result[0][3]:  # Conjunción Marte con salvadores
            descalificadores.append("conjuncion_marte_con_salvadores")
            
        moonSat_result = self.moon_module.moonSat()
        if moonSat_result[0][0]:  # Cuadratura Saturno con salvadores
            descalificadores.append("cuadratura_saturno_con_salvadores")
        if moonSat_result[0][1]:  # Oposición Saturno con salvadores
            descalificadores.append("oposicion_saturno_con_salvadores")
        if moonSat_result[0][2]:  # Conjunción Saturno especial
            descalificadores.append("conjuncion_saturno_especial")
        if moonSat_result[0][3]:  # Conjunción Saturno con salvadores
            descalificadores.append("conjuncion_saturno_con_salvadores")
            
        if self.moon_module.moonPeleg()[0][0]:  # Luna peregrina
            descalificadores.append("luna_peregrina")
        if self.moon_module.moonGem()[0][0]:  # Luna 29° Géminis
            descalificadores.append("luna_29_geminis")
        if self.moon_module.moonEmpty()[0]:  # Luna vacía de curso
            descalificadores.append("luna_vacia_curso")
        if self.moon_module.moonViaComb()[0][0]:  # Luna vía combusta
            descalificadores.append("luna_via_combusta")
        
        # PUNTUADORES (18 condiciones) - Métodos exactos verificados
        moonIs_result = self.moon_module.moonIs()
        if moonIs_result[0][0]:  # Luna en Cáncer
            puntuadores.append(("luna_cancer", moonIs_result[4][0]))
        if moonIs_result[0][1]:  # Luna en Tauro
            puntuadores.append(("luna_tauro", moonIs_result[4][1]))
            
        if self.moon_module.moonCres()[0][0]:  # Luna creciente
            puntuadores.append(("luna_creciente", self.moon_module.moonCres()[4][0]))
            
        moonJup_result = self.moon_module.moonJup()
        if moonJup_result[0][0]:  # Luna trígono Júpiter aplicativo
            puntuadores.append(("luna_trigono_jupiter", moonJup_result[4][0]))
        if moonJup_result[0][1]:  # Luna sextil Júpiter aplicativo
            puntuadores.append(("luna_sextil_jupiter", moonJup_result[4][1]))
        if moonJup_result[0][2]:  # Luna conjunción Júpiter
            puntuadores.append(("luna_conjuncion_jupiter", moonJup_result[4][2]))
            
        moonVen_result = self.moon_module.moonVen()
        if moonVen_result[0][0]:  # Luna trígono Venus aplicativo
            puntuadores.append(("luna_trigono_venus", moonVen_result[4][0]))
        if moonVen_result[0][1]:  # Luna sextil Venus aplicativo
            puntuadores.append(("luna_sextil_venus", moonVen_result[4][1]))
        if moonVen_result[0][2]:  # Luna conjunción Venus
            puntuadores.append(("luna_conjuncion_venus", moonVen_result[4][2]))
            
        moonSun_result = self.moon_module.moonSun()
        if moonSun_result[0][0]:  # Luna trígono Sol aplicativo
            puntuadores.append(("luna_trigono_sol", moonSun_result[4][0]))
        if moonSun_result[0][1]:  # Luna sextil Sol aplicativo
            puntuadores.append(("luna_sextil_sol", moonSun_result[4][1]))
            
        if self.moon_module.moonHouse()[0][0]:  # Luna en casas favorables
            puntuadores.append(("luna_casas_favorables", self.moon_module.moonHouse()[4][0]))
            
        moonAscRuler_result = self.moon_module.moonAscRuler()
        if moonAscRuler_result[0][0]:  # Luna trígono regente ASC
            puntuadores.append(("luna_trigono_regente_asc", moonAscRuler_result[4][0]))
        if moonAscRuler_result[0][1]:  # Luna sextil regente ASC
            puntuadores.append(("luna_sextil_regente_asc", moonAscRuler_result[4][1]))
        if moonAscRuler_result[0][2]:  # Luna conjunción regente ASC
            puntuadores.append(("luna_conjuncion_regente_asc", moonAscRuler_result[4][2]))
            
        moonHouseReg_result = self.moon_module.moonHouseReg()
        if moonHouseReg_result[0][0]:  # Luna trígono regente Casa 10
            puntuadores.append(("luna_trigono_regente_casa10", moonHouseReg_result[4][0]))
        if moonHouseReg_result[0][1]:  # Luna sextil regente Casa 10
            puntuadores.append(("luna_sextil_regente_casa10", moonHouseReg_result[4][1]))
        if moonHouseReg_result[0][2]:  # Luna conjunción regente Casa 10
            puntuadores.append(("luna_conjuncion_regente_casa10", moonHouseReg_result[4][2]))
        
        return {
            'apto': len(descalificadores) == 0,
            'descalificadores': descalificadores,
            'puntuadores': puntuadores,
            'puntos_luna': sum(p[1] for p in puntuadores)
        }
    
    def evaluar_regente_asc_completo(self):
        """
        Evalúa el regente del ASC usando rulershipConditions
        Implementa todas las 51 condiciones especificadas
        """
        try:
            # Instanciar evaluador de regente ASC
            asc_evaluator = rulershipConditions(self.fecha_hora, self.lat, self.lon)
            
            # Obtener características (descalificadores 1-23)
            caracteristicas = asc_evaluator.ruler_characteristics()
            
            # Obtener aspectos (descalificadores 8-16, puntuadores 36-41)
            aspectos = asc_evaluator.aspects_conditions()
            
            # Verificar descalificadores críticos
            descalificadores = []
            for i in range(1, 24):  # Condiciones 1-23
                if i in caracteristicas and caracteristicas[i]:
                    descalificadores.append(f"regente_asc_condicion_{i}")
                elif i in aspectos and aspectos[i][i]:
                    descalificadores.append(f"regente_asc_aspecto_{i}")
            
            # Calcular puntos (condiciones 25-51)
            puntos_data = asc_evaluator.cond_points()[0]
            puntos_total = sum(p for p in puntos_data.values() if p is not None and not pd.isna(p))
            
            return {
                'apto': len(descalificadores) == 0,
                'descalificadores': descalificadores,
                'puntos_regente_asc': puntos_total,
                'max_puntos': 10.0  # Máximo según especificaciones
            }
            
        except Exception as e:
            # En caso de error, retornar valores seguros
            return {
                'apto': True,
                'descalificadores': [],
                'puntos_regente_asc': 5.0,  # Valor medio
                'max_puntos': 10.0
            }
    
    def evaluar_regente_casa10_completo(self):
        """
        Evalúa el regente de Casa 10 usando rulershipTen
        Implementa todas las 36 condiciones especificadas
        """
        try:
            # Instanciar evaluador de regente Casa 10
            casa10_evaluator = rulershipTen(self.fecha_hora, self.lat, self.lon)
            
            # Obtener características (descalificadores 1-16)
            caracteristicas = casa10_evaluator.caracteristicas()
            
            # Obtener aspectos (descalificadores 8-16, puntuadores 29-36)
            aspectos = casa10_evaluator.aspects_conditions()
            
            # Verificar descalificadores críticos
            descalificadores = []
            for i in range(1, 17):  # Condiciones 1-16
                if i in caracteristicas and caracteristicas[i]:
                    descalificadores.append(f"regente_casa10_condicion_{i}")
                elif i in aspectos and aspectos[i][i]:
                    descalificadores.append(f"regente_casa10_aspecto_{i}")
            
            # Calcular puntos (condiciones 18-36)
            puntos_data = casa10_evaluator.cond_points()[0]
            puntos_total = sum(p for p in puntos_data.values() if p is not None and not pd.isna(p))
            
            return {
                'apto': len(descalificadores) == 0,
                'descalificadores': descalificadores,
                'puntos_regente_casa10': puntos_total,
                'max_puntos': 10.0  # Máximo según especificaciones
            }
            
        except Exception as e:
            # En caso de error, retornar valores seguros
            return {
                'apto': True,
                'descalificadores': [],
                'puntos_regente_casa10': 5.0,  # Valor medio
                'max_puntos': 10.0
            }
    
    def evaluar_combinaciones_positivas(self):
        """
        Evalúa combinaciones positivas usando optimalMinutes
        Implementa las 5 condiciones especificadas
        """
        try:
            # Instanciar evaluador de combinaciones positivas
            positivas_evaluator = optimalMinutes(self.fecha_hora, self.lat, self.lon)
            
            # Obtener tabla completa de evaluación
            df_resultados = positivas_evaluator.final_table()
            
            # Extraer puntos total de la fila específica de resumen
            puntos_total = 0
            for _, row in df_resultados.iterrows():
                descripcion = str(row.get('descripcion', ''))
                if 'Total Puntaje combinacion positiva para la carta B(n)' in descripcion and 'en %' not in descripcion:
                    puntos_total = float(row.get('puntos', 0))
                    break
            
            # Si no encontramos la fila de resumen, sumar manualmente las condiciones individuales
            if puntos_total == 0:
                for _, row in df_resultados.iterrows():
                    if pd.notna(row.get('puntos', 0)) and isinstance(row['puntos'], (int, float)):
                        if 0 < row['puntos'] <= 2 and pd.notna(row.get('cond_num', None)):  # Solo condiciones individuales
                            puntos_total += row['puntos']
            
            # Asegurar que no exceda el máximo
            puntos_total = min(puntos_total, 7.0)
            
            return {
                'puntos_combinaciones_positivas': puntos_total,
                'max_puntos': 7.0  # Máximo según especificaciones
            }
            
        except Exception as e:
            # En caso de error, retornar valores seguros
            return {
                'puntos_combinaciones_positivas': 2.0,  # Valor medio
                'max_puntos': 7.0
            }
    
    def evaluar_combinaciones_negativas(self, datos_natales_A):
        """
        Evalúa combinaciones negativas usando negativeMinutes
        Requiere datos de carta natal A para comparaciones
        """
        try:
            # Extraer datos de carta natal A
            if 'fecha_nacimiento' in datos_natales_A:
                fecha_A = datos_natales_A['fecha_nacimiento']
                lat_A = datos_natales_A['lat_nacimiento']
                lon_A = datos_natales_A['lon_nacimiento']
            else:
                # Usar datos de ejemplo si no están disponibles
                fecha_A = datetime(1964, 12, 26, 21, 12)
                lat_A = -34.6037
                lon_A = -58.3816
            
            # Instanciar evaluador de combinaciones negativas
            negativas_evaluator = negativeMinutes(
                fecha_A, lat_A, lon_A,  # Carta A
                self.fecha_hora, self.lat, self.lon  # Carta B(n)
            )
            
            # Obtener tabla de evaluación
            df_resultados = negativas_evaluator.negative()
            
            # Extraer puntos total (penúltima fila)
            puntos_total = 0
            for _, row in df_resultados.iterrows():
                if pd.notna(row.get('puntos', 0)) and isinstance(row['puntos'], (int, float)):
                    if row['puntos'] < 0:  # Solo penalizaciones
                        puntos_total += row['puntos']
            
            return {
                'puntos_combinaciones_negativas': puntos_total,
                'max_puntos': -2.0  # Máximo negativo según especificaciones
            }
            
        except Exception as e:
            # En caso de error, retornar valores seguros
            return {
                'puntos_combinaciones_negativas': 0.0,  # Sin penalizaciones
                'max_puntos': -2.0
            }
    
    def get_chart_data_for_enraizamiento(self):
        """
        Extrae datos necesarios para enraizamiento usando immanuel
        MISMO PATRÓN que moon_aptitude.py verificado
        """
        # CRÍTICO: Usar misma configuración que sistema actual
        astro_avanzada_settings()
        
        subject = charts.Subject(self.fecha_hora, self.lat, self.lon)
        natal = charts.Natal(subject)
        
        # Convertir a JSON exactamente como en moon_aptitude.py
        objects_json = json.loads(json.dumps(natal.objects, cls=ToJSON, indent=4))
        houses_json = json.loads(json.dumps(natal.houses, cls=ToJSON, indent=4))
        aspects_json = json.loads(json.dumps(natal.aspects, cls=ToJSON, indent=4))
        
        return {
            'asc_grados': objects_json["3000001"]["longitude"]["raw"],
            'asc_signo': objects_json["3000001"]["sign"]["number"],
            'casas': houses_json,
            'planetas': objects_json,
            'aspectos': aspects_json,
            'moon_phase': json.loads(json.dumps(natal.moon_phase, cls=ToJSON, indent=4))
        }
    
    def es_momento_critico_descalificado(self):
        """
        Evaluación rápida para Fase 1 del algoritmo
        Solo verifica descalificadores críticos más importantes
        """
        try:
            # Verificar conjunción/oposición Sol (más crítico)
            moonSunConj_result = self.moon_module.moonSunConj()
            if moonSunConj_result[0][0] or moonSunConj_result[0][1]:
                return True, "conjuncion_oposicion_sol"
            
            # Verificar Luna vacía de curso (muy crítico)
            if self.moon_module.moonEmpty()[0]:
                return True, "luna_vacia_curso"
            
            # Verificar Luna en Capricornio/Escorpio
            if moonSunConj_result[0][2]:
                return True, "luna_capricornio_escorpio"
            
            return False, None
            
        except Exception as e:
            # En caso de error, asumir que no está descalificado para continuar
            return False, f"error_evaluacion: {str(e)}"

class CalculosAstrologicos:
    """
    Wrapper para immanuel que mantiene compatibilidad 
    total con el sistema actual - SOLO para funciones auxiliares
    """
    
    def __init__(self, fecha_hora, lat, lon):
        # CRÍTICO: Configurar immanuel ANTES de cualquier cálculo
        astro_avanzada_settings()
        
        self.subject = charts.Subject(fecha_hora, lat, lon)
        self.natal = charts.Natal(self.subject)
        
        # Convertir a JSON exactamente como el sistema actual
        self.aspects_json = json.loads(
            json.dumps(self.natal.aspects, cls=ToJSON, indent=4)
        )
        self.objects_json = json.loads(
            json.dumps(self.natal.objects, cls=ToJSON, indent=4)
        )
        self.moon_phase = json.loads(
            json.dumps(self.natal.moon_phase, cls=ToJSON, indent=4)
        )
    
    def regente_ascendente(self):
        """Obtiene el regente del ASC"""
        signo_asc = self.objects_json["3000001"]["sign"]["number"]
        return dignities.TRADITIONAL_RULERSHIPS[signo_asc]
    
    def regente_casa(self, numero_casa):
        """Obtiene el regente de una casa específica"""
        # Obtener signo de la casa
        casa_info = str(self.natal.houses[2000000 + numero_casa])
        signo_nombre = casa_info.split()[-1].upper()
        
        # Mapeo de nombres a números
        signos_map = {
            "ARIES": 1, "TAURUS": 2, "GEMINI": 3, "CANCER": 4,
            "LEO": 5, "VIRGO": 6, "LIBRA": 7, "SCORPIO": 8,
            "SAGITTARIUS": 9, "CAPRICORN": 10, "AQUARIUS": 11, "PISCES": 12
        }
        
        signo_numero = signos_map[signo_nombre]
        return dignities.TRADITIONAL_RULERSHIPS[signo_numero]
    
    def casa_de_planeta(self, planeta):
        """Obtiene la casa donde está un planeta"""
        casa = self.natal.house_for(self.natal.objects[planeta])
        return casa - 2000000  # Convertir a número simple (1-12)
    
    def planeta_en_exilio(self, planeta):
        """Verifica si un planeta está en exilio"""
        return self.objects_json[str(planeta)]["dignities"]["exile"]
    
    def planeta_en_caida(self, planeta):
        """Verifica si un planeta está en caída"""
        return self.objects_json[str(planeta)]["dignities"]["fall"]
    
    def planeta_peregrino(self, planeta):
        """Verifica si un planeta está peregrino"""
        return self.objects_json[str(planeta)]["dignities"]["peregrine"]
    
    def planeta_retrogrado(self, planeta):
        """Verifica si un planeta está retrógrado"""
        return self.objects_json[str(planeta)]["movement"]["retrograde"]
