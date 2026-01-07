
from typing import Dict, TypedDict, Optional

class ThemeConfig(TypedDict):
    target_house: int  # 1-12
    natural_ruler: Optional[int] # SwissEph ID
    secondary_house: Optional[int]
    name_es: str

# Configuración Central de Temas
THEMES: Dict[str, ThemeConfig] = {
    "trabajo": {
        "target_house": 10, # MC - Carrera, Status
        "natural_ruler": 6, # Saturno (Responsabilidad, Estructura)
        "secondary_house": 6, # Casa 6 (Trabajo diario) o 2 (Dinero)
        "name_es": "Trabajo y Carrera"
    },
    "lanzamiento": {
        "target_house": 10,
        "natural_ruler": 4, # Marte (Acción, Inicio)
        "secondary_house": 1, 
        "name_es": "Lanzamiento de Proyecto"
    },
    "amor": {
        "target_house": 7, # Pareja
        "natural_ruler": 3, # Venus
        "secondary_house": 5, # Romance
        "name_es": "Amor y Pareja"
    },
    "dinero": {
        "target_house": 2, # Recursos
        "natural_ruler": 5, # Júpiter (Abundancia)
        "secondary_house": 8, # Recursos compartidos
        "name_es": "Dinero e Inversiones"
    },
    "viaje": {
        "target_house": 9, # Viajes largos
        "natural_ruler": 5, # Júpiter
        "secondary_house": 3, # Viajes cortos
        "name_es": "Viajes y Extranjero"
    },
    "inmobiliaria": {
        "target_house": 4, # Pasado, Raíces, Hogar
        "natural_ruler": 1, # Luna (Hogar)
        "secondary_house": None,
        "name_es": "Bienes Raíces y Hogar"
    }
}

def get_theme_config(theme_name: str) -> ThemeConfig:
    """Retorna la configuración para un tema dado."""
    return THEMES.get(theme_name.lower(), THEMES["trabajo"]) # Default to trabajo
