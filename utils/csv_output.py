"""
Generador de CSV y Excel optimizado para resultados de carta electiva
Compatible con Excel y otros programas de hojas de cálculo
"""

import csv
import os
import logging
import json
from datetime import datetime
from typing import List, Dict
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import get_categoria_puntuacion
from config.settings import ORBE_CONJUNCION

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

class GeneradorCSV:
    """
    Genera archivos CSV con los resultados de la búsqueda optimizada
    """

    def __init__(self, output_dir: str = None):
        """
        Inicializa el generador de CSV

        Args:
            output_dir: Directorio donde guardar los archivos CSV
        """
        if output_dir is None:
            self.output_dir = os.path.join(os.path.dirname(__file__), '..', 'output_files')
        else:
            self.output_dir = output_dir

        # Asegurar que el directorio existe
        os.makedirs(self.output_dir, exist_ok=True)

        # Lista para almacenar momentos descartados por maléficos
        self.momentos_descartados_maleficos = []

        # Configurar logger
        self.logger = logging.getLogger(self.__class__.__name__)

    def generar_csv_resultados(self, momentos: List[Dict], tema_consulta: str,
                              parametros_busqueda: Dict = None) -> str:
        """
        Genera un archivo CSV con los resultados de la búsqueda

        Args:
            momentos: Lista de momentos encontrados
            tema_consulta: Tema de la consulta
            parametros_busqueda: Parámetros usados en la búsqueda

        Returns:
            Ruta del archivo CSV generado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"carta_electiva_{tema_consulta}_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            # Escribir parámetros de búsqueda
            if parametros_busqueda:
                csvfile.write("# PARÁMETROS DE BÚSQUEDA\n")
                for key, value in parametros_busqueda.items():
                    csvfile.write(f"# {key}: {value}\n")
                csvfile.write("\n")

            # Definir columnas del CSV
            columnas = [
                'ranking',
                'fecha_hora',
                'tema_consulta',
                'puntuacion_total',
                'categoria',
                'enraizamiento_puntos',
                'luna_apta',
                'luna_puntos',
                'descalificadores_count',
                'puntuadores_count',
                'descalificadores_detalle',
                'puntuadores_detalle',
                'observaciones'
            ]

            writer = csv.DictWriter(csvfile, fieldnames=columnas)
            writer.writeheader()

            # Escribir datos de cada momento
            for i, momento in enumerate(momentos, 1):
                categoria = get_categoria_puntuacion(momento['puntuacion_total'])

                # Extraer datos de Luna desde detalles si está disponible
                detalles = momento.get('detalles', {})
                luna_data = detalles.get('luna', {})

                # Preparar detalles de descalificadores y puntuadores
                descalificadores = luna_data.get('descalificadores', momento.get('descalificadores', []))
                puntuadores = luna_data.get('puntuadores', momento.get('puntuadores', []))

                descalificadores_detalle = '; '.join(descalificadores)
                puntuadores_detalle = '; '.join([
                    f"{p[0]}({p[1]})" if isinstance(p, (list, tuple)) else str(p)
                    for p in puntuadores
                ])

                # Generar observaciones
                observaciones = self._generar_observaciones(momento)

                # Obtener valores con fallbacks
                luna_apta = luna_data.get('apta', momento.get('luna_apta', True))
                luna_puntos = luna_data.get('puntos', momento.get('luna_puntos', 0))
                enraizamiento_puntos = momento.get('enraizamiento_pct', momento.get('enraizamiento_puntos', 0))

                row = {
                    'ranking': i,
                    'fecha_hora': momento['fecha_hora'].strftime('%Y-%m-%d %H:%M'),
                    'tema_consulta': momento['tema_consulta'],
                    'puntuacion_total': round(momento['puntuacion_total'], 2),
                    'categoria': categoria,
                    'enraizamiento_puntos': round(enraizamiento_puntos, 2),
                    'luna_apta': 'SÍ' if luna_apta else 'NO',
                    'luna_puntos': luna_puntos,
                    'descalificadores_count': len(descalificadores),
                    'puntuadores_count': len(puntuadores),
                    'descalificadores_detalle': descalificadores_detalle,
                    'puntuadores_detalle': puntuadores_detalle,
                    'observaciones': observaciones
                }

                writer.writerow(row)

        return filepath

    def _generar_observaciones(self, momento: Dict) -> str:
        """
        Genera observaciones explicativas para un momento
        Ahora compatible con SCC (Score Contextual del Enraizamiento)
        """
        observaciones = []

        # Observaciones basadas en Categoría SCC
        scc_categoria = momento.get('scc_categoria', 'NO CALCULADO')
        scc_valor = momento.get('scc', 0)

        if scc_categoria == '🌟 EXCEPCIONAL':
            observaciones.append(f"Momento EXCEPCIONAL (SCC: {scc_valor:.1f}%) - Primera opción recomendada")
        elif scc_categoria == '✅ SOBRE PROMEDIO':
            observaciones.append(f"Momento SOBRE el promedio (SCC: {scc_valor:.1f}%) - Muy recomendable")
        elif scc_categoria == '⚪ PROMEDIO':
            observaciones.append(f"Momento PROMEDIO (SCC: {scc_valor:.1f}%) - Aceptable")
        elif scc_categoria == '⚠️ DEBAJO PROMEDIO':
            observaciones.append(f"Momento DEBAJO del promedio (SCC: {scc_valor:.1f}%) - Única opción si no hay mejores")
        elif scc_categoria == '❌ LIMITADO':
            observaciones.append(f"Momento LIMITADO (SCC: {scc_valor:.1f}%) - Evitar si posible")
        elif scc_categoria == 'NO RECOMENDABLE':
            observaciones.append(f"Momento NO RECOMENDABLE (SCC: {scc_valor:.1f}%) - No usar")
        else:
            observaciones.append(f"Momento evaluado (SCC: {scc_valor:.1f}%)")

        # Observaciones sobre Luna (extraer de detalles si está disponible)
        detalles = momento.get('detalles', {})
        luna_data = detalles.get('luna', {})
        luna_apta = luna_data.get('apta', momento.get('luna_apta', True))  # Fallback

        if luna_apta:
            observaciones.append("Luna en condiciones favorables")
        else:
            desc_count = len(luna_data.get('descalificadores', momento.get('descalificadores', [])))
            if desc_count > 0:
                observaciones.append(f"Luna con {desc_count} condición(es) desfavorable(s)")

        # Observaciones sobre enraizamiento absoluto - Usar la misma lógica que en el resto del código
        detalles = momento.get('detalles', {})
        enraizamiento_puro_valor = 0

        # Intentar obtener de detalles.enraizamiento_puro.puntos_total (misma lógica que en generar_csv_excel_compatible)
        if detalles and 'enraizamiento_puro' in detalles:
            enraizamiento_puro_data = detalles['enraizamiento_puro']
            if isinstance(enraizamiento_puro_data, dict) and 'puntos_total' in enraizamiento_puro_data:
                enraizamiento_puro_valor = enraizamiento_puro_data['puntos_total']

        # Fallback: usar el valor de la columna "Enraizamiento Puro" si está disponible
        if enraizamiento_puro_valor == 0 and 'enraizamiento_puro' in momento:
            enraizamiento_puro_valor = momento['enraizamiento_puro']

        # Generar observaciones basadas en puntos reales
        if enraizamiento_puro_valor >= 3:
            observaciones.append(f"Enraizamiento excepcional ({enraizamiento_puro_valor} pts)")
        elif enraizamiento_puro_valor >= 2:
            observaciones.append(f"Buen enraizamiento ({enraizamiento_puro_valor} pts)")
        elif enraizamiento_puro_valor >= 1:
            observaciones.append(f"Enraizamiento moderado ({enraizamiento_puro_valor} pts)")
        elif enraizamiento_puro_valor >= 0:
            observaciones.append(f"Enraizamiento limitado ({enraizamiento_puro_valor} pts)")
        else:
            observaciones.append(f"Enraizamiento negativo ({enraizamiento_puro_valor} pts)")

        # Observaciones sobre calidad del momento
        calidad = momento.get('calidad_pct', momento.get('calidad_score', 0) * 100)
        if calidad >= 70:
            observaciones.append("Excelente calidad del momento")
        elif calidad >= 50:
            observaciones.append("Buena calidad del momento")
        else:
            observaciones.append("Calidad moderada del momento")

        return '; '.join(observaciones)

    def generar_resumen_estadisticas(self, momentos: List[Dict],
                                   estadisticas_busqueda: Dict) -> str:
        """
        Genera un archivo CSV con estadísticas de la búsqueda
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"estadisticas_busqueda_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Estadísticas generales
            writer.writerow(['ESTADÍSTICAS DE BÚSQUEDA'])
            writer.writerow(['Métrica', 'Valor'])
            writer.writerow(['Total momentos encontrados', len(momentos)])
            writer.writerow(['Cálculos Fase 1', estadisticas_busqueda.get('calculos_fase_1', 0)])
            writer.writerow(['Cálculos Fase 2', estadisticas_busqueda.get('calculos_fase_2', 0)])
            writer.writerow(['Cálculos Fase 3', estadisticas_busqueda.get('calculos_fase_3', 0)])
            writer.writerow(['Total cálculos', estadisticas_busqueda.get('total_calculos', 0)])
            writer.writerow(['Factor de mejora', f"{estadisticas_busqueda.get('mejora_factor', 0):.1f}x"])
            writer.writerow([])

            # Distribución por categorías
            writer.writerow(['DISTRIBUCIÓN POR CATEGORÍAS'])
            categorias_count = {}
            for momento in momentos:
                categoria = get_categoria_puntuacion(momento['puntuacion_total'])
                categorias_count[categoria] = categorias_count.get(categoria, 0) + 1

            writer.writerow(['Categoría', 'Cantidad'])
            for categoria, count in categorias_count.items():
                writer.writerow([categoria, count])

        return filepath

    def generar_csv_excel_compatible(self, momentos: List[Dict], tema_consulta: str,
                                   parametros_busqueda: Dict = None) -> str:
        """
        Genera un archivo CSV limpio y compatible con Excel (sin comentarios)
        Incluye filtro final de descartes críticos por maléficos

        Args:
            momentos: Lista de momentos encontrados
            tema_consulta: Tema de la consulta
            parametros_busqueda: Parámetros usados en la búsqueda

        Returns:
            Ruta del archivo CSV generado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"carta_electiva_{tema_consulta}_excel_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)

        # 🎯 FILTRAR MOMENTOS CRÍTICOS ANTES DE GENERAR CSV
        momentos_filtrados = self._filtrar_momentos_criticos(momentos)

        # Log de estadísticas de filtrado
        descartes = len(momentos) - len(momentos_filtrados)
        if descartes > 0:
            self.logger.info(f"🗑️  {descartes} momentos descartados por maléficos críticos")
            self.logger.info(f"✅ {len(momentos_filtrados)} momentos finales en ranking")

        # Definir columnas del CSV - Optimizado: eliminadas columnas vacías, convertidas a %
        columnas = [
            'Ranking',
            'Fecha y Hora',
            'Tema Consulta',
            'Puntuación Total',
            'Enraizamiento Puro',
            'SCC',
            'Categoría SCC',
            'Luna (%)',
            'ASC (%)',
            'Casa10 (%)',
            'Positivas (%)',
            'Negativas (%)',
            'Observaciones'
        ]

        # Usar UTF-8 con BOM para mejor compatibilidad con Excel
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            # Escribir headers
            writer.writerow(columnas)

            # Escribir datos de cada momento FILTRADO
            for i, momento in enumerate(momentos_filtrados, 1):
                categoria = get_categoria_puntuacion(momento['puntuacion_total'])

                # Extraer datos de Luna desde detalles si está disponible
                detalles = momento.get('detalles', {})
                luna_data = detalles.get('luna', {})

                # Preparar detalles de descalificadores y puntuadores
                descalificadores = luna_data.get('descalificadores', momento.get('descalificadores', []))
                puntuadores = luna_data.get('puntuadores', momento.get('puntuadores', []))

                descalificadores_detalle = '; '.join(descalificadores)
                puntuadores_detalle = '; '.join([
                    f"{p[0]} ({p[1]} pts)" if isinstance(p, (list, tuple)) else str(p)
                    for p in puntuadores
                ])

                # Generar observaciones
                observaciones = self._generar_observaciones(momento)

                # Obtener valores con fallbacks
                luna_apta = luna_data.get('apta', momento.get('luna_apta', True))
                luna_puntos = luna_data.get('puntos', momento.get('luna_puntos', 0))
                enraizamiento_puntos = momento.get('enraizamiento_pct', momento.get('enraizamiento_puntos', 0))

                # Obtener SCC y Categoría SCC
                scc_valor = momento.get('scc', 0)
                scc_categoria = momento.get('scc_categoria', 'NO CALCULADO')

                # Obtener Enraizamiento Puro (valor absoluto de las 23 condiciones)
                enraizamiento_puro_encontrado = False
                enraizamiento_puro_valor = 0
                if detalles and 'enraizamiento_puro' in detalles:
                    enraizamiento_puro_data = detalles['enraizamiento_puro']
                    if isinstance(enraizamiento_puro_data, dict) and 'puntos_total' in enraizamiento_puro_data:
                        enraizamiento_puro_valor = enraizamiento_puro_data['puntos_total']
                        enraizamiento_puro_encontrado = True
                # Fallback solo si no se encontró el valor absoluto (no si es es 0)
                if not enraizamiento_puro_encontrado:
                    enraizamiento_puro_valor = momento.get('enraizamiento_score', 0.0) * 100

                # Obtener desglose de Puntaje Ranking y convertir a porcentajes
                fase1_detalles = detalles.get('fase1', {})
                ranking_detalles = fase1_detalles.get('detalles', {})
                puntos_luna = ranking_detalles.get('luna', {}).get('puntos_luna', 0)
                puntos_asc = ranking_detalles.get('regente_asc', {}).get('puntos_regente_asc', 0)
                puntos_casa10 = ranking_detalles.get('regente_casa10', {}).get('puntos_regente_casa10', 0)
                puntos_positivas = ranking_detalles.get('combinaciones_positivas', {}).get('puntos_combinaciones_positivas', 0)
                puntos_negativas = ranking_detalles.get('combinaciones_negativas', {}).get('puntos_combinaciones_negativas', 0)

                # Convertir puntos a porcentajes según valores máximos
                luna_pct = round((puntos_luna / 10.0) * 100, 1)        # 10 pts = 100%
                asc_pct = round((puntos_asc / 10.0) * 100, 1)          # 10 pts = 100%
                casa10_pct = round((puntos_casa10 / 6.0) * 100, 1)     # 6 pts = 100%
                positivas_pct = round((puntos_positivas / 6.0) * 100, 1) # 6 pts = 100%

                # Lógica especial para negativas: -2 pts = -100%, 0 pts = 0%
                if puntos_negativas >= 0:
                    negativas_pct = 0.0
                else:
                    negativas_pct = round((puntos_negativas / -2.0) * -100, 1)

                row = [
                    i,  # Ranking
                    momento['fecha_hora'].strftime('%Y-%m-%d %H:%M'),  # Fecha y Hora
                    momento['tema_consulta'],  # Tema Consulta
                    round(momento['puntuacion_total'], 1),  # Puntuación Total
                    round(enraizamiento_puro_valor, 1),  # Enraizamiento Puro
                    round(scc_valor, 1),  # SCC
                    scc_categoria,  # Categoría SCC
                    luna_pct,      # Luna (%)
                    asc_pct,       # ASC (%)
                    casa10_pct,    # Casa10 (%)
                    positivas_pct, # Positivas (%)
                    negativas_pct, # Negativas (%)
                    observaciones  # Observaciones
                ]

                writer.writerow(row)

        # Generar archivo de parámetros separado
        if parametros_busqueda:
            self._generar_archivo_parametros(parametros_busqueda, tema_consulta, timestamp)

        # Generar archivo de momentos descartados si hay alguno
        if self.momentos_descartados_maleficos:
            self._generar_archivo_descartes_maleficos(tema_consulta, timestamp)

        return filepath

    def _generar_archivo_parametros(self, parametros_busqueda: Dict, tema_consulta: str, timestamp: str):
        """
        Genera un archivo separado con los parámetros de búsqueda
        """
        filename = f"parametros_{tema_consulta}_{timestamp}.txt"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("PARÁMETROS DE BÚSQUEDA\n")
            f.write("=" * 50 + "\n\n")

            for key, value in parametros_busqueda.items():
                f.write(f"{key}: {value}\n")

    def _generar_archivo_descartes_maleficos(self, tema_consulta: str, timestamp: str):
        """
        Genera un archivo CSV con los momentos descartados por maléficos
        """
        if not self.momentos_descartados_maleficos:
            return None

        filename = f"momentos_descartados_maleficos_{tema_consulta}_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)

        # Usar UTF-8 con BOM para mejor compatibilidad con Excel
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            # Headers
            headers = [
                'Fecha y Hora',
                'Tema Consulta',
                'Razón Descarte',
                'Maléfico',
                'Ángulo',
                'Grados Maléfico',
                'Grados Ángulo',
                'Orbe',
                'Puntuación Total'
            ]
            writer.writerow(headers)

            # Escribir datos de cada momento descartado
            for momento in self.momentos_descartados_maleficos:
                row = [
                    momento['fecha_hora'].strftime('%Y-%m-%d %H:%M'),
                    momento['tema_consulta'],
                    momento['razon_descarte'],
                    momento['malefico'],
                    momento['angulo'],
                    momento['grados_malefico'],
                    momento['grados_angulo'],
                    momento['orbe'],
                    round(momento['puntuacion_total'], 1)
                ]
                writer.writerow(row)

        self.logger.info(f"📄 Archivo de descartes generado: {filepath}")
        return filepath

    def generar_excel_nativo(self, momentos: List[Dict], tema_consulta: str,
                           parametros_busqueda: Dict = None,
                           estadisticas_busqueda: Dict = None) -> str:
        """
        Genera un archivo Excel nativo (.xlsx) con múltiples hojas

        Args:
            momentos: Lista de momentos encontrados
            tema_consulta: Tema de la consulta
            parametros_busqueda: Parámetros usados en la búsqueda
            estadisticas_busqueda: Estadísticas de la búsqueda

        Returns:
            Ruta del archivo Excel generado o None si pandas no está disponible
        """
        if not PANDAS_AVAILABLE:
            print("⚠️  Pandas no disponible. No se puede generar archivo Excel nativo.")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"carta_electiva_{tema_consulta}_{timestamp}.xlsx"
        filepath = os.path.join(self.output_dir, filename)

        # Preparar datos para DataFrame
        datos_momentos = []
        for i, momento in enumerate(momentos, 1):
            categoria = get_categoria_puntuacion(momento['puntuacion_total'])

            descalificadores_detalle = '; '.join(momento.get('descalificadores', []))
            puntuadores_detalle = '; '.join([
                f"{p[0]} ({p[1]} pts)" for p in momento.get('puntuadores', [])
            ])

            observaciones = self._generar_observaciones(momento)

            # Extraer datos de Luna desde detalles si está disponible
            detalles = momento.get('detalles', {})
            luna_data = detalles.get('luna', {})

            # Obtener valores con fallbacks
            luna_apta = luna_data.get('apta', momento.get('luna_apta', True))
            luna_puntos = luna_data.get('puntos', momento.get('luna_puntos', 0))
            enraizamiento_puntos = momento.get('enraizamiento_pct', momento.get('enraizamiento_puntos', 0))
            descalificadores = luna_data.get('descalificadores', momento.get('descalificadores', []))
            puntuadores = luna_data.get('puntuadores', momento.get('puntuadores', []))

            # Obtener Puntaje Ranking
            puntaje_ranking = momento.get('puntaje_ranking', 0)

            # Obtener Enraizamiento Puro (%)
            enraizamiento_puro_pct = momento.get('enraizamiento_score', 0.0) * 100

            # Obtener desglose de Puntaje Ranking y convertir a porcentajes
            fase1_detalles = detalles.get('fase1', {})
            ranking_detalles = fase1_detalles.get('detalles', {})
            puntos_luna = ranking_detalles.get('luna', {}).get('puntos_luna', 0)
            puntos_asc = ranking_detalles.get('regente_asc', {}).get('puntos_regente_asc', 0)
            puntos_casa10 = ranking_detalles.get('regente_casa10', {}).get('puntos_regente_casa10', 0)
            puntos_positivas = ranking_detalles.get('combinaciones_positivas', {}).get('puntos_combinaciones_positivas', 0)
            puntos_negativas = ranking_detalles.get('combinaciones_negativas', {}).get('puntos_combinaciones_negativas', 0)

            # Convertir puntos a porcentajes según valores máximos
            luna_pct = round((puntos_luna / 10.0) * 100, 1)        # 10 pts = 100%
            asc_pct = round((puntos_asc / 10.0) * 100, 1)          # 10 pts = 100%
            casa10_pct = round((puntos_casa10 / 6.0) * 100, 1)     # 6 pts = 100%
            positivas_pct = round((puntos_positivas / 6.0) * 100, 1) # 6 pts = 100%

            # Lógica especial para negativas: -2 pts = -100%, 0 pts = 0%
            if puntos_negativas >= 0:
                negativas_pct = 0.0
            else:
                negativas_pct = round((puntos_negativas / -2.0) * -100, 1)

            # Obtener Enraizamiento Puro (valor absoluto de las 23 condiciones) para Excel también
            enraizamiento_puro_excel_encontrado = False
            enraizamiento_puro_excel = 0
            if detalles and 'enraizamiento_puro' in detalles:
                enraizamiento_puro_data_excel = detalles['enraizamiento_puro']
                if isinstance(enraizamiento_puro_data_excel, dict) and 'puntos_total' in enraizamiento_puro_data_excel:
                    enraizamiento_puro_excel = enraizamiento_puro_data_excel['puntos_total']
                    enraizamiento_puro_excel_encontrado = True
            # Fallback solo si no se encontró el valor absoluto (no si es 0)
            if not enraizamiento_puro_excel_encontrado:
                enraizamiento_puro_excel = momento.get('enraizamiento_score', 0.0) * 100

            # Obtener SCC y Categoría SCC para Excel también
            scc_valor_excel = momento.get('scc', 0)
            scc_categoria_excel = momento.get('scc_categoria', 'NO CALCULADO')

            # DataFrame optimizado - eliminadas columnas vacías, convertidas a %
            datos_momentos.append({
                'Ranking': i,
                'Fecha y Hora': momento['fecha_hora'].strftime('%Y-%m-%d %H:%M'),
                'Tema Consulta': momento['tema_consulta'],
                'Puntuación Total': round(momento['puntuacion_total'], 1),
                'Enraizamiento Puro': round(enraizamiento_puro_excel, 1),
                'SCC': round(scc_valor_excel, 1),
                'Categoría SCC': scc_categoria_excel,
                'Luna (%)': luna_pct,
                'ASC (%)': asc_pct,
                'Casa10 (%)': casa10_pct,
                'Positivas (%)': positivas_pct,
                'Negativas (%)': negativas_pct,
                'Observaciones': observaciones
            })

        # Crear archivo Excel con múltiples hojas
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Hoja 1: Resultados
            df_resultados = pd.DataFrame(datos_momentos)
            df_resultados.to_excel(writer, sheet_name='Resultados', index=False)

            # Hoja 2: Parámetros
            if parametros_busqueda:
                df_parametros = pd.DataFrame([
                    {'Parámetro': k, 'Valor': v} for k, v in parametros_busqueda.items()
                ])
                df_parametros.to_excel(writer, sheet_name='Parámetros', index=False)

            # Hoja 3: Estadísticas
            if estadisticas_busqueda:
                datos_estadisticas = [
                    {'Métrica': 'Total momentos encontrados', 'Valor': len(momentos)},
                    {'Métrica': 'Cálculos Fase 1', 'Valor': estadisticas_busqueda.get('calculos_fase_1', 0)},
                    {'Métrica': 'Cálculos Fase 2', 'Valor': estadisticas_busqueda.get('calculos_fase_2', 0)},
                    {'Métrica': 'Cálculos Fase 3', 'Valor': estadisticas_busqueda.get('calculos_fase_3', 0)},
                    {'Métrica': 'Total cálculos', 'Valor': estadisticas_busqueda.get('total_calculos', 0)},
                    {'Métrica': 'Factor de mejora', 'Valor': f"{estadisticas_busqueda.get('mejora_factor', 0):.1f}x"}
                ]

                # Distribución por categorías
                categorias_count = {}
                for momento in momentos:
                    categoria = get_categoria_puntuacion(momento['puntuacion_total'])
                    categorias_count[categoria] = categorias_count.get(categoria, 0) + 1

                for categoria, count in categorias_count.items():
                    datos_estadisticas.append({'Métrica': f'Categoría {categoria}', 'Valor': count})

                df_estadisticas = pd.DataFrame(datos_estadisticas)
                df_estadisticas.to_excel(writer, sheet_name='Estadísticas', index=False)

        return filepath

    def _filtrar_momentos_criticos(self, momentos: List[Dict]) -> List[Dict]:
        """
        Aplica filtro final de descartes críticos por maléficos
        Verifica conjunciones entre ASC/maléficos y maléficos/ángulos
        """
        momentos_filtrados = []

        for momento in momentos:
            es_apto, razon_descarte = self._verificar_maleficos_en_momento(momento)
            if es_apto:
                momentos_filtrados.append(momento)
            else:
                # Capturar momento descartado con detalles
                momento_descartado = {
                    'fecha_hora': momento['fecha_hora'],
                    'tema_consulta': momento.get('tema_consulta', 'N/A'),
                    'razon_descarte': razon_descarte.get('tipo', 'DESCONOCIDO'),
                    'malefico': razon_descarte.get('malefico', 'N/A'),
                    'angulo': razon_descarte.get('angulo', 'N/A'),
                    'grados_malefico': razon_descarte.get('grados_malefico', 0.0),
                    'grados_angulo': razon_descarte.get('grados_angulo', 0.0),
                    'orbe': razon_descarte.get('orbe', 0.0),
                    'puntuacion_total': momento.get('puntuacion_total', 0.0)
                }
                self.momentos_descartados_maleficos.append(momento_descartado)
                self.logger.debug(f"🗑️ Momento {momento['fecha_hora']} descartado: {razon_descarte.get('tipo', 'DESCONOCIDO')}")

        # Reordenar rankings después del filtrado
        for i, momento in enumerate(momentos_filtrados, 1):
            momento['ranking'] = i

        return momentos_filtrados

    def _verificar_maleficos_en_momento(self, momento: Dict) -> tuple:
        """
        Verifica si un momento debe ser descartado por conjunciones con maléficos
        Returns: (es_apto: bool, razon_descarte: dict)
        - es_apto: True si el momento DEBE mantenerse, False si debe descartarse
        - razon_descarte: dict con detalles del descarte si aplica
        """
        try:
            # Obtener coordenadas del momento
            lat = momento.get('lat', -34.6037)  # Default Buenos Aires
            lon = momento.get('lon', -58.3816)

            # Recalcular carta del momento para verificación
            carta_B = self._recalcular_carta_momento(momento['fecha_hora'], lat, lon)

            if not carta_B:
                self.logger.warning(f"No se pudo recalcular carta para {momento['fecha_hora']}")
                return True, {}  # Mantener en caso de error

            # Verificar conjunciones críticas
            tiene_conjunciones, detalles_conjuncion = self._tiene_conjunciones_maleficas(carta_B)

            if tiene_conjunciones:
                return False, detalles_conjuncion  # Descartar con detalles
            else:
                return True, {}  # Mantener

        except Exception as e:
            self.logger.warning(f"Error verificando maléficos en {momento['fecha_hora']}: {e}")
            return True, {}  # Mantener en caso de error

    def _recalcular_carta_momento(self, momento: datetime, lat: float, lon: float) -> Dict:
        """
        Recalcula la carta del momento para verificación de maléficos
        """
        try:
            from immanuel import charts
            from immanuel.classes.serialize import ToJSON
            from legacy_astro.settings_astro import astro_avanzada_settings

            # Configurar immanuel
            astro_avanzada_settings()

            subject = charts.Subject(momento, lat, lon)
            natal = charts.Natal(subject)

            return {
                'planetas': json.loads(json.dumps(natal.objects, cls=ToJSON, indent=4)),
                'casas': json.loads(json.dumps(natal.houses, cls=ToJSON, indent=4)),
                '_houses': natal._houses
            }
        except Exception as e:
            self.logger.error(f"Error recalculando carta del momento: {e}")
            return {}

    def _tiene_conjunciones_maleficas(self, carta_B: Dict) -> tuple:
        """
        Verifica si hay conjunciones problemáticas entre maléficos y ángulos
        Returns: (tiene_conjunciones: bool, detalles: dict)
        - tiene_conjunciones: True si HAY conjunciones problemáticas (debe descartarse)
        - detalles: información detallada de la conjunción encontrada
        """
        # Obtener posiciones de maléficos
        marte_grados = carta_B.get('planetas', {}).get('4000005', {}).get('longitude', {}).get('raw', 0)
        saturno_grados = carta_B.get('planetas', {}).get('4000007', {}).get('longitude', {}).get('raw', 0)

        # Obtener posiciones de ángulos
        mc_grados = self._get_angulo_carta(carta_B, 'MC')
        ic_grados = self._get_angulo_carta(carta_B, 'IC')
        dsc_grados = self._get_angulo_carta(carta_B, 'DSC')

        angulos = {
            'MC': mc_grados,
            'IC': ic_grados,
            'DSC': dsc_grados
        }

        # Verificar conjunciones
        for malefico_nombre, malefico_grados in [('Marte', marte_grados), ('Saturno', saturno_grados)]:
            for angulo_nombre, angulo_grados in angulos.items():
                if abs(malefico_grados - angulo_grados) <= ORBE_CONJUNCION:
                    # Encontrada conjunción problemática - devolver detalles
                    detalles = {
                        'tipo': f'{malefico_nombre} conjunct {angulo_nombre}',
                        'malefico': malefico_nombre,
                        'angulo': angulo_nombre,
                        'grados_malefico': round(malefico_grados, 1),
                        'grados_angulo': round(angulo_grados, 1),
                        'orbe': round(abs(malefico_grados - angulo_grados), 1)
                    }
                    return True, detalles  # Encontrada conjunción problemática

        return False, {}  # No hay conjunciones problemáticas

    def _get_angulo_carta(self, carta: Dict, angulo: str) -> float:
        """
        Obtiene la posición de un ángulo específico en la carta
        """
        try:
            if angulo == 'MC':
                # MC es la cúspide de la Casa 10
                return self._get_cuspide_casa(carta, 10)
            elif angulo == 'IC':
                # IC es la cúspide de la Casa 4
                return self._get_cuspide_casa(carta, 4)
            elif angulo == 'DSC':
                # DSC es la cúspide de la Casa 7
                return self._get_cuspide_casa(carta, 7)
            else:
                return 0.0
        except Exception as e:
            logger.debug(f"Error obteniendo ángulo {angulo}: {e}")
            return 0.0

    def _get_cuspide_casa(self, carta: Dict, numero_casa: int) -> float:
        """
        Obtiene la cúspide de una casa específica
        """
        try:
            if '_houses' not in carta:
                return 0.0

            # Intentar con formato immanuel
            try:
                from immanuel.const import chart
                house_key = getattr(chart, f'HOUSE{numero_casa}')
                house_info = carta['_houses'][house_key]
                return getattr(house_info, 'lon', 0.0)
            except:
                # Fallback: buscar en casas
                casa_id = str(2000000 + numero_casa)
                if casa_id in carta.get('casas', {}):
                    return carta['casas'][casa_id].get('longitude', {}).get('raw', 0.0)

            return 0.0

        except Exception as e:
            logger.debug(f"Error obteniendo cúspide casa {numero_casa}: {e}")
            return 0.0


def crear_parametros_busqueda(fecha_inicio: datetime, fecha_fin: datetime,
                            tema_consulta: str, lat: float, lon: float,
                            tiempo_ejecucion: float = None, total_calculos: int = None,
                            mejora_factor: float = None) -> Dict:
    """
    Crea diccionario con parámetros de búsqueda para incluir en archivos
    """
    parametros = {
        'Fecha inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'Fecha fin': fecha_fin.strftime('%Y-%m-%d'),
        'Tema consulta': tema_consulta,
        'Latitud': lat,
        'Longitud': lon,
        'Generado': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    if tiempo_ejecucion is not None:
        parametros['Tiempo ejecución'] = f"{tiempo_ejecucion:.2f} segundos"

    if total_calculos is not None:
        parametros['Total cálculos'] = total_calculos

    if mejora_factor is not None:
        parametros['Factor mejora'] = f"{mejora_factor:.1f}x"

    return parametros
