
import numpy as np
import swisseph as swe
from typing import Tuple, List
from .vectorized_ephemeris import VectorizedEphemeris
from .astro_config import AstroConfig

class VectorizedHouses:
    """
    Motor vectorial para el cálculo de casas astrológicas.
    Utiliza SwissEph para calcular Cúspides y Ángulos (Asc, MC) para múltiples tiempos.
    """
    
    def __init__(self):
        # Aseguramos que las efemérides estén en su lugar (path set by Ephemeris class usually)
        # VectorizedEphemeris sets the path in __init__, so we assume it was called or we call it
        pass

    def calculate_houses(self, 
                        times: np.ndarray, 
                        lat: float, 
                        lon: float, 
                        alt: float = 0.0,
                        system: str = AstroConfig.DEFAULT_HOUSE_SYSTEM) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcula casas para un array de tiempos en una ubicación geográfica fija.
        
        Args:
            times: Array de datetime o timestamps.
            lat: Latitud (dec).
            lon: Longitud (dec).
            system: Sistema de casas (Default 'P' - Placidus).
            
        Returns:
            Tuple (cusps_matrix, ascmc_matrix)
            - cusps_matrix: (N, 12) -> Las 12 cúspides.
            - ascmc_matrix: (N, 10) -> [Asc, MC, ARMC, Vertex, Equasc, Coasc, Mooncross, PolarAsc...]
              - index 0: Ascendente
              - index 1: MC
        """
        # Reutilizamos la conversión de tiempos de VectorizedEphemeris
        # Nota: Idealmente esta lógica de conversión debería ser estática o utilidad compartida.
        # Por ahora instanciamos (ligero overhead) o duplicamos.
        # Duplicamos la lógica simple para evitar dependencia circular o overhead.
        
        jds = []
        for t in times:
            t_utc = t # Asumimos t ya es UTC o naive tratado como UT
             # Si t es datetime
            hour = t.hour + t.minute/60.0 + t.second/3600.0
            jd = swe.julday(t.year, t.month, t.day, hour)
            jds.append(jd)
            
        # SwissEph houses wrapper no es vectorizado. Hacemos list comprehension.
        # swe.houses(jd, lat, lon, hsys) -> returns (cusps, ascmc)
        # cusps es tuple de 13 floats (index 0 es 0.0, casas son 1-12)
        # ascmc es tuple de 10 floats
        
        batch_results = [swe.houses(jd, lat, lon, bytes(system, 'utf-8')) for jd in jds]
        
        # Desempaquetar
        # batch_results es una lista de tuplas ((cusps), (ascmc))
        
        # Extraer cusps
        # Según debug, swe.houses retorna tupla de 12 elementos (Casas 1-12)
        # NO hay elemento dummy en índice 0 en esta versión
        cusps_list = [r[0] for r in batch_results]
        ascmc_list = [r[1] for r in batch_results]
        
        return np.array(cusps_list), np.array(ascmc_list)
        
    def get_ascendant(self, ascmc_matrix: np.ndarray) -> np.ndarray:
        """Helper para obtener solo array de Ascendentes."""
        return ascmc_matrix[:, 0]

    def get_mc(self, ascmc_matrix: np.ndarray) -> np.ndarray:
        """Helper para obtener solo array de Medio Cielos."""
        return ascmc_matrix[:, 1]
