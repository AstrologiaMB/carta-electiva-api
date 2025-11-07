#!/usr/bin/env python3
"""
Script de prueba del sistema de ranking con datos reales
=======================================================

Aplica el sistema de ranking A-E a los 20 momentos reales del archivo CSV
y genera un reporte completo.
"""

import pandas as pd
import sys
import os

# Agregar el directorio padre al path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ranking_system import RankingSystem

def main():
    """Función principal para probar el ranking con datos reales"""

    print("🔬 TEST SISTEMA DE RANKING - DATOS REALES")
    print("=" * 60)

    # Leer archivo CSV con datos reales
    archivo_csv = "output_files/carta_electiva_trabajo_excel_20250831_134126.csv"

    try:
        # Leer CSV y mostrar su estructura
        print(f"Leyendo archivo: {archivo_csv}")
        df_raw = pd.read_csv(archivo_csv, nrows=5)  # Leer solo primeras 5 líneas para ver estructura
        print(f"Columnas encontradas: {list(df_raw.columns)}")
        print(f"Primeras filas:")
        print(df_raw.head())

        # Leer el CSV completo
        df = pd.read_csv(archivo_csv)

        # Verificar que tenemos las columnas necesarias
        columnas_requeridas = ['Fecha y Hora', 'Tema Consulta', 'Enraizamiento (%)']
        for col in columnas_requeridas:
            if col not in df.columns:
                print(f"❌ Error: Columna '{col}' no encontrada en el CSV")
                print(f"Columnas disponibles: {list(df.columns)}")
                return

        print(f"✅ Archivo cargado exitosamente: {len(df)} momentos encontrados")

        # Aplicar sistema de ranking
        print("\n🔄 Aplicando sistema de ranking...")
        df_con_ranking = RankingSystem.procesar_dataframe(df, columna_enraizamiento='Enraizamiento (%)')

        # Mostrar resultados
        print("\n📊 RESULTADOS DEL RANKING:")
        print("-" * 60)

        # Mostrar top 5 momentos
        print("\n🏆 TOP 5 MOMENTOS RECOMENDADOS:")
        top_5 = df_con_ranking.nlargest(5, 'Enraizamiento (%)')
        for i, (_, row) in enumerate(top_5.iterrows(), 1):
            fecha_hora = str(row['Fecha y Hora'])[:16]  # Solo fecha y hora
            enraizamiento = row['Enraizamiento (%)']
            ranking = row['ranking']
            nivel = row['nivel']
            percentil = row['percentil']

            print(f"{i}. {fecha_hora} → {enraizamiento}% ({ranking}) - P{percentil}")

        # Mostrar distribución por ranking
        print("\n📈 DISTRIBUCIÓN POR RANKING:")
        distribucion = df_con_ranking['ranking'].value_counts().sort_index()
        total = len(df_con_ranking)

        for ranking, cantidad in distribucion.items():
            porcentaje = (cantidad / total) * 100
            descripcion = RankingSystem.UMBRALES_RANKING[ranking]['descripcion']
            print(f"  {ranking}: {cantidad} momentos ({porcentaje:.1f}%)")
            print(f"    └─ {descripcion}")

        # Estadísticas generales
        print("\n📊 ESTADÍSTICAS GENERALES:")
        print(f"  • Total momentos: {total}")
        print(f"  • Enraizamiento promedio: {df_con_ranking['Enraizamiento (%)'].mean():.1f}%")
        print(f"  • Enraizamiento máximo: {df_con_ranking['Enraizamiento (%)'].max():.1f}%")
        print(f"  • Enraizamiento mínimo: {df_con_ranking['Enraizamiento (%)'].min():.1f}%")
        print(f"  • Desviación estándar: {df_con_ranking['Enraizamiento (%)'].std():.1f}")
        # Mostrar momentos por ranking
        print("\n🔍 DETALLE POR RANKING:")
        for ranking in ['A_Excelente', 'B_Muy_Bueno', 'C_Bueno', 'D_Aceptable', 'E_Regular']:
            momentos_ranking = df_con_ranking[df_con_ranking['ranking'] == ranking]
            if not momentos_ranking.empty:
                print(f"\n{ranking} ({len(momentos_ranking)} momentos):")
                for _, row in momentos_ranking.iterrows():
                    fecha_hora = str(row['Fecha y Hora'])[:16]
                    enraizamiento = row['Enraizamiento (%)']
                    print(f"    • {fecha_hora}: {enraizamiento:.1f}%")
        # Generar reporte completo
        print("\n" + "="*60)
        print("📋 REPORTE COMPLETO:")
        print("="*60)

        reporte = RankingSystem.generar_reporte_ranking(df_con_ranking)
        print(reporte)

        # Guardar resultados en CSV
        archivo_salida = "output_files/ranking_aplicado_20250831_134126.csv"
        df_con_ranking.to_csv(archivo_salida, index=False)
        print(f"\n💾 Resultados guardados en: {archivo_salida}")

    except FileNotFoundError:
        print(f"❌ Error: Archivo '{archivo_csv}' no encontrado")
        print(f"   Ruta actual: {os.getcwd()}")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
