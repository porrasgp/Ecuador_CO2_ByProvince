import streamlit as st
import boto3
import xarray as xr
import os

# Configuración de AWS S3
s3 = boto3.client(
    's3',
    aws_access_key_id='TU_ACCESS_KEY',
    aws_secret_access_key='TU_SECRET_KEY'
)

bucket_name = 'meeo-s5p'
prefix = 'products/CO2/2023/10/'

# Descargar el archivo más reciente
response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
for obj in response.get('Contents', []):
    file_key = obj['Key']
    if file_key.endswith('.nc'):
        s3.download_file(bucket_name, file_key, 'local_file.nc')
        break

# Cargar y mostrar los datos en Streamlit
st.title("Datos de CO2 de Sentinel-5P")

ds = xr.open_dataset('local_file.nc')
st.write(ds)

if 'CO2' in ds:
    st.line_chart(ds['CO2'].mean(dim=['lat', 'lon']))

# Limpiar el archivo descargado
os.remove('local_file.nc')
