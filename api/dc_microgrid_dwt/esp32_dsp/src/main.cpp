/**
 * DC Microgrid Fault Detection — ESP32 Firmware
 *
 * This is the main entry point for the ESP32 DSP engine.
 * It creates a high-priority FreeRTOS task on Core 1 that runs the
 * DSP pipeline at 20 kHz, reading from the ADC and tripping the relay
 * on fault detection.
 *
 * Core 0: Arduino loop() — telemetry & system management
 * Core 1: dspTask() — deterministic DSP sampling (pinned, highest priority)
 */

#include <Arduino.h>
#include "dsp_config.h"
#include "dsp_core_esp32.h"

// ============================================================================
// Global DSP Pipeline
// ============================================================================

static mg::DSPPipeline pipeline;
static volatile bool    system_tripped = false;
static volatile int64_t last_trip_sample = 0;

// ============================================================================
// DSP Task — Runs on Core 1 at highest priority
// ============================================================================

void dspTask(void* param) {
    (void)param;

    const unsigned long period_us = (unsigned long)(1000000.0f / mg::SAMPLE_RATE_HZ);

    Serial.printf("[DSP] Task started on Core %d — target rate=%dHz, period=%luus\n",
                  xPortGetCoreID(), (int)mg::SAMPLE_RATE_HZ, period_us);

    while (true) {
        unsigned long loop_start = micros();

        // 1. Read ADC
        int raw_adc = analogRead(mg::ADC_PIN);
        float voltage = ((float)raw_adc / 4095.0f) * mg::ADC_VREF * mg::VOLTAGE_DIVIDER;

        // 2. Process through DSP pipeline
        mg::DSPResult result = pipeline.process_sample(voltage);

        // 3. Immediate trip action
        if (result.trip.triggered && !system_tripped) {
            // OPEN RELAY IMMEDIATELY — this is the critical sub-2ms path
            digitalWrite(mg::RELAY_PIN, HIGH);
            system_tripped = true;
            last_trip_sample = result.sample_count;

            Serial.printf("\n!!! FAULT TRIP @ sample %lld — D1_energy=%.1f, D1_peak=%.1f, latency=%dus !!!\n",
                          result.sample_count,
                          result.trip.d1_energy,
                          result.trip.d1_peak,
                          result.processing_time_us);
        }

        // 4. Precise timing to maintain sample rate
        unsigned long elapsed = micros() - loop_start;
        if (elapsed < period_us) {
            delayMicroseconds(period_us - elapsed);
        }
    }
}

// ============================================================================
// Arduino Setup
// ============================================================================

void setup() {
    Serial.begin(115200);
    delay(500); // Let serial settle

    Serial.println();
    Serial.println("╔══════════════════════════════════════════════════════╗");
    Serial.println("║  DC Microgrid DSP Engine — ESP32                    ║");
    Serial.println("║  Wavelet Fault Detection (Daubechies-4 Lifting)     ║");
    Serial.println("╚══════════════════════════════════════════════════════╝");
    Serial.println();

    // Configure pins
    pinMode(mg::RELAY_PIN, OUTPUT);
    digitalWrite(mg::RELAY_PIN, LOW);  // Relay starts CLOSED (normal operation)

    pinMode(mg::STATUS_LED_PIN, OUTPUT);
    digitalWrite(mg::STATUS_LED_PIN, LOW);

    // Configure ADC
    analogReadResolution(12);       // 12-bit (0-4095)
    analogSetAttenuation(ADC_11db); // Full range 0-3.3V

    // Print configuration
    Serial.printf("[CFG] Window=%d, Levels=%d, Rate=%.0fHz, Cutoff=%.0fHz\n",
                  mg::WINDOW_SIZE, mg::DWT_LEVELS,
                  mg::SAMPLE_RATE_HZ, mg::FILTER_CUTOFF_HZ);
    Serial.printf("[CFG] Thresholds: energy=%.1f, peak=%.1f, noise_floor=%.1f\n",
                  mg::D1_ENERGY_TRIP, mg::D1_PEAK_TRIP, mg::NOISE_FLOOR);
    Serial.printf("[CFG] DWT stride=%d → max detection latency=%.1fms\n",
                  mg::DWT_STRIDE,
                  (float)mg::DWT_STRIDE * 1000.0f / mg::SAMPLE_RATE_HZ);
    Serial.printf("[CFG] ADC pin=%d, Relay pin=%d\n", mg::ADC_PIN, mg::RELAY_PIN);
    Serial.println();

    // Create DSP task on Core 1
    xTaskCreatePinnedToCore(
        dspTask,                    // Task function
        "DSP",                      // Name
        mg::DSP_TASK_STACK,         // Stack size
        NULL,                       // Parameter
        mg::DSP_TASK_PRIORITY,      // Priority (highest)
        NULL,                       // Task handle (not needed)
        mg::DSP_TASK_CORE           // Core 1
    );

    Serial.println("[SYS] DSP task created on Core 1 — system ARMED");
}

// ============================================================================
// Arduino Loop — Telemetry (runs on Core 0, low priority)
// ============================================================================

void loop() {
    static unsigned long last_print = 0;
    static int64_t last_count = 0;

    unsigned long now = millis();
    if (now - last_print >= mg::TELEMETRY_INTERVAL_MS) {
        last_print = now;

        int64_t current_count = pipeline.total_samples();
        float   avg_us        = pipeline.avg_processing_us();
        int64_t trips         = pipeline.total_trips();
        int64_t samples_delta = current_count - last_count;
        last_count = current_count;

        // Status LED: blink normally, solid on trip
        if (system_tripped) {
            digitalWrite(mg::STATUS_LED_PIN, HIGH);
        } else {
            digitalWrite(mg::STATUS_LED_PIN, !digitalRead(mg::STATUS_LED_PIN));
        }

        // Telemetry output
        Serial.printf("[TEL] samples=%lld (+%lld/s) | avg=%.1fus | trips=%lld | %s\n",
                      current_count,
                      samples_delta,
                      avg_us,
                      trips,
                      system_tripped ? "*** TRIPPED ***" : "OK");
    }

    delay(100); // Don't hog Core 0
}
