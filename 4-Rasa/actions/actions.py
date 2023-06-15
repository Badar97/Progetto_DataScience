# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []






import json
from pathlib import Path
from typing import Any, Text, Dict, List
import requests
from rasa_sdk.events import SlotSet

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.knowledge_base.storage import InMemoryKnowledgeBase
from rasa_sdk.knowledge_base.actions import ActionQueryKnowledgeBase
from rasa_sdk.events import SlotSet

import pandas as pd
from datetime import datetime
import csv



class MyFallback(Action):
    
    def name(self) -> Text:
        return "action_my_fallback"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(response = "utter_fallback")
        return []

def check_slash(string):
    if '/' in string:
        return True
    else:
        return False


class ActionInfoDay(Action):
    
    def name(self) -> Text:
        return "action_info_day"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:


        data = str(tracker.get_slot('data'))
        
        data = data.replace('-','/')

        


        #Funzione per 'richiesta info su spesa su un dato giorno'
        def info_spesa_day(data):
            try:
                dataframe = pd.read_csv('./File_Spesa.csv', delimiter = ',')
                filtro = dataframe['data'] == data
                righe_selezionate = dataframe[filtro]

                if righe_selezionate.empty:
                    return "Non ci sono stati acquisti il giorno : {} ".format(data)
                else:               
                    somma_prezzi = righe_selezionate['prezzo'].sum()
                    oggetti = righe_selezionate['oggetto'].tolist()
                    oggetti_stringa = ', '.join(oggetti)
                    return "Il giorno {}, hai speso {} euro (anticamente si usavano le rupie), comprando : {}.".format(data,somma_prezzi,oggetti_stringa)
            except:
                return "Non ci sono stati acquisti il giorno : {} ".format(data)

        #concatena_con_backslash(giorno, mese, anno)  # Esempio giorno da cercare

        output = info_spesa_day(data)
        dispatcher.utter_message(text=output)
        return []
    

#Classe per definire l'azione di inserimento elementi nel file
class ActionAdd(Action):
    
    def name(self) -> Text:
        return "action_add"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
            
        data = (str(tracker.get_slot('data'))).replace('-' , '/')
        oggetto = str(tracker.get_slot('oggetto'))
        tipologia = str(tracker.get_slot('tipologia'))
        prezzo = str(tracker.get_slot('prezzo'))
        data_oggetto = datetime.strptime(data, "%d/%m/%Y")
        giorno = data_oggetto.day
        mese = data_oggetto.month
        anno = data_oggetto.year
        
        
        def inserisci_elemento( giorno, mese, anno, oggetto, tipologia, prezzo, data):
            dataframe = pd.read_csv('./File_Spesa.csv', delimiter = ',')
            nuovo_elemento = pd.DataFrame({'giorno': [giorno], 'mese': [mese], 'anno': [anno], 'oggetto': [oggetto],
                     'tipologia': [tipologia], 'prezzo': [prezzo], 'data': [data]})
            pd.concat([dataframe, nuovo_elemento]).to_csv('./File_Spesa.csv', lineterminator='\n', index=False)
            #print("Nuovo elemento inserito correttamente.")

        
        inserisci_elemento(giorno, mese, anno, oggetto, tipologia, prezzo, data)


        output="Ho appena salvato {}, in : {} , prezzo : {}, data : {}.".format(oggetto, tipologia, prezzo, data)

        dispatcher.utter_message(text=output)
        return []








#Classe per eliminare un acquisto
class ActionDelete(Action):
    
    def name(self) -> Text:
        return "action_delete"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:


        oggetto = str(tracker.get_slot('oggetto'))
        output = ""

         #Funzione per modificare il dataframe
        def delete_oggetto(oggetto):
            dataframe = pd.read_csv('./File_Spesa.csv', delimiter = ',')
            try:
                dataframe_filtrato = dataframe[dataframe['oggetto'] != oggetto]
                dataframe_filtrato.to_csv('./File_Spesa.csv', lineterminator='\n', index=False)
                return "Ho appena eliminato questo oggetto comprato: {}.".format(oggetto)
            except:
                return "Oggetto non trovato."

                
        output = delete_oggetto(oggetto)

        

        dispatcher.utter_message(text=output)
        return []



#Classe per calcolo statistica per tipologia
class ActionInfoTipology(Action):
    
    def name(self) -> Text:
        return "action_info_tipology"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:


        tipologia = str(tracker.get_slot('tipologia'))
        output = ""

         #Funzione per modificare il dataframe
        def stats_tipology(tipologia):
            dataframe = pd.read_csv('./File_Spesa.csv', delimiter = ',')
            try:
                prezzo_totale = dataframe['prezzo'].sum()
                dataframe_filtrato = dataframe[dataframe['tipologia'] == tipologia]
                prezzo_tipologia = dataframe_filtrato['prezzo'].sum()
                prezzo_percentuale = (prezzo_tipologia / prezzo_totale) * 100

                return "Per la tipologia: {}, hai speso : {} , in percentuale : {}.".format(tipologia, prezzo_tipologia, prezzo_percentuale)
            except:
                return "C'è qualcosa che non va, non ho trovato la tipologia : {}.".format(tipologia)

                
        output = stats_tipology(tipologia)

        

        dispatcher.utter_message(text=output)
        return []




#Classe per calcolo statistica totale
class ActionInfoStats(Action):
    
    def name(self) -> Text:
        return "action_info_stats"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        output = ""

         #Funzione per modificare il dataframe
        def stats():
            dataframe = pd.read_csv('./File_Spesa.csv', delimiter = ',')
            try:

                prezzo_totale = dataframe['prezzo'].sum()
                prezzo_medio = dataframe['prezzo'].mean()
                spesa_per_categoria = dataframe.groupby('tipologia')['prezzo'].sum()
                # Trova le due categorie con la spesa totale più alta e le salva in una stringa
                categorie_top = spesa_per_categoria.nlargest(2)
                categorie_top_stringa = categorie_top.to_string()

                return "Il prezzo totale che hai sostenuto è di : {} , la media per oggetto acquistato è : {}, le due categorie su cui hai speso di più sono : {} ".format(prezzo_totale, prezzo_medio, categorie_top_stringa)
            except:
                return "C'è qualcosa che non va."

                
        output = stats()    

        dispatcher.utter_message(text=output)
        return []



#Classe per calcolo statistica per mese
class ActionStatsMonth(Action):
    
    def name(self) -> Text:
        return "action_stats_month"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        mese_testuale = str(tracker.get_slot('mese'))
        mesi = {"gennaio": 1,"febbraio": 2,"marzo": 3,"aprile": 4,"maggio": 5,"giugno": 6,"luglio": 7,"agosto": 8,"settembre": 9,"ottobre": 10,"novembre": 11,"dicembre": 12}
        output = ""

        try:
            mese_lower = mese_testuale.lower()
            mese_numerico = mesi[mese_lower]
        except:
            output = "C'è un errore nel mese"
        
        #Funzione per modificare il dataframe
        def stats_month():
            dataframe = pd.read_csv('./File_Spesa.csv', delimiter = ',')
            try:
                df_month = dataframe[dataframe['mese'] == mese_numerico]
                spesa_totale = df_month['prezzo'].sum()
                spesa_media = df_month['prezzo'].mean()
                # Calcola la spesa totale per categoria
                spesa_per_categoria = df_month.groupby('tipologia')['prezzo'].sum()
                # Trova le due categorie con la spesa totale più alta e le salva in una stringa
                categorie_top = spesa_per_categoria.nlargest(2)
                categorie_top_stringa = categorie_top.to_string()
                return "Il prezzo totale che hai sostenuto nel mese di {} è di {} , la media del mese è di {}. Le due categorie su cui hai speso di più sono : {}".format(mese_testuale, spesa_totale, spesa_media, categorie_top_stringa )
            except:
                return "C'è qualcosa che non va, forse non hai fatto spese nel mese di : {}.".format(mese_testuale)

                
        output = stats_month()    

        dispatcher.utter_message(text=output)
        return []



#Classe per range temporale
class ActionStatsRange(Action):
    
    def name(self) -> Text:
        return "action_info_range"

    def run(self, dispatcher: CollectingDispatcher,tracker: Tracker,domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        range = str(tracker.get_slot('range'))

        data_inizio, data_fine = range.split('/')
        data_inizio = data_inizio.replace('-', '/')
        data_fine = data_fine.replace('-', '/')

        output = ""

        def is_date_between(date, date1, date2):

            date1_obj = datetime.datetime.strptime(date1, "%d/%m/%Y")
            date2_obj = datetime.datetime.strptime(date2, "%d/%m/%Y")
            date_obj = datetime.datetime.strptime(date, "%d/%m/%Y")

            return date1_obj <= date_obj <= date2_obj


        def filter_rows_by_date(date1, date2):
            dataframe = pd.read_csv('./File_Spesa.csv', delimiter= ',')
            filtered_rows = []
            #print(type(dataframe))
            for index, row in dataframe.iterrows():
                date_str = row['data'].strip()

                if is_date_between(date_str, date1, date2):
                    filtered_rows.append(row)

            return filtered_rows

                
        def sum_prices_and_get_items():

            try:
                filtered_rows = filter_rows_by_date(data_inizio, data_fine)
                oggetti = []
                df_filtered = pd.DataFrame(filtered_rows, columns=['giorno', 'mese','anno','oggetto','tipologia','prezzo','data'])
                somma_prezzi = df_filtered['prezzo'].sum()
                oggetti = df_filtered['oggetto'].tolist()
                oggetti_stringa = ', '.join(oggetti)

                return "Dal giorno {} al giorno {}, hai speso in totale {} euro. Gli oggetti acquistati sono : {}".format(data_inizio, data_fine, somma_prezzi, oggetti_stringa)
            except:
                return "C'è stato un errore con le date. 1: {} 2: {}".format(data_inizio,data_fine)

                
        output = sum_prices_and_get_items()
        dispatcher.utter_message(text=output)
        return []








"""
print("Somma dei prezzi:", somma)

print("Oggetti del giorno", oggetti_stringa)

try:
    dataframe = pd.read_csv('File_Spesa.csv')
    print(dataframe.head())  # Stampa le prime righe del dataframe
except FileNotFoundError:
    print("File non trovato. Assicurati di fornire il percorso corretto del file CSV.")

    








dataframe = leggi_csv(file_path)
print(dataframe.tail())

def elimina_per_data(file_path, giorno, mese, anno):
    dataframe = leggi_csv(file_path)
    filtro = (dataframe['giorno'] == giorno) & (dataframe['mese'] == mese) & (dataframe['anno'] == anno)
    dataframe = dataframe[~filtro]
    salva_csv(dataframe, file_path)
    print("Elementi eliminati con successo.")

def elimina_per_oggetto(file_path, oggetto):
    dataframe = leggi_csv(file_path)
    filtro = dataframe['oggetto'] == oggetto
    dataframe = dataframe[~filtro]
    salva_csv(dataframe, file_path)
    print("Elementi eliminati con successo.")

# Esempio di utilizzo per eliminare per data
elimina_per_data(file_path, 31, 5, 2023)

# Esempio di utilizzo per eliminare per oggetto
elimina_per_oggetto(file_path, "Smartwatch")

"""