import boto3
from botocore import UNSIGNED
from botocore.client import Config
import xarray as xr
import os
import streamlit as st

# Configuración de AWS S3 sin credenciales (acceso público)
s3 = boto3.client(
    's3',
    config=Config(signature_version=UNSIGNED),  # Desactiva la autenticación
    region_name='eu-central-1'  # Región del bucket
)

bucket_name = 'meeo-s5p'
prefix = 'NRTI/'  # Prefijo para los datos Near Real Time (NRTI)

try:
    # Listar objetos en el bucket
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    if 'Contents' not in response:
        st.warning("No se encontraron archivos en el bucket con el prefijo especificado.")
    else:
        # Descargar el primer archivo .nc encontrado
        for obj in response['Contents']:
            file_key = obj['Key']
            if file_key.endswith('.nc'):
                s3.download_file(bucket_name, file_key, 'local_file.nc')
                st.success(f"Archivo descargado: {file_key}")
                break

        # Cargar y mostrar los datos en Streamlit
        st.title("Datos de Sentinel-5P Near Real Time (NRTI)")

        try:
            ds = xr.open_dataset('local_file.nc')
            st.write(ds)

            # Verificar si el archivo contiene datos de CO2
            if 'CO2' in ds:
                st.line_chart(ds['CO2'].mean(dim=['lat', 'lon']))
            else:
                st.warning("El archivo no contiene datos de CO2.")
        except Exception as e:
            st.error(f"Error al abrir el archivo NetCDF: {e}")
finally:
    # Limpiar el archivo descargado (si existe)
    if os.path.exists('local_file.nc'):
        os.remove('local_file.nc')
