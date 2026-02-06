from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime

# Importar getter de config para validación
# Nota: Asumimos que config.py está accesible. 
# Si no, deberemos mover get_temas_disponibles a un lugar común o duplicar la validación.
try:
    from config import get_temas_disponibles
except ImportError:
    # Fallback si falla la importación durante generación de esquema
    def get_temas_disponibles():
        return ["trabajo", "amor", "salud", "dinero", "viajes"]

class CartaNatalData(BaseModel):
    """Modelo para datos de carta natal"""
    fecha_nacimiento: str = Field(..., description="Fecha de nacimiento (YYYY-MM-DD)")
    hora_nacimiento: str = Field(..., description="Hora de nacimiento (HH:MM)")
    ciudad: str = Field(..., description="Ciudad de nacimiento")
    pais: str = Field(..., description="País de nacimiento")
    timezone: str = Field(..., description="Zona horaria")

    @validator('fecha_nacimiento')
    def validar_fecha(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError("Formato de fecha debe ser YYYY-MM-DD")

    @validator('hora_nacimiento')
    def validar_hora(cls, v):
        try:
            datetime.strptime(v, '%H:%M')
            return v
        except ValueError:
            raise ValueError("Formato de hora debe ser HH:MM")

class BusquedaRequest(BaseModel):
    """Modelo para solicitud de búsqueda de carta electiva"""
    user_id: str = Field(..., description="ID del usuario")
    tema: str = Field(..., description="Tema astrológico (trabajo, amor, etc.)")
    fecha_inicio: str = Field(..., description="Fecha de inicio (YYYY-MM-DD)")
    dias: int = Field(30, ge=1, le=365, description="Número de días a analizar")
    ubicacion: Dict[str, str] = Field(..., description="Ubicación con ciudad y país")
    carta_natal: CartaNatalData = Field(..., description="Datos de carta natal del usuario")

    @validator('tema')
    def validar_tema(cls, v):
        temas_validos = get_temas_disponibles()
        if v not in temas_validos:
            raise ValueError(f"Tema '{v}' no válido. Disponibles: {temas_validos}")
        return v

    @validator('fecha_inicio')
    def validar_fecha(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError("Formato de fecha debe ser YYYY-MM-DD")

class MomentoElectivo(BaseModel):
    """Modelo para un momento electivo encontrado"""
    ranking: int = Field(..., description="Posición en el ranking (1 es mejor)")
    fecha_hora: str = Field(..., description="Fecha y hora del momento (ISO 8601)")
    puntuacion_total: float = Field(..., description="Puntuación calculada")
    enraizamiento_pct: float = Field(..., description="Porcentaje de enraizamiento")
    calidad_pct: float = Field(..., description="Porcentaje de calidad astrológica")
    categoria: str = Field(..., description="Categoría descriptiva")
    detalles: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales del cálculo")

class EstadisticasBusqueda(BaseModel):
    """Estadísticas de la búsqueda realizada"""
    total_momentos: int
    tiempo_calculo: str
    factor_optimizacion: str

class TaskResponse(BaseModel):
    """Respuesta de inicio de tarea"""
    success: bool
    task_id: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

class ProgressResponse(BaseModel):
    """Respuesta de progreso"""
    progress: int
    status: str
    result: Optional[Dict[str, Any]] = None # El resultado final (BusquedaResponse.data)
    error: Optional[str] = None

class BusquedaData(BaseModel):
    """Datos de la respuesta de búsqueda"""
    momentos: List[MomentoElectivo]
    estadisticas: EstadisticasBusqueda
    task_id: Optional[str] = None

class BusquedaResponse(BaseModel):
    """Respuesta de búsqueda de carta electiva"""
    success: bool
    data: Optional[BusquedaData] = None
    error: Optional[str] = None
    task_id: Optional[str] = None # Added for consistency with legacy if needed, or rely on data.task_id
