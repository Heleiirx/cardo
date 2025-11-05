from pymongo import MongoClient
from datetime import datetime, timezone
import random
import os
import platform
import time

# ---------- Configuración de conexión ----------
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "cardo"

# Nombres de colecciones
COL_PARTIDAS = "partidas"
CATEGORIES = ["situaciones", "objetos", "emociones", "lugares"]


def clear_console():
    cmd = "cls" if platform.system().lower().startswith("win") else "clear"
    os.system(cmd)

def connect_db(uri=MONGO_URI):
    client = MongoClient(uri)
    db = client[DB_NAME]
    return db

def bold(text):
    return f"\033[1m{text}\033[0m"

def green(text):
    return f"\033[1;32m{text}\033[0m"

def red(text):
    return f"\033[1;31m{text}\033[0m"

def yellow(text):
    return f"\033[1;33m{text}\033[0m"

# ---------- Verificación de datos ----------

def verify_collections(db):
    """Verifica que todas las colecciones necesarias tengan datos"""
    missing_data = []
    for category in CATEGORIES:
        col = db[category]
        count = col.count_documents({})
        if count == 0:
            missing_data.append(category)
        else:
            print(f"Colección '{category}': {count} documentos encontrados")
            # Mostrar un documento de ejemplo para ver la estructura
            sample_doc = col.find_one()
            if sample_doc:
                print(f"  Ejemplo de documento: {sample_doc}")
    
    if missing_data:
        print(f"\nError: Las siguientes colecciones están vacías: {missing_data}")
        print("Asegúrate de haber cargado los datos en MongoDB.")
        return False
    return True


# ---------- Funciones auxiliares para cartas ----------

def get_card_by_id(db, card_id, category):
    """Obtiene los datos completos de una carta por su ID y categoría"""
    col = db[category]
    doc = col.find_one({"_id": card_id})
    if doc:
        return {
            "_id": doc.get("_id"),
            "description": doc.get("descripcion", "Sin descripción"),
            "score": doc.get("puntaje", 1),
            "category": category
        }
    return None

def get_cards_by_ids(db, card_ids):
    """Obtiene múltiples cartas por sus IDs buscando en todas las categorías"""
    cards = []
    for card_id in card_ids:
        card_found = None
        # Buscar en todas las categorías hasta encontrar la carta
        for category in CATEGORIES:
            card_found = get_card_by_id(db, card_id, category)
            if card_found:
                break
        if card_found:
            cards.append(card_found)
    return cards

def get_card_by_id_any_category(db, card_id):
    """Busca una carta por ID en todas las categorías"""
    for category in CATEGORIES:
        card = get_card_by_id(db, card_id, category)
        if card:
            return card
    return None

def get_player_cards_by_role(db, partida, player_name, role):
    """Obtiene las cartas ganadas por un jugador en un rol específico"""
    cards = []
    for round_data in partida['rounds']:
        if round_data.get(role) == player_name:
            if role == 'cardomante' and round_data.get('outcome') == 'correct_guess':
                card = get_card_by_id_any_category(db, round_data['choice_card_id'])
                if card:
                    cards.append(card['description'])
            elif role == 'cardoelector' and round_data.get('outcome') == 'wrong_guess':
                card = get_card_by_id_any_category(db, round_data['choice_card_id'])
                if card:
                    cards.append(card['description'])
    return cards

# ---------- Lógica de selección de 3 cartas de categorías distintas ----------

def pick_three_cards(db):
    chosen_cats = random.sample(CATEGORIES, 3)
    cards = []
    for cat in chosen_cats:
        col = db[cat]
        count = col.count_documents({})
        if count == 0:
            raise RuntimeError(f"La colección '{cat}' está vacía.")
        rand_idx = random.randint(0, count - 1)
        doc = col.find().skip(rand_idx).limit(1)[0]
        
        description = doc.get("descripcion", "Sin descripción")
        score = doc.get("puntaje", 1)
        
        cards.append({
            "_id": doc.get("_id"),
            "description": description,
            "score": score,
            "category": cat
        })
    random.shuffle(cards)
    return cards

def ask_choice(prompt, min_val, max_val):
    while True:
        try:
            val = input(prompt).strip()
            if val == "":
                print("Entrada vacía — por favor ingresa un número.")
                continue
            n = int(val)
            if n < min_val or n > max_val:
                print(f"Por favor ingresa un número entre {min_val} y {max_val}.")
                continue
            return n
        except ValueError:
            print("Entrada no válida — ingresa un número.")


# ---------- Juego: flujo principal ----------

def play_game(db):
    clear_console()
    print("Cardo\n")

    player1 = input("Nombre/Alias del Jugador 1: ").strip() or "Jugador 1"
    player2 = input("Nombre/Alias del Jugador 2: ").strip() or "Jugador 2"

    rounds_input = input("Número de rondas (3-10): ").strip()
    try:
        rounds = int(rounds_input)
        if rounds < 3 or rounds > 10:
            print("El numero está fuera del rango — se usarán 5 rondas.")
            rounds = 5
    except Exception:
        rounds = 5

    partida = {
        "players": [player1, player2],
        "rounds_total": rounds,
        "rounds": [],
        "created_at": datetime.now(timezone.utc),
        "winner": None,
        "scores": {player1: 0, player2: 0}
    }
    partida_id = db[COL_PARTIDAS].insert_one(partida).inserted_id

    scores = {player1: 0, player2: 0}

    clear_console()

    for r in range(1, rounds + 1):
        cardoelector = player1 if r % 2 == 1 else player2
        cardomante = player2 if cardoelector == player1 else player1

        cards = pick_three_cards(db)

        print(bold(f"Hora de elegir {cardoelector}\n"))
        for i, c in enumerate(cards, start=1):
            print(f"{i}) {c['description']} ({c['score']})")
        choice = ask_choice(f"{cardoelector}, elige 1, 2 o 3: ", 1, 3)
        chosen_card = cards[choice - 1]

        time.sleep(0.9)
        clear_console()

        print(bold(f"Hora de adivinar {cardomante}\n"))
        for i, c in enumerate(cards, start=1):
            print(f"{i}) {c['description']} ({c['score']})")
        guess = ask_choice(f"{cardomante}, adivina 1, 2 o 3: ", 1, 3)
        guessed_card = cards[guess - 1]

        time.sleep(0.9)
        clear_console()

        round_result = {
            "round": r,
            "cardoelector": cardoelector,
            "cardomante": cardomante,
            "offered_cards_ids": [card["_id"] for card in cards],
            "choice_index": choice - 1,
            "choice_card_id": chosen_card["_id"],
            "guess_index": guess - 1,
            "guessed_card_id": guessed_card["_id"],
            "timestamp": datetime.now(timezone.utc)
        }

        if guessed_card['_id'] == chosen_card['_id']:
            base_score = chosen_card['score']
            penalty = 1 if base_score >= 2 else 0
            gained = base_score - penalty
            scores[cardomante] += gained
            round_result['outcome'] = 'correct_guess'
            round_result['points_awarded'] = {cardomante: gained, cardoelector: 0}
            round_result['points_detail'] = {'base_score': base_score, 'penalty': penalty, 'gained': gained}
        else:
            gained = chosen_card['score']
            scores[cardoelector] += gained
            round_result['outcome'] = 'wrong_guess'
            round_result['points_awarded'] = {cardomante: 0, cardoelector: gained}
            round_result['points_detail'] = {'base_score': gained, 'penalty': 0, 'gained': gained}

        db[COL_PARTIDAS].update_one({"_id": partida_id}, {"$push": {"rounds": round_result}, "$set": {"scores": scores}})

        print(f"Ronda {r} completa. {cardoelector} eligió: '{chosen_card['description']}' ({chosen_card['score']})")
        if round_result['outcome'] == 'correct_guess':
            print(bold(f"{cardomante} {green("adivinó correctamente")} y obtuvo {gained} punto(s)."))
        else:
            print(bold(f"{cardomante} {red("no adivinó.")} {cardoelector} obtuvo {gained} punto(s)."))
        print("Puntuaciones actuales:")
        print(f" - {player1}: {scores[player1]}  |  {player2}: {scores[player2]}\n")

        input(f"Presiona {bold("Enter")} para continuar a la siguiente ronda...")
        clear_console()

    if scores[player1] > scores[player2]:
        winner = player1
    elif scores[player2] > scores[player1]:
        winner = player2
    else:
        winner = None

    final_update = {
        "winner": winner,
        "scores": scores,
        "finished_at": datetime.now()
    }
    db[COL_PARTIDAS].update_one({"_id": partida_id}, {"$set": final_update})

    if winner is None:
        print(yellow("La partida terminó en empate!\n"))
        print(f"Puntuaciones finales: {player1}: {scores[player1]}  |  {player2}: {scores[player2]}")
    else:
        # Obtener cartas ganadas dinámicamente
        partida_final = db[COL_PARTIDAS].find_one({"_id": partida_id})
        puntos_cardomante = get_player_cards_by_role(db, partida_final, winner, 'cardomante')
        puntos_cardoelector = get_player_cards_by_role(db, partida_final, winner, 'cardoelector')
        total = scores[winner]
        print(green(f"¡Gana {winner}!"))
        print(f"Puntos como 'cardomante': {puntos_cardomante}")
        print(f"Puntos como 'cardoelector': {puntos_cardoelector}")
        print(f"Total de puntos: {total}")

    print("\nRegistro de la partida guardado en la colección 'partidas' de la base de datos 'cardo'.")
    


if __name__ == '__main__':
    try:
        db = connect_db()
        print("Conectado a MongoDB exitosamente.")
        
        # Verificar que las colecciones tengan datos
        if not verify_collections(db):
            exit(1)
            
        print("\nTodas las colecciones están listas. Iniciando juego...\n")
        
    except Exception as e:
        print("No se pudo conectar a MongoDB en la URI configurada. Asegúrate de que MongoDB esté corriendo.")
        print(str(e))
        exit(1)

    play_game(db)
