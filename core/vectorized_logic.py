
import numpy as np
import logging
from typing import Dict, List, Tuple

# Configurar logging
logger = logging.getLogger(__name__)

class VectorizedLogic:
    """
    Motor Lógico Vectorizado.
    Transforma posiciones planetarias (NumPy arrays) en decisiones de negocio (Boolean Masks).
    """

    # Signos (0=Aries, 1=Taurus, ..., 11=Pisces)
    ARIES = 0
    TAURUS = 1
    GEMINI = 2
    CANCER = 3
    LEO = 4
    VIRGO = 5
    LIBRA = 6
    SCORPIO = 7
    SAGITTARIUS = 8
    CAPRICORN = 9
    AQUARIUS = 10
    PISCES = 11

    def __init__(self):
        # Traditional Rulerships
        self.RULER_MAP = {
            self.ARIES: 4, # Mars
            self.TAURUS: 3, # Venus
            self.GEMINI: 2, # Mercury
            self.CANCER: 1, # Moon
            self.LEO: 0, # Sun
            self.VIRGO: 2, # Mercury
            self.LIBRA: 3, # Venus
            self.SCORPIO: 4, # Mars (Traditional)
            self.SAGITTARIUS: 5, # Jupiter
            self.CAPRICORN: 6, # Saturn
            self.AQUARIUS: 6, # Saturn (Traditional)
            self.PISCES: 5, # Jupiter (Traditional)
        }
        
        # Exaltations (Planet ID -> Sign ID)
        self.EXALTATION_MAP = {
            0: self.ARIES, # Sun
            1: self.TAURUS, # Moon
            2: self.VIRGO, # Mercury
            3: self.PISCES, # Venus
            4: self.CAPRICORN, # Mars
            5: self.CANCER, # Jupiter
            6: self.LIBRA # Saturn
        }
        
        # Detriments (Opposite to Rulership)
        # Falls (Opposite to Exaltation)
        # We can compute these or hardcode for speed. 
        # Hardcoding is faster/clearer.
        
        self.DETRIMENT_MAP = {} # Populated in init for simplicity logic
        for sign, planet in self.RULER_MAP.items():
            opposite = (sign + 6) % 12
            if planet not in self.DETRIMENT_MAP:
                self.DETRIMENT_MAP[planet] = []
            self.DETRIMENT_MAP[planet].append(opposite)
            
        self.FALL_MAP = {}
        for planet, sign in self.EXALTATION_MAP.items():
            opposite = (sign + 6) % 12
            self.FALL_MAP[planet] = opposite

        # Triplicities (Dorothean/Standard) - (Day, Night, Participating)
        # We can simplify to "Is it a triplicity ruler?"
        # Fire: Sun, Jup, Sat
        # Earth: Ven, Moon, Mars
        # Air: Sat, Mer, Jup
        # Water: Ven, Mar, Moon
        self.TRIPLICITY_RULERS = {
            self.ARIES: [0, 5, 6], self.LEO: [0, 5, 6], self.SAGITTARIUS: [0, 5, 6],
            self.TAURUS: [3, 1, 4], self.VIRGO: [3, 1, 4], self.CAPRICORN: [3, 1, 4],
            self.GEMINI: [6, 2, 5], self.LIBRA: [6, 2, 5], self.AQUARIUS: [6, 2, 5],
            self.CANCER: [3, 4, 1], self.SCORPIO: [3, 4, 1], self.PISCES: [3, 4, 1]
        }
        
        # Egyptian Terms (Bounds) - {Sign: [(DegreeBound, PlanetID), ...]}
        # Simplification: We need a function to check terms.
        # Format: Sign -> List of (UpperLimit, Planet)
        self.TERMS_MAP = {
            self.ARIES: [(6, 5), (12, 3), (20, 2), (25, 4), (30, 6)], # Jup, Ven, Mer, Mar, Sat
            self.TAURUS: [(8, 3), (14, 2), (22, 5), (27, 6), (30, 4)], # Ven, Mer, Jup, Sat, Mar
            self.GEMINI: [(6, 2), (12, 5), (17, 3), (24, 4), (30, 6)], # Mer, Jup, Ven, Mar, Sat
            self.CANCER: [(7, 4), (13, 3), (19, 2), (26, 5), (30, 6)], # Mar, Ven, Mer, Jup, Sat
            self.LEO: [(6, 5), (11, 3), (18, 6), (24, 2), (30, 4)],    # Jup, Ven, Sat, Mer, Mar
            self.VIRGO: [(7, 2), (17, 3), (21, 5), (28, 4), (30, 6)],  # Mer, Ven, Jup, Mar, Sat
            self.LIBRA: [(6, 6), (14, 3), (21, 5), (28, 2), (30, 4)],  # Sat, Ven, Jup, Mer, Mar
            self.SCORPIO: [(7, 4), (11, 3), (19, 2), (24, 5), (30, 6)],# Mar, Ven, Mer, Jup, Sat
            self.SAGITTARIUS: [(12, 5), (17, 3), (21, 2), (26, 6), (30, 4)], # Jup, Ven, Mer, Sat, Mar
            self.CAPRICORN: [(7, 2), (14, 5), (22, 3), (26, 6), (30, 4)], # Mer, Jup, Ven, Sat, Mar
            self.AQUARIUS: [(7, 2), (13, 3), (20, 5), (25, 4), (30, 6)],  # Mer, Ven, Jup, Mar, Sat
            self.PISCES: [(12, 3), (16, 5), (19, 2), (28, 4), (30, 6)]    # Ven, Jup, Mer, Mar, Sat
        }

    def get_ruler_for_sign(self, sign_index: int) -> int:
        """Retorna SwissEph ID del regente tradicional del signo."""
        return self.RULER_MAP.get(sign_index, 0)

    def mask_dignity(self, planet_id: int, longitudes: np.ndarray) -> np.ndarray:
        """
        Retorna máscara True si el planeta está en Domicilio o Exaltación.
        """
        signs = self.get_sign_indices(longitudes)
        
        # Domicile Check
        # Does this planet rule the sign it is in?
        # Vectorized approach: map sign -> ruler, compare with planet_id
        # Since planet_id is scalar here (we evaluate one planet at a time), we can do:
        
        # Which signs does this planet rule?
        ruled_signs = [s for s, p in self.RULER_MAP.items() if p == planet_id]
        exalted_sign = self.EXALTATION_MAP.get(planet_id)
        
        good_signs = ruled_signs
        if exalted_sign is not None:
            good_signs.append(exalted_sign)
            
        return np.isin(signs, good_signs)

    def mask_debility(self, planet_id: int, longitudes: np.ndarray) -> np.ndarray:
        """
        Retorna máscara True si el planeta está en Exilio o Caída.
        """
        signs = self.get_sign_indices(longitudes)
        
        detriment_signs = self.DETRIMENT_MAP.get(planet_id, [])
        fall_sign = self.FALL_MAP.get(planet_id)
        
        bad_signs = list(detriment_signs)
        if fall_sign is not None:
            bad_signs.append(fall_sign)
            
        return np.isin(signs, bad_signs)


    def get_sign_indices(self, longitudes: np.ndarray) -> np.ndarray:
        """
        Retorna el índice del signo (0-11) para cada longitud.
        """
        return (longitudes // 30).astype(int) % 12

    def mask_signs(self, longitudes: np.ndarray, forbidden_signs: List[int]) -> np.ndarray:
        """
        Retorna máscara TRUE si el planeta está en un signo prohibido.
        """
        sign_indices = self.get_sign_indices(longitudes)
        # np.isin es vectorizado y muy rápido
        return np.isin(sign_indices, forbidden_signs)

    def calculate_aspects(self, body1_longs: np.ndarray, body2_longs: np.ndarray) -> np.ndarray:
        """
        Calcula la diferencia angular mínima (0-180) entre dos cuerpos.
        """
        diff = np.abs(body1_longs - body2_longs)
        return np.minimum(diff, 360 - diff)

    def mask_exact_aspect(self, body1: np.ndarray, body2: np.ndarray, 
                         aspect_angle: float, orb: float) -> np.ndarray:
        """
        Retorna True si hay un aspecto exacto dentro del orbe.
        """
        ang_diff = self.calculate_aspects(body1, body2)
        return np.abs(ang_diff - aspect_angle) <= orb

    def mask_void_of_course(self, times: np.ndarray, moon_longs: np.ndarray, 
                          planet_positions: Dict[int, np.ndarray]) -> np.ndarray:
        """
        Detección Vectorizada de Luna Vacía de Curso (VoC).
        
        Definición: La Luna es VoC si NO hace aspectos exactos (Ptolomeicos: 0, 60, 90, 120, 180)
        antes de cambiar de signo.
        
        Estrategia Vectorizada:
        1. Calcular 'Distancia' (en grados) hasta el final del signo para la Luna.
        2. Calcular 'Distancia' hasta el próximo aspecto exacto con cada planeta.
           (Considerando velocidades relativas: Tiempo = Distancia / VelRelativa).
           O más simple geométricamente: ¿Se cruzan las trayectorias antes de los 30 grados?
           
        Para este POC, usaremos una aproximación geométrica robusta:
        - Luna VoC = (NextAspectLongitude > SignBoundaryLongitude)
        """
        # Distancia al final del signo actual
        # Ej: Luna en 15° Aries -> Faltan 15° para llegar a 30° (Tauro)
        current_sign_start = (moon_longs // 30) * 30
        next_sign_start = current_sign_start + 30
        dist_to_ingress = next_sign_start - moon_longs
        
        # Inicia asumiendo que es VoC (True), y trataremos de probar lo contrario (falsificar)
        # Si encontramos UN aspecto aplicativo dentro del signo, entonces NO es VoC (False)
        is_voc = np.ones(len(moon_longs), dtype=bool)
        
        major_aspects = [0, 60, 90, 120, 180]
        
        # Planetas tradicionales a considerar (excluyendo Nodos y la misma Luna)
        # IDs: 0=Sun, 2=Merc, 3=Ven, 4=Mars, 5=Jup, 6=Sat
        target_bodies = [0, 2, 3, 4, 5, 6] 
        
        for pid in target_bodies:
            if pid not in planet_positions: continue
            
            p_longs = planet_positions[pid]
            
            # Calcular dónde ocurrirían los aspectos exactos proyectando posiciones
            # Esto es complejo porque los planetas se mueven.
            # Alternativa "Look Ahead" simplificada para POC:
            # Si estamos en un punto t, miramos el futuro.
            # Pero eso rompe la vectorización pura sin ventanas.
            
            # Enfoque "Snapshot":
            # Un aspecto es aplicativo si:
            # 1. El aspecto no es exacto todavía.
            # 2. La Luna (más rápida) se acerca al punto del aspecto.
            # 3. La distancia al aspecto es MENOR que la distancia al cambio de signo.
            
            # Ángulo actual entre cuerpos
            angle = np.abs(moon_longs - p_longs) % 360
            
            for asp in major_aspects:
                # Distancia al aspecto (considerando movimiento directo de Luna)
                # Casos: 
                # Luna 10, Sol 20 (Diff 10). Aspecto 0. Luna debe recorrer 10.
                # Luna 10, Sol 70 (Diff 60). Aspecto 60. Luna YA lo hizo (separativo) o lo hará?
                # Depende de quién es más rápido. Asumimos Luna siempre más rápida.
                
                # Simplificación: Calcular "distancia forward" al aspecto
                # Target places en el zodíaco donde el planeta P formaría aspecto A
                # places = [P + A, P - A]
                
                targets = [
                    (p_longs + asp) % 360,
                    (p_longs - asp) % 360
                ]
                
                for target in targets:
                    # Distancia de Luna a Target (siempre hacia adelante, 0-360)
                    dist_to_target = (target - moon_longs) % 360
                    
                    # Si esa distancia es menor que la distancia al cambio de signo
                    # ENTONCES el aspecto ocurre dentro del signo actual
                    # Y por tanto, NO está vacía de curso
                    
                    # NOTA: Esto asume que el otro planeta está "quieto".
                    # Para períodos cortos (horas), es aceptable.
                    # Para mayor precisión, deberíamos usar velocidades relativas.
                    # dist_real = dist_geo / (v_luna - v_planeta)
                    
                    aspect_occurs_in_sign = dist_to_target < dist_to_ingress
                    
                    # Si ocurre en signo -> is_voc False
                    # Actualizamos máscara: Donde hallamos aspecto, VoC se apaga
                    is_voc[aspect_occurs_in_sign] = False
                    
        return is_voc

    def mask_phase(self, sun: np.ndarray, moon: np.ndarray, orb: float = 8.0) -> np.ndarray:
        """
        Retorna True si es Luna Nueva o Llena (orbe X).
        """
        diff = self.calculate_aspects(sun, moon)
        # New Moon (0) or Full Moon (180)
        is_new = diff <= orb
        is_full = np.abs(diff - 180) <= orb
        return is_new | is_full
