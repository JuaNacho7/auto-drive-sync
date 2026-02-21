import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# ¡NO OLVIDES PEGAR AQUÍ TU ID DE NUEVO!
UNIDAD_COMPARTIDA_ID = '0AOretv_KlnerUk9PVA'
ARCHIVO_REGISTRO = 'copiados.txt'

def autenticar_github():
    try:
        # Lee el token directamente desde los Secrets de GitHub
        token_info = json.loads(os.environ['GCP_TOKEN'])
        creds = Credentials.from_authorized_user_info(token_info)
        return build('drive', 'v3', credentials=creds)
    except KeyError:
        print("❌ Error: No se encontraron las credenciales en los Secrets (GCP_TOKEN).")
        return None
    except Exception as e:
        print(f"❌ Error de autenticación: {e}")
        return None

def obtener_copiados():
    if os.path.exists(ARCHIVO_REGISTRO):
        with open(ARCHIVO_REGISTRO, 'r') as f:
            return set(f.read().splitlines())
    return set()

def registrar_copia(file_id):
    with open(ARCHIVO_REGISTRO, 'a') as f:
        f.write(f"{file_id}\n")

def ejecutar_copia(servicio):
    if not servicio:
        return

    print("Buscando archivos en la unidad compartida...")
    copiados = obtener_copiados()
    
    try:
        resultados = servicio.files().list(
            q="trashed = false", 
            corpora='drive',
            driveId=UNIDAD_COMPARTIDA_ID,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields="files(id, name, size)"
        ).execute()
        
        archivos = resultados.get('files', [])
        
        if not archivos:
            print("No se encontraron archivos en la unidad compartida.")
            return

        for archivo in archivos:
            if archivo['id'] in copiados:
                continue 
                
            tamano_bytes = int(archivo.get('size', 0))
            tamano_mb = tamano_bytes / (1024 * 1024)
            tamano_gb = tamano_bytes / (1024 * 1024 * 1024)
            
            # Filtro: Más de 100 MB y menos de 7 GB
            if 100 < tamano_mb and tamano_gb < 7:
                print(f"Copiando: {archivo['name']} ({tamano_mb:.2f} MB)")
                
                try:
                    servicio.files().copy(
                        fileId=archivo['id'],
                        body={'parents': ['root']},
                        supportsAllDrives=True
                    ).execute()
                    
                    registrar_copia(archivo['id'])
                    print(f"✅ ¡Copia exitosa a tu unidad!: {archivo['name']}")
                    
                except Exception as e:
                    print(f"Error al copiar {archivo['name']}: {e}")
            else:
                # Opcional: Para saber qué está ignorando el script
                print(f"Ignorado por tamaño: {archivo['name']} ({tamano_mb:.2f} MB)")

    except Exception as e:
        print(f"Error al buscar en la unidad compartida: {e}")

if __name__ == '__main__':
    servicio = autenticar_github()
    if servicio:
        ejecutar_copia(servicio)
    else:
        print("No se pudo iniciar el servicio de Google Drive. Deteniendo script.")

