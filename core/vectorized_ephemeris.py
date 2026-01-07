
import swisseph as swe
import numpy as np
from datetime import datetime
from typing import List, Tuple, Dict, Union
import logging

# Configurar logging
logger = logging.getLogger(__name__)

class VectorizedEphemeris:
    """
    Motor de Efemérides Vectorizado (NumPy + SwissEph).
    
    Diseñado para calcular posiciones planetarias masivas (miles de momentos)
    en una fracción del tiempo que toma el enfoque orientado a objetos.
    """
    
    # Mapeo de cuerpos celestes (SwissEph IDs)
    BODIES = {
        'sun': 0,      # swe.SUN
        'moon': 1,     # swe.MOON
        'mercury': 2,  # swe.MERCURY
        'venus': 3,    # swe.VENUS
        'mars': 4,     # swe.MARS
        'jupiter': 5,  # swe.JUPITER
        'saturn': 6,   # swe.SATURN
        'uranus': 7,   # swe.URANUS
        'neptune': 8,  # swe.NEPTUNE
        'pluto': 9,    # swe.PLUTO
        'mean_node': 10, # swe.MEAN_NODE (North Node)
        'true_node': 11  # swe.TRUE_NODE
    }

    # Indices en el array de resultados de swe.calc_ut
    IDX_LONG = 0
    IDX_LAT = 1
    IDX_DIST = 2
    IDX_SPEED_LONG = 3
    
    def __init__(self):
        # Configurar efemérides (asegurar path si es necesario, 
        # aunque swisseph suele encontrarlo si está instalado via pip)
        # swe.set_ephe_path('/path/to/ephe') 
        pass

    def calculate_positions(self, times: np.ndarray, bodies: List[int] = None) -> Dict[str, np.ndarray]:
        """
        Calcula posiciones para un array de tiempos y una lista de cuerpos.
        
        Args:
            times: Array 1D de timestamps (datetime objects o JulDays).
                   Si son datetimes, se convierten a Julian Days internamente.
            bodies: Lista de IDs de cuerpos celestes (swisseph ints).
                    Si es None, calcula todos los principales (Sol a Plutón + Nodo).
                    
        Returns:
            Diccionario {body_id: matriz_posiciones}
            Cada matriz_posiciones es shape (N, 6) con [lon, lat, dist, speed_lon, speed_lat, speed_dist]
            O simplificado a (N, 4) según necesidad.
        """
        if bodies is None:
            bodies = list(self.BODIES.values())
            
        # 1. Convertir tiempos a Julian Days (Vectorizado)
        jds = self._convert_times_to_jd(times)
        
        results = {}
        
        # 2. Calcular posiciones (Bucle optimizado)
        # SwissEph no es vectorizado nativamente en C para arrays, 
        # pero list comprehension es suficientemente rápido para ~10k-100k puntos.
        # Para >1M, se requeriría interacción C directa o chunking.
        
        for body in bodies:
            # Flag FLG_SPEED para obtener velocidades
            # Flag FLG_SWIEPH para usar efemérides suizas (alta precisión)
            flags = swe.FLG_SPEED | swe.FLG_SWIEPH
            
            # List comprehension optimizada (lo más rápido en Python puro)
            # swe.calc_ut retorna ((lon, lat, dist, speed...), rflag)
            # Nos quedamos con la tupla de datos (índice 0)
            
            # NOTA: Para máxima velocidad, evitamos wrappers y llamadas extra
            try:
                body_data = [swe.calc_ut(jd, body, flags)[0] for jd in jds]
                
                # Convertir a NumPy array (N, 6)
                # 0: Longitude, 1: Latitude, 2: Distance, 3: Long. Speed, 4: Lat. Speed, 5: Dist. Speed
                results[body] = np.array(body_data, dtype=np.float64)
                
            except Exception as e:
                logger.error(f"Error calculando cuerpo {body}: {e}")
                results[body] = np.zeros((len(jds), 6)) # Fallback seguro
                
        return results

    def _convert_times_to_jd(self, times: np.ndarray) -> np.ndarray:
        """Convierte array de datetimes a Julian Days (UTC)"""
        # Función auxiliar para aplicar vectorización si es posible, 
        # o map simple si son objetos datetime mixtos.
        
        converter = lambda t: self._to_jd(t)
        # Vectorize de numpy es conveniente aunque no necesariamente más rápido que list comp para objetos
        vfunc = np.vectorize(converter) 
        return vfunc(times)

    def _to_jd(self, t: datetime) -> float:
        """Convierte un datetime a Julian Day UT"""
        # swe.julday espera (año, mes, dia, hora_decimal)
        hour_decimal = t.hour + t.minute/60.0 + t.second/3600.0
        return swe.julday(t.year, t.month, t.day, hour_decimal)

    @staticmethod
    def get_body_id(name: str) -> int:
        return VectorizedEphemeris.BODIES.get(name.lower())

    def get_longitudes(self, positions: Dict[int, np.ndarray]) -> Dict[int, np.ndarray]:
        """Extrae solo las longitudes de los resultados completos"""
        return {k: v[:, self.IDX_LONG] for k, v in positions.items()}

    def get_speeds(self, positions: Dict[int, np.ndarray]) -> Dict[int, np.ndarray]:
        """Extrae solo las velocidades longitudinales de los resultados completos"""
        return {k: v[:, self.IDX_SPEED_LONG] for k, v in positions.items()}
