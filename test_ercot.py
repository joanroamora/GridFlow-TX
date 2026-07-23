#!/usr/bin/env python3
"""
Script de prueba para la conexión a la API de ERCOT usando gridstatus.
Extrae la mezcla de generación (Fuel Mix) y los datos de demanda (Load) para el día de hoy,
con enfoque en la red de Texas y la zona de Houston (COAST).
"""

import sys
import logging
import pandas as pd
import requests
import gridstatus

# Configuración de logging para producción / depuración DevOps
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("test_ercot")


def main():
    logger.info("=== INICIANDO VALIDACIÓN DE CONEXIÓN API ERCOT (GridFlow-TX) ===")

    # 1. Inicializar cliente ERCOT
    try:
        iso = gridstatus.Ercot()
        logger.info("Cliente ERCOT (gridstatus.Ercot) inicializado correctamente.")
    except Exception as e:
        logger.critical(f"Fallo al inicializar el cliente de ERCOT: {e}", exc_info=True)
        sys.exit(1)

    # 2. Extraer Mezcla de Generación (Fuel Mix) para 'today'
    logger.info("Consultando Mezcla de Generación (Fuel Mix) para hoy...")
    try:
        fuel_mix = iso.get_fuel_mix(date="today")
        if fuel_mix is not None and not fuel_mix.empty:
            logger.info(f"Fuel Mix obtenido exitosamente: {len(fuel_mix)} registros.")
            print("\n" + "=" * 70)
            print("1. MEZCLA DE GENERACIÓN ACTUAL (FUEL MIX - TODAY)")
            print("=" * 70)
            print(fuel_mix.tail(10).to_string(index=False))
        else:
            logger.warning("Respuesta vacía al consultar Fuel Mix.")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Fallo de red/conectividad HTTP al solicitar Fuel Mix: {req_err}")
    except Exception as err:
        logger.error(f"Error inesperado o cambio de estructura en portal de ERCOT al obtener Fuel Mix: {err}", exc_info=True)

    # 3. Extraer Demanda de la Red (Load) para 'today'
    logger.info("Consultando Demanda del Sistema (System Load) para hoy...")
    try:
        system_load = iso.get_load(date="today")
        if system_load is not None and not system_load.empty:
            logger.info(f"Demanda del sistema (System Load) obtenida exitosamente: {len(system_load)} registros.")
            print("\n" + "=" * 70)
            print("2. DEMANDA TOTAL DE LA RED DE TEXAS (SYSTEM LOAD - TODAY)")
            print("=" * 70)
            print(system_load.tail(5).to_string(index=False))
        else:
            logger.warning("Respuesta vacía al consultar System Load.")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Fallo de red/conectividad HTTP al solicitar System Load: {req_err}")
    except Exception as err:
        logger.error(f"Error inesperado al obtener System Load: {err}", exc_info=True)

    # 4. Extraer Demanda por Zonas (Weather Zones - Enfocado en Houston/COAST y Texas Total)
    logger.info("Consultando Demanda Zonal por Clima (Weather Zone Load - Houston/COAST)...")
    try:
        zonal_load = iso.get_load_by_weather_zone(date="today")
        if zonal_load is not None and not zonal_load.empty:
            logger.info(f"Demanda zonal obtenida exitosamente: {len(zonal_load)} registros.")
            
            # Filtrar columnas de interés (Time, Coast [Houston], System Total [Texas])
            cols_of_interest = [c for c in zonal_load.columns if c in ['Time', 'Interval Start', 'Coast', 'System Total']]
            filtered_df = zonal_load[cols_of_interest] if cols_of_interest else zonal_load
            
            print("\n" + "=" * 70)
            print("3. DEMANDA ZONAL ENFOCADA: HOUSTON (COAST) Y REGIONAL (TEXAS TOTAL)")
            print("=" * 70)
            print(filtered_df.tail(10).to_string(index=False))
        else:
            logger.warning("Respuesta vacía al consultar Zonal Load.")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"Fallo de red/conectividad HTTP al solicitar Weather Zone Load: {req_err}")
    except Exception as err:
        logger.error(f"Error inesperado o cambio de formato público al obtener Weather Zone Load: {err}", exc_info=True)

    logger.info("=== PRUEBA DE CONEXIÓN Y EXTRACCIÓN COMPLETADA EXITOAMENTE ===")


if __name__ == "__main__":
    main()
