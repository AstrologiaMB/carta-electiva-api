import json
import os
from datetime import datetime
from immanuel import charts
from immanuel.const import chart, dignities, calc
from immanuel.classes.serialize import ToJSON
from immanuel.setup import settings
import pandas as pd
import numpy as np
import csv
import sys
#yours
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from settings_astro import *
from .utils.decorators import *

astro_avanzada_settings()

class moonAptitude:
    def __init__(self, dob,lat, lon, act="work"):
        self.dob = dob
        self.lat = lat
        self.lon = lon
        self.activity = act
        
        try:
            subject = charts.Subject(dob, lat, lon)
            self.natal = charts.Natal(subject)
            aspects_json = json.dumps(self.natal.aspects, cls=ToJSON, indent=4)
            self.aspect_json = json.loads(aspects_json)
            objects_json = json.dumps(self.natal.objects, cls=ToJSON, indent=4)
            self.object_json = json.loads(objects_json)
            self.moon_phase = json.loads(json.dumps(self.natal.moon_phase,cls=ToJSON,indent=4))
            # Get moon data silently
            moon_json = json.dumps(self.natal.objects[chart.MOON], cls=ToJSON, indent=4)
        except Exception as e:
            raise ValueError(f"Error creating subject or natal: {str(e)}")
        
    # Funcion para convertir grados a sistema decimal
    @staticmethod
    def dgs_to_dcl(degrees, minutes, seconds):
        dd = float(degrees) + float(minutes) / 60 + float(seconds) / 3600
        return dd
    #Funcion para convertir un string de fecha en objeto datetime
    @staticmethod
    def str_to_dt(datetimestr):
        datetime_str = datetimestr
        datetime_obj = datetime.strptime(datetime_str, '%d/%m/%Y %H:%M')
        return datetime_obj
    
    @staticmethod
    def aspect(degree1, degree2, orb, grado):
        #calculo la diferencia de los dos angulos dados y  calculo el resto de 360 por si el numero es mayor
        diferencia = abs(degree1 - degree2) % 360
        diferencia= min( diferencia, 360-diferencia)
        #para cuando el primer grado es mayor que el segundo
        cond= abs(diferencia - grado) <= orb
        orb = abs(diferencia - grado)
        return cond, grado, orb

    
        #la luna esta en trigono aplicativo a jupiter (19)
    #la luna esta en sextil aplicativo a jupiter (20)
    #la luna esta en conjuncion a jupiter (28)
    def moonJup(self):
        cond_bool = []
        tipo_conjuncion = []
        movimiento= []
        diff_raw = []
        puntos= []
        try:
            dict_jm = self.aspect_json[str(chart.JUPITER)][str(chart.MOON)]
            #veo si la luna esta en trigono aplicativo a jupiter
            c19_1 = dict_jm["aspect"] == 120.0
            c19_2= dict_jm["movement"]["applicative"] or dict_jm["movement"]["exact"]
            if c19_1 and c19_2:
                # Hay trigono aplicativo a Jupiter
                cond_bool.append(True)
                #Tipo de Aspecto
                tipo_conjuncion.append("Trigono")
                #Es Aplicativo
                movimiento.append("Aplicativo")
            else:
                cond_bool.append(False)
                tipo_conjuncion.append(np.nan)
                movimiento.append(np.nan)
            #veo si la luna esta en sextil aplicativo a jupiter
            c20_1 = dict_jm["aspect"] == 60.0
            c20_2= dict_jm["movement"]["applicative"] or dict_jm["movement"]["exact"]
            if c20_1 and c20_2:
                cond_bool.append(True)
                tipo_conjuncion.append("Sextil")
                movimiento.append("Aplicativo")
            else:
                cond_bool.append(False)
                tipo_conjuncion.append(np.nan)
                movimiento.append(np.nan)
            #veo si la luna esta en conjuncion aplicativo a jupiter
            c28 = dict_jm["aspect"] == 0.0
            if c28:
                cond_bool.append(True)
                tipo_conjuncion.append("Conjuncion")
                conjuncion= dict_jm["movement"]["applicative"] or dict_jm["movement"]["exact"]
                movimiento.append( conjuncion)
            else:
                cond_bool.append(False)
                tipo_conjuncion.append(np.nan)
                movimiento.append(np.nan)
        except KeyError:
                for i in range(3):
                    cond_bool.append(False)
                    tipo_conjuncion.append(np.nan)
                    movimiento.append(np.nan)
                    diff_raw.append(np.nan)
        for i in range(3):
            if cond_bool[i]==True:
                # Corrección: Condiciones 29, 31, 33 deben otorgar 2 puntos según CSV
                puntos.append(2)
            else:
                puntos.append(0)
        return cond_bool, tipo_conjuncion, diff_raw, movimiento, puntos

    #la luna esta en trigono aplicativo a venus
    #la luna esta en sextil aplicativo a venus
    #la luna esta en conjuncion a venus (27)
    def moonVen(self):
        cond_bool = []
        tipo_conjuncion = []
        movimiento= []
        diff_raw = [np.nan, np.nan, np.nan]
        puntos= []
        try:
            dict_jm = self.aspect_json[str(chart.VENUS)][str(chart.MOON)]
            #veo si la luna esta en trigono aplicativo a venus
            c19_1 = dict_jm["aspect"] == 120.0
            c19_2= dict_jm["movement"]["applicative"] or dict_jm["movement"]["exact"]
            if c19_1 and c19_2:
                cond_bool.append(True)
                tipo_conjuncion.append("Trigono")
                movimiento.append("Aplicativo")
            else:
                cond_bool.append(False)
                tipo_conjuncion.append(np.nan)
                movimiento.append(np.nan)
            #veo si la luna esta en sextil aplicativo a venus
            c20_1 = dict_jm["aspect"] == 60.0
            c20_2= dict_jm["movement"]["applicative"] or dict_jm["movement"]["exact"]
            if c20_1 and c20_2:
                cond_bool.append(True)
                tipo_conjuncion.append("Sextil")
                movimiento.append("aplicative")
            else:
                cond_bool.append(False)
                tipo_conjuncion.append(np.nan)
                movimiento.append(np.nan)
            #veo si hay conjuncion con venus
            c27 = dict_jm["aspect"] == 0.0
            if c27:
                cond_bool.append(True)
                tipo_conjuncion.append("Conjuncion")
                movimiento.append( dict_jm["movement"]["applicative"] or dict_jm["movement"]["exact"])
            else:
                cond_bool.append(False)
                tipo_conjuncion.append(np.nan)
                movimiento.append(np.nan)
        except KeyError:
                for i in range(3):
                    cond_bool.append(False)
                    tipo_conjuncion.append(np.nan)
                    movimiento.append(np.nan)
        for i in range(3):
            if cond_bool[i]==True:
                # Corrección: Condiciones 30, 32, 34 deben otorgar 2 puntos según CSV
                puntos.append(2)
            else:
                puntos.append(0)
        return cond_bool, tipo_conjuncion, diff_raw, movimiento, puntos

    #condicion aplicativa o separativa entre la luna y el sol (1)
    #la luna esta a una diferencia +8/-8 grados del sol (oposicion aplicativo o separativo)
    #la luna esta en capricornio o escorpio (2)
    def moonSunConj(self):
        cond_bool = []
        tipo_conjuncion = []
        diff_raw = []
        movimiento= []
        # Condicion 1 y 2: Condiciones aspectos entre la luna y el sol
        # Condicion 1: Conjuncion aplicativa y separativa con el sol, orbe 8 grados
        # Condicion 2: Oposicion aplicativa sol, orbe 8 grados
        # Titulos de las condiciones 
        try:
            dict_sm = self.aspect_json[str(chart.SUN)][str(chart.MOON)]
            # Seteo orbe de la condicion 1 y 2
            orb_c1 = 8.0
            # Condiciones de la condicion 1
            c1_1 = dict_sm["aspect"] == 0  # Conjuncion
            c1_2 = (
                abs(
                    moonAptitude.dgs_to_dcl(
                        dict_sm["difference"]["degrees"],
                        dict_sm["difference"]["minutes"],
                        dict_sm["difference"]["seconds"],
                    )
                )
                <= orb_c1
            )
            c1_3 = (dict_sm["movement"]["applicative"] == True) or (dict_sm["movement"]["exact"] == True)
            c1_4 = (dict_sm["movement"]["separative"] == True)  
            # Condiciones de la condicion 2
            c2_1 = dict_sm["aspect"]== 180.0
            # Adjunto informacion que es independiente de aptitud o no.
            for i in range(2):
                tipo_conjuncion.append(dict_sm["type"])
                diff_raw.append(dict_sm["difference"]["raw"])
                if (dict_sm["movement"]["applicative"] or dict_sm["movement"]["exact"]):
                    movimiento.append("Applicative")
                elif (dict_sm["movement"]["separative"]):
                    movimiento.append("Separative")
                else:
                    movimiento.append("Exact")
            # Evaluacion de las condiciones de la condicion 1
            if c1_1 and c1_2 and (c1_3 or c1_4):
                cond_bool.append(True)
            else:
                cond_bool.append(False)

            if c2_1 and c1_2 and (c1_3 or c1_4):
                cond_bool.append(True)  # Luna no apta
            else:
                cond_bool.append(False)  # Luna apta
        except KeyError:
            for i in range(2):
                cond_bool.append(False)
                tipo_conjuncion.append(np.nan)
                diff_raw.append(np.nan)
                movimiento.append(np.nan)
        #condicion si luna esta en capricornio o escorpio (2)
        tipo_conjuncion.append(np.nan)
        diff_raw.append(np.nan)
        c3_1 = self.object_json[str(chart.MOON)]["sign"]["number"] == chart.SCORPIO
        c3_2 = self.object_json[str(chart.MOON)]["sign"]["number"] == chart.CAPRICORN
        if c3_1 or c3_2:
            cond_bool.append(True)  # Luna no apta
            movimiento.append(self.object_json[str(chart.MOON)]["sign"]["name"])
        else:
            cond_bool.append(False)  # Luna apta
            movimiento.append(np.nan)

        return cond_bool, tipo_conjuncion, diff_raw, movimiento
            

    def saving_cond(self, orb):
        # Get the Aspects of Venus/Moon, Jupiter/Moon, from the aspect_json
        moon_aspect = self.aspect_json.get(str(chart.MOON),{})
        venus = moon_aspect.get(str(chart.VENUS),{})
        jupiter = moon_aspect.get(str(chart.JUPITER), {})
        # Define aspect degrees for different types of aspects
        grados = {'Conjuncion': 0.0, 'Trigono': 120.0, 'Sextil': 60.0}

        aspects = []
        for name, i in grados.items():
            # Check if Venus forms an aspect with the Moon
            venus_aspect = venus.get('aspect') == i
            venus_movement = venus.get('movement',{}).get('applicative') or venus.get('movement',{}).get('exact')
            raw_diff_venus = venus.get('difference',{}).get('raw')
            if venus_aspect and venus_movement:
                if raw_diff_venus<orb:
                    # Append relevant information about the aspect if it exists
                    aspects.append((True, 'Venus', raw_diff_venus, name + ' Venus'))
                else:
                    aspects.append((False, 'Venus', raw_diff_venus, name + ' Venus'))

            # Check if Jupiter forms an aspect with the Moon
            jupiter_aspect = jupiter.get('aspect') == i
            jupiter_movement = jupiter.get('movement',{}).get('applicative') or jupiter.get('movement',{}).get('exact')
            raw_diff_jupiter = jupiter.get('difference',{}).get('raw')
            if jupiter_aspect and jupiter_movement:
                if raw_diff_jupiter<orb:
                    # Append relevant information about the aspect if it exists
                    aspects.append((True, 'Jupiter', raw_diff_jupiter, name + ' Jupiter'))
                else:
                    aspects.append((False, 'Jupiter', raw_diff_jupiter, name + ' Jupiter'))

        # If there are any aspects found, return the one with the lowest difference
        if aspects:
            best_aspect = min(aspects, key=lambda x: x[2])
            return best_aspect

        # If no aspects are found, return default values
        return False, np.nan, np.nan, np.nan
    
    # Condicion 3,4,5 y 6: Aspectos entre la Luna y Marte
    # Condicion 3: Cuadratura aplicativa con marte, orbe 10 grados salvo que haya una conjuncion/trigono/sextil aplicativo a Venus o Jupiter y la DIF Luna/Venus OR Dif Luna/Jupiter < DIF Luna/Marte
    # Condicion 4: Oposicion aplicativa con marte, orbe 10 grados salvo que haya una conjuncion/trigono/sextil aplicativo a Venus o Jupiter y la DIF Luna/Venus OR Dif Luna/Jupiter < DIF Luna/Marte
    # Condicion 5: Conjuncion aplicativa con marte, orbe 10 grados  Y la cuspide de la casa 10  esta en Aries o Escorpio
    # Condicion 6: Conjuncion aplicativa con marte, orbe 10 grados salvo que haya una conjuncion/trigono/sextil aplicativo a Venus o Jupiter y la DIF Luna/Venus OR Dif Luna/Jupiter < DIF Luna/Marte
    @print_attributes_on_error
    def moonMarte(self):
        cond_bool = []
        caract = {}
        movimiento = ""
        try:
            dict_mm = self.aspect_json[str(chart.MOON)][str(chart.MARS)]
            # Seteo orbe para relacion luna, marte
            orb_c456 = 10
            # condicion salvo que... (3,4,6)
            # Adjunto info independientemente de la condicion
            tipo_conjuncion = dict_mm["type"]
            caract['tipo_conjuncion'] = tipo_conjuncion
            diff_raw = dict_mm["difference"]["raw"]
            caract['diff_raw'] = diff_raw
            if (dict_mm["movement"]["applicative"] or dict_mm["movement"]["exact"] ):
                movimiento = "applicative"
                caract['movimiento'] = "applicative"
            if (dict_mm["movement"]["separative"]):
                movimiento =movimiento + " " +"separative"
                movimiento = movimiento.strip()
            caract['movimiento'] = movimiento

            # Condiciones de la condicion 3
            c4_1 = dict_mm["aspect"] == 90.0
            orb_mars= abs(dict_mm['difference']['raw'])
            c4_2 = (orb_mars) <= orb_c456
            c4_3 = (dict_mm["movement"]["applicative"]) or (dict_mm["movement"]["exact"])
            c5_1 = dict_mm["aspect"] == 180.0

            # Condiciones de la condicion 5
            c6_1 = dict_mm["aspect"] == 0.0
            cusp_10_info = str(self.natal.houses[2000010]) 
            cusp_10_sign = cusp_10_info.split(' ')[-1]
            c6_2= cusp_10_sign == "Aries"
            c6_3=  cusp_10_sign == "Scorpio"
            
             # Diferencias con Venus y Júpiter
            venus_result = self.saving_cond(orb_mars)
            jupiter_result = self.saving_cond(orb_mars)
            
            caract['asp_ven'], caract['diff_ven'] = (venus_result[3], venus_result[2]) if venus_result[1] == 'Venus' else (np.nan, np.nan)
            caract['asp_jup'], caract['diff_jup'] = (jupiter_result[3], jupiter_result[2]) if jupiter_result[1] == 'Jupiter' else (np.nan, np.nan)

            #condicion 3
            if c4_1 and c4_2 and c4_3:
                resultado= not(self.saving_cond(orb_mars)[0])
                cond_bool.append(resultado)  # Luna no apta
            else:
                cond_bool.append(False)  # Luna apta
            #condicion 4
            if c5_1 and c4_2 and c4_3:
                resultado= not(self.saving_cond(orb_mars)[0])
                cond_bool.append(resultado)  # Luna no apta
            else:
                cond_bool.append(False)  # Luna apta
            #condicion 5
            if c6_1 and c4_2 and c4_3 and not (c6_2 or c6_3):
                cond_bool.append(True)  # Luna no apta
            else:
                cond_bool.append(False)  # Luna apta
            #condicion 6
            if c6_1 and c4_2 and c4_3:
                resultado= not (self.saving_cond(orb_mars)[0])
                cond_bool.append(resultado)  # Luna no apta
            else:
                cond_bool.append(False)  # Luna apta

        except KeyError:
            for i in range(4):
                cond_bool.append(False)
            caract['diff_jup'] = np.nan
            caract['diff_ven'] = np.nan
            caract['asp_jup'] = np.nan
            caract['asp_ven'] = np.nan
            caract['movimiento'] = np.nan
            caract['tipo_conjuncion'] = np.nan
            caract['diff_raw'] = np.nan
        return cond_bool, caract
    

            
    # Condiciones 7,8,9,y 10: Aspecto entre la Luna y Saturno
    # Condicion 7: Cuadratura aplicativa saturno, orbe 10 grados
    # Condicion 8: Oposicion aplicativa saturno, orbe 10 grados
    # Condicion 9: Conjuncion aplicativa saturno, orbe 12 grados
    # la luna tiene una diferencia de 10 grados a saturno (conjuncion aplicativa) salvo que haya una conjuncion/trigono/sextil aplicativo a Venus o Jupiter y la DIF Luna/Venus OR Dif Luna/Jupiter < DIF Luna/Saturno
    
    def moonSat(self):
        cond_bool = []
        caract= {}
        movimiento = ""
        try:
            dict_mm = self.aspect_json[str(chart.MOON)][str(chart.SATURN)]
            # Seteo orbe para relacion luna, sat
            orb_c456 = 10
            # Adjunto info independientemente de la condicion
            tipo_conjuncion = dict_mm["type"]
            caract['tipo_conjuncion'] = tipo_conjuncion
            diff_raw = dict_mm["difference"]["raw"]
            caract['diff_raw'] = diff_raw
            if (dict_mm["movement"]["applicative"] or dict_mm["movement"]["exact"] ):
                movimiento = "applicative"
                caract['movimiento'] = "applicative"
            if (dict_mm["movement"]["separative"]):
                movimiento =movimiento + " " +"separative"
                movimiento = movimiento.strip()
            caract['movimiento'] = movimiento
            # Condiciones de la condicion 7
            c4_1 = dict_mm["aspect"] == 90.0
            orb_sat = (
                abs(
                    moonAptitude.dgs_to_dcl(
                        dict_mm["difference"]["degrees"],
                        dict_mm["difference"]["minutes"],
                        dict_mm["difference"]["seconds"],
                    )
                )   
            )
            c4_2= orb_sat <= orb_c456
            c4_3 = dict_mm["movement"]["applicative"] or dict_mm["movement"]["exact"]
            # Condiciones de la condicion 8
            c5_1 = dict_mm["aspect"] == 180.0
            # Condiciones de la condicion 9
            c6_1 = dict_mm["aspect"] == 0.0
            cusp_10_info = str(self.natal.houses[2000010]) 
            cusp_10_sign = cusp_10_info.split(' ')[-1]
            c6_2= cusp_10_sign == "Capricorn"
            c6_3=  cusp_10_sign == "Aquarius"
           
            # Diferencias con Venus y Júpiter
            venus_result = self.saving_cond(orb_sat)
            jupiter_result = self.saving_cond(orb_sat)
            
            caract['asp_ven'], caract['diff_ven'] = (venus_result[3], venus_result[2]) if venus_result[1] == 'Venus' else (np.nan, np.nan)
            caract['asp_jup'], caract['diff_jup'] = (jupiter_result[3], jupiter_result[2]) if jupiter_result[1] == 'Jupiter' else (np.nan, np.nan)


            #condicion 7
            if c4_1 and c4_2 and c4_3:
                resultado= not (self.saving_cond(orb_sat)[0])
                cond_bool.append(resultado)  # Luna no apta
            else:
                cond_bool.append(False)  # Luna apta
            #condicion 8
            if c5_1 and c4_2 and c4_3:
                resultado= not(self.saving_cond(orb_sat)[0])
                cond_bool.append(resultado)  # Luna no apta
            else:
                cond_bool.append(False)  # Luna apta
            #condicion 9
            if c6_1 and c4_2 and c4_3 and not (c6_2 or c6_3):
                cond_bool.append(True)  # Luna no apta
            else:
                cond_bool.append(False)  # Luna apta
            #condicion 10
            if c6_1 and c4_2 and c4_3:
                resultado= not(self.saving_cond(orb_sat)[0])
                cond_bool.append(resultado)  # Luna no apta
            else:
                cond_bool.append(False)  # Luna apta

        except KeyError:
            for i in range(4):
                cond_bool.append(False)
            caract['diff_jup'] = np.nan
            caract['diff_ven'] = np.nan
            caract['asp_jup'] = np.nan
            caract['asp_ven'] = np.nan
            caract['movimiento'] = np.nan
            caract['tipo_conjuncion'] = np.nan
            caract['diff_raw'] = np.nan
        return cond_bool, caract
    #"v/f", "Tipo Conjuncion", "movimiento", "dif raw", "Aspecto Venus", "Dif Venus", "Aspecto Jup", "Dif Jupiter",
    # Condicion 10: La Luna está peregrina
    def moonPeleg(self):
        cond_bool = []
        tipo_conjuncion = []
        diff_raw = []
        movimiento= []
        if self.object_json[str(chart.MOON)]["dignities"]["peregrine"] == True:
            cond_bool.append(True)
        else:
            cond_bool.append(False)
        tipo_conjuncion.append(np.nan)
        diff_raw.append(np.nan)
        movimiento.append(np.nan)
        return cond_bool,tipo_conjuncion,diff_raw,  movimiento

    # Condicion 12: 29 grados con respecto a Geminis. Exactos.
    def moonGem(self):
        cond_bool = []
        tipo_conjuncion = []
        diff_raw = []
        movimiento= []
        if (
            self.object_json[str(chart.MOON)]["sign"]["number"] == 3
            and self.object_json[str(chart.MOON)]["sign_longitude"]["raw"] > 29.0
            and  self.object_json[str(chart.MOON)]["sign_longitude"]["raw"] < 30.0

        ):
            cond_bool.append(True)
            movimiento.append("Geminis")
        else:
            cond_bool.append(False)
        tipo_conjuncion.append(np.nan)
        diff_raw.append(np.nan)
        movimiento.append(np.nan)
        return cond_bool, tipo_conjuncion,diff_raw, movimiento

    # Condicion 13: Luna vacía de curso
    # La Luna está vacía de curso cuando no forma ningún aspecto aplicativo con Mercurio o Júpiter
    # Sin embargo, hay una excepción importante: si la Luna está en Tauro o Cáncer,
    # NO se considera vacía de curso independientemente de sus aspectos
    def moonEmpty(self):
        cond_bool = False  # False = Luna apta, True = Luna no apta
        tipo_conjuncion = np.nan
        diff_raw = np.nan
        movimiento = np.nan

        # Primero verificamos si la Luna está en Tauro o Cáncer
        # En estos signos, la Luna NUNCA está vacía de curso
        moon_sign = self.object_json[str(chart.MOON)]["sign"]["number"]
        if moon_sign == 2 or moon_sign == 4:  # Tauro = 2, Cáncer = 4
            return cond_bool, tipo_conjuncion, diff_raw, movimiento  # Luna apta
        
        try:
            void = True
            
            # Check Mercury aspects
            mercury_aspects = self.aspect_json.get('4000003', {})
            if str(chart.MOON) in mercury_aspects:
                aspect = mercury_aspects[str(chart.MOON)]
                is_applying = aspect["movement"]["applicative"] or aspect["movement"]["exact"]
                if is_applying:
                    void = False
            
            # Check Jupiter aspects
            jupiter_aspects = self.aspect_json.get('4000006', {})
            if str(chart.MOON) in jupiter_aspects:
                aspect = jupiter_aspects[str(chart.MOON)]
                is_applying = aspect["movement"]["applicative"] or aspect["movement"]["exact"]
                if is_applying:
                    void = False
            
            # Also check aspects from Moon's perspective
            moon_aspects = self.aspect_json.get(str(chart.MOON), {})
            if '4000003' in moon_aspects:  # Mercury
                aspect = moon_aspects['4000003']
                is_applying = aspect["movement"]["applicative"] or aspect["movement"]["exact"]
                if is_applying:
                    void = False
            
            if '4000006' in moon_aspects:  # Jupiter
                aspect = moon_aspects['4000006']
                is_applying = aspect["movement"]["applicative"] or aspect["movement"]["exact"]
                if is_applying:
                    void = False
            cond_bool = void
        except KeyError:
            cond_bool = True
        
        return cond_bool, tipo_conjuncion, diff_raw, movimiento
    
    #La luna esta en la via combusta, entre 15 grados de libra y 15 grados de escorpio (15)
    def moonViaComb(self):
        cond_bool = []
        tipo_conjuncion = []
        diff_raw = []
        movimiento= []
        if (
            self.object_json[str(chart.MOON)]["sign"]["number"] == chart.LIBRA
            and self.object_json[str(chart.MOON)]["sign_longitude"]["raw"] >= 15.0
        ) or (
            self.object_json[str(chart.MOON)]["sign"]["number"] ==  chart.SCORPIO
            and self.object_json[str(chart.MOON)]["sign_longitude"]["raw"] <= 15.0
            ):
            cond_bool.append(True)
            movimiento.append(self.object_json[str(chart.MOON)]["sign"]["name"])
        else:
            cond_bool.append(False)
        tipo_conjuncion.append(np.nan)
        diff_raw.append(np.nan)
        movimiento.append(np.nan)
        return cond_bool, tipo_conjuncion,diff_raw, movimiento

    #SUMO PUNTOS

    #la luna esta en cancer (17)
    #la luna esta en tauro (18)
    def moonIs(self):
        cond_bool = []
        tipo_conjuncion= []
        movimiento = [np.nan, np.nan]
        diff_raw = [np.nan, np.nan]
        puntos= []
        #agrega el signo para cada condicion
        tipo_conjuncion.append( self.object_json[str(chart.MOON)]["sign"]["name"])
        tipo_conjuncion.append( self.object_json[str(chart.MOON)]["sign"]["name"])
        #se fija si la luna esta en cancer (17)
        if (
            self.object_json[str(chart.MOON)]["sign"]["number"] == 4
        ):
            cond_bool.append(True) 
            puntos.append(1)
        else: 
            cond_bool.append(False) 
            puntos.append(0)

        #se fija si la luna esta en tauro (18)
        if (
            self.object_json[str(chart.MOON)]["sign"]["number"] == 2
        ):
            cond_bool.append(True) 
            puntos.append(1)
        else: 
            cond_bool.append(False)
            puntos.append(0)
        return cond_bool, tipo_conjuncion,diff_raw,  movimiento, puntos

    #la luna esta creciente
    def moonCres(self):
        cond_bool = []
        tipo_conjuncion = []
        movimiento= [np.nan]
        diff_raw = [np.nan]
        puntos=[]
        tipo_conjuncion.append(self.moon_phase["formatted"])
        growing_phases = [
    'Waxing Crescent',
    'First Quarter',
    'Waxing Gibbous'
]
        if self.moon_phase["formatted"] in growing_phases:
            cond_bool.append(True)
            puntos.append(1)
        else:
            cond_bool.append(False)
            puntos.append(0)
        
        return  cond_bool, tipo_conjuncion,diff_raw,  movimiento, puntos


    #la luna esta en trigono aplicativo al sol 
    #la luna esta en sextil aplicativo al sol
    def moonSun(self):
        cond_bool = []
        tipo_conjuncion = []
        movimiento= []
        diff_raw = [np.nan, np.nan]
        puntos= []
        # Instancio para armar la data
        try:
            dict_sm = self.aspect_json[str(chart.SUN)][str(chart.MOON)]
            #24: veo si la luna esta en trigono aplicativo al sol
            c19_1 = dict_sm["aspect"] == 120.0
            c19_2= dict_sm["movement"]["applicative"] or dict_sm["movement"]["exact"]
            if c19_1 and c19_2:
                cond_bool.append(True)
                tipo_conjuncion.append("Trigono")
                movimiento.append("Aplicativo")
            else:
                cond_bool.append(False)
                tipo_conjuncion.append(np.nan)
                movimiento.append(np.nan)
            #25: veo si la luna esta en sextil aplicativo al sol
            c20_1 = dict_sm["aspect"] == 60.0
            c20_2= dict_sm["movement"]["applicative"] or dict_sm["movement"]["exact"]
            if c20_1 and c20_2:
                cond_bool.append(True)
                tipo_conjuncion.append("Sextil")
                movimiento.append("Aplicativo")
            else:
                cond_bool.append(False)
                tipo_conjuncion.append(np.nan)
                movimiento.append(np.nan)
        except KeyError:
                for i in range(2):
                    cond_bool.append(False)
                    tipo_conjuncion.append(np.nan)
                    movimiento.append(np.nan)
        for i in range(2):
            if cond_bool[i]==True:
                puntos.append(1)
            else:
                puntos.append(0)
        return cond_bool, tipo_conjuncion, diff_raw, movimiento, puntos

    #la luna esta en casa 5 o 9 o 10 o 11
    def moonHouse(self):
        cond_bool = []
        tipo_conjuncion = []
        movimiento= [np.nan]
        diff_raw = [np.nan]
        puntos= []
        # Instancio para armar la data
        subject = charts.Subject(self.dob, self.lat, self.lon)
        natal = charts.Natal(subject)
        house= natal.house_for(natal.objects[4000002])
        if (house== 2000005 or house==2000005 or house==2000009 or house==2000010 or house==2000011):
            cond_bool.append(True)
            tipo_conjuncion.append(house-2000000)
        else: 
            cond_bool.append(False)
            tipo_conjuncion.append(house-2000000)
        if cond_bool==[True]:
           
            puntos.append(1)
        else:
            puntos.append(0)
        return cond_bool, tipo_conjuncion, diff_raw, movimiento, puntos

    #la luna esta en trigono aplicativo al regente del ASC 
    #la luna esta en sextil aplicativa al regente del ASC 
    #la luna esta en conjuncion aplicativa al regente del ASC 
    def moonAscRuler(self):
        signo_ascendente = self.object_json["3000001"]["sign"]["number"]
        regente= dignities.TRADITIONAL_RULERSHIPS[signo_ascendente]
        cond_bool= []
        tipo_conjuncion = []
        movimiento= []
        diff_raw = [np.nan, np.nan]
        puntos= []
        try:
                dict_jm = self.aspect_json[str(regente)][str(chart.MOON)]
                #veo si la luna esta en trigono aplicativo al regente del ASC
                c19_1 = dict_jm["aspect"] == 120.0
                c19_2= dict_jm["movement"]["applicative"] or dict_jm["movement"]["exact"]
                if c19_1 and c19_2:
                    cond_bool.append(True)
                    tipo_conjuncion.append("Trigono")
                    movimiento.append("Aplicativo")
                else:
                    cond_bool.append(False)
                    tipo_conjuncion.append(np.nan)
                    movimiento.append(np.nan)
                #veo si la luna esta en sextil aplicativo al regente del ASC
                c20_1 = dict_jm["aspect"] == 60.0
                c20_2= dict_jm["movement"]["applicative"] or dict_jm["movement"]["exact"]
                if c20_1 and c20_2:
                    cond_bool.append(True)
                    tipo_conjuncion.append("Sextil")
                    movimiento.append("Aplicativo")
                else:
                    cond_bool.append(False)
                    tipo_conjuncion.append(np.nan)
                    movimiento.append(np.nan)
                #veo si la luna esta en conjuncion aplicativa al regente del ASC
                c21_1 = dict_jm["aspect"] == 0.0
                c21_2= dict_jm["movement"]["applicative"] or dict_jm["movement"]["exact"]
                if c21_1 and c21_2:
                    cond_bool.append(True)
                    tipo_conjuncion.append("Conjuncion")
                    movimiento.append("Aplicativo")
                else:
                    cond_bool.append(False)
                    tipo_conjuncion.append(np.nan)
                    movimiento.append(np.nan)
        except KeyError:
                    for i in range(3):
                        cond_bool.append(False)
                        tipo_conjuncion.append(np.nan)
                        movimiento.append(np.nan)
        for i in range(3):
            if cond_bool[i]==True:
           
                puntos.append(1)
            else:
                puntos.append(0)
        return cond_bool, tipo_conjuncion, diff_raw, movimiento, puntos
    

    #la luna esta en trigno aplicativo al regente de la casa 10 (32)
    #la luna esta en sextil aplicativa al regente de la casa 10 (34)
    def moonHouseReg(self):
        subject = charts.Subject(self.dob, self.lat, self.lon)
        natal = charts.Natal(subject)

        signos= { "ARIES" :1,
        "TAURUS" : 2,
        "GEMINI" : 3,
        "CANCER" : 4,
        "LEO" : 5,
        "VIRGO" : 6,
        "LIBRA" : 7,
        "SCORPIO" :8,
        "SAGITTARIUS" :9,
        "CAPRICORN" : 10,
        "AQUARIUS" : 11,
        "PISCES" :12 }

        signo=str(natal.houses[2000010]).split()[-1].upper()
        numero= signos[signo]
        regente= dignities.TRADITIONAL_RULERSHIPS[numero]
        cond_bool= []
        tipo_conjuncion = []
        movimiento= [np.nan, np.nan]
        diff_raw = [np.nan, np.nan]
        puntos= []
        try:
                dict_jm = self.aspect_json[str(regente)][str(chart.MOON)]
                #veo si la luna esta en trigono aplicativo al regente de la casa 10
                c19_1 = dict_jm["aspect"] == 120.0
                c19_2= dict_jm["movement"]["applicative"] or dict_jm["movement"]["exact"]
                if c19_1 and c19_2:
                    cond_bool.append(True)
                    tipo_conjuncion.append("Trigono")
                    movimiento.append("Aplicativo")
                else:
                    cond_bool.append(False)
                    tipo_conjuncion.append(np.nan)
                    movimiento.append(np.nan)
                #veo si la luna esta en sextil aplicativo al regente de la casa 10
                c2 = dict_jm["aspect"] == 60.0
                c2_b= dict_jm["movement"]["applicative"] or dict_jm["movement"]["exact"]
                if c2 and c2_b:
                    cond_bool.append(True)
                    tipo_conjuncion.append("Sextil")
                    movimiento.append("Aplicativo")
                else:
                    cond_bool.append(False)
                    tipo_conjuncion.append(np.nan)
                    movimiento.append(np.nan)     

                #veo si la luna esta en conjuncion aplicativo al regente de la casa 10
                c2 = dict_jm["aspect"] == 0.0
                c2_b= dict_jm["movement"]["applicative"] or dict_jm["movement"]["exact"]
                if c2 and c2_b:
                    cond_bool.append(True)
                    tipo_conjuncion.append("Conjuncion")
                    movimiento.append("Aplicativo")
                else:
                    cond_bool.append(False)
                    tipo_conjuncion.append(np.nan)
                    movimiento.append(np.nan)        
        except KeyError:
                    for i in range(3):
                        cond_bool.append(False)
                        tipo_conjuncion.append(np.nan)
                        movimiento.append(np.nan)
        for i in range(3):
            if cond_bool[i]==True:
           
                puntos.append(1)
            else:
                puntos.append(0)
        return cond_bool, tipo_conjuncion, diff_raw, movimiento, puntos

   

    def generate_df(self):
        # Obtener los resultados de las funciones
        moonSunConj= self.moonSunConj()
        moonMarte= self.moonMarte()
        moonSat= self.moonSat()
        moonPeleg= self.moonPeleg()
        moonGem= self.moonGem()
        moonEmpty= self.moonEmpty()
        moonViaComb= self.moonViaComb()
        moonIs= self.moonIs()
        moonCres= self.moonCres()
        moonJup= self.moonJup()
        moonVen= self.moonVen()
        moonSun= self.moonSun()
        moonHouse= self.moonHouse()
        ascendant_aspects = self.moonAscRuler()
        house_aspects = self.moonHouseReg()
        
        headers=['cond_num','descripcion','v/f','Tipo Conjuncion','movimiento','dif raw','Aspecto Venus','Dif Venus','Aspecto Jup','Dif Jupiter','Puntos']
        cond_num=[1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34]
        condicion_descripcion=[{1:'la luna tiene una diferencia +8/-8  del sol (conjunción aplicativa o separativa)'},{2:'la luna esta en capricornio o escorpio '},{3:'la luna tiene una diferencia +10/-10 de marte (cuadratura aplicativa) salvo que haya una conjuncion/trigono/sextil aplicativo a Venus o Jupiter y la DIF Luna/Venus OR Dif Luna/Jupiter < DIF Luna/Marte'},{4:'la luna tiene una diferencia de 10 grados  a marte (oposicion aplicativa) salvo que haya una conjuncion/trigono/sextil aplicativo a Venus o Jupiter y la DIF Luna/Venus OR Dif Luna/Jupiter < DIF Luna/Marte'},{5:'la luna tiene una diferencia de a 10 grados a marte (conjuncion aplicativa) Y la cuspide de la casa 10  esta en Aries o Escorpio'},{6:'la luna tiene una diferencia de 10 grados  a marte (conjuncion aplicativa) salvo que haya una conjuncion/trigono/sextil aplicativo a Venus o Jupiter y la DIF Luna/Venus OR Dif Luna/Jupiter < DIF Luna/Marte'},{7:'la luna tiene una diferencia +10/-10  a saturno (cuadratura aplicativa) salvo que haya una conjuncion/trigono/sextil aplicativo a Venus o Jupiter y la DIF Luna/Venus OR Dif Luna/Jupiter < DIF Luna/Saturno'},{8:'la luna tiene una diferencia de 10 grados a saturno (oposicion aplicativa) salvo que haya una conjuncion/trigono/sextil aplicativo a Venus o Jupiter y la DIF Luna/Venus OR Dif Luna/Jupiter < DIF Luna/Saturno'},{9:'la luna tiene una diferencia de 10 grados a saturno (conjuncion aplicativa) Y en la cuspide de la casa 10 esta capricornio o acuario'},{10:'la luna tiene una diferencia de 10 grados a saturno (conjuncion aplicativa) salvo que haya una conjuncion/trigono/sextil aplicativo a Venus o Jupiter y la DIF Luna/Venus OR Dif Luna/Jupiter < DIF Luna/Saturno'},{11:'la luna esta a una diferencia +8/-8 grados del sol (oposicion aplicativo o separativo)'},{12:'29 grados con respecto a Geminis. Exactos.'},{13:'La Luna esta peregrina'},{14:'Luna vacía de curso'},{15:'La luna esta en la via combusta, entre 15 grados de libra y 15 grados de escorpio'},{17:'la luna esta en cancer '},{18:'la luna esta en tauro '},{19:'La luna esta creciente'},{20:'la luna esta en trigono aplicativo a jupiter'},{21:'la luna esta en sextil aplicativo a jupiter'},{22:'la luna esta en trigono aplicativo a venus'},{23:'la luna esta en sextil aplicativo a venus'},{24:'la luna esta en trigono aplicativo al sol'},{25:'la luna esta en sextil aplicativo al sol'},{26:'la luna esta en casa 5 o 9 o 10 o 11'},{27:'La luna esta en conjuncion a venus (27)'},{28:'la luna esta en conjuncion a jupiter'},{29:'Luna en conjuncion aplicativo al regente del ASC'},{30:'Luna en conjuncion aplicativa al regente de la casa 10'},{31:'Luna en sextil aplicativo al regente del ASC'},{32:'Luna en sextil aplicativo al regente de la casa 10'},{33:'Luna en trígono aplicativo al regente del ASC'},{34:'Luna en trígono aplicativo al regente de la casa 10'}]
        resultado=[{1: moonSunConj[0][0]},{2: moonSunConj[0][2]},{3: moonMarte[0][0]},{4: moonMarte[0][1]},{5: moonMarte[0][2]},{6: moonMarte[0][3]},{7: moonSat[0][0]},{8: moonSat[0][1]},{9: moonSat[0][2]},{10: moonSat[0][3]},{11: moonSunConj[0][1]},{12: moonGem[0][0]},{13: moonPeleg[0][0]},{14: moonEmpty[0]},{15: moonViaComb[0][0]},{17: moonIs[0][0]},{18: moonIs[0][1]},{19: moonCres[0][0]},{20: moonJup[0][0]},{21: moonJup[0][1]},{22: moonVen[0][0]},{23: moonVen[0][1]},{24: moonSun[0][0]},{25: moonSun[0][1]},{26: moonHouse[0][0]},{27: moonVen[0][2]},{28: moonJup[0][2]},{29: ascendant_aspects[0][2]},{30: house_aspects[0][2]},{31: ascendant_aspects[0][1]},{32: house_aspects[0][1]},{33: ascendant_aspects[0][0]},{34: house_aspects[0][0]}]
        tipo_conjuncion=[{1: moonSunConj[1][0]},{2: moonSunConj[1][2]},{3:moonMarte[1]['tipo_conjuncion']},{4: moonMarte[1]['tipo_conjuncion']},{5: moonMarte[1]['tipo_conjuncion']},{6:moonMarte[1]['tipo_conjuncion']},{7:moonSat[1]['tipo_conjuncion']},{8: moonSat[1]['tipo_conjuncion']},{9: moonSat[1]['tipo_conjuncion']},{10:moonSat[1]['tipo_conjuncion']},{11: moonSunConj[1][1]},{12: moonGem[1][0]},{13: moonPeleg[1][0]},{14: moonEmpty[1]},{15: moonViaComb[1][0]},{17: moonIs[1][0]},{18: moonIs[1][1]},{19: moonCres[1][0]},{20: moonJup[1][0]},{21: moonJup[1][1]},{22: moonVen[1][0]},{23: moonVen[1][1]},{24: moonSun[1][0]},{25: moonSun[1][1]},{26: moonHouse[1][0]},{27: moonVen[1][2]},{28: moonJup[1][2]},{29: ascendant_aspects[1][2]},{30: house_aspects[1][2]},{31: ascendant_aspects[1][1]},{32: house_aspects[1][1]},{33: ascendant_aspects[1][0]},{34: house_aspects[1][0]}]
        movimiento=[{1: moonSunConj[3][0]},{2: moonSunConj[3][2]},{3: moonMarte[1]['movimiento']},{4: moonMarte[1]['movimiento']},{5: moonMarte[1]['movimiento']},{6: moonMarte[1]['movimiento']},{7: moonSat[1]['movimiento']},{8: moonSat[1]['movimiento']},{9: moonSat[1]['movimiento']},{10: moonSat[1]['movimiento']},{11: moonSunConj[3][1]},{12: moonGem[3][0]},{13: moonPeleg[3][0]},{14: moonEmpty[3]},{15: moonViaComb[3][0]},{17: moonIs[3][0]},{18: moonIs[3][1]},{19: moonCres[3][0]},{20: moonJup[3][0]},{21: moonJup[3][1]},{22: moonVen[3][0]},{23: moonVen[3][1]},{24: moonSun[3][0]},{25: moonSun[3][1]},{26: moonHouse[3][0]},{27: moonVen[3][2]},{28: moonJup[3][2]},{29: ascendant_aspects[3][2]},{30: house_aspects[3][2]},{31: ascendant_aspects[3][1]},{32: house_aspects[3][1]},{33: ascendant_aspects[3][0]},{34: house_aspects[3][0]}]
        dif_raw=[{1: moonSunConj[2][0]},{2: moonSunConj[2][2]},{3: moonMarte[1]['diff_raw']},{4: moonMarte[1]['diff_raw']},{5: moonMarte[1]['diff_raw']},{6: moonMarte[1]['diff_raw']},{7: moonSat[1]['diff_raw']},{8: moonSat[1]['diff_raw']},{9: moonSat[1]['diff_raw']},{10: moonSat[1]['diff_raw']},{11: moonSunConj[2][1]},{12: moonGem[2][0]},{13: moonPeleg[2][0]},{14: moonGem[2]},{15: moonViaComb[2][0]},{17: np.nan},{18: np.nan},{19: np.nan},{20: np.nan},{21: np.nan},{22: np.nan},{23: np.nan},{24: np.nan},{25: np.nan},{26: np.nan},{27: np.nan},{28: np.nan},{29: np.nan},{30: np.nan},{31: np.nan},{32: np.nan},{33: np.nan},{34: np.nan}]
        aspecto_venus=[{1: np.nan},{2: np.nan},{3: moonMarte[1]['asp_ven']},{4: moonMarte[1]['asp_ven']},{5: moonMarte[1]['asp_ven']},{6: moonMarte[1]['asp_ven']},{7: moonSat[1]['asp_ven']},{8: moonSat[1]['asp_ven']},{9: moonSat[1]['asp_ven']},{10: moonSat[1]['asp_ven']},{11: np.nan},{12: np.nan},{13: np.nan},{14: np.nan},{15: np.nan},{17: np.nan},{18: np.nan},{19: np.nan},{20: np.nan},{21: np.nan},{22: np.nan},{23: np.nan},{24: np.nan},{25: np.nan},{26: np.nan},{27: np.nan},{28: np.nan},{29:np.nan},{30: np.nan},{31:np.nan},{32: np.nan},{33: np.nan},{34: np.nan}]
        dif_venus=[{1: np.nan},{2: np.nan},{3: moonMarte[1]['diff_ven']},{4: moonMarte[1]['diff_ven']},{5: moonMarte[1]['diff_ven']},{6: moonMarte[1]['diff_ven']},{7: moonSat[1]['diff_ven']},{8: moonSat[1]['diff_ven']},{9: moonSat[1]['diff_ven']},{10: moonSat[1]['diff_ven']},{11: np.nan},{12: np.nan},{13: np.nan},{14: np.nan},{15: np.nan},{17: np.nan},{18: np.nan},{19: np.nan},{20: np.nan},{21: np.nan},{22: np.nan},{23: np.nan},{24: np.nan},{25: np.nan},{26: np.nan},{27: np.nan},{28: np.nan},{29: np.nan},{30:np.nan},{31: np.nan},{32:np.nan},{33:np.nan},{34:np.nan}]
        aspecto_jupiter=[{1: np.nan},{2: np.nan},{3: moonMarte[1]['asp_jup']},{4: moonMarte[1]['asp_jup']},{5: moonMarte[1]['asp_jup']},{6: moonMarte[1]['asp_jup']},{7: moonSat[1]['asp_jup']},{8: moonSat[1]['asp_jup']},{9: moonSat[1]['asp_jup']},{10: moonSat[1]['asp_jup']},{11: np.nan},{12: np.nan},{13: np.nan},{14: np.nan},{15: np.nan},{17: np.nan},{18: np.nan},{19: np.nan},{20:np.nan},{21: np.nan},{22: np.nan},{23: np.nan},{24: np.nan},{25: np.nan},{26: np.nan},{27: np.nan},{28: np.nan},{29: np.nan},{30: np.nan},{31: np.nan},{32:np.nan},{33: np.nan},{34: np.nan}]
        dif_jupiter=[{1: np.nan},{2: np.nan},{3:moonMarte[1]['diff_jup']},{4:moonMarte[1]['diff_jup']},{5:moonMarte[1]['diff_jup']},{6:moonMarte[1]['diff_jup']},{7:moonSat[1]['diff_jup']},{8:moonSat[1]['diff_jup']},{9:moonSat[1]['diff_jup']},{10:moonSat[1]['diff_jup']},{11: np.nan},{12: np.nan},{13: np.nan},{14: np.nan},{15: np.nan},{17:np.nan},{18:np.nan},{19:np.nan},{20: np.nan},{21: np.nan},{22: np.nan},{23:np.nan},{24:np.nan},{25: np.nan},{26:np.nan},{27:np.nan},{28:np.nan},{29: np.nan},{30: np.nan},{31: np.nan},{32: np.nan},{33: np.nan},{34: np.nan}]
        puntos=[{1: np.nan},{2: np.nan},{3: np.nan},{4: np.nan},{5: np.nan},{6: np.nan},{7: np.nan},{8: np.nan},{9: np.nan},{10: np.nan},{11: np.nan},{12: np.nan},{13: np.nan},{14: np.nan},{15: np.nan},{17: moonIs[4][0]},{18: moonIs[4][1]},{19: moonCres[4][0]},{20: moonJup[4][0]},{21:moonJup[4][1]},{22:moonVen[4][0]},{23: moonVen[4][1]},{24: moonSun[4][0]},{25:moonSun[4][1]},{26: moonHouse[4][0]},{27: moonVen[4][2]},{28: moonJup[4][2]},{29: ascendant_aspects[4][2]},{30: house_aspects[4][2]},{31: ascendant_aspects[4][1]},{32: house_aspects[4][1]},{33: ascendant_aspects[4][0]},{34: house_aspects[4][0]}]
        data = []
        for i in range(0,len(cond_num)):
            num = int(cond_num[i])
            row = [
                num,
                condicion_descripcion[i].get(num),
                resultado[i].get(num),
                tipo_conjuncion[i].get(num),
                movimiento[i].get(num),
                dif_raw[i].get(num),
                aspecto_venus[i].get(num),
                dif_venus[i].get(num),
                aspecto_jupiter[i].get(num),
                dif_jupiter[i].get(num),
                puntos[i].get(num)
            ]
            data.append(row)
        
            # Crear el DataFrame
        df = pd.DataFrame(data, columns=headers)
        # Calcular el total de la columna "Puntos", omitiendo np.nan
        total_puntos = df["Puntos"].dropna().sum()
        # Máximo corregido: 20 puntos (6 condiciones × 1 punto + 6 condiciones × 2 puntos)
        cuenta= 20.0
        
        # Agregar una nueva fila al final con el puntaje total
        total_row = [35,"Puntaje total para la Luna para B(n)", np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, total_puntos]
        df.loc[len(df)] = total_row

        # Agregar una nueva fila al final con el porcentaje
        perc_row = [36,"Puntaje total para la Luna para B(n) en %", np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, total_puntos/cuenta]
        df.loc[len(df)] = perc_row

        df.rename(columns={"v/f": "resultado", "Puntos":"puntos"}, inplace=True)
        #Cambio 1 y 0 por Verdadero y Falso
        # Replace 1 with 'TRUE' and 0 with 'FALSE' in the 'resultado' column
        df['resultado'] = df['resultado'].replace({True: 'TRUE', False: 'FALSE'})
        return df
    def generate_xlsx(self,path):
        try:
            parameters = {
                "Date": self.dob,
                "Latitude": self.lat,
                "Longitude": self.lon
            }
            # Escribir el DataFrame en un archivo de Excel
            with pd.ExcelWriter(path, engine='xlsxwriter') as writer:
                # Escribir los parámetros como filas separadas en una hoja "Parameters"
                parameters_df = pd.DataFrame.from_dict(parameters, orient='index', columns=['Value'])
                parameters_df.to_excel(writer, sheet_name='Parameters', startrow=1, header=False)

                # Escribir el DataFrame en una hoja "Data"
                df = self.generate_df()
                df.to_excel(writer, sheet_name='Data', index=False)


            print(f"Excel generado exitosamente en: {path}")
        except Exception as e:
            print(f"An error occurred: {e}")
    def write_to_csv(self, path, filename="output.csv"):
        try:
            entire_path = os.path.join(path,filename)
            parameters = {
                    "Date": self.dob,
                    "Latitude": self.lat,
                    "Longitude": self.lon
                }
            #Convierto el diccionario en un dataframe
            parameters_df = pd.DataFrame(parameters,index=[0])
            #Escribo el df a un csv
            parameters_df.to_csv(entire_path, index=False,encoding='utf-8')
            #Append two lines
            with open(entire_path,mode = 'a', encoding='utf-8') as f:
                f.write('\n\n')
            
            #Append the existing df, to the csv file 
            df = self.generate_df()
            df.to_csv(entire_path, mode='a', index = False, encoding='utf-8')
            print(f"CSV generado exitosamente en {entire_path}")
        except Exception as e:
            print(f"An error occurred: {e}")
