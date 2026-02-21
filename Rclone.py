import os

UNIDAD_COMPARTIDA_ID = 'PEGA_AQUI_TU_ID'
ARCHIVO_REGISTRO = 'copiados.txt'

def obtener_copiados():
    # Lee el archivo de texto para saber qué IDs ya se copiaron
    if os.path.exists(ARCHIVO_REGISTRO):
        with open(ARCHIVO_REGISTRO, 'r') as f:
            return set(f.read().splitlines())
    return set()

def registrar_copia(file_id):
    # Agrega el nuevo ID al archivo de texto
    with open(ARCHIVO_REGISTRO, 'a') as f:
        f.write(f"{file_id}\n")

def ejecutar_copia(servicio):
    print("Buscando archivos en la unidad compartida...")
    copiados = obtener_copiados()
    
    resultados = servicio.files().list(
        q="trashed = false", 
        corpora='drive',
        driveId=UNIDAD_COMPARTIDA_ID,
        includeItemsFromAllDrives=True,
        supportsAllDrives=True,
        fields="files(id, name, size)"
    ).execute()
    
    archivos = resultados.get('files', [])
    
    for archivo in archivos:
        # Si el archivo ya está en nuestro registro, lo saltamos
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
                
                # Guardamos el ID para no volver a copiarlo en el futuro
                registrar_copia(archivo['id'])
                print(f"✅ ¡Copia exitosa a tu unidad!: {archivo['name']}")
                
            except Exception as e:
                print(f"Error al copiar {archivo['name']}: {e}")

if __name__ == '__main__':
    # 1. Obtenemos la conexión usando los Secrets y la guardamos en 'servicio'
    servicio = autenticar_github()
    
    # 2. Le pasamos esa conexión a la función que hace la copia
    ejecutar_copia(servicio)
