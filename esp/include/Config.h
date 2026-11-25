#pragma once
#include <Arduino.h>

// Projeto para ESP32 DevKit / ESP32-WROOM-32 (nao ESP32-C3/S3).
namespace Config {
// NUNCA publique a senha real do Wi-Fi em um repositorio publico.
constexpr const char* WIFI_SSID = "DANONET_2G";
constexpr const char* WIFI_SENHA = "Gbk62799!";
constexpr uint8_t IP_RPI[4] = {192, 168, 0, 30};
constexpr uint16_t PORTA_TCP = 5000;

// Altere para 1 se o sensor fisico for VL53L1X; 0 = VL53L0X.
#define MODELO_VL53L1X 0

constexpr uint8_t PINO_SDA       = 21;
constexpr uint8_t PINO_SCL       = 22;
constexpr uint8_t PINO_DHT       = 4;
constexpr uint8_t PINO_POT       = 34; // ADC1: funciona durante Wi-Fi
constexpr uint8_t PINO_LED       = 25;
constexpr uint8_t PINO_BUZZER    = 27; // buzzer ATIVO 3,3 V, baixo consumo

// Agendamento cooperativo: millis(), sem delay bloqueante no loop.
constexpr uint32_t PERIODO_TOF_MS     = 200;
constexpr uint32_t PERIODO_DHT_MS     = 2200; // DHT11: nao ler muito rapido
constexpr uint32_t PERIODO_POT_MS     = 100;
constexpr uint32_t VALIDADE_TOF_MS    = 1200;
constexpr uint32_t VALIDADE_DHT_MS    = 7000;
constexpr uint32_t TEMPO_INICIO_MS    = 2000;
constexpr uint32_t PERIODO_TELEMETRIA_MS = 1000;

// Limites e histerese ficam em ConfigLimites.h (nucleo C++ testavel).
// Meios-periodos: 1 Hz, 2,5 Hz e 5 Hz respectivamente.
constexpr uint32_t LED_INICIO_MEIO_PERIODO_MS = 500;
constexpr uint32_t LED_ALERTA_MEIO_PERIODO_MS = 200;
constexpr uint32_t LED_FALHA_MEIO_PERIODO_MS = 100;
} // namespace Config
