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

class rulershipTen:
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
        self.house_10_sign = self.natal.houses[chart.HOUSE10].sign.number
        self.r10=str(dignities.TRADITIONAL_RULERSHIPS[self.house_10_sign])
        self.r10_obj = self.object_json[self.r10]
        self.houses = json.loads(json.dumps(self.natal.houses, cls = ToJSON, indent = 4))
        self.r10_asp = self.aspect_json.get(self.r10,{})
    #Ascendente en Aries o Ascendente en Capricornio o Acuario.
    def saving_conditions(self):
        save = {}
        keys = [8,9,12,36]
        #Params
        in_aries = [chart.ARIES]
        in_capricorn_aquarius = [chart.CAPRICORN,chart.AQUARIUS]
        dign_r10 = self.r10_obj['dignities']
        dign_rAsc = self.object_json[self.asc_ruler]['dignities']
        #Primeras 3 condiciones salvadoras
        save[keys[0]]=self.asc_sign in in_aries
        save[keys[1]]=self.asc_sign in in_capricorn_aquarius
        save[keys[2]]=self.asc_sign in in_aries
        #Condiciones 36 que salvan
        c_36_2= dign_r10['ruler'] or dign_r10['exalted']
        c_36_3= dign_r10['term_ruler'] and  dign_r10['triplicity_ruler']
        c_36_4= dign_r10['triplicity_ruler'] and dign_r10['face_ruler']
        c_36_5= dign_rAsc['triplicity_ruler'] and dign_rAsc['face_ruler']
        c_36_save = c_36_2 or c_36_3 or c_36_4 or c_36_5
        save[keys[3]] = c_36_save
        return save

    #Evaluacion de todas las condiciones.
    def caracteristicas(self):
        results = {}
        condiciones_dignidades = {
            1:'detriment',
            2:'fall',
            3:'peregrine',
            18:'ruler',
            19:'exalted',
            20:'triplicity_ruler',
            21:'term_ruler'}
        #dignidades regente casa 10
        dignidades = self.r10_obj['dignities']
        #caracteristica/dignidades
        for i, item in condiciones_dignidades.items():
            results[i]=dignidades[item]
        #caracteristica/casa
        condiciones_casas = {
            5:6,
            6:8,
            7:12,
            24:1,
            25:10,
            26:11,
            27:9,
            28:5
            }
        r10_casa = int(self.r10_obj['house']['number'])
        for i, item in condiciones_casas.items():
            results[i]= r10_casa == item
        #el regente de la casa 10 este directo
        results[22] = self.r10_obj['movement']['direct']
        #el regente de la casa 10 esta retrogrado
        results[4] = self.r10_obj['movement']['retrograde']
        #el regente de la casa 10 este a mas de 17 grados del sol
        results[23] = abs(self.r10_obj['longitude']['raw']-self.object_json[str(chart.SUN)]['longitude']['raw'])>17.0
        return results
    #Funcion para aspectos
    def check_aspect(self,cond_number, planet2,aspect,save=False,orb=0,planet1=None, movement=0):

        if planet1 is None:
            planet1 = self.r10
        result ={}
        #Keys result: planeta, aspecto, movimiento, numero de condicion
        result['planeta']=planet2
        if save or self.r10==str(planet2):
            result[cond_number]=np.nan
            return result
        try:
            planet_aspect = self.aspect_json[planet1][str(planet2)]
            if movement == 1:
                if int(planet_aspect['aspect'])==aspect:
                    result['aspecto']= int(planet_aspect['aspect'])
                    result['movimiento']=planet_aspect['movement']['formatted']
                    if orb != 0:
                        result[cond_number] = planet_aspect['difference']['raw'] <= orb
                    else:
                        result[cond_number] = True
            else:
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
            8:{'planet2':chart.MARS,'aspect':0,'save':self.saving_conditions()[8], 'movement': 0},
            9:{'planet2':chart.SATURN,'aspect':0,'save':self.saving_conditions()[9],  'movement': 0},
            10:{'planet2':chart.MARS,'aspect':90,'movement': 0},
            11:{'planet2':chart.SATURN,'aspect':90,'movement': 0},
            12:{'planet2':chart.MARS,'aspect':180, 'save':self.saving_conditions()[12],'movement': 0},
            13:{'planet2':chart.SATURN,'aspect':180,'movement': 0},
            14:{'planet2':chart.SUN,'aspect':0,'orb':8,'movement': 1},
            15:{'planet2':self.asc_ruler,'aspect':90,'movement': 1},
            16:{'planet2':self.asc_ruler,'aspect':90,'movement': 1},
            29:{'planet2':chart.JUPITER,'aspect':120,'movement': 0},
            30:{'planet2':chart.VENUS,'aspect':120,'movement': 0},
            31:{'planet2':chart.VENUS,'aspect':60,'movement': 0},
            32:{'planet2':chart.JUPITER,'aspect':60,'movement': 0},
            33:{'planet2':self.asc_ruler,'aspect':0,'movement': 0},
            34:{'planet2':self.asc_ruler,'aspect':60,'movement': 0},
            35:{'planet2':self.asc_ruler,'aspect':120,'movement': 0},
            36:{'planet2':self.asc_ruler,'aspect':90,'save':self.saving_conditions()[36],'movement': 0}}
        for i, arguments in condiciones.items():
            if i not in args:
                orb = arguments.get('orb',0)
                save = arguments.get('save',False)
                result = self.check_aspect(cond_number=i,planet2=arguments['planet2'],aspect=arguments['aspect'],save=save,orb=orb, movement=arguments['movement'])
                results[i] = result
        return results        
    def titles_table(self):
        titulos = {
1:'el regente de la casa 10 esta en exilio',
2:'el regente de la casa 10 esta en su caida',
3:'el regente de la casa 10 esta peregrino',
4:'el regente de la casa 10 esta retrogrado',
5:'el regente de la casa 10 esta en casa 6',
6:'el regente de la casa 10 esta en casa 8',
7:'el regente de la casa 10 esta en casa 12',
8:'el regente de la casa 10 esta en conjuncion aplicativa a marte, no considerar esta situacion si el ASC  esta en Aries',
9:'el regente de la casa 10 esta en conjuncion aplicativa a saturno, no considerar esta situacion si el ASC esta en capricornio o acuario',
10:'el regente de la casa 10 esta en cuadratura aplicativa a marte',
11:'el regente de la casa 10 esta en cuadratura aplicativa a saturno',
12:'el regente de la casa 10 esta en oposicion aplicativa a marte, al menos que el ASC este en Aries',
13:'el regente de la casa 10 esta en oposicion aplicativa a saturno',
14:'el regente de la casa 10 esta a menos de 8 grados del sol (combusto)',
15:'Si el regente de la casa 10 esta en cuadratura aplicativa/separativa al regente del ASC  ',
16:'Si el regente del ASC esta en cuadratura aplicativa/separativa al regente de la casa 10',
17:'Sumo Puntos',
18:'el regente de la casa 10 en su domicilio',
19:'el regente de la casa 10 en su exaltacion',
20:'el regente de la casa 10 en triplicidadad',
21:'el regente de la casa 10 en su termino',
22:'el regente de la casa 10 este directo',
23:'el regente de la casa 10 este a mas de 17 grados del sol ',
24:'el regente de la casa 10 este en la casa 1',
25:'el regente de la casa 10 este en la casa 10',
26:'el regente de la casa 10 este en la casa 11',
27:'el regente de la casa 10 este en la casa 9',
28:'el regente de la casa 10 este en la casa 5',
29:'el regente de la casa 10 trigono aplicativo a jupiter',
30:'el regente de la casa 10 trigono aplicativo a venus',
31:'el regente de la casa 10 sextil  aplicativo a venus',
32:'el regente de la casa 10 sextil  aplicativo a jupiter',
33:'el regente de la casa 10 en conjuncion aplicativa al regente del ASC B(n)',
34:'el regente de la casa 10 en sextil aplicativa al regente del ASC B(n)',
35:'el regente de la casa 10 en trigono aplicativa al regente del ASC B(n)',
36: 'Si el regente de la casa 10 esta en cuadratura aplicativa al regente del ASC B(n) al menos que  el regente de la casa 10 esta en el signo de (domicilio/ruler O Exaltacion/exalted) O en el signo de (triplicidad/triplicity_ruler y Termino/term_ruler) O (triplicidad/triplicity_ruler y Decanato/face_ruler) O (Termino/triplicity_ruler y Decanato/face_ruler) del regente del ASC'
}
        return titulos
    def calc_points(self,cond_num,si_cumple,si_no_cumple = 0,tipo = 'caracteristica'):
        if tipo == 'caracteristica':
            result = self.caracteristicas()
            points =np.nan if np.isnan(result[cond_num]) else (si_cumple if result[cond_num] else si_no_cumple)
        else:
            result = self.aspects_conditions()
            points = np.nan if np.isnan(result[cond_num][cond_num]) else (si_cumple if result[cond_num][cond_num] else si_no_cumple)
        return points    
    def cond_points(self):
        results = {}
        condiciones_con_puntos = {
18:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
19:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
20:{'si_cumple':0.5,'si_no_cumple':0,'tipo':'caracteristica'},
21:{'si_cumple':0.5,'si_no_cumple':0,'tipo':'caracteristica'},
22:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
23:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
24:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
25:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
26:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
27:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
28:{'si_cumple':1,'si_no_cumple':0,'tipo':'caracteristica'},
29:{'si_cumple':1,'si_no_cumple':0,'tipo':'aspecto'},
30:{'si_cumple':1,'si_no_cumple':0,'tipo':'aspecto'},
31:{'si_cumple':1,'si_no_cumple':0,'tipo':'aspecto'},
32:{'si_cumple':1,'si_no_cumple':0,'tipo':'aspecto'},
33:{'si_cumple':1,'si_no_cumple':0,'tipo':'aspecto'},
34:{'si_cumple':1,'si_no_cumple':0,'tipo':'aspecto'},
35:{'si_cumple':1,'si_no_cumple':0,'tipo':'aspecto'},
36:{'si_cumple':0.5,'si_no_cumple':1,'tipo':'aspecto'}
}
        for i, condiciones in condiciones_con_puntos.items():
            results[i]=self.calc_points(i,condiciones['si_cumple'],condiciones['si_no_cumple'],condiciones['tipo'])
        return results, condiciones_con_puntos
    
    def merge_data(self, *args):
        #Inicializo una lista vacia para appendear las filas
        data = []
        
        #Loopeo por todas las rows hasta la ultima con condicion. Despues appendeo las de resumen
        for i in range(1,37):
            if i not in args:
                cond_result = self.caracteristicas().get(i, self.aspects_conditions().get(i, {}).get(i, np.nan))
        #Inicializo la fila
                row = {
        'cond_num': i,
        'description': self.titles_table().get(i, 'Unknown'),
        'Resultado': cond_result,
        'Reg ASC o Casa 10': self.r10_obj['name'] + " y " + self.object_json[self.asc_ruler]['name'] if i in range(15,17) or i in range(33,37) else int(self.r10_obj['house']['number']) if (i in range(5,8) or i in range(24,29)) and self.caracteristicas().get(i, self.aspects_conditions().get(i, {}).get(i, np.nan)) == True else self.r10_obj['name'],
        'Tipo Aspecto/Casa': self.aspects_conditions().get(i, {}).get('aspecto', np.nan),
        'Dignidad': self.r10_obj['dignities']['formatted'] if i in range(1,5) or i in range(18,23) or i in range(35,37) else np.nan,
        'Movimiento': self.aspects_conditions().get(i, {}).get('movimiento', np.nan),
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
        'descripcion': "Puntaje total regente de la casa 10 para B(n)",
        'Puntos': total_puntos
        }
    
        df.loc[len(df)] = {
        'cond_num': last_cond_num+2,
        'descripcion': "Puntaje total regente de la casa 10 para B(n) en %",
        'Puntos': total_puntos / max_puntos
        }

        df.rename(columns={"Resultado": "resultado", "description": "descripcion", "Puntos":"puntos"}, inplace=True)
        
        return df
