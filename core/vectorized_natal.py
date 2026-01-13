
import numpy as np
from typing import Dict, List, Optional
from .vectorized_logic import VectorizedLogic
from .astro_config import AstroConfig

class VectorizedNatal:
    """
    Motor para integración de Carta Natal (Enraizamiento).
    Calcula aspectos entre Tránsitos (Vector) y Natal (Escalar/Fijo).
    """

    def __init__(self):
        self.logic = VectorizedLogic()

    def calculate_aspects_transit_to_natal(self, 
                                         transit_longs: np.ndarray, 
                                         natal_long: float) -> np.ndarray:
        """
        Calcula ángulo (0-180) entre un cuerpo en tránsito (array) y un punto natal (float).
        """
        diff = np.abs(transit_longs - natal_long)
        return np.minimum(diff, 360 - diff)

    def mask_transiting_aspect(self, 
                             transit_longs: np.ndarray, 
                             natal_long: float, 
                             aspect_angle: float, 
                             orb: float = AstroConfig.ORB_ASPECTS["SQUARE"]) -> np.ndarray:
        """
        Retorna True si el planeta en tránsito hace un aspecto específico al punto natal.
        Ej: Saturno Transito cuadratura Sol Natal.
        """
        angles = self.calculate_aspects_transit_to_natal(transit_longs, natal_long)
        return np.abs(angles - aspect_angle) <= orb

    def mask_hard_aspects_to_natal_lights(self, 
                                        transits: Dict[int, np.ndarray], 
                                        natal_chart: Dict[int, float],
                                        malefics: List[int] = [4, 6]) -> np.ndarray:
        """
        Filtro "Deal Breaker":
        Retorna True si hay aspectos TENSOS (Cuadratura/Oposición) de Maléficos en Tránsito
        a las Luminares (Sol/Luna) Natales.
        
        Args:
            transits: Dict {planet_id: array_longitudes}
            natal_chart: Dict {planet_id: longitude}
            malefics: IDs de maléficos (Default: 4=Mars, 6=Saturn, maybe 12/13 for outer)
        """
        n_points = len(next(iter(transits.values())))
        is_bad = np.zeros(n_points, dtype=bool)
        
        hard_angles = [90, 180] # Cuadratura, Oposición (y tal vez Conjunción 0 para maléficos)
        # Añadimos Conjunción (0) para Marte/Saturno? Sí, generalmente es tensa.
        hard_angles.append(0)
        
        lights = [0, 1] # Sun, Moon
        
        for malefic_id in malefics:
            if malefic_id not in transits: continue
            
            t_longs = transits[malefic_id]
            
            for light_id in lights:
                if light_id not in natal_chart: continue
                
                n_long = natal_chart[light_id]
                
                for angle in hard_angles:
                    orb = AstroConfig.get_orb(angle)
                    mask = self.mask_transiting_aspect(t_longs, n_long, angle, orb)
                    
                    # Accumulate badness
                    is_bad |= mask
                    
        return is_bad

    def mask_benefic_aspects_to_angles(self,
                                     transits: Dict[int, np.ndarray],
                                     natal_asc: float,
                                     natal_mc: float,
                                     benefics: List[int] = [3, 5]) -> np.ndarray:
        """
        Filtro "Booster":
        Retorna True si hay aspectos FLUIDOS (Trígono/Sextil/Conjunción) de Benéficos en Tránsito
        a los Ángulos (Asc/MC) Natales.
        """
        n_points = len(next(iter(transits.values())))
        is_good = np.zeros(n_points, dtype=bool)
        
        soft_angles = [0, 60, 120] # Conjunción, Sextil, Trígono
        
        # Targets: Asc, MC
        # We handle them separately as floats
        targets = [natal_asc, natal_mc]
        
        for benefic_id in benefics:
            if benefic_id not in transits: continue
            
            t_longs = transits[benefic_id]
            
            for target_long in targets:
                for angle in soft_angles:
                    orb = AstroConfig.get_orb(angle)
                    mask = self.mask_transiting_aspect(t_longs, target_long, angle, orb)
                    is_good |= mask
                    
        return is_good
