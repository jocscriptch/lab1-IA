from flask import Flask, jsonify, request
import random

app = Flask(__name__)

N = 2  # num de agentes
DADOS_POR_RONDA = (N * 2) + 1
COLORES = ["rojo", "azul", "verde", "amarillo", "morado"]


class EstadoDelJuego:
    def __init__(self):
        self.ronda_actual = 0
        self.turno_actual = 1
        self.dados_reserva = []
        self.tableros = {1: [], 2: []}
        self.seleccionados = {1: [], 2: []}
        self.colores_asignados = {}

    def asignar_colores_a_agentes(self):
        # asignar un color aleatorio a cada agente
        colores_disponibles = random.sample(COLORES, N)
        self.colores_asignados = {i + 1: color for i, color in enumerate(colores_disponibles)}

    def generar_dados(self):
        dados = set()
        while len(dados) < DADOS_POR_RONDA:
            color = random.choice(COLORES)
            valor = random.randint(1, 6)
            dado = (color, valor)
            dados.add(dado)
        self.dados_reserva = [{"color": color, "valor": valor} for color, valor in dados]

    def siguiente_turno(self):
        self.turno_actual = 1 if self.turno_actual == 2 else 2

    def es_posicion_valida(self, tablero, dado, posicion):
        fila, columna = posicion
        if not (0 <= fila < 4 and 0 <= columna < 5):
            return False

        if any(d["posicion"] == posicion for d in tablero):
            return False

        if len(tablero) == 0:
            return fila in [0, 3] or columna in [0, 4]

        for d in tablero:
            f, c = d["posicion"]
            if abs(fila - f) <= 1 and abs(columna - c) <= 1:
                if fila == f or columna == c:
                    if d["dado"]["color"] == dado["color"] or d["dado"]["valor"] == dado["valor"]:
                        return False
                return True

        return False


estado_juego = EstadoDelJuego()


@app.route('/iniciar_ronda', methods=['POST'])
def iniciar_ronda():
    if estado_juego.ronda_actual == 0:
        estado_juego.asignar_colores_a_agentes()
    estado_juego.generar_dados()
    estado_juego.seleccionados = {1: [], 2: []}
    estado_juego.ronda_actual += 1
    estado_juego.turno_actual = 1
    return jsonify({
        "ronda": estado_juego.ronda_actual,
        "dados": estado_juego.dados_reserva,
        "colores_asignados": estado_juego.colores_asignados
    })


@app.route('/solicitar_dado', methods=['POST'])
def solicitar_dado():
    agente_id = request.json.get('agente_id')
    dado = request.json.get('dado')

    if agente_id != estado_juego.turno_actual:
        return jsonify({"success": False, "mensaje": "No es tu turno."}), 400

    if len(estado_juego.seleccionados[agente_id]) >= 2:
        return jsonify({"success": False, "mensaje": "Ya has seleccionado tus dos dados."}), 400

    if dado in estado_juego.dados_reserva:
        estado_juego.dados_reserva.remove(dado)
        estado_juego.seleccionados[agente_id].append(dado)
        return jsonify({"success": True, "dado": dado, "dados_seleccionados": estado_juego.seleccionados[agente_id]})
    else:
        return jsonify({"success": False, "mensaje": "Dado no disponible o ya tomado."}), 404


@app.route('/colocar_dado', methods=['POST'])
def colocar_dado():
    agente_id = request.json.get('agente_id')
    dado = request.json.get('dado')
    posicion = request.json.get('posicion')

    if agente_id != estado_juego.turno_actual:
        return jsonify({"success": False, "mensaje": "No es tu turno."}), 400

    if dado not in estado_juego.seleccionados[agente_id]:
        return jsonify({"success": False, "mensaje": "El dado no ha sido seleccionado por este agente."}), 400

    if not estado_juego.es_posicion_valida(estado_juego.tableros[agente_id], dado, posicion):
        return jsonify({"success": False, "mensaje": "Posición no válida según las reglas de colocación."}), 400

    estado_juego.tableros[agente_id].append({"dado": dado, "posicion": posicion})
    estado_juego.seleccionados[agente_id].remove(dado)

    estado_juego.siguiente_turno()

    return jsonify(
        {"success": True, "tablero": estado_juego.tableros[agente_id], "turno_siguiente": estado_juego.turno_actual})


@app.route('/estado', methods=['GET'])
def estado():
    return jsonify({
        "ronda_actual": estado_juego.ronda_actual,
        "turno_actual": estado_juego.turno_actual,
        "dados_reserva": estado_juego.dados_reserva,
        "tableros": estado_juego.tableros,
        "colores_asignados": estado_juego.colores_asignados
    })


def calcular_puntaje(tablero, color_asignado):
    filas_completas = sum(
        1 for i in range(4) if all(pos in [d["posicion"] for d in tablero] for pos in [(i, j) for j in range(5)]))
    columnas_completas = sum(
        1 for j in range(5) if all(pos in [d["posicion"] for d in tablero] for pos in [(i, j) for i in range(4)]))

    puntos_color_asignado = sum(1 for d in tablero if d["dado"]["color"] == color_asignado)

    return filas_completas + columnas_completas + puntos_color_asignado


@app.route('/finalizar_juego', methods=['GET'])
def finalizar_juego():
    # calcular el ganador segun sus puntos del dado del color asignado
    puntaje_agente_1 = calcular_puntaje(estado_juego.tableros[1], estado_juego.colores_asignados[1])
    puntaje_agente_2 = calcular_puntaje(estado_juego.tableros[2], estado_juego.colores_asignados[2])

    # sumar los puntos de los dados del color asignado a cada agente
    puntos_color_asignado_agente_1 = sum(d['dado']['valor'] for d in estado_juego.tableros[1] if d['dado']['color'] == estado_juego.colores_asignados[1])
    puntos_color_asignado_agente_2 = sum(d['dado']['valor'] for d in estado_juego.tableros[2] if d['dado']['color'] == estado_juego.colores_asignados[2])

    if puntaje_agente_1 > puntaje_agente_2:
        ganador = "Agente 1"
    elif puntaje_agente_2 > puntaje_agente_1:
        ganador = "Agente 2"
    else:
        ganador = "Empate"

    return jsonify({
        "puntaje_agente_1": puntaje_agente_1,
        "puntos_color_asignado_agente_1": puntos_color_asignado_agente_1,
        "puntaje_agente_2": puntaje_agente_2,
        "puntos_color_asignado_agente_2": puntos_color_asignado_agente_2,
        "colores_asignados": estado_juego.colores_asignados,
        "ganador": ganador
    })

if __name__ == '__main__':
    app.run(debug=True)