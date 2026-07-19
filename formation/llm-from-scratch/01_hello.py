"""Premier contact avec un LLM : envoyer un message a Ollama et lire la reponse.

Ollama expose une API HTTP sur jarvis-central. On lui POST du JSON
(le modele a utiliser + la liste des messages), il repond du JSON
(le message genere par le modele). C'est tout ce qu'est un appel LLM.
"""

import httpx

OLLAMA_URL = "http://192.168.1.57:11434"
MODEL = "qwen3:4b-instruct-2507-q4_K_M"

reponse = httpx.post(
    f"{OLLAMA_URL}/api/chat",
    json={
        "model": MODEL,
        "messages": [
            {"role": "user", "content": "Bonjour ! Presente-toi en une phrase."},
        ],
        # stream=False : Ollama attend la fin de la generation et renvoie
        # tout d'un coup. Le streaming (mot a mot) viendra plus tard.
        "stream": False,
    },
    # Le premier appel charge le modele en VRAM : ca peut prendre du temps.
    timeout=120,
)

donnees = reponse.json()
print(donnees["message"]["content"])
