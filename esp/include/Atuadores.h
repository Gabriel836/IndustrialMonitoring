#pragma once
#include <Arduino.h>
#include "MaquinaEstados.h"

class Atuadores {
public:
  void iniciar();
  void atualizar(EstadoMaquina estado, uint32_t agoraMs);
private:
  EstadoMaquina estadoAnterior_ = EstadoMaquina::DESLIGADA;
  uint32_t inicioEstadoMs_ = 0;
};
