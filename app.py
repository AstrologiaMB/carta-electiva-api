"""
Carta Electiva API - Microservicio Astrowellness
Servicio FastAPI para cálculo de cartas electivas optimizadas
"""

import os
import sys
import signal
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import logging

# Agregar paths necesarios
sys.path.append(os.path.dirname(__file__))

from core.algoritmo_busqueda import AlgoritmoBusqueda
from core.legacy_wrapper import LegacyAstroWrapper
from utils.scc_calculator import SCC_Calculator
from config import get_temas_disponibles

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Modelos Pydantic
class CartaNatalData(BaseModel):
    """Modelo para datos de carta natal"""
    fecha_nacimiento: str = Field(..., description="Fecha de nacimiento (YYYY-MM-DD)")
    hora_nacimiento: str = Field(..., description="Hora de nacimiento (HH:MM)")
    ciudad: str = Field(..., description="Ciudad de nacimiento")
    pais: str = Field(..., description="País de nacimiento")
    timezone: str = Field(..., description="Zona horaria")

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
    ranking: int
    fecha_hora: str
    puntuacion_total: float
    enraizamiento_pct: float
    calidad_pct: float
    categoria: str

class EstadisticasBusqueda(BaseModel):
    """Estadísticas de la búsqueda realizada"""
    total_momentos: int
    tiempo_calculo: str
    factor_optimizacion: str

class BusquedaResponse(BaseModel):
    """Respuesta de búsqueda de carta electiva"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Estado global para tareas en background y progreso real
background_tasks_status = {}
task_progress = {}  # Nuevo: estado de progreso por task_id

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejador de ciclo de vida de la aplicación"""
    logger.info("🚀 Iniciando Carta Electiva API")
    yield
    logger.info("🛑 Deteniendo Carta Electiva API")

# Crear aplicación FastAPI
app = FastAPI(
    title="Carta Electiva API",
    description="Servicio de cálculo de cartas electivas optimizadas para Astrowellness",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CartaElectivaService:
    """Servicio principal para cálculo de cartas electivas"""

    def __init__(self):
        logger.info("🌟 Inicializando CartaElectivaService")

    def calcular_carta_natal(self, fecha_nacimiento: datetime, lat: float, lon: float) -> Dict:
        """
        Calcula carta natal para el usuario

        Args:
            fecha_nacimiento: Fecha y hora de nacimiento
            lat: Latitud
            lon: Longitud

        Returns:
            Dict con datos de la carta natal
        """
        try:
            wrapper = LegacyAstroWrapper(fecha_nacimiento, lat, lon)
            chart_data = wrapper.get_chart_data_for_enraizamiento()
            logger.info(f"✅ Carta natal calculada para {fecha_nacimiento.strftime('%Y-%m-%d %H:%M')}")
            return chart_data
        except Exception as e:
            logger.error(f"❌ Error calculando carta natal: {e}")
            raise HTTPException(status_code=500, detail=f"Error calculando carta natal: {str(e)}")

    def calcular_carta_natal_desde_datos(self, carta_natal_data: CartaNatalData) -> Dict:
        """
        Calcula carta natal usando datos del usuario

        Args:
            carta_natal_data: Datos de nacimiento del usuario

        Returns:
            Dict con datos de la carta natal
        """
        try:
            # Parsear fecha y hora
            fecha_str = f"{carta_natal_data.fecha_nacimiento} {carta_natal_data.hora_nacimiento}"
            fecha_nacimiento = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M')

            # Obtener coordenadas de la ubicación
            lat, lon = self._obtener_coordenadas({
                'ciudad': carta_natal_data.ciudad,
                'pais': carta_natal_data.pais
            })

            logger.info(f"📊 Calculando carta natal para: {fecha_nacimiento.strftime('%Y-%m-%d %H:%M')} ({carta_natal_data.ciudad}, {carta_natal_data.pais})")

            # Calcular carta natal
            wrapper = LegacyAstroWrapper(fecha_nacimiento, lat, lon)
            chart_data = wrapper.get_chart_data_for_enraizamiento()

            logger.info(f"✅ Carta natal calculada: ASC {chart_data['asc_grados']:.1f}° (signo {chart_data['asc_signo']})")
            return chart_data

        except Exception as e:
            logger.error(f"❌ Error calculando carta natal desde datos: {e}")
            raise HTTPException(status_code=500, detail=f"Error procesando datos de nacimiento: {str(e)}")

    async def buscar_momentos_electivos_async(self, request: BusquedaRequest, carta_natal: Dict) -> Dict[str, Any]:
        """
        Ejecuta búsqueda completa de momentos electivos con timeout de 5 minutos

        Args:
            request: Datos de la solicitud
            carta_natal: Datos de carta natal del usuario

        Returns:
            Dict con resultados de la búsqueda
        """
        try:
            # Parsear fecha de inicio
            fecha_inicio = datetime.strptime(request.fecha_inicio, '%Y-%m-%d')

            # Validar fecha no sea en el pasado
            hoy = datetime.now().date()
            if fecha_inicio.date() < hoy:
                raise HTTPException(status_code=400, detail="La fecha de inicio no puede ser anterior a hoy")

            # Obtener coordenadas (simplificado - en producción usar geocodificación)
            lat, lon = self._obtener_coordenadas(request.ubicacion)

            # Calcular rango de fechas
            fecha_fin = fecha_inicio + timedelta(days=request.dias)

            # Inicializar algoritmo de búsqueda
            algoritmo = AlgoritmoBusqueda(carta_natal, request.tema, lat, lon)

            # Medir tiempo de ejecución
            tiempo_inicio = datetime.now()

            # Ejecutar búsqueda optimizada con timeout de 5 minutos
            logger.info(f"⚡ Ejecutando búsqueda para tema '{request.tema}' ({request.dias} días) - Timeout: 5 min")

            try:
                # Ejecutar búsqueda en un thread separado para poder timeout
                loop = asyncio.get_event_loop()
                mejores_momentos = await asyncio.wait_for(
                    loop.run_in_executor(None, algoritmo.buscar_mejores_momentos, fecha_inicio, fecha_fin),
                    timeout=300.0  # 5 minutos timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Timeout excedido (5 min) para búsqueda: user={request.user_id}, tema={request.tema}")
                raise HTTPException(
                    status_code=408,
                    detail="La búsqueda tomó más de 5 minutos. Inténtalo con un período más corto (máximo 30 días recomendado)."
                )

            tiempo_fin = datetime.now()
            tiempo_total = (tiempo_fin - tiempo_inicio).total_seconds()

            # Preparar estadísticas
            estadisticas = {
                'total_momentos': len(mejores_momentos),
                'tiempo_calculo': f"{tiempo_total:.2f}s",
                'factor_optimizacion': f"{algoritmo.calculos_fase_1 + algoritmo.calculos_fase_2} cálculos"
            }

            # Extraer valores de enraizamiento para calcular SCC
            valores_enraizamiento = []
            for momento in mejores_momentos[:20]:
                # Extraer puntos de enraizamiento
                enraizamiento_puntos = self._extraer_enraizamiento_puntos(momento)
                valores_enraizamiento.append(enraizamiento_puntos)

            # Convertir momentos a formato API con categorías SCC correctas
            momentos = []
            for i, momento in enumerate(mejores_momentos[:20], 1):  # Top 20
                # Calcular categoría usando SCC
                enraizamiento_puntos = valores_enraizamiento[i-1]
                scc_data = SCC_Calculator.calcular_scc(enraizamiento_puntos, valores_enraizamiento)
                categoria = scc_data['categoria']

                momentos.append({
                    'ranking': i,
                    'fecha_hora': momento['fecha_hora'].strftime('%Y-%m-%dT%H:%M:%S'),
                    'puntuacion_total': momento['puntuacion_total'],
                    'enraizamiento_pct': momento.get('enraizamiento_pct', momento.get('enraizamiento_score', 0) * 100),
                    'calidad_pct': momento.get('calidad_pct', momento.get('calidad_score', 0) * 100),
                    'categoria': categoria
                })

            logger.info(f"✅ Búsqueda completada: {len(momentos)} momentos encontrados en {tiempo_total:.2f}s")

            return {
                'momentos': momentos,
                'estadisticas': estadisticas
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Error en búsqueda de momentos electivos: {e}")
            raise HTTPException(status_code=500, detail=f"Error interno en el cálculo astrológico: {str(e)}")

    # Mantener método síncrono para compatibilidad
    def buscar_momentos_electivos(self, request: BusquedaRequest, carta_natal: Dict) -> Dict[str, Any]:
        """
        Wrapper síncrono para compatibilidad
        """
        # Crear event loop si no existe
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Ejecutar búsqueda asíncrona
        return loop.run_until_complete(self.buscar_momentos_electivos_async(request, carta_natal))

    def _extraer_enraizamiento_puntos(self, momento: Dict) -> float:
        """
        Extrae los puntos de enraizamiento de un momento

        Args:
            momento: Diccionario con datos del momento

        Returns:
            Puntos de enraizamiento como float
        """
        # Intentar obtener de detalles.enraizamiento_puro.puntos_total
        detalles = momento.get('detalles', {})
        if detalles and 'enraizamiento_puro' in detalles:
            enraizamiento_data = detalles['enraizamiento_puro']
            if isinstance(enraizamiento_data, dict) and 'puntos_total' in enraizamiento_data:
                return float(enraizamiento_data['puntos_total'])

        # Fallback: intentar de enraizamiento_score
        if 'enraizamiento_score' in momento:
            # Si es un score 0-1, convertir aproximado a puntos
            score = momento['enraizamiento_score']
            if 0 <= score <= 1:
                # Aproximación: score 0.5 ≈ 2 puntos (promedio)
                return (score - 0.5) * 8  # Escala aproximada

        # Último fallback: intentar de enraizamiento_pct
        if 'enraizamiento_pct' in momento:
            # Convertir porcentaje aproximado a puntos
            pct = momento['enraizamiento_pct']
            if 0 <= pct <= 100:
                # Aproximación: 50% ≈ 2 puntos
                return (pct / 50.0) - 2.0

        # Si no se encuentra, devolver 0
        logger.warning(f"No se pudo extraer enraizamiento de momento: {momento.get('fecha_hora', 'N/A')}")
        return 0.0

    def _obtener_coordenadas(self, ubicacion: Dict[str, str]) -> tuple[float, float]:
        """
        Obtiene coordenadas de una ubicación (simplificado)

        Args:
            ubicacion: Dict con ciudad y país

        Returns:
            Tuple (lat, lon)
        """
        # Para esta implementación inicial, usar coordenadas hardcodeadas
        # En producción, integrar con servicio de geocodificación
        ciudad = ubicacion.get('ciudad', '').lower()
        pais = ubicacion.get('pais', '').lower()

        # Coordenadas de ejemplo
        if 'buenos aires' in ciudad and 'argentina' in pais:
            return -34.6037, -58.3816
        elif 'madrid' in ciudad and 'españa' in pais:
            return 40.4168, -3.7038
        elif 'méxico' in ciudad and 'méxico' in pais:
            return 19.4326, -99.1332
        else:
            # Buenos Aires por defecto
            logger.warning(f"Ubicación no reconocida: {ubicacion}, usando Buenos Aires por defecto")
            return -34.6037, -58.3816

# Instancia del servicio
service = CartaElectivaService()

@app.get("/")
async def root():
    """Endpoint raíz con información del servicio"""
    return {
        "service": "Carta Electiva API - Astrowellness",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "temas": "/temas",
            "buscar": "/buscar (POST)",
            "progress": "/progress/{task_id}"
        }
    }

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud"""
    return {
        "status": "healthy",
        "service": "Carta Electiva API - Astrowellness",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "dependencies_ok": True
    }

@app.get("/temas")
async def obtener_temas():
    """Obtiene lista de temas disponibles"""
    return {
        "success": True,
        "temas": get_temas_disponibles()
    }

@app.post("/buscar")
async def buscar_momentos_electivos(request: BusquedaRequest, background_tasks: BackgroundTasks):
    """
    Endpoint principal para búsqueda de momentos electivos

    Inicia la búsqueda en background y devuelve un task_id para seguimiento del progreso.
    """
    try:
        # Generar task_id único
        task_id = str(uuid.uuid4())

        # Inicializar progreso
        task_progress[task_id] = {
            "progress": 0,
            "status": "Iniciando búsqueda...",
            "result": None,
            "error": None
        }

        logger.info(f"🔍 Nueva búsqueda: task_id={task_id}, user={request.user_id}, tema={request.tema}, dias={request.dias}")

        # Iniciar búsqueda en background
        background_tasks.add_task(run_search_background, task_id, request)

        return {
            "success": True,
            "task_id": task_id,
            "message": "Búsqueda iniciada. Usa el task_id para consultar progreso."
        }

    except Exception as e:
        logger.error(f"❌ Error iniciando búsqueda: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.get("/progress/{task_id}")
async def get_progress(task_id: str):
    """
    Consulta el progreso de una tarea de búsqueda
    """
    if task_id not in task_progress:
        return {"error": "Task ID no encontrado"}

    progress_data = task_progress[task_id]

    # Si la tarea está completa, devolver resultado
    if progress_data["progress"] >= 100 and progress_data["result"]:
        return {
            "progress": 100,
            "status": "Completado",
            "result": progress_data["result"]
        }

    # Si hay error, devolver error
    if progress_data["error"]:
        return {
            "progress": -1,
            "status": f"Error: {progress_data['error']}",
            "error": progress_data["error"]
        }

    # Devolver progreso actual
    return {
        "progress": progress_data["progress"],
        "status": progress_data["status"]
    }

async def run_search_background(task_id: str, request: BusquedaRequest):
    """
    Ejecuta la búsqueda en background con actualizaciones de progreso real
    """
    try:
        # Actualizar progreso: Iniciando
        task_progress[task_id]["progress"] = 5
        task_progress[task_id]["status"] = "Calculando carta natal..."

        # Calcular carta natal
        carta_natal = service.calcular_carta_natal_desde_datos(request.carta_natal)

        # Actualizar progreso: Carta natal lista
        task_progress[task_id]["progress"] = 20
        task_progress[task_id]["status"] = "Analizando constelaciones básicas..."

        # Ejecutar búsqueda completa
        resultado = await service.buscar_momentos_electivos_async(request, carta_natal)

        # Actualizar progreso: Completado
        task_progress[task_id]["progress"] = 100
        task_progress[task_id]["status"] = "Búsqueda completada"
        task_progress[task_id]["result"] = resultado

        logger.info(f"✅ Búsqueda completada: task_id={task_id}, momentos={len(resultado.get('momentos', []))}")

    except Exception as e:
        logger.error(f"❌ Error en búsqueda background task_id={task_id}: {e}")
        task_progress[task_id]["progress"] = -1
        task_progress[task_id]["status"] = f"Error: {str(e)}"
        task_progress[task_id]["error"] = str(e)

# Método auxiliar para generar carta natal de ejemplo (temporal)
def _generar_carta_natal_ejemplo(service_instance=None) -> Dict:
    """
    Genera carta natal de ejemplo para desarrollo
    En producción, esto vendría de la base de datos
    """
    # Usar carta natal real del usuario (26/12/1964, 21:12, Buenos Aires)
    fecha_natal = datetime(1967, 11, 3, 14, 14)
    lat_natal = -34.6037  # Buenos Aires
    lon_natal = -58.3816

    try:
        wrapper = LegacyAstroWrapper(fecha_natal, lat_natal, lon_natal)
        chart_data = wrapper.get_chart_data_for_enraizamiento()

        logger.info(f"📊 Carta natal de ejemplo: {fecha_natal.strftime('%Y-%m-%d %H:%M')} (Buenos Aires)")
        logger.info(f"   ASC: {chart_data['asc_grados']:.1f}° (signo {chart_data['asc_signo']})")

        return chart_data

    except Exception as e:
        logger.warning(f"Error generando carta natal de ejemplo: {e}")
        # Retornar datos mínimos simulados
        return {
            'asc_grados': 0.0,
            'asc_signo': 1,
            'planetas': {},
            'casas': {},
            'aspectos': {}
        }

# Agregar método al servicio
CartaElectivaService._generar_carta_natal_ejemplo = staticmethod(_generar_carta_natal_ejemplo)

if __name__ == "__main__":
    # Ejecutar servidor
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info"
    )
