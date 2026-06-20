import math
import logging

logger = logging.getLogger(__name__)

def calculate_pulse_duration(current_data: list, timebase: int) -> float:
    """
    Calculates the duration of the current pulse (positive or negative half cycle)
    in milliseconds from the PicoScope current waveform data.
    """
    if not current_data or len(current_data) < 2:
        return 0.0

    # Calculate interval per sample in milliseconds
    interval_ns = 10 * (2 ** timebase)
    interval_ms = interval_ns / 1000000.0

    # Find peak absolute value to set threshold
    peak_val = max(abs(x) for x in current_data)
    
    # Noise threshold: if peak value is too small, assume no pulse
    if peak_val < 0.05:
        logger.debug(f"Peak current value ({peak_val:.2f}) is below noise threshold 0.05. No pulse detected.")
        return 0.0

    # Find the index of the peak absolute value
    max_idx = 0
    for i in range(len(current_data)):
        if abs(current_data[i]) == peak_val:
            max_idx = i
            break

    # Determine start and end indices using a 1.5% peak threshold
    threshold = peak_val * 0.015

    # Walk backwards from the peak to find the start of the pulse
    start_idx = max_idx
    while start_idx > 0 and abs(current_data[start_idx]) >= threshold:
        start_idx -= 1

    # Walk forwards from the peak to find the end of the pulse
    end_idx = max_idx
    while end_idx < len(current_data) - 1 and abs(current_data[end_idx]) >= threshold:
        end_idx += 1

    duration_samples = end_idx - start_idx
    duration_ms = duration_samples * interval_ms
    logger.debug(f"Detected current pulse from index {start_idx} to {end_idx} ({duration_samples} samples, {duration_ms:.2f} ms). Peak: {peak_val:.2f}")
    return duration_ms

def calculate_pf_from_duration(duration_ms: float) -> float:
    """
    Calculates the Power Factor (PF) from the pulse duration in milliseconds.
    Formula:
        extra_ms = duration_ms - 10.0
        angle_deg = extra_ms * 18.0 (1ms = 18 degrees at 50Hz half cycle)
        pf = cos(angle_deg)
    """
    if duration_ms <= 0.0:
        return 1.0 # Default to UPF

    extra_ms = duration_ms - 10.0
    angle_deg = extra_ms * 18.0
    pf = math.cos(math.radians(angle_deg))
    
    # Clamp between 0.0 and 1.0
    pf_clamped = max(0.0, min(1.0, pf))
    logger.debug(f"Duration: {duration_ms:.2f} ms -> Extra: {extra_ms:.2f} ms -> Angle: {angle_deg:.1f}° -> PF: {pf_clamped:.3f}")
    return pf_clamped
