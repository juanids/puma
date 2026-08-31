import serial
import struct
import csv
import time
import os
from datetime import datetime
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cm
import pickle
import subprocess
import os
import logging
import sys

# Configuración básica de registros (logging) para ver los eventos en consola
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def subir_a_google_drive(ruta_local, destino_remote, solo_nuevos=False):
    """
    Ejecuta el comando 'rclone copy' para subir archivos de forma segura a Google Drive.
    
    Por defecto, Rclone ya es inteligente: compara los archivos locales con los de Drive 
    por tamaño y fecha de modificación, y de manera automática SALTA los archivos que 
    sean idénticos para no volver a subirlos ni gastar ancho de banda.
    
    :param ruta_local: Ruta de la carpeta o archivo en la Raspberry Pi (ej. '/home/pi/datos')
    :param destino_remote: Nombre del remote y carpeta de destino (ej. 'PumaDrive:Puma/jd886')
    :param solo_nuevos: Si es True, añade la bandera '--ignore-existing'. Esto evita que 
                        se sobrescriba cualquier archivo que ya exista en Google Drive, 
                        incluso si la versión local es más nueva o ha sido modificada.
    """
    # 1. Convertimos la ruta local a una RUTA ABSOLUTA (ej. de './../Resultados/muestra' a '/home/pi/Resultados/muestra')
    ruta_local_absoluta = os.path.abspath(ruta_local)
    
    # 2. Normalizamos la ruta de destino remota para eliminar "." o ".." que confunden a Google Drive
    destino_remote_limpio = destino_remote
    if ":" in destino_remote:
        # Separamos el nombre del remote (ej. 'PumaDrive') de la ruta (ej. 'Puma/Resultados/./../Resultados/JD985')
        remote_part, path_part = destino_remote.split(":", 1)
        # os.path.normpath resuelve y elimina los '.' y '..' de manera inteligente
        path_part_limpio = os.path.normpath(path_part).replace("\\", "/")
        destino_remote_limpio = f"{remote_part}:{path_part_limpio}"
    else:
        destino_remote_limpio = os.path.normpath(destino_remote).replace("\\", "/")
    
    # Comando base con ambas rutas totalmente limpias y resueltas
    comando = ["rclone", "copy", ruta_local_absoluta, destino_remote_limpio]
    
    # Si quieres un comportamiento súper estricto donde no se toque nada ya existente
    if solo_nuevos:
        comando.append("--ignore-existing")
    
    logging.info(f"Iniciando transferencia: {ruta_local_absoluta} -> {destino_remote_limpio}")
    
    try:
        # Explicación de los parámetros clave:
        # - capture_output=True: Guarda la salida estándar (stdout) y de error (stderr) para poder leerlas en Python.
        # - text=True: Convierte los bytes devueltos por la consola directamente a cadenas de texto (strings).
        # - check=True: Si el comando rclone falla (código de salida distinto de 0), lanza automáticamente un CalledProcessError.
        resultado = subprocess.run(comando, capture_output=True, text=True, check=True)
        
        logging.info("¡Transferencia completada con éxito en Google Drive!")
        
        # Opcional: Si rclone arrojó información adicional, la mostramos en modo depuración (debug)
        if resultado.stdout:
            logging.debug(f"Salida de Rclone:\n{resultado.stdout}")
            
    except subprocess.CalledProcessError as e:
        # Este bloque se ejecuta si rclone falla (por ejemplo, si no hay internet o el remote no existe)
        logging.error("La transferencia falló. Detalles del error:")
        logging.error(f"Código de salida de Rclone (exit code): {e.returncode}")
        logging.error(f"Error de consola:\n{e.stderr.strip()}")
        
    except FileNotFoundError:
        # Este bloque se ejecuta si rclone ni siquiera está instalado en el sistema
        logging.error("No se encontró el ejecutable de 'rclone'. Asegúrate de que esté instalado en la Raspberry Pi.")
        
    except Exception as ex:
        # Captura de cualquier otra excepción imprevista
        logging.error(f"Ocurrió un error inesperado al intentar subir los archivos: {ex}")

def CreaMapa(tareas,muestra,nombre,cont,rserie,v,ciclos,delay,tipo,comentario):
    tareas.append({'tipo': 'M', 'archivo': muestra+'/Txt/'+nombre+'_'+str(cont)+'.csv', 'params': (rserie, v, ciclos, delay, tipo), 'coment': comentario})
    cont+=1
    return tareas, cont
def CreaIV(tareas,muestra,nombre,cont,inputs,outputs,rserie,vmax,ciclos,delay,pulsos,cota,puntos,pasos2,comentario):
    estados=[0,0,0,0,0,0,0,0]
    comunes = set(inputs) & set(outputs)

    if comunes:
        print("Error")
        estados=[51,51,51,51,51,51,51,51]
    else:
        for i in range(1,17):
            ind=(i-1)//2
            if i<9:
                
                if i in inputs:
                    estados[ind]+=0
                elif i in outputs:
                    if (i-1)%2==0:
                        estados[ind]+=(rserie<<1)
                    else:
                        estados[ind]+=(rserie<<5)
                else:
                    if (i-1)%2==0:
                        estados[ind]+=2
                    else:
                        estados[ind]+=(2<<4)
            else:
                if i in inputs:
                    estados[ind]+=0
                elif i in outputs:
                    if (i-1)%2!=0:
                        estados[ind]+=(rserie<<1)
                    else:
                        estados[ind]+=(rserie<<5)
                else:
                    if (i-1)%2!=0:
                        estados[ind]+=2
                    else:
                        estados[ind]+=(2<<4)


    # print(estados)
    tareas.append({'tipo': 'I', 'archivo': muestra+'/Txt/'+nombre+'_'+str(cont)+'.csv', 'params': (estados[0], estados[1], estados[2], estados[3], estados[4], estados[5], estados[6], estados[7], vmax, ciclos, delay,pulsos,cota,puntos,pasos2), 'coment': comentario})
    cont+=1
    return tareas, cont
def CreaP(tareas,muestra,nombre,cont,inputs,outputs,rserie,v1,c1,v2,c2,ciclos,delay,comentario):
    estados=[0,0,0,0,0,0,0,0]
    comunes = set(inputs) & set(outputs)

    if comunes:
        print("Error")
        estados=[34,34,34,34,34,34,34,34]
    else:
        for i in range(1,17):
            ind=(i-1)//2
            if i<9:
                
                if i in inputs:
                    estados[ind]+=0
                elif i in outputs:
                    if (i-1)%2==0:
                        estados[ind]+=(rserie<<1)
                    else:
                        estados[ind]+=(rserie<<5)
                else:
                    if (i-1)%2==0:
                        estados[ind]+=2
                    else:
                        estados[ind]+=(2<<4)
            else:
                if i in inputs:
                    estados[ind]+=0
                elif i in outputs:
                    if (i-1)%2!=0:
                        estados[ind]+=(rserie<<1)
                    else:
                        estados[ind]+=(rserie<<5)
                else:
                    if (i-1)%2!=0:
                        estados[ind]+=2
                    else:
                        estados[ind]+=(2<<4)


    # print(estados)
    tareas.append({'tipo': 'P', 'archivo': muestra+'/Txt/'+nombre+'_'+str(cont)+'.csv', 'params': (estados[0], estados[1], estados[2], estados[3], estados[4], estados[5], estados[6], estados[7], v1, c1, v2, c2, ciclos, delay), 'coment': comentario})
    cont+=1
    return tareas, cont



class EstacionBalseiro:
    def __init__(self, puerto='COM11', baudios=921600):
        try:
            self.ser = serial.Serial(puerto, baudios, timeout=2)
            try:
                self.ser.set_buffer_size(2097152, 1048576)
            except AttributeError:
                # En Linux (Raspberry Pi) ignoramos pacientemente este paso
                pass
            self.ser.dtr = True
            self.ser.rts = True
            
            time.sleep(2)
            self.ser.reset_input_buffer()
            print(f"✅ Conectado en {puerto}")

            self.version=self.obtener_version()
        except Exception as e:
            print(f"❌ Error: {e}")
    def obtener_version(self):
        """Pide al Arduino la versión actual del firmware y la imprime."""
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(b"V\n")
                version = self.ser.readline().decode().strip()
                print(f"🤖 Firmware detectado: {version}")
                return version
            except Exception as e:
                print(f"⚠️ No se pudo obtener la versión: {e}")
        return None
    def cerrar(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("🔌 Puerto cerrado correctamente.")
    
    def ejecutar_secuencia(self, lista_rutinas):
        print("\n--- 🧠 Cargando Secuencia ---")
        self.ser.write(b"Q\n")
        self.ser.readline() 
        
        for r in lista_rutinas:
            p = r['params']
            if r['tipo'] == 'M': t = f"M,{p[0]},{p[1]},{p[2]},{p[3]},{p[4]}\n"
            elif r['tipo'] == 'I': t = f"I,{p[0]},{p[1]},{p[2]},{p[3]},{p[4]},{p[5]},{p[6]},{p[7]},{p[8]},{p[9]},{p[10]},{p[11]},{p[12]},{p[13]},{p[14]}\n"
            elif r['tipo'] == 'P': t = f"P,{p[0]},{p[1]},{p[2]},{p[3]},{p[4]},{p[5]},{p[6]},{p[7]},{p[8]},{p[9]},{p[10]},{p[11]},{p[12]},{p[13]}\n"
            
            self.ser.write(t.encode())
            self.ser.readline()

        # --- FASE 1: CAPTURA TOTAL ---
        print("\n🚀 DISPARANDO SECUENCIA (T=0)...")
        self.ser.write(b"S\n")
        
        raw_file = "/tmp/full_experiment.raw"
        buffer_total = b""
        with open(raw_file, "wb") as f:
            while True:
                if self.ser.in_waiting > 0:
                    chunk = self.ser.read(self.ser.in_waiting)
                    f.write(chunk)
                    buffer_total += chunk
                    if b"ALL_DONE" in buffer_total:
                        break
                time.sleep(0.0001)

        self._procesar_experimento_total(raw_file, lista_rutinas)

    def _procesar_experimento_total(self, archivo_raw, lista_rutinas):
        with open(archivo_raw, "rb") as f:
            full_data = f.read()
        
        # DIAGNÓSTICO CRÍTICO
        count_ready = full_data.count(b"READY_MAPEO")
        count_done  = full_data.count(b"DONE_MAPEO")
        

        fecha_py = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor = 0

        for idx, r in enumerate(lista_rutinas):
            label_ready = b"READY_MAPEO" if r['tipo'] == 'M' else b"READY"
            label_done  = b"DONE_MAPEO"  if r['tipo'] == 'M' else b"DONE_EXP"
            label_tstart = b"T_START_REL:"

            t_rel_idx = full_data.find(label_tstart, cursor)
            t_relativo = "N/A"
            if t_rel_idx != -1:
                end_line = full_data.find(b"\r\n", t_rel_idx)
                if end_line == -1:
                    end_line = full_data.find(b"\n", t_rel_idx)
                t_relativo = full_data[t_rel_idx+12:end_line].decode().strip()

            start_idx = full_data.find(label_ready, cursor)
            end_idx   = full_data.find(label_done, start_idx) if start_idx != -1 else -1

            # DIAGNÓSTICO POR TAREA
            # print(f"[{idx:02d}] cursor={cursor} | start={start_idx} | end={end_idx} | archivo={r['archivo']}")

            if start_idx != -1 and end_idx != -1:
                bloque = full_data[start_idx:end_idx]
                datos  = self._parsear_bloque(bloque, r['tipo'])
                # print(f"      → bloque={len(bloque)} bytes | filas parseadas={len(datos)}")
                
                header = ['t_us','i','j','Vi','Vj'] if r['tipo'] == 'M' else ['t_us'] + [f'ADC{k}' for k in range(16)]
                self._guardar_csv_final(r['archivo'], header, datos, r, fecha_py, t_relativo)
                cursor = end_idx + len(label_done)  # ← AVANZAR DESPUÉS DEL DONE, no en el DONE
            else:
                print(f"      ⚠️ NO ENCONTRADO")

    def _parsear_bloque(self, bloque, tipo):
        datos = []
        ptr = 0
        newline = bloque.find(b'\n')
        if newline != -1:
            ptr = newline + 1

        if tipo == 'M':
            while ptr + 14 <= len(bloque):
                try:
                    # Desempaquetamos: i(2b), j(2b), v1(2b), v2(2b), t_global(4b), cs(2b)
                    i, j, v1, v2, t_global, cs = struct.unpack('<4hLh', bloque[ptr:ptr+14])
                    
                    # Replicar la división del tiempo de 32 bits para validar el checksum
                    t_bajo = t_global & 0xFFFF
                    t_alto = (t_global >> 16) & 0xFFFF
                    
                    cs_esperado = (i + j + v1 + v2 + t_bajo + t_alto) & 0xFFFF
                    if cs_esperado > 32767:
                        cs_esperado -= 65536
                        
                    if cs_esperado == cs:
                        datos.append([t_global, i, j, v1, v2])
                        ptr += 14
                    else:
                        ptr += 1
                except:
                    ptr += 1
        else:  # 'I' o 'P'
            while ptr + 37 <= len(bloque):
                paquete = bloque[ptr:ptr+37]
                if sum(paquete[4:36]) & 0xFF == paquete[36]:
                    t, *adcs, _ = struct.unpack('<L16hB', paquete)
                    datos.append([t] + list(adcs))
                    ptr += 37
                else:
                    ptr += 1
        return datos

    def _guardar_csv_final(self, nombre, header, filas, rutina, fecha_py, t_delta):
        with open(nombre, 'w', newline='') as f:
            f.write(f"#Experimento realizado con "+str(self.version)+f" --- Fecha de experimento: {fecha_py}\n")
            f.write(f"# Delay desde comando 'S' (micros): {t_delta}\n")
            f.write(f"# Tarea: {rutina['tipo']} \n")
            if (rutina['tipo']=='M'):
                f.write('# Rserie \t Voltaje \t Ciclos \t Delay \t Tipo \n')
            elif (rutina['tipo']=='I'):
                f.write('# Estado1 \t Estado2 \t Estado3 \t Estado4 \t Estado5 \t Estado6 \t Estado7 \t Estado8 \t Vmax \t Ciclos \t Delay \t Pulsos \t Cota \t Puntos \t Pasos2 \n')
            else:
                f.write('# Estado1 \t Estado2 \t Estado3 \t Estado4 \t Estado5 \t Estado6 \t Estado7 \t Estado8 \t V1 \t C1 \t V2 \t c2 \t Ciclos \t Delay \n')
            f.write(f"# Params: {rutina['params']}\n")
            f.write(f"# Coment: {rutina['coment']}\n")
            f.write("# ------------------------------------------\n")
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(filas)
        print(f"✅ Guardado: {nombre} (Delta T: {t_delta} us)")


def transformar_array(rango, x_input):

    with open("./../Calibracion/R"+str(rango-1)+".pkl", "rb") as f:
        spl = pickle.load(f)
    knots = spl.get_knots()

    xmin = knots[0]
    xmax = knots[-1]

    x_input = np.asarray(x_input)
    x_clip = np.clip(x_input, xmin, xmax)
    y_output = spl(x_clip)
    return y_output

pos=[[1,4],[2,4],[3,4],[4,4],[1,3],[2,3],[3,3],[4,3],[1,2],[2,2],[3,2],[4,2],[1,1],[2,1],[3,1],[4,1]]

lista=[]

for i in range(len(pos)):
    
    for j in range(i+1,len(pos)):
        
        if((pos[i][0]-pos[j][0])**2+(pos[i][1]-pos[j][1])**2)==1:
            lista.append([i+1,j+1])
voltajes=np.zeros(len(lista))
voltajes=np.array([3000,1400,3700,2800,4000,3700,4000,3100,4000,3100,3500,3700,4000,4000,4000,4000,4000,4000,4000,3400,3400,4000,3100,1300])
tiemposp=np.array([100,100,1000,50,10000,1000,10000,100,10000,1000,10000,1000,1000,1000,10000,10000,1000,10000,1000,1000,1000,10000,10000,100])
indices = np.arange(len(lista))
lista=np.array(lista)


for ik3 in range(10):
    np.random.shuffle(indices)
lista=lista[indices]
voltajes=voltajes[indices]
tiemposp=tiemposp[indices]

if __name__ == "__main__":
    ##################################################################################################
    ################################CAMBIAR############################################################
    ###################################################################################################
    
    id_muestra = 'JD1005' 
    nombre = 'A'
    comentario = ''

    ##################################################################################################
    ###################################################################################################
    ###################################################################################################


    # Definimos una ruta ABSOLUTA para tu Raspberry Pi (asumiendo que tu usuario es ia-consofi)
    DIRECTORIO_BASE_LOCAL = "/home/ia-consofi/Desktop/Puma_v2/Resultados" 
    
    # Armamos las rutas de forma segura usando os.path.join
    muestra = os.path.join(DIRECTORIO_BASE_LOCAL, id_muestra)
    ruta_txt = os.path.join(muestra, 'Txt')
    
    # Creamos las carpetas correspondientes
    os.makedirs(ruta_txt, exist_ok=True)
    nw = EstacionBalseiro('/dev/ttyACM0')
    
#     cont=0
#     while(os.path.isfile(muestra+'/Txt/'+str(nombre)+'_'+str(cont)+'.csv')):
#         cont+=1
#     # print(cont)
#     cont_inicial=cont
    
    cont = 0
    if os.path.exists(ruta_txt):
        # Listamos todos los archivos de la carpeta Txt
        archivos = os.listdir(ruta_txt)
        
        numeros = []
        for arch in archivos:
            # Validamos que empiece con el prefijo, tenga el guion bajo y termine en .csv
            if arch.startswith(nombre + "_") and arch.endswith(".csv"):
                try:
                    # 'A_12.csv' -> quitamos '.csv', partimos por '_' y nos quedamos con el número
                    num_str = arch.split(".csv")[0].split("_")[-1]
                    numeros.append(int(num_str))
                except ValueError:
                    # Por si hay algún archivo con formato raro que no tenga un número válido al final
                    continue
        
        if numeros:
            cont = max(numeros) + 1  # El próximo será el máximo absoluto + 1
    # -----------------------------------------------------------

    cont_inicial = cont
    



   
    try:
        ##################################################################################################
        ################################CAMBIAR############################################################
        ###################################################################################################


        

        
        #CrearMapa(tareas,muestra,nombre,cont,RSERIE,VMAPA,#CICLOS,DELAYENTRECICLOS,TIPODEMAPA,comentario)
        #RSERIE 1: 10 M 2: 1 M 3: 100 k 4: 10 k 5: 5 k 6: 1 k 7: 0
        #VMAPA DAC 0-4095 cuentas 4095: 10 V
        #TIPO DE MAPA 1: TODOS CON TODOS ORDEN CRECIENTE
        #DELAYENTRECICLOS en uS
        
        #CreaIV(tareas,muestra,nombre,cont,INPUTS,OUTPUTS,RSERIE,VMAX,CICLOS,DELAYENTRECICLOS,PULSOS,COTA,PUNTOS,PASOS2,comentario)
        #INPUTS Y OUTPUS desde 1 a 16.
        #INPUTS electrodos conectados al DAC en forma de lista [3]: Electrodo 3 conectado a DAC [2,5] Electros 2 y 5 a DAC
        #OUTPUTS electrodos a tierra por medio de RSERIE.Tambien en forma de lista. [1,3]: 1 y 3 conectados a tierra por Rserie El resto estan a 10 M a tierra. 
        #VMAX maximo voltaje en unidades de DAC 0-4095.
        #PULSOS Cantidad de puntos en VMAX
        #COTA limite de activación. Pongo 10 o 20 
        #PUNTOS ANCHO DE ESCALON
        #PASOS2 ANCHO UNA VEZ QUE ACTIVO, POR DEFAULT PONERLO EN 1
        
        #CreaP(tareas,muestra,nombre,cont,INPUTS,OUTPUTS,RSERIE,V1,C1,V2,C2,ciclos,delay,comentario):
        #INPUTS electrodos conectados al DAC en forma de lista [3]: Electrodo 3 conectado a DAC [2,5] Electros 2 y 5 a DAC
        #OUTPUTS electrodos a tierra por medio de RSERIE.Tambien en forma de lista. [1,3]: 1 y 3 conectados a tierra por Rserie El resto estan a 10 M a tierra. 
        #V1 Voltaje de actuación de primer pulso en unidades DAC 
        #C1 Duración del tiempo del primer pulso en puntos
        #V2 Voltaje de actuación de segundo pulso en unidades DAC 
        #C2 Duración del tiempo del segundo pulso en puntos
        
        tareas = []
        tareas,cont= CreaMapa(tareas,muestra,nombre,cont,3,50,1,0,1,comentario)
        

        if(len(tareas)<100):
            nw.ejecutar_secuencia(tareas)
            # time.sleep(60)
        else:
            print("Hay mas de 100 tareas")

        
        # tareas = []
        # tareas,cont= CreaMapa(tareas,muestra,nombre,cont,3,50,5,0,1,comentario)
        # tareas,cont=CreaP(tareas,muestra,nombre,cont,[6],[10],5,4000,100000,0,0,1,0,comentario)
        # tareas,cont= CreaMapa(tareas,muestra,nombre,cont,3,50,100,10000,1,comentario)
        
        # if(len(tareas)<100):
        #     nw.ejecutar_secuencia(tareas)
        #     time.sleep(60)
        # else:
        #     print("Hay mas de 100 tareas")

        
        # rserie=[1,2,3,4,5]
        # tes=[0,1000,1000,10000,100000,100000]
        # te2=[0,10,100,1000]
        # for up in range(2,3):
        #     for up2 in range(1):
        #         for pruebas in range(1):
        #             #  time.sleep(10*60)
                 
        #              # Como 'muestra' ya es la ruta local absoluta completa, la pasamos directamente
        #             CARPETA_MEDICIONES = muestra  
                    
        #             # Usamos 'id_muestra' (ej: 'JD1003') para armar la ruta en la nube
        #             DESTINO_GOOGLE_DRIVE = f"PumaDrive:Puma/Resultados/{id_muestra}"  
                    
        #             subir_a_google_drive(CARPETA_MEDICIONES, DESTINO_GOOGLE_DRIVE, solo_nuevos=True)
        #             for ik3 in range(10):
        #                 np.random.shuffle(indices)
        #             lista=lista[indices]
        #             voltajes=voltajes[indices]
        #             tiemposp=tiemposp[indices]
        #             for i, v2aux, tp in list(zip(lista, voltajes,tiemposp)):
        #                 tareas = []
                    

        #                 tareas,cont= CreaMapa(tareas,muestra,nombre,cont,3,50,5,0,1,comentario)
        #                 tareas,cont=CreaIV(tareas,muestra,nombre,cont,[i[0]],[i[1]],up,4080,1,0,10000,10,1,te2[up2],comentario)

                    
        #                 tareas,cont= CreaMapa(tareas,muestra,nombre,cont,3,50,100,tes[up],1,comentario)
        #                 if(len(tareas)<100):
        #                     nw.ejecutar_secuencia(tareas)
        #                     time.sleep(60)
        #                 else:
        #                     print("Hay mas de 100 tareas")
                    
                      
        
        # Como 'muestra' ya es la ruta local absoluta completa, la pasamos directamente
        CARPETA_MEDICIONES = muestra  
        # Usamos 'id_muestra' (ej: 'JD1003') para armar la ruta en la nube
        DESTINO_GOOGLE_DRIVE = f"PumaDrive:Puma/Resultados/{id_muestra}"  
        subir_a_google_drive(CARPETA_MEDICIONES, DESTINO_GOOGLE_DRIVE, solo_nuevos=True)
        

    ##################################################################################################
    ###################################################################################################
    ###################################################################################################

        
    except Exception as e:
        print(f"💥 Error durante la ejecución: {e}")
        nw.cerrar()
    finally:
        nw.cerrar()
    