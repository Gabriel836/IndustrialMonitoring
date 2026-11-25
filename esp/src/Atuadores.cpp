#include "Atuadores.h"
#include "Config.h"

void Atuadores::iniciar() {
  pinMode(Config::PINO_LED, OUTPUT);
  pinMode(Config::PINO_BUZZER, OUTPUT);
  digitalWrite(Config::PINO_LED, LOW);
  digitalWrite(Config::PINO_BUZZER, LOW);
  inicioEstadoMs_ = millis();
}

void Atuadores::atualizar(EstadoMaquina estado, uint32_t agoraMs) {
  if (estado != estadoAnterior_) {
    estadoAnterior_ = estado;
    inicioEstadoMs_ = agoraMs;
  }
  const uint32_t decorrido = agoraMs - inicioEstadoMs_;
  bool led = false;
  switch (estado) {
    case EstadoMaquina::DESLIGADA: break;
    case EstadoMaquina::INICIANDO:
      led = (decorrido / Config::LED_INICIO_MEIO_PERIODO_MS) % 2U == 0U;
      break;
    case EstadoMaquina::NORMAL: led = true; break;
    case EstadoMaquina::ALERTA:
      led = (decorrido / Config::LED_ALERTA_MEIO_PERIODO_MS) % 2U == 0U;
      break;
    case EstadoMaquina::FALHA:
      led = (decorrido / Config::LED_FALHA_MEIO_PERIODO_MS) % 2U == 0U;
      break;
  }
  digitalWrite(Config::PINO_LED, led ? HIGH : LOW);
  if (estado == EstadoMaquina::FALHA) {
    tone(Config::PINO_BUZZER, 1000);
  } else {
    noTone(Config::PINO_BUZZER);
}
}
