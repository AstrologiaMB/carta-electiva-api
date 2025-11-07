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
#yours
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from legacy_astro.settings_astro import astro_avanzada_settings

#run your settings
astro_avanzada_settings()

class rulershipConditions:
    def __init__(self, dob, lat, lon, act="work"):
        self.dob = dob
        self.lat = lat
        self.lon = lon
        self.activity = act
        try:
            self.subject = charts.Subject(dob, lat, lon)
            self.natal = charts.Natal(self.subject)
            aspects_json = json.dumps(self.natal.aspects, cls=ToJSON, indent=4)
            self.aspect_json = json.loads(aspects_json)
            objects_json = json.dumps(self.natal.objects, cls=ToJSON, indent=4)
            self.object_json = json.loads(objects_json)
        except Exception as e:
            raise ValueError(f"Error creating subject or natal: {str(e)}")
        self.asc_sign = self.natal.objects[chart.ASC].sign.number
        self.asc_ruler = str(dignities.TRADITIONAL_RULERSHIPS[self.asc_sign])
        self.asc_ruler_object = self.object_json[self.asc_ruler]
        self.houses = json.loads(json.dumps(self.natal.houses, cls = ToJSON, indent = 4))
        self.aspects_ruler = self.aspect_json.get(self.asc_ruler,{})
        self.house_10_sign = self.natal.houses[chart.HOUSE10].sign.number
        self.ruler_10=dignities.TRADITIONAL_RULERSHIPS[self.house_10_sign]
    def ruler_characteristics(self, *args):
        caracteristicas = {}
        # Solo agarro la info del regente del ascendente
        asc_obj = self.asc_ruler_object
        # Solo agarro la info de dignidades del regente del ascendente
        dignidades = self.asc_ruler_object['dignities']
        #Agarro el numero de casa del ascendente
        casa = int(asc_obj['house']['number'])
        if 1 not in args:
            caracteristicas[1] = dignidades['detriment']
        if 2 not in args:
            caracteristicas[2] = dignidades['fall']
        if 3 not in args:
            caracteristicas[3] = dignidades['peregrine']
        if 4 not in args:
            caracteristicas[4] = asc_obj['movement']['retrograde']
        if 5 not in args:
            caracteristicas[5] = casa == 6
        if 6 not in args:
            caracteristicas[6] = casa == 8
        if 7 not in args:
            caracteristicas[7] = casa == 12
        if 19 not in args:
            caracteristicas[19] = True if str(chart.MERCURY) == self.asc_ruler and abs(asc_obj['speed']) < 0.667 else False
        if 20 not in args:
            caracteristicas[20] = True if str(chart.VENUS) == self.asc_ruler and abs(asc_obj['speed']) < 0.583 else False
        if 21 not in args:
            caracteristicas[21] = True if str(chart.MARS) == self.asc_ruler and abs(asc_obj['speed']) < 0.283 else False
        if 22 not in args:
            caracteristicas[22] = True if str(chart.JUPITER) == self.asc_ruler and abs(asc_obj['speed']) < 0.042 else False
        if 23 not in args:
            caracteristicas[23] = True if str(chart.SATURN) == self.asc_ruler and abs(asc_obj['speed']) < 0.017 else False
        if 25 not in args:
            caracteristicas[25] = dignidades['ruler']
        if 26 not in args:
            caracteristicas[26] = dignidades['exalted']
        if 27 not in args:
            caracteristicas[27]= dignidades['triplicity_ruler']
        if 28 not in args:
            caracteristicas[28]= dignidades['term_ruler']
        if 29 not in args:
            caracteristicas[29]= asc_obj['movement']['direct']
        if 30 not in args:
            caracteristicas[30] = abs(asc_obj['longitude']['raw']-self.object_json[str(chart.SUN)]['longitude']['raw'])>17.0
        if 31 not in args:
            caracteristicas[31] = casa == 1
        if 32 not in args:
            caracteristicas[32] = casa == 10
        if 33 not in args:
            caracteristicas[33] = casa == 11
        if 34 not in args:
            caracteristicas[34] = casa == 9
        if 35 not in args:
            caracteristicas[35] = casa == 5
        if 42 not in args:
            caracteristicas[42] = str(chart.MERCURY) == self.asc_ruler and 0.067 <= abs(asc_obj['speed']) <= 1.333
        if 43 not in args:
            caracteristicas[43] = str(chart.MERCURY) == self.asc_ruler and 1.333 < abs(asc_obj['speed'])
        if 44 not in args:
            caracteristicas[44] = str(chart.VENUS) == self.asc_ruler and 0.583 <= abs(asc_obj['speed']) <= 0.833
        if 45 not in args:
            caracteristicas[45] = str(chart.VENUS) == self.asc_ruler and 0.833 < abs(asc_obj['speed'])
        if 46 not in args:
            caracteristicas[46] = str(chart.MARS) == self.asc_ruler and 0.283 <= abs(asc_obj['speed']) <= 0.417
        if 47 not in args:
            caracteristicas[47] = str(chart.MARS) == self.asc_ruler and 0.417 < abs(asc_obj['speed'])
        if 48 not in args:
            caracteristicas[48] = str(chart.JUPITER) == self.asc_ruler and 0.042 <= abs(asc_obj['speed']) <= 0.067
        if 49 not in args:
            caracteristicas[49] = str(chart.JUPITER) == self.asc_ruler and 0.067 < abs(asc_obj['speed'])
        if 50 not in args:
            caracteristicas[50] = str(chart.SATURN) == self.asc_ruler and 0.017 <= abs(asc_obj['speed']) <= 0.028
        if 51 not in args:
            caracteristicas[51] = str(chart.SATURN) == self.asc_ruler and 0.028 < abs(asc_obj['speed'])
        
        return caracteristicas
    def saving_conditions(self):
        save = {}
        #Signos Casa 10
        signo_casa_10 = self.houses[str(chart.HOUSE10)]['sign']['number']
        key_8 = 8
        save[key_8] = signo_casa_10 in [chart.ARIES,chart.SCORPIO]
        key_9 = 9
        save[key_9] = signo_casa_10 in [chart.CAPRICORN,chart.AQUARIUS]
        return save
    
    def check_aspect(self,cond_number, planet2,aspect,save=False,orb=0):
        result ={}
        #Keys result: planeta, aspecto, movimiento, numero de condicion
        result['planeta']=planet2
        if save or self.asc_ruler==str(planet2):
            result[cond_number]=np.nan
            return result
        try:
            planet_aspect = self.aspects_ruler[str(planet2)]
            if int(planet_aspect['aspect'])==aspect and (planet_aspect['movement']['applicative'] or planet_aspect['movement']['exact']):
                result['aspecto']=aspect
                result['movimiento']='Aplicativo'
                if orb != 0:
                    result[cond_number] = planet_aspect['difference']['raw'] <= orb
                else:
                    result[cond_number] = True
            else:
                result[cond_number]=False
                result['aspecto']=int(planet_aspect['aspect'])
                result['movimiento']= 'Aplicativo' if (planet_aspect['movement']['applicative'] or planet_aspect['movement']['exact']) else 'Separativo'
            return result
        except KeyError:
            result[cond_number]=False
            return result
    def aspects_conditions(self,*args):
        results = {}
        #chequeo_aspectos_keys = ['cond_number','planeta2','aspect','save','orb']
        condiciones = {
            8:{'planet2':chart.MARS,'aspect':0,'save':self.saving_conditions()[8]},
            9:{'planet2':chart.SATURN,'aspect':0,'save':self.saving_conditions()[9]},
            10:{'planet2':chart.MARS,'aspect':90},
            11:{'planet2':chart.SATURN,'aspect':90},
            12:{'planet2':chart.MARS,'aspect':180},
            13:{'planet2':chart.SATURN,'aspect':180},
            14:{'planet2':chart.SUN,'aspect':0,'orb':8},
            15:{'planet2':self.ruler_10,'aspect':90},
            16:{'planet2':self.ruler_10,'aspect':180},
            36:{'planet2':chart.JUPITER,'aspect':120},
            37:{'planet2':chart.VENUS,'aspect':120},
            38:{'planet2':chart.VENUS,'aspect':60},
            39:{'planet2':chart.JUPITER,'aspect':60},
            40:{'planet2':chart.VENUS,'aspect':0},
            41:{'planet2':chart.JUPITER,'aspect':0}}
        for i, arguments in condiciones.items():
            if i not in args:
                orb = arguments.get('orb',0)
                save = arguments.get('save',False)
                result = self.check_aspect(cond_number=i,planet2=arguments['planet2'],aspect=arguments['aspect'],save=save,orb=orb)
                results[i] = result
        return results
    def titles_table(self):
        titulos = {
1:'el regente del ASC esta en exilio/detriment',
2:'el regente del ASC esta en su caida/fall',
3:'el regente del ASC esta peregrino/peregrine',
4:'el regente del ASC esta retrogrado/retrograde',
5:'el regente del ASC esta en casa 6',
6:'el regente del ASC esta en casa 8',
7:'el regente del ASC esta en casa 12',
8:'el regente del ASC esta en conjuncion aplicativa a marte, no considerar esta situacion  si la casa 10 este Aries o Escorpio',
9:'el regente del ASC esta en conjuncion aplicativa a saturno, no considerar esta situacion si  la casa 10 este Capricornio o Acuario',
10:'el regente del ASC esta en cuadratura aplicativa a marte',
11:'el regente del ASC esta en cuadratura aplicativa a saturno',
12:'el regente del ASC esta en oposicion aplicativa a marte',
13:'el regente del ASC esta en oposicion aplicativa a saturno',
14:'el regente del ASC esta a menos de 8 grados del sol (combusto) aspecto conjuncion',
15:'el regente del ASC en cuadratura aplicativa al regente de la casa 10',
16:'el regente del ASC en oposicion aplicativa al regente de la casa 10',
17:'el regente de la casa 10 en cuadratura aplicativa al regente del ASC',
18:'el regente de la casa 10 en oposicion aplicativa al regente del ASC',
19:'si Mercurio es el regente del ASC y su velocidad (SPEED) es menor a  0.667 grados decimales (40 minutos sexagesimal)',
20:'Si Venus es el regente del ASC y su velocidad es menor a 0.583 grados decimales (35 minutos sexagesimal)',
21:'Si Marte es el regente del ASC y su velocidad es menor a 0.283 grados decimales (17 minutos sexagesimal)',
22:'Si Jupiter es el regente del ASC y su velocidad es menor a 0.042 grados decimales (2 minutos 30 segundos sexagesimal)',
23:'Si Saturno es el regente del ASC y su velocidad es menor a 0.017 grados decimales (1 minutos sexagesimal)',
24:'Sumo Puntos',
25:'el regente del ASC en su domicilio/ruler',
26:'el regente del ASC en su exaltacion/exalted',
27:'el regente del ASC en triplicidad/triplicity_ruler',
28:'el regente del ASC en su termino/termino_ruler',
29:'el regente del ASC este directo/direct',
30:'el regente del ASC este a mas de 17 grados del sol ',
31:'el regente del ASC este en la casa 1',
32:'el regente del ASC este en la casa 10',
33:'el regente del ASC este en la casa 11',
34:'el regente del ASC este en la casa 9',
35:'el regente del ASC este en la casa 5',
36:'el regente del ASC trigono aplicativo a jupiter',
37:'el regente del ASC trigono aplicativo a venus',
38:'el regente del ASC sextil  aplicativo a venus',
39:'el regente del ASC sextil  aplicativo a jupiter',
40:'el regente del ASC conjuncion aplicativo a venus',
41:'el regente del ASC conjuncion aplicativo a Jupiter',
42:'si Mercurio es el regente del ASC y su velocidad (SPEED) esta entre 0.067 y 1,333 grados decimales (40 y 80 minutos sexagesimales)',
43:'si Mercurio es el regente del ASC y su velocidad (SPEED) es mayor a 1,333 grados decimales (80 minutos de grado)',
44:'si Venus es el regente del ASC y su velocidad (SPEED) esta entre 0,583 y 0,833 grados decimales (35 y 50 minutos de grado)',
45:'si Venus es el regente del ASC y su velocidad (SPEED) es mayor a 0,833 grados decimales (50 minutos de grado)',
46:'si Marte es el regente del ASC y su velocidad (SPEED) esta entre 0,283 y 0,417 grados decimales (17 y 25 minutos de grado)',
47:'si Marte es el regente del ASC y su velocidad (SPEED) es mayor a 0,417 grados decimales  (25 minutos de grado)',
48:'si Jupiter es el regente del ASC y su velocidad (SPEED) esta entre 0.042 y 0.067 grados decimales y (2,5 y 4 minutos de grado)',
49:'si Jupiter es el regente del ASC y su velocidad (SPEED) es mayor a  0,067 grados decimales (4 minutos de grado)',
50:'si Saturno es el regente del ASC y su velocidad (SPEED) esta entre 0,017 y 0,028 grados decimales (1 y 1  minutos y 40 segundos de grado)',
51:'si Saturno es el regente del ASC y su velocidad (SPEED) es mayor a 0,028 grados decimales (1 minutos de grado y 40 segundos)',
52:'Puntaje total Regente del ASC para B(n)',
53:'Puntaje total Regente del ASC para B(n) en %'
}
        return titulos
    def calc_points(self,cond_num,si_cumple,si_no_cumple, tipo):
        if tipo == 'caracteristica':
            result = self.ruler_characteristics()
            points = si_cumple if result[cond_num] else si_no_cumple
        else:
            result = self.aspects_conditions()
            points = si_cumple if result[cond_num][cond_num] else si_no_cumple
        return points
    def cond_points(self):
        resultados = {}
        condiciones_con_puntos = {
25:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
26:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
27:{'si_cumple':0.5,'si_no_cumple':0,'tipo':'caracteristica'},
28:{'si_cumple':0.5,'si_no_cumple':0,'tipo':'caracteristica'},
29:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
30:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
31:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
32:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
33:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
34:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
35:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
36:{'si_cumple':1,'si_no_cumple':0,'tipo':'aspecto'},
37:{'si_cumple':1,'si_no_cumple':0,'tipo':'aspecto'},
38:{'si_cumple':1,'si_no_cumple':0,'tipo':'aspecto'},
39:{'si_cumple':1,'si_no_cumple':0,'tipo':'aspecto'},
40:{'si_cumple':1,'si_no_cumple':0,'tipo':'aspecto'},
41:{'si_cumple':1,'si_no_cumple':0,'tipo':'aspecto'},
42:{'si_cumple':-1,'si_no_cumple':0,'tipo':'caracteristica'},
43:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
44:{'si_cumple':-1,'si_no_cumple':0,'tipo':'caracteristica'},
45:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
46:{'si_cumple':-1,'si_no_cumple':0,'tipo':'caracteristica'},
47:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
48:{'si_cumple':-1,'si_no_cumple':0,'tipo':'caracteristica'},
49:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
50:{'si_cumple':-1,'si_no_cumple':0,'tipo':'caracteristica'},
51:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'}
}
        for i, condiciones in condiciones_con_puntos.items():
            resultados[i]=self.calc_points(i,condiciones['si_cumple'],condiciones['si_no_cumple'],condiciones['tipo'])
        return resultados, condiciones_con_puntos
    def merge_data(self, *args):
        #Inicializo una lista vacia para appendear las filas
        data = []
        
        #Loopeo por todas las rows hasta la ultima con condicion. Despues appendeo las de resumen
        for i in range(1,52):
            if i not in args:
        #Inicializo la fila
                row = {
        'cond_num': i,
        'description': self.titles_table().get(i, 'Unknown'),
        'Resultado': self.ruler_characteristics().get(i, self.aspects_conditions().get(i, {}).get(i, np.nan)),
        'Reg ASC o Casa 10': self.asc_ruler_object['name'] + " y " + self.object_json[str(self.ruler_10)]['name'] if i in range(15,19) else self.asc_ruler_object['name'],
        'Tipo Aspecto/Casa': int(self.asc_ruler_object['house']['number']) if i in range(5,8) else self.aspects_conditions().get(i, {}).get('aspecto', np.nan),
        'Movimiento': self.aspects_conditions().get(i, {}).get('movimiento', np.nan),
        'Dignidad/Casa': self.asc_ruler_object['dignities']['formatted'] if i in range(1,5) or i in range(25,30) else self.houses[str(chart.HOUSE10)]['sign']['name']  if i in range(8,10) else np.nan,
        'Speed': abs(self.asc_ruler_object['speed']) if i in range(19,24) or i in range(42,52) else abs(self.asc_ruler_object['longitude']['raw']-self.object_json[str(chart.SUN)]['longitude']['raw']) if i ==30 else np.nan,
        'Puntos': self.cond_points()[0].get(i, np.nan)
    }
                data.append(row)
        df = pd.DataFrame(data)
        max_puntos = 7.0
        total_puntos = df["Puntos"].dropna().sum()
        last_cond_num = df['cond_num'].max()
            # Append the two additional rows
        df.loc[len(df)] = {
        'cond_num': last_cond_num+1,
        'descripcion': "Puntaje total para el Regente del ASC B(n)",
        'Puntos': total_puntos
        }
    
        df.loc[len(df)] = {
        'cond_num': last_cond_num+2,
        'descripcion': "Puntaje total para el Regente del ASC B(n) en %",
        'Puntos': total_puntos / max_puntos
        }

        df.rename(columns={"Resultado": "resultado", "description": "descripcion", "Puntos":"puntos"}, inplace=True)
        
        return df
