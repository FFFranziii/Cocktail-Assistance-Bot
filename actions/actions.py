import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List

# class ActionSucheCocktail(Action):
#     def name(self):
#         return "action_suche_cocktail"

#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: dict):
        
#         print("Nutzer Zutaten extrahieren.")
#         # Nutzer-Zutaten extrahieren
#         user_zutaten = [e['value'].lower() for e in tracker.latest_message['entities'] if e['entity']=='zutaten']
#         if not user_zutaten:
#             dispatcher.utter_message(text="Bitte nenne mir mindestens eine Zutat.")
#             return []
#         # response = {"cocktails": ["Mojito", "Caipirinha"]}
#         # cocktails = response.get("cocktails", [])
#         response = requests.post(
#             "http://localhost:1880/cocktail_lookup",
#             json={"zutaten": user_zutaten},
#             timeout=5)
#         data = response.json()  # Node-RED Response
#         print("Node-RED hat geantwortet:", data)

#         # Einfach alle Cocktails zurückgeben
#         cocktails = data.get("cocktails", [])
#         cocktail_namen=[]
#         for c in cocktails:
#             cocktail_namen.append(c['name'])
#         if len(cocktail_namen) > 1:
#             cocktail_namen_text = ", ".join(cocktail_namen[:-1]) + " und " + cocktail_namen[-1]
#         else:
#             cocktail_namen_text = cocktail_namen[0]
#         dispatcher.utter_message(text=f"Verfügbare cocktails:{cocktail_namen_text}")
#         return []

class ActionSucheCocktail(Action):
    def name(self):
        return "action_suche_cocktail"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict):

        print("Nutzer-Zutaten aus Slot extrahieren")

        # ✅ Slot verwenden (Entity heißt ebenfalls 'zutaten')
        user_zutaten = tracker.get_slot("zutaten") or []

        # Sicherheit: alles lowercase
        user_zutaten = [z.lower() for z in user_zutaten]

        if not user_zutaten:
            dispatcher.utter_message(
                text="Bitte nenne mir mindestens eine Zutat."
            )
            return []

        # Anfrage an Node-RED
        response = requests.post(
            "http://localhost:1880/cocktail_lookup",
            json={"zutaten": user_zutaten},
            timeout=5
        )

        data = response.json()
        print("Node-RED hat geantwortet:", data)

        cocktails = data.get("cocktails", [])

        if not cocktails:
            dispatcher.utter_message(
                text="Leider habe ich keinen Cocktail mit diesen Zutaten gefunden."
            )
            return []

        # Cocktailnamen extrahieren
        cocktail_namen = [c["name"] for c in cocktails]

        if len(cocktail_namen) > 1:
            cocktail_namen_text = (
                ", ".join(cocktail_namen[:-1]) + " und " + cocktail_namen[-1]
            )
        else:
            cocktail_namen_text = cocktail_namen[0]

        dispatcher.utter_message(
            text=f"Mit diesen Zutaten kannst du folgende Cocktails machen: {cocktail_namen_text}. Welchen möchtest du?"
        )

        return []



class ActionSucheRezept(Action):
    def name(self):
        return "action_suche_rezept"

    def run(self, dispatcher, tracker, domain):

        user_cocktail = tracker.latest_message['text'].lower()

        if not user_cocktail:
            dispatcher.utter_message(text="Bitte nenne mir einen Cocktailnamen.")
            return []

        response = requests.post(
            "http://localhost:1880/zutaten_lookup",
            json={"cocktail": user_cocktail},
            timeout=5
        )

        data = response.json()
        print("Node-RED hat geantwortet:", data)

        zutaten = data.get("zutaten")

        if not zutaten:
            dispatcher.utter_message(
                text=f"Ich habe leider kein Rezept für {user_cocktail} gefunden."
            )
            return []

        if len(zutaten) > 1:
            zutaten_text = ", ".join(zutaten[:-1]) + " und " + zutaten[-1]
        else:
            zutaten_text = zutaten[0]

        dispatcher.utter_message(
            text=f"Für einen {data.get('name', user_cocktail)} brauchst du: {zutaten_text}"
        )

        return []



