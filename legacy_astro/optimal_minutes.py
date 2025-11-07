
#standard
import json
from datetime import datetime
import csv
import sys
import os
#third party
from immanuel import charts
from immanuel.const import chart, dignities
from immanuel.classes.serialize import ToJSON
from immanuel.setup import settings
import pandas as pd
import numpy as np
from immanuel import charts
from immanuel.const import chart, dignities
from immanuel.classes.serialize import ToJSON
from immanuel.setup import settings
import pandas as pd
import numpy as np
import csv
#yours
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from legacy_astro.settings_astro import astro_avanzada_settings

#run your settings
astro_avanzada_settings()


class optimalMinutes:
    def __init__(self, dob,lat, lon, act="work"):
        self.dob = dob
        self.lat = lat
        self.lon = lon
       
        try:
            self.subject = charts.Subject(dob, lat, lon)
            self.natal = charts.Natal(self.subject)
            self.aspects_json = json.dumps(self.natal.aspects, cls=ToJSON, indent=4)
            self.aspect_json = json.loads(self.aspects_json)
            self.objects_json = json.dumps(self.natal.objects, cls=ToJSON, indent=4)
            self.object_json = json.loads(self.objects_json)
            self.asc_sign = self.natal.objects[chart.ASC].sign.number
            self.asc_ruler = str(dignities.TRADITIONAL_RULERSHIPS[self.asc_sign])
            self.house_10_sign = self.natal.houses[chart.HOUSE10].sign.number
            self.r10=str(dignities.TRADITIONAL_RULERSHIPS[self.house_10_sign])
            self.r10_obj = self.object_json[self.r10]

        except Exception as e:
            raise ValueError(f"Error creating subject or natal: {str(e)}")
        
    @staticmethod
    def dgs_to_dcl(degrees, minutes, seconds):
        dd = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
        return dd

    def calc_aspect(self, planet1, planet2, orb, aspect, save= False):
        if save== False:
            try:
                planet_aspect =  self.aspect_json[str(planet1)][str(planet2)]
                if int(planet_aspect['aspect'])==aspect and (planet_aspect['movement']['applicative'] or planet_aspect['movement']['exact']):
                    if orb != 0:
                        result = planet_aspect['difference']['raw'] <= orb
                    else:
                        result= True
                else:
                    result=False
            except KeyError:
                result=False
        else:
            result= np.nan
        return result
    
    def saving_conditions(self):
        save = {}
        #Params
        dign_r10 = self.r10_obj['dignities']
        dign_rAsc = self.object_json[self.asc_ruler]['dignities']
        #Condiciones 37 que salvan
        c_37_2= dign_rAsc['ruler']
        c_37_3 = dign_rAsc['exalted']
        c_37_4= dign_rAsc['term_ruler'] and  dign_rAsc['triplicity_ruler']
        c_37_5= dign_rAsc['triplicity_ruler'] and dign_rAsc['face_ruler']
        c_37_6= dign_r10['term_ruler'] and dign_r10['face_ruler']
        save[2]=not(c_37_2 or c_37_3 or c_37_4 or c_37_5 or c_37_6)
        return save

  
    def final_table(self):
        condiciones_descripciones = {
            1: "El regente del ASC está en aspecto de conjunción aplicativa o sextil aplicativa o trígono aplicativa al regente de la Casa 10",
            2: "Si el regente del ASC está en cuadratura aplicativa al regente de la Casa 10 y está en dignidad por domicilio, exaltación, triplicidad/término, o triplicidad/decanato",
            3: "El Sol está en la Casa 10 o hasta 5 grados antes de la Casa 10",
            4: "Júpiter está en la Casa 10 o hasta 5 grados antes de la Casa 10",
            5: "La Luna está en la Casa 10 o hasta 5 grados antes de la Casa 10",
        }

        resultados = []

        # Condición 1:
        grados = {'Conjuncion': 0.0, 'Trigono': 120.0, 'Sextil': 60.0}
        try:
            es_aspecto = False
            for name, grado in grados.items():
                es_aspecto_i = self.calc_aspect(self.asc_ruler, self.r10, 0, grado)
                if es_aspecto_i:
                    es_aspecto= True
                    resultados.append({
                        "cond_num": 1,
                        "descripcion": condiciones_descripciones[1],
                        "resultado": True,
                        "Tipo de Aspecto": name,
                        "Movimiento": "Aplicativo",
                        "puntos": 2
                    })
            if es_aspecto== False:
                resultados.append({
                    "cond_num": 1,
                    "descripcion": condiciones_descripciones[1],
                    "resultado": False,
                    "Tipo de Aspecto": np.nan,
                    "Movimiento": np.nan,
                    "puntos": 0
                })
        except Exception as e:
            resultados.append({
                "cond_num": 1,
                "descripcion": condiciones_descripciones[1],
                "resultado": False,
                "Tipo de Aspecto": np.nan,
                "Movimiento": np.nan,
                "puntos": 0
            })

        # Condición 2
        try:
            cuadratura = self.calc_aspect(self.asc_ruler, self.r10, orb=0, aspect=90.0, save=self.saving_conditions())
            puntos = 1 if cuadratura else 0.5
            resultados.append({
                "cond_num": 2,
                "descripcion": condiciones_descripciones[2],
                "resultado": True if puntos > 0 else False,
                "Regentes": f"{self.asc_ruler} y {self.r10}",
                "Tipo de Aspecto": "Cuadratura" if cuadratura else np.nan,
                "Movimiento": "Aplicativo" if cuadratura else np.nan,
                "puntos": puntos
            })
        except Exception as e:
            resultados.append({
                "cond_num": 2,
                "descripcion": condiciones_descripciones[2],
                "resultado": False,
                "Regentes": f"{self.asc_ruler} y {self.r10}",
                "Tipo de Aspecto": np.nan,
                "Movimiento": np.nan,
                "puntos": 0
            })

        # Definir los planetas y sus respectivas condiciones
        planetas = [
            {"planeta": chart.SUN, "condicion_index": 3, "puntos": 2},
            {"planeta": chart.JUPITER, "condicion_index": 4, "puntos": 1},
            {"planeta": chart.MOON, "condicion_index": 5, "puntos": 2}
        ]


        # Verificar las condiciones de los planetas en la Casa 10
        for atributo in planetas:
            try:
                # Obtener la información del planeta
                id_planeta= atributo["planeta"]
                planet_house = self.natal.objects[id_planeta].house.number
                planet_house = self.natal.objects[id_planeta].house.number
                planet_degree = self.object_json[str(id_planeta)]['longitude']['raw']
                
                house_start_degree = self.natal.houses[chart.HOUSE10].longitude.raw
                house_start_degree_minus_5 = (house_start_degree - 5) % 360

                # Verificar si el planeta está en Casa 10 o en Casa 9 cerca de Casa 10 (menos 5 grados)
                en_casa10 = planet_house == 10 or (planet_house == 9 and planet_degree >= house_start_degree_minus_5)
                puntos = atributo["puntos"] if en_casa10 else 0

                # Agregar los resultados
                resultados.append({
                    "cond_num": atributo["condicion_index"],
                    "descripcion": condiciones_descripciones[atributo["condicion_index"]],
                    "resultado": en_casa10,
                    "Regentes": f"{self.asc_ruler} y {self.r10}",
                    "Tipo de Aspecto": np.nan,
                    "Movimiento": np.nan,
                    "puntos": puntos
                })

            except Exception as e:
                # En caso de error, se maneja la excepción y se asigna False al resultado
                resultados.append({
                    "cond_num": atributo["condicion_index"],
                    "descripcion": condiciones_descripciones[atributo["condicion_index"]],
                    "resultado": False,
                    "Regentes": f"{self.asc_ruler} y {self.r10}",
                    "Tipo de Aspecto": np.nan,
                    "Movimiento": np.nan,
                    "puntos": 0
                })


        # Calculamos el puntaje total
        total_puntaje = sum(row["puntos"] for row in resultados if isinstance(row["puntos"], (int, float)))
        #maximo puntaje
        max_puntos = 7.0
        total_puntaje_porcentaje = (total_puntaje/max_puntos)

        # Agregamos las filas del puntaje total
        resultados.append({
            "cond_num": np.nan,
            "descripcion": "Total Puntaje combinacion positiva para la carta B(n)",
            "resultado": np.nan,
            "Regentes": np.nan,
            "Tipo de Aspecto": np.nan,
            "movimiento": np.nan,
            "puntos": total_puntaje
        })

        resultados.append({
            "cond_num": np.nan,
            "descripcion": "Total Puntaje combinacion positiva para la carta B(n) en %",
            "resultado": np.nan,
            "Regentes": np.nan,
            "Tipo de Aspecto": np.nan,
            "movimiento": np.nan,
            "puntos": total_puntaje_porcentaje
        })

        df = pd.DataFrame(resultados)
        return df
    
    '''
    CODIGO ANTERIOR
    # El regente del ASC y el regente de la Casa 10 esten en aspecto de conjuncion  aplicativa o sextil aplicativa o trigono aplicativa
    def aspect(self):
        resultado = []
        regentes = [self.asc_ruler, self.r10]
        tipo_conjuncion = []
        movimiento = []
        puntos = []
        try:
            grados= {'Conjuncion': 0.0, 'Trigono': 120.0, 'Sextil': 60.0, 'Cuadratura':90.0}
            for name, grado in grados.items():
                # Calculamos si hay aspecto aplicativo entre el ASC y la Casa 10
                if grado== 90.0:
                    es_aspecto = self.calc_aspect(self.asc_ruler, self.r10, settings.planet_orbs[grado], grado, save= True)
                else:
                    es_aspecto = self.calc_aspect(self.asc_ruler, self.r10, settings.planet_orbs[grado], grado)
                # Si hay aspecto, se guarda el tipo y los puntos correspondientes
                if es_aspecto:
                    resultado.append(True)
                    tipo_conjuncion.append(name)
                    movimiento.append("Aplicativo")
                else:
                    resultado.append(False)
                    tipo_conjuncion.append(np.nan)
                    movimiento.append(np.nan)

        except KeyError:
            resultado.append(False)
            tipo_conjuncion.append(np.nan)
            movimiento.append(np.nan)
            puntos.append(0)

        if True in resultado:
            index = resultado.index(True)  # Usamos el primer aspecto aplicativo válido
        else:
            index = 0

        row_aspect_1 = {
                "cond_num": 1,
                "Condicion": 'El regente del ASC y el regente de la Casa 10 esten en aspecto de conjuncion  aplicativa o sextil aplicativa o trigono aplicativa',
                "resultado": resultado[index],
                "Reg Casa 10/Casa": f"{regentes[0]} y {regentes[1]}",
                "Tipo de Aspecto": tipo_conjuncion[index],
                "Aplicativo": movimiento[index],
                "puntos": puntos[index]
            }
        


        return row_aspect_1

    # el Sol esta en la casa 10 o hasta 5 grados antes de la casa 10
    # Jupiter esta en la casa 10 o hasta 5 grados antes de la casa 10
    # Luna esta en la casa 10 o hasta 5 grados antes de la casa 10
    def house10(self):
        table = []

        condiciones= ["el Sol esta en la casa 10 o hasta 5 grados antes de la casa 10",
                      "Jupiter esta en la casa 10 o hasta 5 grados antes de la casa 10",
                      "Luna esta en la casa 10 o hasta 5 grados antes de la casa 10"]
        
        try:
            
            planetas = [
                (chart.SUN),
                (chart.JUPITER),
                (chart.MOON)
            ]

            for i, id_planeta in enumerate(planetas) :
                planet_house = self.natal.objects[id_planeta].house.number
                planet_degree = self.object_json[str(id_planeta)]['longitude']['raw']
                

                house_start_degree = self.natal.houses[2000010].longitude.raw
                house_start_degree_minus_5 = (house_start_degree - 5) % 360

                row = {
                    "cond_num": i+3,
                    "Condicion": condiciones[i],  # Condición correspondiente a cada planeta
                    "resultado": None,
                    "Reg Casa 10/Casa": planet_house,
                    "Tipo de Aspecto": None,
                    "Aplicativo": None,
                    "puntos": 0
                }

                if planet_house == 10 or (planet_house == 9 and planet_degree >= house_start_degree_minus_5):
                    row["resultado"] = True
                    row["puntos"] = 2
                else:
                    row["resultado"] = False

                table.append(row)

        except KeyError:
            for i in planetas:
                row = {
                    "cond_num": 1,
                    "Condicion": condiciones[i],
                    "resultado": False,
                    "Reg Casa 10/Casa": None,
                    "Tipo de Aspecto": None,
                    "Aplicativo": None,
                    "puntos": 0
                }
                table.append(row)

        return table

    def final_table(self):
        row_aspect= self.aspect()
        house10_resultados = self.house10()
        table = []        

        table.append(row_aspect)
       
        table.extend(house10_resultados)


        # Calculamos el puntaje total
        total_puntaje = sum(row["puntos"] for row in table if row["puntos"] is not None)
        max_puntos = 7.0
        total_puntaje_porcentaje = (total_puntaje / max_puntos) 

        # Agregamos las filas del puntaje total
        table.append({
            "cond_num": len(table)+1,
            "Condicion": "Total Puntaje combinacion positiva para la carta B(n)",
            "Aplicativo": None,
            "resultado": None,
            "Reg Casa 10/Casa": None,
            "Tipo de Aspecto": None,
            "puntos": total_puntaje
        })

        table.append({
            "cond_num": len(table)+2,
            "Condicion": "Total Puntaje combinacion positiva para la carta B(n) en %",
            "resultado": None,
            "Reg Casa 10/Casa": None,
            "Tipo de Aspecto": None,
            "Aplicativo": None,
            "puntos": total_puntaje_porcentaje
        })
        df = pd.DataFrame(table)
        return df

      '''
