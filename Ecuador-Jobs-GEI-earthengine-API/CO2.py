import boto3
import os

# Configuración de AWS S3 (sin credenciales explícitas)
s3 = boto3.client('s3')

bucket_name = 'meeo-s5p'
prefix = 'products/CO2/2023/10/'

try:
    # Listar objetos en el bucket
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    for obj in response.get('Contents', []):
        file_key = obj['Key']
        if file_key.endswith('.nc'):
            # Descargar el archivo NetCDF
            s3.download_file(bucket_name, file_key, 'local_file.nc')
            print(f"Archivo descargado: {file_key}")
            break
except Exception as e:
    print(f"Error al acceder a S3: {e}")
