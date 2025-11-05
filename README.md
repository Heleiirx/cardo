# 🎮 Cardo - Simulador de Juego de Cartas

Un simulador interactivo del juego de cartas **Cardo** desarrollado en Python con MongoDB como base de datos. El juego consiste en adivinar qué carta eligió tu oponente entre tres opciones de diferentes categorías.

## ✨ Características

- 🎯 **Juego interactivo** para 2 jugadores
- 🗃️ **Base de datos MongoDB** 
- 📊 **Sistema de puntuación** dinámico con penalizaciones
- 📈 **Historial detallado** de partidas
- 🔄 **Roles alternos** (cardoelector/cardomante)
- 📝 **Registro completo** de estadísticas

## 🛠️ Tecnologías

- **Python 3.7+**
- **MongoDB 4.0+**
- **PyMongo** - Driver de MongoDB para Python
- **Datetime** - Manejo de fechas y timestamps

## 🚀 Instalación

### Prerrequisitos

1. **Python 3.7 o superior**
2. **MongoDB** instalado y ejecutándose
3. **pip** para instalar dependencias

### Pasos de instalación

1. **Clona el repositorio:**
```bash
git clone https://github.com/tu-usuario/cardo-simulator.git
cd cardo-simulator
```

2. **Instala las dependencias:**
```bash
pip install pymongo
```

3. **Configura MongoDB:**
   - Asegúrate de que MongoDB esté ejecutándose en `localhost:27017`
   - O modifica la variable `MONGO_URI` en `cardo_simulator.py`

4. **Carga los datos iniciales:**
   - Usa `mongosh` o MongoDB Compass para cargar las cartas en las colecciones:
     - `situaciones`
     - `objetos` 
     - `emociones`
     - `lugares`

## 🎮 Uso

### Ejecutar el juego

```bash
python cardo_simulator.py
```

### Flujo del juego

1. **Configuración inicial:**
   - Ingresa nombres de los 2 jugadores
   - Selecciona número de rondas (3-10)

2. **Cada ronda:**
   - El **cardoelector** elige una carta de 3 opciones
   - El **cardomante** intenta adivinar cuál eligió
   - Se calculan y asignan puntos según el resultado

3. **Final:**
   - Se muestra el ganador y estadísticas
   - Opción de ver historial detallado

## 🎯 Reglas del Juego

### Roles
- **Cardoelector:** Elige una carta entre 3 opciones
- **Cardomante:** Intenta adivinar la carta elegida
- Los roles se alternan cada ronda

### Sistema de Puntuación
- **Adivinanza correcta:** Cardomante gana `(puntaje_carta - 1)` puntos
- **Adivinanza incorrecta:** Cardoelector gana `puntaje_carta` puntos
- **Penalización:** Se resta 1 punto si la carta vale 2+ puntos

### Categorías de Cartas
- 🎭 **Situaciones** 
- 🎲 **Objetos**
- 😊 **Emociones**
- 🏠 **Lugares**

## 🗄️ Estructura de la Base de Datos

### Base de Datos: `cardo`

#### Colecciones de Cartas
```javascript
// Estructura de cada carta
{
  "_id": ObjectId("..."),
  "descripcion": "Texto de la carta",
  "puntaje": 2
}
```

#### Colección de Partidas
```javascript
{
  "_id": ObjectId("..."),
  "players": ["Jugador1", "Jugador2"],
  "rounds_total": 5,
  "rounds": [
    {
      "round": 1,
      "cardoelector": "Jugador1",
      "cardomante": "Jugador2", 
      "offered_cards_ids": [ObjectId("..."), ObjectId("..."), ObjectId("...")],
      "choice_index": 0,
      "choice_card_id": ObjectId("..."),
      "guess_index": 1,
      "guessed_card_id": ObjectId("..."),
      "outcome": "correct_guess",
      "points_awarded": {"Jugador1": 0, "Jugador2": 1},
      "points_detail": {"base_score": 2, "penalty": 1, "gained": 1},
      "timestamp": ISODate("...")
    }
  ],
  "created_at": ISODate("..."),
  "finished_at": ISODate("..."),
  "winner": "Jugador2",
  "scores": {"Jugador1": 3, "Jugador2": 5}
}
```

## 🔍 Consultas de Ejemplo

### Partidas con ganador de más de 5 puntos
```javascript
{
  "winner": { "$ne": null },
  "$expr": {
    "$gt": [
      { "$getField": { "field": "$winner", "input": "$scores" } },
      5
    ]
  }
}
```

### Partidas por jugador específico
```javascript
{
  "players": "NombreJugador"
}
```

### Partidas por fecha
```javascript
{
  "created_at": {
    "$gte": ISODate("2025-01-01"),
    "$lt": ISODate("2025-12-31")
  }
}