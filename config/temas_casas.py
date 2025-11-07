"""
Configuración de mapeo entre temas astrológicos y casas
"""

TEMAS_CASAS = {
    'trabajo': 10,
    'amor': 7,
    'viajes': 9,
    'salud': 6,
    'dinero': 2,
    'estudios': 3,
    'familia': 4,
    'creatividad': 5,
    'amistades': 11,
    'espiritualidad': 12
}

# Descripciones de los temas para documentación
DESCRIPCIONES_TEMAS = {
    'trabajo': 'Carrera profesional, empleo, reconocimiento público',
    'amor': 'Relaciones románticas, matrimonio, asociaciones',
    'viajes': 'Viajes largos, estudios superiores, filosofía, religión',
    'salud': 'Salud física, trabajo diario, servicio',
    'dinero': 'Recursos propios, posesiones, valores materiales',
    'estudios': 'Comunicación, aprendizaje, hermanos, viajes cortos',
    'familia': 'Hogar, familia, raíces, propiedades inmobiliarias',
    'creatividad': 'Creatividad, hijos, romance, entretenimiento',
    'amistades': 'Amigos, grupos, esperanzas, objetivos',
    'espiritualidad': 'Espiritualidad, karma, sacrificio, retiro'
}

def get_casa_for_tema(tema):
    """
    Obtiene el número de casa para un tema dado
    
    Args:
        tema (str): Nombre del tema
        
    Returns:
        int: Número de casa (1-12)
        
    Raises:
        ValueError: Si el tema no existe
    """
    if tema not in TEMAS_CASAS:
        raise ValueError(f"Tema '{tema}' no reconocido. Temas disponibles: {list(TEMAS_CASAS.keys())}")
    
    return TEMAS_CASAS[tema]

def get_temas_disponibles():
    """
    Obtiene lista de todos los temas disponibles
    
    Returns:
        list: Lista de nombres de temas
    """
    return list(TEMAS_CASAS.keys())

def get_descripcion_tema(tema):
    """
    Obtiene la descripción de un tema
    
    Args:
        tema (str): Nombre del tema
        
    Returns:
        str: Descripción del tema
    """
    return DESCRIPCIONES_TEMAS.get(tema, "Descripción no disponible")
