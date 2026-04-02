#pragma once
/**
 * DC Microgrid DSP Core — ESP32 Port
 *
 * Faithful port of the x86_64 dsp_core.h / dsp_core.cpp engine.
 * Every algorithm is preserved exactly — only the platform layer changes:
 *
 *   double        → float       (ESP32 HW FPU is single-precision only)
 *   std::vector   → static arrays (no heap in the hot path)
 *   std::mutex    → (removed)    (single-task, ISR-pinned to one core)
 *   std::chrono   → micros()     (ESP32 hardware timer)
 *
 * Performance target: ≤40 µs per sample at 240 MHz → sub-2ms fault detection.
 */

#include "dsp_config.h"
#include <cmath>
#include <cstring>
#include <algorithm>

// For native testing, provide a micros() stub
#ifdef NATIVE_TEST
static unsigned long _native_micros_counter = 0;
static inline unsigned long micros() { return _native_micros_counter++; }
#else
#include <Arduino.h>
#endif

namespace mg {

// ============================================================================
// TripResult
// ============================================================================

struct TripResult {
    bool   triggered      = false;
    float  d1_energy      = 0.0f;
    float  d1_peak        = 0.0f;
    float  threshold_used = 0.0f;
    int64_t timestamp_us  = 0;
};

// ============================================================================
// DSPResult
// ============================================================================

struct DSPResult {
    float  energy_levels[5] = {0};  // D1, D2, D3, D4, A4
    float  d1_peak           = 0.0f;
    float  total_energy      = 0.0f;
    float  high_freq_ratio   = 0.0f;
    TripResult trip;
    float  filtered_value    = 0.0f;
    int32_t processing_time_us = 0;
    int64_t sample_count     = 0;
    bool   window_ready      = false;
};

// ============================================================================
// CircularBuffer — Zero-allocation ring buffer
// ============================================================================

template <size_t CAPACITY>
class CircularBuffer {
public:
    CircularBuffer() { memset(buffer_, 0, sizeof(buffer_)); }

    void push(float value) {
        buffer_[head_] = value;
        head_ = (head_ + 1) % CAPACITY;
        if (count_ < CAPACITY) ++count_;
    }

    float get(size_t index_from_newest) const {
        if (index_from_newest >= count_) return 0.0f;
        size_t idx = (head_ + CAPACITY - 1 - index_from_newest) % CAPACITY;
        return buffer_[idx];
    }

    size_t size() const { return count_; }
    bool   full() const { return count_ >= CAPACITY; }

    void clear() {
        head_ = 0;
        count_ = 0;
        memset(buffer_, 0, sizeof(buffer_));
    }

    // Copy N most recent samples into `out` (oldest first)
    void get_window(float* out, size_t count) const {
        size_t n = (count < count_) ? count : count_;
        for (size_t i = 0; i < n; ++i) {
            out[n - 1 - i] = get(i);
        }
    }

private:
    float  buffer_[CAPACITY];
    size_t head_  = 0;
    size_t count_ = 0;
};

// ============================================================================
// ButterworthLPF — 4th-order IIR (2 cascaded biquads), identical algorithm
// ============================================================================

class ButterworthLPF {
public:
    ButterworthLPF() = default;

    void design(float cutoff_hz, float sample_rate_hz) {
        float wc = 2.0f * sample_rate_hz * tanf(M_PI * cutoff_hz / sample_rate_hz);
        float K  = wc / (2.0f * sample_rate_hz);
        float K2 = K * K;

        // 4th-order Butterworth: two biquad sections
        float Q1 = 1.0f / (2.0f * cosf(M_PI / 8.0f));     // ≈ 0.5412
        float Q2 = 1.0f / (2.0f * cosf(3.0f * M_PI / 8.0f)); // ≈ 1.3066

        design_biquad(sections_[0], K, K2, Q1);
        design_biquad(sections_[1], K, K2, Q2);
        designed_ = true;
    }

    float process(float input) {
        if (!designed_) return input;
        float y = sections_[0].process(input);
        return sections_[1].process(y);
    }

    void reset() {
        sections_[0].reset();
        sections_[1].reset();
    }

private:
    struct Biquad {
        float b0 = 1, b1 = 0, b2 = 0;
        float a1 = 0, a2 = 0;
        float z1 = 0, z2 = 0;

        float process(float x) {
            float y = b0 * x + z1;
            z1 = b1 * x - a1 * y + z2;
            z2 = b2 * x - a2 * y;
            return y;
        }

        void reset() { z1 = z2 = 0; }
    };

    void design_biquad(Biquad& bq, float K, float K2, float Q) {
        float norm = 1.0f + K / Q + K2;
        bq.b0 = K2 / norm;
        bq.b1 = 2.0f * K2 / norm;
        bq.b2 = K2 / norm;
        bq.a1 = 2.0f * (K2 - 1.0f) / norm;
        bq.a2 = (1.0f - K / Q + K2) / norm;
        bq.z1 = bq.z2 = 0.0f;
    }

    Biquad sections_[2];
    bool   designed_ = false;
};

// ============================================================================
// LiftingDWT — Daubechies-4 via Lifting Scheme (zero-heap version)
// ============================================================================

class LiftingDWT {
public:
    static constexpr size_t MAX_WINDOW = WINDOW_SIZE;
    static constexpr size_t MAX_LEVELS = DWT_LEVELS;
    // Padded to next power of 2
    static constexpr size_t PADDED = MAX_WINDOW; // WINDOW_SIZE is already power of 2

    LiftingDWT() = default;

    /**
     * Transform signal in-place. Coefficients written to coeff_out.
     * coeff_out layout: [A_n, D_n, D_{n-1}, ..., D_1]
     *   index 0 = deepest approximation
     *   index DWT_LEVELS = D1 (finest detail)
     *
     * Each sub-array is stored flat with a length field.
     */
    void transform(const float* signal, size_t sig_len) {
        // Copy into work buffer with symmetric boundary extension
        size_t padded = 1;
        while (padded < sig_len) padded <<= 1;
        if (padded > PADDED) padded = PADDED; // Safety clamp

        memcpy(work_, signal, sig_len * sizeof(float));
        for (size_t i = sig_len; i < padded; ++i) {
            work_[i] = signal[2 * sig_len - 2 - i]; // Mirror
        }

        size_t current_len = padded;
        for (size_t level = 0; level < MAX_LEVELS; ++level) {
            lifting_step(work_, current_len);
            size_t half = current_len / 2;

            // Extract detail coefficients: result[MAX_LEVELS - level] = D_{level+1}
            size_t dest_idx = MAX_LEVELS - level;
            coeff_len_[dest_idx] = half;
            memcpy(coeffs_[dest_idx], work_ + half, half * sizeof(float));

            current_len = half;
        }

        // Remaining = deepest approximation
        coeff_len_[0] = current_len;
        memcpy(coeffs_[0], work_, current_len * sizeof(float));
    }

    /**
     * Compute energy per level: [D1, D2, D3, D4, A4]
     */
    void compute_energy(float energy_out[5]) const {
        // D1 = coeffs_[MAX_LEVELS], D2 = coeffs_[MAX_LEVELS-1], etc.
        for (int i = 0; i < 4; ++i) {
            size_t idx = MAX_LEVELS - i;
            energy_out[i] = calc_energy(coeffs_[idx], coeff_len_[idx]);
        }
        // A4 = coeffs_[0]
        energy_out[4] = calc_energy(coeffs_[0], coeff_len_[0]);
    }

    /**
     * Peak absolute value of D1 coefficients.
     */
    float find_d1_peak() const {
        const float* d1 = coeffs_[MAX_LEVELS];
        size_t len = coeff_len_[MAX_LEVELS];
        float peak = 0.0f;
        for (size_t i = 0; i < len; ++i) {
            float abs_v = fabsf(d1[i]);
            if (abs_v > peak) peak = abs_v;
        }
        return peak;
    }

private:
    // Work buffer (in-place lifting)
    float work_[PADDED];

    // Coefficient storage: [A4, D4, D3, D2, D1]
    // Max sub-array size = PADDED / 2
    float  coeffs_[MAX_LEVELS + 1][PADDED / 2];
    size_t coeff_len_[MAX_LEVELS + 1] = {0};

    // Scratch buffers for lifting (avoid stack alloc in hot path)
    float even_[PADDED / 2];
    float odd_[PADDED / 2];

    void lifting_step(float* data, size_t length) {
        // Daubechies-4 lifting coefficients
        static const float sqrt3     = sqrtf(3.0f);
        static const float c1        = sqrt3;
        static const float c2        = sqrt3 / 4.0f;
        static const float c3        = (sqrt3 - 2.0f) / 4.0f;
        static const float scale     = (sqrt3 + 1.0f) / (2.0f * sqrtf(2.0f));
        static const float inv_scale = (sqrt3 - 1.0f) / (2.0f * sqrtf(2.0f));

        size_t half = length / 2;
        if (half == 0) return;

        // Split into even/odd
        for (size_t i = 0; i < half; ++i) {
            even_[i] = data[2 * i];
            odd_[i]  = data[2 * i + 1];
        }

        // Predict step 1
        for (size_t i = 0; i < half; ++i) {
            odd_[i] += c1 * even_[i];
        }

        // Update step 1
        for (size_t i = 0; i < half; ++i) {
            size_t prev = (i == 0) ? half - 1 : i - 1;
            even_[i] += c2 * odd_[i] + c3 * odd_[prev];
        }

        // Predict step 2
        for (size_t i = 0; i < half; ++i) {
            size_t next = (i + 1) % half;
            odd_[i] -= even_[next];
        }

        // Scale
        for (size_t i = 0; i < half; ++i) {
            even_[i] *= scale;
            odd_[i]  *= inv_scale;
        }

        // Write back: approximation + detail
        for (size_t i = 0; i < half; ++i) {
            data[i]        = even_[i];
            data[half + i] = odd_[i];
        }
    }

    static float calc_energy(const float* v, size_t len) {
        if (len == 0) return 0.0f;
        float sum = 0.0f;
        for (size_t i = 0; i < len; ++i) sum += v[i] * v[i];
        return sum / (float)len;
    }
};

// ============================================================================
// FastTripCheck — Sub-microsecond threshold comparator
// ============================================================================

class FastTripCheck {
public:
    FastTripCheck() = default;

    TripResult check(float d1_energy, float d1_peak) {
        TripResult result;
        result.timestamp_us  = (int64_t)micros();
        result.d1_energy     = d1_energy;
        result.d1_peak       = d1_peak;
        result.threshold_used = D1_ENERGY_TRIP;

        // Skip noise floor
        if (d1_energy < NOISE_FLOOR && d1_peak < NOISE_FLOOR) {
            return result;
        }

        // OR logic: either energy or peak exceeds threshold → TRIP
        if (d1_energy > D1_ENERGY_TRIP || d1_peak > D1_PEAK_TRIP) {
            result.triggered = true;
        }

        return result;
    }
};

// ============================================================================
// DSPPipeline — Full sample→trip orchestration (ESP32 optimized)
// ============================================================================

class DSPPipeline {
public:
    DSPPipeline() {
        filter_.design(FILTER_CUTOFF_HZ, SAMPLE_RATE_HZ);
        memset(energy_history_, 0, sizeof(energy_history_));
    }

    /**
     * Process one ADC sample through the full pipeline.
     * MUST be called from a single task (no locking needed).
     */
    DSPResult process_sample(float raw_voltage) {
        unsigned long start = micros();

        DSPResult result;
        result.sample_count = ++sample_count_;

        // Step 1: Anti-aliasing filter
        float filtered = filter_.process(raw_voltage);
        result.filtered_value = filtered;

        // Step 2: Store in circular buffer
        sample_buffer_.push(filtered);

        // Step 3: Check if we have enough samples for DWT
        if (sample_buffer_.size() < WINDOW_SIZE) {
            result.window_ready = false;
            result.processing_time_us = (int32_t)(micros() - start);
            return result;
        }

        result.window_ready = true;

        // Step 4: Rolling DWT
        ++stride_counter_;
        if (stride_counter_ >= DWT_STRIDE) {
            stride_counter_ = 0;

            // Get current window into local buffer
            float window[WINDOW_SIZE];
            sample_buffer_.get_window(window, WINDOW_SIZE);

            // Run DWT
            dwt_.transform(window, WINDOW_SIZE);

            // Compute energy levels
            dwt_.compute_energy(result.energy_levels);
            result.d1_peak = dwt_.find_d1_peak();

            // Total energy (detail levels only)
            result.total_energy = 0;
            for (int i = 0; i < 4; ++i) result.total_energy += result.energy_levels[i];
            result.high_freq_ratio = (result.total_energy > 0.001f)
                ? result.energy_levels[0] / result.total_energy : 0.0f;

            // Store in energy history ring buffer
            memcpy(energy_history_[energy_hist_write_], result.energy_levels, sizeof(float) * 5);
            energy_hist_write_ = (energy_hist_write_ + 1) % ENERGY_HIST_MAX;
            if (energy_hist_count_ < ENERGY_HIST_MAX) ++energy_hist_count_;

            // Step 5: Fast trip check
            result.trip = trip_check_.check(result.energy_levels[0], result.d1_peak);
            if (result.trip.triggered) {
                ++trip_count_;
            }
        } else {
            // Between DWT runs, carry forward last energy
            if (energy_hist_count_ > 0) {
                size_t last = (energy_hist_write_ + ENERGY_HIST_MAX - 1) % ENERGY_HIST_MAX;
                memcpy(result.energy_levels, energy_history_[last], sizeof(float) * 5);
            }
        }

        result.processing_time_us = (int32_t)(micros() - start);
        total_processing_us_ += result.processing_time_us;

        return result;
    }

    void reset() {
        filter_.reset();
        sample_buffer_.clear();
        memset(energy_history_, 0, sizeof(energy_history_));
        sample_count_ = 0;
        trip_count_ = 0;
        total_processing_us_ = 0;
        stride_counter_ = 0;
        energy_hist_write_ = 0;
        energy_hist_count_ = 0;
    }

    // Stats
    int64_t total_samples() const { return sample_count_; }
    int64_t total_trips()   const { return trip_count_; }
    float   avg_processing_us() const {
        return sample_count_ > 0
            ? (float)total_processing_us_ / (float)sample_count_
            : 0.0f;
    }

private:
    ButterworthLPF                  filter_;
    CircularBuffer<HISTORY_CAPACITY> sample_buffer_;
    LiftingDWT                      dwt_;
    FastTripCheck                   trip_check_;

    // Energy history ring buffer
    float   energy_history_[ENERGY_HIST_MAX][5];
    size_t  energy_hist_write_ = 0;
    size_t  energy_hist_count_ = 0;

    // Counters
    int64_t sample_count_ = 0;
    int64_t trip_count_   = 0;
    double  total_processing_us_ = 0;
    size_t  stride_counter_ = 0;
};

} // namespace mg
