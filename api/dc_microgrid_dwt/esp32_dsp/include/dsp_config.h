#pragma once
/**
 * DSP Configuration — ESP32 DC Microgrid Fault Detection
 *
 * All tunable parameters in one place. Matches the x86_64 C++ engine
 * defaults while being optimized for ESP32 memory constraints.
 *
 * To tune for your grid, change ONLY this file — no other code edits needed.
 */

#include <cstddef>
#include <cstdint>

namespace mg {

// ============================================================================
// DSP Pipeline
// ============================================================================
constexpr size_t WINDOW_SIZE      = 128;      // DWT window (must be power of 2)
constexpr size_t DWT_LEVELS       = 4;        // Daubechies-4 decomposition levels
constexpr float  SAMPLE_RATE_HZ   = 20000.0f; // ADC sample rate
constexpr float  FILTER_CUTOFF_HZ = 8000.0f;  // Butterworth anti-alias cutoff
constexpr size_t HISTORY_CAPACITY = 512;       // Voltage ring buffer (reduced from 4096 for RAM)
constexpr size_t ENERGY_HIST_MAX  = 64;        // Energy history entries

// Rolling DWT stride: 1 = every sample (most responsive, ~30µs/sample)
// Higher values reduce CPU but increase detection latency.
// stride=1  → detection in ~80µs (1 sample period + processing)
// stride=32 → detection in ~1.6ms worst case
constexpr size_t DWT_STRIDE       = 1;

// ============================================================================
// Trip Thresholds
// ============================================================================
constexpr float D1_ENERGY_TRIP    = 100.0f;   // D1 energy threshold for fast trip
constexpr float D1_PEAK_TRIP      = 50.0f;    // D1 peak absolute threshold
constexpr float D2_ENERGY_WARN    = 50.0f;    // D2 energy warning level
constexpr float NOISE_FLOOR       = 0.5f;     // Below this → ignore as noise

// ============================================================================
// Hardware Pins
// ============================================================================
constexpr int ADC_PIN             = 36;       // GPIO36 (VP) — analog input
constexpr int RELAY_PIN           = 17;       // GPIO17 — relay/breaker output
constexpr int STATUS_LED_PIN      = 2;        // Built-in LED for status

// ============================================================================
// ADC Scaling
// ============================================================================
// Convert 12-bit ADC (0-4095) to voltage:
//   V_grid = (adc_raw / 4095.0) * V_REF * DIVIDER_RATIO
constexpr float ADC_VREF          = 3.3f;     // ESP32 ADC reference voltage
constexpr float VOLTAGE_DIVIDER   = 200.0f;   // Resistor divider ratio (for 400V DC bus)
// Effective range: 0 - 660V

// ============================================================================
// FreeRTOS Task
// ============================================================================
#ifndef configMAX_PRIORITIES
#define configMAX_PRIORITIES 25   // Default for ESP32 FreeRTOS
#endif
constexpr int   DSP_TASK_PRIORITY = configMAX_PRIORITIES - 1; // Highest priority
constexpr int   DSP_TASK_CORE     = 1;        // Pin to Core 1 (Core 0 = WiFi)
constexpr size_t DSP_TASK_STACK   = 8192;     // Stack size in bytes

// ============================================================================
// Telemetry
// ============================================================================
constexpr unsigned long TELEMETRY_INTERVAL_MS = 1000; // Serial stats every 1s

} // namespace mg
