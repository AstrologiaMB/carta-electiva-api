
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


class negativeMinutes:
    def __init__(self, dob_a, lat_a, lon_a, dob_bn, lat_bn, lon_bn,act="work"):
        self.dob_a = dob_a
        self.lat_a = lat_a
        self.lon_a = lon_a
        self.dob_bn = dob_bn
        self.lat_bn = lat_bn
        self.lon_bn = lon_bn
        self.act = act
       
        try:
             
            # carta b(n)
            self.subject_bn = charts.Subject(dob_bn, lat_bn, lon_bn)
            self.natal_bn = charts.Natal(self.subject_bn)
            self.aspects_json_bn = json.dumps(self.natal_bn.aspects, cls=ToJSON, indent=4)
            self.aspect_json_bn = json.loads(self.aspects_json_bn)
            self.objects_json_bn = json.dumps(self.natal_bn.objects, cls=ToJSON, indent=4)
            self.object_json_bn = json.loads(self.objects_json_bn)
            self.asc_sign_bn = self.natal_bn.objects[chart.ASC].sign.number
            self.asc_ruler_bn = str(dignities.TRADITIONAL_RULERSHIPS[self.asc_sign_bn])
            self.house_10_sign_bn = self.natal_bn.houses[chart.HOUSE10].sign.number
            self.r10_bn = str(dignities.TRADITIONAL_RULERSHIPS[self.house_10_sign_bn])
            
            # carta natal a 
            self.subject_a = charts.Subject(dob_a, lat_a, lon_a)
            self.natal_a = charts.Natal(self.subject_a)
            self.aspects_json_a = json.dumps(self.natal_a.aspects, cls=ToJSON, indent=4)
            self.aspect_json_a = json.loads(self.aspects_json_a)
            self.objects_json_a = json.dumps(self.natal_a.objects, cls=ToJSON, indent=4)
            self.object_json_a = json.loads(self.objects_json_a)
            self.asc_sign_a = self.natal_a.objects[chart.ASC].sign.number
            self.asc_ruler_a = str(dignities.TRADITIONAL_RULERSHIPS[self.asc_sign_a])
            self.house_10_sign_a = self.natal_a.houses[chart.HOUSE10].sign.number
            self.r10_a = str(dignities.TRADITIONAL_RULERSHIPS[self.house_10_sign_a])

            
        except Exception as e:
            raise ValueError(f"Error creating subject or natal: {str(e)}")



    def negative(self):
        sat_house = self.object_json_bn[str(chart.SATURN)]["house"]["number"]
        mar_house = self.object_json_bn[str(chart.MARS)]["house"]["number"]
        mar_sign = self.object_json_bn[str(chart.MARS)]["sign"]["number"]

        # Creo la tabla
        table = [
            {"cond_num": 1,"descripcion": "Si el ASC de la Carta natal A estรก en Capricornio o Acuario ir a 5 (no analizo 2 y 3)", "V/F": None, "Signo/Casa": None, "puntos": 0},
            {"cond_num": 2,"descripcion": "Saturno estรก en la casa 10", "V/F": None, "Signo/Casa": None, "puntos": 0},
            {"cond_num": 3,"descripcion": "Saturno estรก en el ASC", "V/F": None, "Signo/Casa": None, "puntos": 0},
            {"cond_num": 5,"descripcion": "Si Marte rige el ASC de la carta natal A ir a 8 (no analizo 6 y 7)", "V/F": None, "Nota": "Planeta regente de ASC", "puntos": 0},
            {"cond_num": 6,"descripcion": "Marte estรก en la casa 10", "V/F": None, "Signo/Casa": None, "puntos": 0},
            {"cond_num": 7,"descripcion": "Marte estรก en el ASC", "V/F": None, "Signo/Casa": None, "puntos": 0},
            {"cond_num": None,"descripcion": "Total puntaje combinaciรณn negativos para B(n)", "V/F": None, "Signo/Casa": "X", "puntos": None},
            {"cond_num": None,"descripcion": "Total puntaje combinaciรณn negativos para B(n) en %", "V/F": None, "Signo/Casa": "%", "puntos": None},
        ]

        # Completo la tabla segรบn los datos
        # Si el ASC de la Carta natal A estรก en Capricornio o Acuario ir a 5 (no analizo 2 y 3)
        if self.asc_sign_a in [chart.AQUARIUS, chart.CAPRICORN]:  
            table[0]["V/F"] = True
            table[0]["puntos"] = -1
        
        else:
            table[0]["V/F"] = False
            # Saturno estรก en la casa 10
            table[1]["V/F"] = sat_house == 10
            # Saturno estรก en el ASC
            try:
                table[2]["V/F"] = self.natal_bn.aspects[chart.ASC][chart.SATURN].aspect == 0.0
            except:
                table[2]["V/F"] = False

        # Si Marte rige el ASC de la carta natal A ir a 8 (no analizo 6 y 7)
        if self.asc_ruler_a == str(chart.MARS):
            table[3]["V/F"] = True
        
        else:
            table[3]["V/F"] = False
            # Marte estรก en la casa 10
            table[4]["V/F"] = mar_house == 10
            # Marte estรก en el ASC
            try:
                table[5]["V/F"] = self.natal_bn.aspects[chart.ASC][chart.MARS].aspect == 0.0
            except:
                table[5]["V/F"] = False

        # Asigno -1 a "puntos" donde "V/F" es True
        for row in table:
            if row["V/F"] == True:
                row["puntos"] = -1

        # Calculo puntos
        negative_points = sum([-1 if row["V/F"] == True else 0 for row in table])
        max_puntos = -2.0
        negative_percentage = (negative_points / max_puntos)
        table[6]["puntos"] = negative_points
        table[7]["puntos"] = negative_percentage

        df = pd.DataFrame(table)
        df.rename(columns={"V/F": "resultado"}, inplace=True)
    
        return df
