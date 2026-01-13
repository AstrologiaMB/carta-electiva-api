
from typing import Dict, List

class AstroConfig:
    """
    Configuración centralizada para el motor astrológico.
    Permite ajustar orbes y reglas sin modificar la lógica interna.
    """
    
    # Orbes para Aspectos Planetarios (Grados)
    # Basado en la lógica legacy que usaba 8.0 para todo "Major" aspect implicito en algunos casos
    # o configurable. Aquí definimos defaults razonables.
    ORB_ASPECTS: Dict[str, float] = {
        "CONJUNCTION": 8.0,
        "OPPOSITION": 8.0,
        "TRINE": 8.0,
        "SQUARE": 8.0,
        "SEXTILE": 6.0
    }
    
    # Orbe para Fase Lunar (Nueva/Llena)
    ORB_MOON_PHASE: float = 8.0
    
    # Aspectos considerados "Mayores" (Ptolomeicos)
    MAJOR_ASPECTS: List[int] = [0, 60, 90, 120, 180]
    
    # Planetas considerados para "Vacío de Curso"
    # Tradicionalmente: Sol, Mer, Ven, Mar, Jup, Sat
    # IDs SwissEph: Sun=0, Moon=1 (excluido), Mer=2, Ven=3, Mar=4, Jup=5, Sat=6
    VOC_TARGETS: List[int] = [0, 2, 3, 4, 5, 6]
    
    # Sistema de Casas por defecto (P=Placidus, W=Whole Sign, etc.)
    # Legacy usaba Placidus ('P') por defecto en immanuel
    DEFAULT_HOUSE_SYSTEM: str = 'P' 
    
    # Configuración de Dignidades (Puntos) -> Para Fase 5 (Scoring)
    SCORE_DIGNITY_DOMICILE = 10
    SCORE_DIGNITY_EXALTATION = 7
    SCORE_DEBILITY_DETRIMENT = -10
    SCORE_DEBILITY_FALL = -7

    @classmethod
    def get_orb(cls, aspect_angle: float) -> float:
        """Devuelve el orbe apropiado para un ángulo dado."""
        if aspect_angle == 0: return cls.ORB_ASPECTS["CONJUNCTION"]
        if aspect_angle == 180: return cls.ORB_ASPECTS["OPPOSITION"]
        if aspect_angle == 120: return cls.ORB_ASPECTS["TRINE"]
        if aspect_angle == 90: return cls.ORB_ASPECTS["SQUARE"]
        if aspect_angle == 60: return cls.ORB_ASPECTS["SEXTILE"]
        return 1.0 # Default fallback
