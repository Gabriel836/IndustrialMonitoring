#!/usr/bin/env python3
"""Supervisório TCP com painel fixo curses. Python 3, Linux, sem dependências externas."""
import argparse
import curses
import socket
import time
from datetime import datetime

CAMPOS = {'STATE', 'TEMP_C', 'HUM_PCT', 'LOAD_PCT', 'DIST_MM', 'DHT_OK', 'TOF_OK', 'REASON'}
ESTADOS = {'DESLIGADA', 'INICIANDO', 'NORMAL', 'ALERTA', 'FALHA'}
TECLAS = {'s': 'START', 'x': 'STOP', 'r': 'RESET', 'i': 'STATUS'}


class Supervisor:
    def __init__(self, servidor):
        self.servidor = servidor
        self.cliente = None
        self.endereco = None
        self.buffer = b''
        self.dados = {}
        self.ultima_leitura = None
        self.hora_leitura = '--:--:--'
        self.conectado_em = None
        self.mensagem = 'Aguardando ESP32.'
        self.comando_pendente = None

    def desconectar(self, motivo):
        if self.cliente is not None:
            self.cliente.close()
        self.cliente = None
        self.endereco = None
        self.buffer = b''
        self.comando_pendente = None
        self.mensagem = motivo

    def enviar(self, comando):
        if self.cliente is None:
            self.mensagem = 'ESP32 desconectado; comando nao enviado.'
            return
        try:
            self.cliente.sendall(('CMD|' + comando + '\n').encode('ascii'))
            self.mensagem = f'{comando} enviado.'
            if comando != 'STATUS':
                self.comando_pendente = (comando, time.monotonic())
                self.mensagem += ' Aguardando resposta.'
        except OSError:
            self.desconectar('Conexao perdida ao enviar comando.')

    def processar(self, linha):
        partes = linha.split('|')
        tipo = partes[0]
        if tipo in ('DATA', 'STATUS'):
            campos = dict(p.split('=', 1) for p in partes[1:] if '=' in p)
            if CAMPOS <= campos.keys() and campos['STATE'] in ESTADOS:
                self.dados = campos
                self.ultima_leitura = time.monotonic()
                self.hora_leitura = datetime.now().strftime('%H:%M:%S')
        elif tipo in ('ACK', 'NACK') and len(partes) >= 3:
            self.mensagem = f'{partes[1]}: {partes[2]}'
            if self.comando_pendente and self.comando_pendente[0] == partes[1]:
                self.comando_pendente = None
        elif tipo == 'EVENT' and len(partes) >= 5 and partes[1] == 'STATE':
            if partes[3] in ESTADOS:
                self.dados.update(STATE=partes[3], REASON=partes[4])
        # Nao ha resposta automatica de teste de rede.

    def atualizar(self):
        if self.cliente is None:
            try:
                self.cliente, self.endereco = self.servidor.accept()
            except (BlockingIOError, InterruptedError):
                return
            self.cliente.settimeout(0.05)
            self.cliente.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.buffer = b''
            self.dados = {}
            self.ultima_leitura = None
            self.hora_leitura = '--:--:--'
            self.conectado_em = time.monotonic()
            self.mensagem = 'ESP32 conectado. Aguardando telemetria.'
        try:
            pacote = self.cliente.recv(4096)
            if not pacote:
                self.desconectar('ESP32 encerrou a conexao.')
                return
            self.buffer += pacote
            while b'\n' in self.buffer:
                linha, self.buffer = self.buffer.split(b'\n', 1)
                if len(linha) <= 512:
                    self.processar(linha.decode('ascii', errors='replace').strip())
            if len(self.buffer) > 4096:
                self.desconectar('Mensagem TCP excessiva.')
                return
        except socket.timeout:
            pass
        except OSError:
            self.desconectar('Conexao perdida. Aguardando reconexao.')
            return
        agora = time.monotonic()
        if self.comando_pendente and agora - self.comando_pendente[1] > 5:
            self.mensagem = self.comando_pendente[0] + ': resposta nao recebida.'
            self.comando_pendente = None
        # A propria telemetria permite detectar uma sessao inativa, sem mensagens extras.
        referencia = self.ultima_leitura if self.ultima_leitura is not None else self.conectado_em
        if agora - referencia > 15:
            self.desconectar('Sem telemetria por 15 s. Aguardando reconexao.')

    def fresco(self):
        return self.cliente is not None and self.ultima_leitura is not None and time.monotonic() - self.ultima_leitura <= 3


def valor(dados, campo, unidade, valido=True):
    v = dados.get(campo, 'NA')
    if v == 'NA':
        return '--'
    return f'{v} {unidade}' + ('' if valido else ' (ultima leitura)')


def painel(tela, sup, porta, cores):
    # O curses compara a tela virtual com a real; nao imprime novas linhas a cada leitura.
    tela.erase()
    h, w = tela.getmaxyx()
    def texto(y, x, s, estilo=0):
        if 0 <= y < h and 0 <= x < w - 1:
            try:
                tela.addnstr(y, x, s, w - x - 1, estilo)
            except curses.error:
                pass
    if h < 20 or w < 58:
        texto(0, 0, 'Aumente o terminal (minimo 58 colunas x 20 linhas).')
        texto(2, 0, 'Q: sair')
        tela.refresh()
        return
    def cor(n):
        return curses.color_pair(n) if cores else 0
    d = sup.dados
    fresco = sup.fresco()
    ativo = sup.cliente is not None
    estado = d.get('STATE', '--')
    estado_cor = {'NORMAL': 2, 'ALERTA': 3, 'FALHA': 4, 'INICIANDO': 1}.get(estado, 0)
    linha = '-' * min(w - 2, 76)
    texto(0, 1, 'MONITORAMENTO INDUSTRIAL  /  ESP32 + RASPBERRY PI', curses.A_BOLD | cor(1))
    texto(1, 1, linha)
    conexao = 'ONLINE' if ativo else 'OFFLINE'
    if ativo and not fresco:
        conexao = 'AGUARDANDO / SEM TELEMETRIA RECENTE'
    texto(2, 1, f'TCP :{porta}   {conexao}', cor(2 if fresco else 3 if ativo else 4))
    texto(3, 1, f'ESP32: {sup.endereco[0] if sup.endereco else "--"}    Ultima leitura: {sup.hora_leitura}')
    texto(4, 1, linha)
    texto(5, 1, 'ESTADO DA MAQUINA', curses.A_BOLD)
    texto(6, 3, estado + ('' if fresco else '  [sem dados atuais]'), curses.A_BOLD | cor(estado_cor if fresco else 3))
    texto(7, 3, 'Motivo: ' + d.get('REASON', '--'))
    texto(8, 1, linha)
    texto(9, 1, 'SENSORES', curses.A_BOLD)
    dht = d.get('DHT_OK') == '1' and fresco
    tof = d.get('TOF_OK') == '1' and fresco
    texto(10, 3, f'Temperatura : {valor(d, "TEMP_C", "°C", dht)}', cor(2 if dht else 3))
    texto(11, 3, f'Umidade     : {valor(d, "HUM_PCT", "%", dht)}', cor(2 if dht else 3))
    texto(12, 3, f'Distancia   : {valor(d, "DIST_MM", "mm", tof)}', cor(2 if tof else 3))
    texto(13, 3, f'Carga       : {valor(d, "LOAD_PCT", "%", fresco)}')
    try:
        carga = max(0, min(100, int(d.get('LOAD_PCT', ''))))
    except ValueError:
        carga = None
    if carga is not None and fresco:
        cheios = carga * 20 // 100
        texto(13, 29, '[' + '#' * cheios + '.' * (20 - cheios) + ']', cor(4 if carga >= 95 else 3 if carga >= 75 else 2))
    texto(14, 3, f'DHT11: {"OK" if dht else "SEM LEITURA VALIDA"}   |   ToF: {"OK" if tof else "INVALIDO"}')
    texto(15, 1, linha)
    texto(16, 1, 'S: iniciar   X: parar   R: reset   I: status   Q: sair', curses.A_BOLD)
    texto(17, 1, 'Comando / rede: ' + sup.mensagem)
    tela.refresh()


def executar(tela, servidor, porta):
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    tela.timeout(100)
    cores = curses.has_colors()
    if cores:
        curses.start_color()
        try:
            curses.use_default_colors()
            fundo = -1
        except curses.error:
            fundo = curses.COLOR_BLACK
        for i, c in enumerate((curses.COLOR_CYAN, curses.COLOR_GREEN, curses.COLOR_YELLOW, curses.COLOR_RED), 1):
            curses.init_pair(i, c, fundo)
    sup = Supervisor(servidor)
    try:
        while True:
            sup.atualizar()
            painel(tela, sup, porta, cores)
            tecla = tela.getch()
            if 0 <= tecla <= 255:
                chave = chr(tecla).lower()
                if chave == 'q':
                    break
                if chave in TECLAS:
                    sup.enviar(TECLAS[chave])
    finally:
        if sup.cliente:
            sup.cliente.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--porta', type=int, default=5000)
    args = parser.parse_args()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind(('0.0.0.0', args.porta))
        servidor.listen(1)
        servidor.setblocking(False)
        try:
            curses.wrapper(executar, servidor, args.porta)
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
