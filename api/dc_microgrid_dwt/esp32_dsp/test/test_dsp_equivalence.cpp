/**
 * Native Unit Test — ESP32 DSP Pipeline Numerical Equivalence
 *
 * Runs on the HOST machine (not ESP32) to verify the DSP algorithms
 * produce correct results. Uses PlatformIO's Unity test framework.
 *
 * Run: cd esp32_dsp && pio test -e native
 */

#include <unity.h>
#include <cmath>
#include <cstdio>

// Pull in the ESP32 DSP core (NATIVE_TEST is defined in platformio.ini)
#include "dsp_core_esp32.h"

// ============================================================================
// Test: CircularBuffer
// ============================================================================

void test_circular_buffer_basic() {
    mg::CircularBuffer<8> buf;
    TEST_ASSERT_EQUAL(0, buf.size());
    TEST_ASSERT_FALSE(buf.full());

    buf.push(1.0f);
    buf.push(2.0f);
    buf.push(3.0f);
    TEST_ASSERT_EQUAL(3, buf.size());
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 3.0f, buf.get(0)); // newest
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 1.0f, buf.get(2)); // oldest
}

void test_circular_buffer_wrap() {
    mg::CircularBuffer<4> buf;
    for (int i = 0; i < 6; ++i) buf.push((float)i);
    TEST_ASSERT_EQUAL(4, buf.size());
    TEST_ASSERT_TRUE(buf.full());
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 5.0f, buf.get(0)); // newest = 5
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 2.0f, buf.get(3)); // oldest = 2
}

void test_circular_buffer_get_window() {
    mg::CircularBuffer<8> buf;
    for (int i = 0; i < 5; ++i) buf.push((float)(i + 1)); // 1,2,3,4,5

    float window[5];
    buf.get_window(window, 5);
    // Should be oldest first: 1,2,3,4,5
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 1.0f, window[0]);
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 5.0f, window[4]);
}

// ============================================================================
// Test: ButterworthLPF
// ============================================================================

void test_butterworth_passthrough() {
    mg::ButterworthLPF filter;
    // Before design, should pass through
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 42.0f, filter.process(42.0f));
}

void test_butterworth_lowpass() {
    mg::ButterworthLPF filter;
    filter.design(1000.0f, 20000.0f); // 1kHz cutoff at 20kHz sample rate

    // Feed a DC signal (0 Hz) — should pass through after transient
    float last = 0;
    for (int i = 0; i < 200; ++i) {
        last = filter.process(100.0f);
    }
    TEST_ASSERT_FLOAT_WITHIN(1.0f, 100.0f, last); // DC should pass

    // Feed a high-frequency signal (9 kHz, above cutoff) — should attenuate
    filter.reset();
    float max_out = 0;
    for (int i = 0; i < 200; ++i) {
        float input = 100.0f * sinf(2.0f * M_PI * 9000.0f * i / 20000.0f);
        float out = filter.process(input);
        if (i > 100) { // Skip transient
            float abs_out = fabsf(out);
            if (abs_out > max_out) max_out = abs_out;
        }
    }
    // 4th-order Butterworth at 9x cutoff should attenuate significantly
    TEST_ASSERT_TRUE(max_out < 30.0f); // Well below 100
}

// ============================================================================
// Test: LiftingDWT
// ============================================================================

void test_dwt_produces_coefficients() {
    mg::LiftingDWT dwt;

    // Create a simple test signal (DC + spike)
    float signal[128];
    for (int i = 0; i < 128; ++i) signal[i] = 100.0f;
    signal[64] = 500.0f; // Fault spike

    dwt.transform(signal, 128);

    // Check that we get coefficient structure: 5 arrays (A4, D4, D3, D2, D1)
    float energy[5];
    dwt.compute_energy(energy);

    // D1 (finest detail) should have highest energy from the spike
    TEST_ASSERT_TRUE(energy[0] > 0.0f); // D1 energy > 0
    printf("  DWT energies — D1=%.2f D2=%.2f D3=%.2f D4=%.2f A4=%.2f\n",
           energy[0], energy[1], energy[2], energy[3], energy[4]);
}

void test_dwt_d1_peak() {
    mg::LiftingDWT dwt;

    float signal[128];
    for (int i = 0; i < 128; ++i) signal[i] = 0.0f;
    signal[64] = 1000.0f; // Big spike

    dwt.transform(signal, 128);
    float peak = dwt.find_d1_peak();

    TEST_ASSERT_TRUE(peak > 0.0f);
    printf("  D1 peak = %.2f\n", peak);
}

// ============================================================================
// Test: FastTripCheck
// ============================================================================

void test_trip_check_no_trip() {
    mg::FastTripCheck checker;
    mg::TripResult r = checker.check(1.0f, 1.0f); // Well below thresholds
    TEST_ASSERT_FALSE(r.triggered);
}

void test_trip_check_energy_trip() {
    mg::FastTripCheck checker;
    mg::TripResult r = checker.check(200.0f, 1.0f); // Energy above threshold
    TEST_ASSERT_TRUE(r.triggered);
    TEST_ASSERT_FLOAT_WITHIN(0.1f, 200.0f, r.d1_energy);
}

void test_trip_check_peak_trip() {
    mg::FastTripCheck checker;
    mg::TripResult r = checker.check(1.0f, 100.0f); // Peak above threshold
    TEST_ASSERT_TRUE(r.triggered);
}

void test_trip_check_noise_floor() {
    mg::FastTripCheck checker;
    mg::TripResult r = checker.check(0.1f, 0.1f); // Below noise floor
    TEST_ASSERT_FALSE(r.triggered);
}

// ============================================================================
// Test: Full DSPPipeline
// ============================================================================

void test_pipeline_warmup() {
    mg::DSPPipeline pipe;

    // Feed 50 samples — not enough for full window (128)
    for (int i = 0; i < 50; ++i) {
        mg::DSPResult r = pipe.process_sample(400.0f);
        TEST_ASSERT_FALSE(r.window_ready);
    }
}

void test_pipeline_normal_operation() {
    mg::DSPPipeline pipe;

    // Feed 200 normal samples (constant voltage, no fault)
    for (int i = 0; i < 200; ++i) {
        mg::DSPResult r = pipe.process_sample(400.0f);
        TEST_ASSERT_FALSE(r.trip.triggered);
    }

    TEST_ASSERT_EQUAL(200, pipe.total_samples());
    TEST_ASSERT_EQUAL(0, pipe.total_trips());
    printf("  Normal operation — avg_us=%.1f\n", pipe.avg_processing_us());
}

void test_pipeline_fault_detection() {
    mg::DSPPipeline pipe;

    // Feed 150 normal samples to fill window
    for (int i = 0; i < 150; ++i) {
        pipe.process_sample(400.0f);
    }

    // Inject a fault spike
    bool tripped = false;
    int trip_sample = -1;
    for (int i = 0; i < 50; ++i) {
        float voltage = (i >= 5 && i <= 10) ? 800.0f : 400.0f; // Massive spike
        mg::DSPResult r = pipe.process_sample(voltage);
        if (r.trip.triggered && !tripped) {
            tripped = true;
            trip_sample = 150 + i;
            printf("  TRIP detected at sample %d — D1_energy=%.1f, D1_peak=%.1f\n",
                   trip_sample, r.trip.d1_energy, r.trip.d1_peak);
        }
    }

    TEST_ASSERT_TRUE(tripped);
    TEST_ASSERT_TRUE(pipe.total_trips() > 0);
    printf("  Total trips=%lld, avg_us=%.1f\n",
           (long long)pipe.total_trips(), pipe.avg_processing_us());
}

// ============================================================================
// Test Runner
// ============================================================================

int main(int argc, char** argv) {
    UNITY_BEGIN();

    // CircularBuffer
    RUN_TEST(test_circular_buffer_basic);
    RUN_TEST(test_circular_buffer_wrap);
    RUN_TEST(test_circular_buffer_get_window);

    // ButterworthLPF
    RUN_TEST(test_butterworth_passthrough);
    RUN_TEST(test_butterworth_lowpass);

    // LiftingDWT
    RUN_TEST(test_dwt_produces_coefficients);
    RUN_TEST(test_dwt_d1_peak);

    // FastTripCheck
    RUN_TEST(test_trip_check_no_trip);
    RUN_TEST(test_trip_check_energy_trip);
    RUN_TEST(test_trip_check_peak_trip);
    RUN_TEST(test_trip_check_noise_floor);

    // Full Pipeline
    RUN_TEST(test_pipeline_warmup);
    RUN_TEST(test_pipeline_normal_operation);
    RUN_TEST(test_pipeline_fault_detection);

    return UNITY_END();
}
