"""
Configuraciones generales del sistema de carta electiva optimizada
"""

import os
from datetime import datetime

# Configuraciones de directorios
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output_files')
CACHE_DIR = os.path.join(PROJECT_ROOT, 'cache')
LEGACY_ASTRO_DIR = os.path.join(PROJECT_ROOT, 'legacy_astro')

# Configuraciones del algoritmo de búsqueda
FASE_1_INTERVALO_HORAS = 0.5      # Cada 30 minutos (optimizado)
FASE_2_INTERVALO_MINUTOS = 10     # Cada 10 minutos (optimizado)
FASE_3_INTERVALO_MINUTOS = 3      # Cada 3 minutos (optimizado)

# Umbrales de puntuación
UMBRAL_ENRAIZAMIENTO_MINIMO = 25  # 25% mínimo para v2.0 (era 40 en v1.0)
UMBRAL_CALIDAD_MINIMO = 10
UMBRAL_PUNTUACION_TOTAL_MINIMO = 50

# Pesos del sistema de puntuación
PESO_ENRAIZAMIENTO = 0.8
PESO_CALIDAD = 0.2

# Orbes para aspectos de enraizamiento
ORBE_CONJUNCION = 8.0
ORBE_TRIGONO_SEXTIL = 6.0
ORBE_CUADRATURA_OPOSICION = 8.0

# Configuraciones de output
MAX_RESULTADOS_FINALES = 25
CATEGORIAS_PUNTUACION = {
    'EXCELENTE': (80, 100),    # 80-100% - Conexiones excepcionales
    'MUY_BUENO': (65, 79),     # 65-79% - Conexiones muy favorables
    'BUENO': (45, 64),         # 45-64% - Conexiones favorables
    'REGULAR': (35, 44),       # 35-44% - Conexiones moderadas
    'MALO': (0, 34)            # 0-34% - Conexiones desfavorables
}

# Configuraciones de cache
CACHE_ENABLED = True
CACHE_EXPIRY_HOURS = 24
MAX_CACHE_SIZE_MB = 500

# Configuraciones de performance
MAX_WORKERS = 4  # Para procesamiento paralelo
BATCH_SIZE = 100  # Tamaño de lote para procesamiento

# Configuraciones de logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def get_categoria_puntuacion(puntuacion):
    """
    Obtiene la categoría para una puntuación dada
    
    Args:
        puntuacion (float): Puntuación total
        
    Returns:
        str: Categoría de la puntuación
    """
    for categoria, (min_val, max_val) in CATEGORIAS_PUNTUACION.items():
        if min_val <= puntuacion <= max_val:
            return categoria
    return 'INDEFINIDO'

def ensure_directories():
    """
    Asegura que todos los directorios necesarios existan
    """
    directories = [OUTPUT_DIR, CACHE_DIR]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Configuraciones específicas de enraizamiento
ENRAIZAMIENTO_WEIGHTS = {
    # Conexiones ASC B(n) con Carta A
    "asc_conjuncion_asc_A": 15,      # Máxima conexión personal
    "asc_conjuncion_sol_A": 12,      # Identidad y propósito
    "asc_conjuncion_luna_A": 12,     # Emociones y instintos
    "asc_conjuncion_venus_A": 10,    # Armonía y atracción
    "asc_conjuncion_jupiter_A": 10,  # Expansión y suerte
    
    # Aspectos armónicos ASC B(n)
    "asc_trigono_planetas_A": 8,     # Por cada planeta
    "asc_sextil_planetas_A": 6,      # Por cada planeta
    
    # Conexiones Casa Tema B(n) con Carta A
    "casa_tema_conjuncion_sol_A": 10,    # Propósito en el área
    "casa_tema_conjuncion_luna_A": 8,    # Emociones en el área
    "casa_tema_conjuncion_venus_A": 8,   # Armonía en el área
    "casa_tema_conjuncion_jupiter_A": 8, # Expansión en el área
    
    # Regentes importantes
    "regente_asc_B_conjuncion_planetas_A": 6,  # Por planeta
    "regente_tema_B_conjuncion_planetas_A": 6, # Por planeta
    
    # Penalizaciones críticas
    "asc_conjuncion_saturno_A": -15,    # Restricción personal
    "asc_conjuncion_marte_A": -12,      # Conflicto personal
    "asc_en_casa_6_8_12_A": -20,        # Casas problemáticas
    "casa_tema_conjuncion_saturno_A": -10, # Restricción en área
    "casa_tema_conjuncion_marte_A": -8,    # Conflicto en área
}

# Configuraciones del sistema híbrido de enraizamiento
ENRAIZAMIENTO_HIBRIDO = {
    'peso_original': 0.4,        # 40% para las 23 condiciones originales
    'peso_comprensivo': 0.6,     # 60% para el sistema comprensivo actual
    'usar_hibrido': True,        # Activar sistema híbrido
    'max_puntos_original': 23.0, # Puntos máximos teóricos del sistema original
    'descripcion': 'Sistema híbrido que respeta el espíritu del código original'
}

# Configuraciones de calidad del momento
CALIDAD_WEIGHTS = {
    # Dignidades planetarias
    "luna_dignificada": 3,
    "regente_asc_dignificado": 4,
    "regente_tema_dignificado": 4,
    
    # Aspectos internos favorables
    "aspectos_positivos_internos": 5,
    
    # Combinaciones especiales
    "regentes_en_buen_aspecto": 4,
}

# Configuraciones de validación
VALIDATION_SETTINGS = {
    'check_known_moments': True,
    'compare_with_legacy': True,
    'performance_threshold_minutes': 15,
    'accuracy_threshold_percent': 95
}
