import os
import pandas as pd
from functools import wraps
import logging

def save_output(file_format='csv', filepath=None):
    """
    Decorador para guardar el output de una función que devuelve un DataFrame como CSV o Excel.

    Args:
        file_format (str): Formato del archivo ('csv' o 'excel'). Por defecto, 'csv'.
        filepath (str, opcional): Ruta donde se guardará el archivo. Si es None, se guardará en '../output_files/output.{file_format}'.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Ejecuta la función original
            result = func(*args, **kwargs)
            
            if not isinstance(result, pd.DataFrame):
                print("El resultado no es un DataFrame. No se guardará el archivo.")
                return result
            
            # Determina la carpeta de salida relativa a la raíz del proyecto
            nonlocal filepath  # Declara filepath como no local para modificar su valor
            if filepath is None or filepath == "":
                project_root = os.path.dirname(os.path.abspath(__file__))  # Obtén la raíz del decorador
                output_dir = os.path.abspath(os.path.join(project_root, '../../output_files'))
                os.makedirs(output_dir, exist_ok=True)  # Crea la carpeta si no existe
                filepath = os.path.join(output_dir, f"output")
            
            # Asegura que la extensión del archivo sea correcta
            if file_format.lower() == 'excel' and not filepath.endswith('.xlsx'):
                filepath += '.xlsx'
            elif file_format.lower() == 'csv' and not filepath.endswith('.csv'):
                filepath += '.csv'
            
            # Guarda el archivo en el formato elegido
            if file_format.lower() == 'csv':
                result.to_csv(filepath, index=False)
            elif file_format.lower() == 'excel':
                try:
                    result.to_excel(filepath, index=False, engine='openpyxl')
                except ImportError:
                    raise ValueError("Para guardar como Excel, necesitas instalar 'openpyxl'. Puedes instalarlo con: pip install openpyxl")
            else:
                raise ValueError("Formato no soportado. Usa 'csv' o 'excel'.")
            
            print(f"Archivo guardado en {filepath} como {file_format.upper()}.")
            return result
        return wrapper
    return decorator


def log_attributes_on_error(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            # Log the class attributes
            logging.error(f"Error in {func.__name__}: {e}")
            logging.error(f"Attributes - dob: {getattr(self, 'dob', 'N/A')}, "
                          f"lat: {getattr(self, 'lat', 'N/A')}, "
                          f"lon: {getattr(self, 'lon', 'N/A')}, "
                          f"activity: {getattr(self, 'activity', 'N/A')}")
            raise
    return wrapper

def print_attributes_on_error(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            print(f"Error in function '{func.__name__}': {e}")
            print(f"Attributes:")
            print(f"  dob: {getattr(self, 'dob', 'N/A')}")
            print(f"  lat: {getattr(self, 'lat', 'N/A')}")
            print(f"  lon: {getattr(self, 'lon', 'N/A')}")
            print(f"  activity: {getattr(self, 'activity', 'N/A')}")
            raise
    return wrapper