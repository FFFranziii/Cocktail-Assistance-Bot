import requests
from typing import Any, Dict, List, Text

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

NODE_RED = "http://localhost:1880"


def frage_node_red(pfad: str, payload: dict):
    """Schickt eine Anfrage an Node-RED, gibt None zurück wenn es nicht klappt."""
    try:
        antwort = requests.post(f"{NODE_RED}/{pfad}", json=payload, timeout=5)
        antwort.raise_for_status()
        return antwort.json()
    except (requests.RequestException, ValueError) as fehler:
        print(f"Node-RED-Fehler bei /{pfad}: {fehler}")
        return None


def aufzaehlung(liste: List[str]) -> str:

    if len(liste) > 1:
        return ", ".join(liste[:-1]) + " und " + liste[-1]
    return liste[0]



class ActionSucheCocktail(Action):
    def name(self) -> Text:
        return "action_suche_cocktail"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        aktuelle_zutaten=[z.lower() for z in tracker.get_latest_entity_values("zutaten")]
        print("aktuelle zutaten:",aktuelle_zutaten)
        user_zutaten = [z.lower() for z in (tracker.get_slot("zutaten") or [])]
        print("user_zutaten:",user_zutaten)
        user_zutaten=list(set(aktuelle_zutaten + user_zutaten))
        print("user_zutaten:",user_zutaten)
        user_kategorie=[z.lower() for z in (tracker.get_slot("kategorie") or [])]
        if (not user_zutaten) and (not user_kategorie):
            dispatcher.utter_message(text="Bitte nenne mir mindestens eine Zutat oder Kategorie.")
            return [SlotSet("zutaten",[])]
        print(user_zutaten,user_kategorie)
        data = frage_node_red("cocktail_lookup", {"zutaten": user_zutaten,"kategorie":user_kategorie})
        if data is None:
            dispatcher.utter_message(text="Die Cocktail-Datenbank ist gerade nicht erreichbar. Läuft Node-RED?")
            return [SlotSet("zutaten",[])]

        namen = [c["name"] for c in data.get("cocktails", [])]
        if not namen:
            dispatcher.utter_message(text="Leider habe ich keinen passenden Cocktail gefunden.")
            return [SlotSet("zutaten",user_zutaten)]
        elif user_zutaten != [] and user_kategorie==[]:
            dispatcher.utter_message(
                response="utter_nur_zutaten",namen=aufzaehlung(namen), zutaten=aufzaehlung(user_zutaten))
        elif user_zutaten == [] and user_kategorie!=[]:
            dispatcher.utter_message(
                response="utter_nur_kategorie",namen=aufzaehlung(namen), kategorie=aufzaehlung(user_kategorie))
        else:
            dispatcher.utter_message(
                response="utter_beides",namen=aufzaehlung(namen), kategorie=aufzaehlung(user_kategorie), zutaten=aufzaehlung(user_zutaten))
        return [SlotSet("zutaten",user_zutaten)]


class ActionSucheRezept(Action):
    def name(self) -> Text:
        return "action_suche_rezept"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # 1. erkannter Cocktailname aus DIESER Nachricht, 2. Notlösung: ganze Nachricht
        cocktail = next(tracker.get_latest_entity_values("cocktail"), None)
        if not cocktail:
            cocktail = tracker.latest_message.get("text", "")
        cocktail = cocktail.strip().lower()

        if not cocktail:
            dispatcher.utter_message(text="Bitte nenne mir einen Cocktailnamen.")
            return []

        data = frage_node_red("zutaten_lookup", {"cocktail": cocktail})
        if data is None:
            dispatcher.utter_message(text="Die Cocktail-Datenbank ist gerade nicht erreichbar. Läuft Node-RED?")
            return []

        zutaten = data.get("zutaten")
        if not zutaten:
            dispatcher.utter_message(text=f"Ich habe leider kein Rezept für {cocktail} gefunden.")
            return []

        dispatcher.utter_message(
            text=f"Für einen {data.get('name', cocktail)} brauchst du: {aufzaehlung(zutaten)}"
        )
        return []

class ActionNeustart(Action):
    def name(self) -> Text:
        return "action_Neustart"
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_zutaten=[]
        user_kategorie=[]
        dispatcher.utter_message(response="utter_Neustart")
        return [SlotSet("zutaten",user_zutaten), SlotSet("kategorie",user_kategorie)]
