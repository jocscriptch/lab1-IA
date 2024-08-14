import requests
import matplotlib.pyplot as plt
import numpy as np


class Agente:
    def __init__(self, agente_id):
        self.agente_id = agente_id
        self.tablero = []
        self.seleccionados = []

    def solicitar_dados(self, dados_disponibles):
        self.seleccionados = []
        for dado in dados_disponibles:
            if len(self.seleccionados) < 2:
                self.seleccionados.append(dado)
        print(f"Agente{self.agente_id}: Ha seleccionado los dados {self.seleccionados}")
        return self.seleccionados

    def colocar_dado(self, dado):
        # colocar el dado en la primera posicion valida
        for fila in range(4):
            for columna in range(5):
                if self.es_posicion_valida(dado, (fila, columna)):
                    return (fila, columna)
        return None

    def es_posicion_valida(self, dado, posicion):
        fila, columna = posicion
        # comprobar si la celda ya esta ocupada
        for d in self.tablero:
            if d["posicion"] == posicion:
                return False

        # el primer dado, va en el borde
        if len(self.tablero) == 0:
            if fila == 0 or fila == 3 or columna == 0 or columna == 4:
                return True
            else:
                return False

        # verificar adyacencia y reglas de colocacion
        adyacente = False
        for d in self.tablero:
            f, c = d["posicion"]
            if abs(fila - f) <= 1 and abs(columna - c) <= 1:
                adyacente = True
                if fila == f or columna == c:
                    if d["dado"]["color"] == dado["color"] or d["dado"]["valor"] == dado["valor"]:
                        return False

        return adyacente

    def jugar_turno(self, servidor_url):
        estado = requests.get(f"{servidor_url}/estado").json()

        if estado['turno_actual'] != self.agente_id:
            return False

        if len(self.seleccionados) == 0:
            dados_disponibles = estado['dados_reserva']
            self.solicitar_dados(dados_disponibles)

            for dado in self.seleccionados:
                response = requests.post(f"{servidor_url}/solicitar_dado", json={
                    "agente_id": self.agente_id,
                    "dado": dado
                }).json()

        if len(self.seleccionados) > 0:
            dado_a_jugar = self.seleccionados.pop(0)
            posicion = self.colocar_dado(dado_a_jugar)
            if posicion:
                response = requests.post(f"{servidor_url}/colocar_dado", json={
                    "agente_id": self.agente_id,
                    "dado": dado_a_jugar,
                    "posicion": posicion
                }).json()
                self.tablero.append({"dado": dado_a_jugar, "posicion": posicion})
                print(f"Agente{self.agente_id}: Jugó el dado {dado_a_jugar} en la posición {posicion}")
            else:
                print(f"Agente{self.agente_id}: No pudo jugar el dado {dado_a_jugar} en ninguna posición válida.")
        else:
            print(f"Agente{self.agente_id}: No pudo jugar en este turno y pasa.")

        return True


# crear los agentes
agente1 = Agente(1)
agente2 = Agente(2)
servidor_url = "http://127.0.0.1:5000"

def color_to_rgb(color_name):
    colors = {
        "rojo": "red",
        "azul": "blue",
        "verde": "green",
        "amarillo": "yellow",
        "morado": "purple"
    }
    return colors.get(color_name, "black")

def mostrar_tableros(agente1, agente2, ronda):
    fig, axs = plt.subplots(1, 2, figsize=(12, 6))

    # tablero Agente 1
    axs[0].imshow(np.zeros((4, 5)), cmap='gray', vmin=0, vmax=1)
    for d in agente1.tablero:
        fila, columna = d["posicion"]
        axs[0].text(columna, fila, f'{d["dado"]["valor"]}', ha='center', va='center', fontsize=16,
                    bbox=dict(facecolor=color_to_rgb(d["dado"]["color"]), edgecolor='black', boxstyle='round,pad=0.5'))

    axs[0].set_title(f'Agente 1 (ID: {agente1.agente_id})')
    axs[0].axis('off')

    # tablero Agente 2
    axs[1].imshow(np.zeros((4, 5)), cmap='gray', vmin=0, vmax=1)
    for d in agente2.tablero:
        fila, columna = d["posicion"]
        axs[1].text(columna, fila, f'{d["dado"]["valor"]}', ha='center', va='center', fontsize=16,
                    bbox=dict(facecolor=color_to_rgb(d["dado"]["color"]), edgecolor='black', boxstyle='round,pad=0.5'))

    axs[1].set_title(f'Agente 2 (ID: {agente2.agente_id})')
    axs[1].axis('off')

    plt.suptitle(f'Ronda {ronda}', fontsize=20)
    plt.show()

# simulando la partida
for ronda in range(1, 11):
    response = requests.post(f"{servidor_url}/iniciar_ronda").json()
    dados_disponibles = response["dados"]
    print(f"Ronda {ronda}: Dados disponibles {dados_disponibles}")

    agente1.jugar_turno(servidor_url)
    agente2.jugar_turno(servidor_url)
    agente1.jugar_turno(servidor_url)
    agente2.jugar_turno(servidor_url)

    print(f"Ronda {ronda}: Terminada\n")
    mostrar_tableros(agente1, agente2, ronda)

resultado = requests.get(f"{servidor_url}/finalizar_juego").json()
print(f"El juego ha terminado. Ganador: {resultado['ganador']}")