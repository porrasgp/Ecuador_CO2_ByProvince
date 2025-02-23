import streamlit as st
import boto3
import xarray as xr
import os
from dotenv import load_dotenv  # Importar load_dotenv para cargar variables de entorno

# Cargar variables de entorno desde un archivo .env (solo si no se ejecuta en GitHub Actions)
if not os.getenv("GITHUB_ACTIONS"):
    load_dotenv()

# Obtener credenciales de AWS desde variables de entorno
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Verificar que las credenciales estén disponibles
if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
    st.error("Credenciales de AWS no configuradas. Asegúrate de definir AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY.")
    st.stop()

# Configuración de AWS S3
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY_ID,  # Usar las variables, no cadenas literales
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

bucket_name = 'meeo-s5p'
prefix = 'products/CO2/2023/10/'

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
        st.title("Datos de CO2 de Sentinel-5P")

        try:
            ds = xr.open_dataset('local_file.nc')
            st.write(ds)

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
