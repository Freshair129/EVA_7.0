"""
compute_pulse_drift.py

EVA ECL Module: Pulse Engine
อ้างอิงสเปกจาก Pulse_EngineLogic และความสำคัญของ Temporal Channel ใน RI

หน้าที่:
- รับ timestamp_prev, timestamp_now
- คำนวณ latency, drift_score, pulse_state

Logic: ปรับเกณฑ์ Pulse State และ Drift Score ให้สะท้อน Temporal Stability ที่แท้จริง
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Dict
import math


PulseState = Literal["stable", "slightly_delayed", "unstable_lag", "overdrive", "unknown"]


@dataclass
class PulseResult:
    drift_score: float
    pulse_state: PulseState
    latency_ms: float


def _compute_latency_ms(timestamp_prev: float, timestamp_now: float) -> float:
    """
    คำนวณ Latency เป็นมิลลิวินาที (ms)
    """
    dt = float(timestamp_now) - float(timestamp_prev)
    return max(0.0, dt * 1000.0)


def _classify_pulse_state(latency_ms: float) -> PulseState:
    """
    เกณฑ์การจัดประเภท Pulse State ที่สอดคล้องกับ Logic การควบคุมจังหวะของ LYRA OS
    อ้างอิงค่า Baseline/Max Latency ที่พบใน Memory_Log.json (Turn 1=1234ms, Turn 2=2056ms, Turn 3=1056ms)
    
    เกณฑ์ที่ใช้:
      - Baseline Target: 1200ms (ค่าเฉลี่ยในอุดมคติ)
      - Max Tolerable Delay: 4000ms
    """
    # 1. Overdrive/Too Fast (เสี่ยงต่อการประมวลผลไม่สมบูรณ์)
    if latency_ms < 500.0:
        return "overdrive"
        
    # 2. Stable (อยู่ในช่วงปกติ, ประมวลผลได้ราบรื่น)
    if 500.0 <= latency_ms <= 1500.0:
        return "stable"
        
    # 3. Slightly Delayed (เริ่มมีภาระงานสูงหรือความต่อเนื่องเริ่มลด)
    if 1500.0 < latency_ms <= 4000.0:
        return "slightly_delayed"
        
    # 4. Unstable (ล่าช้าเกินไป, สัญญาณความไม่เสถียรของ Temporal)
    if latency_ms > 4000.0:
        return "unstable_lag"
        
    return "unknown"


def _compute_drift_score(latency_ms: float, baseline_ms: float = 1200.0) -> float:
    """
    drift_score = Normalized Absolute Deviation
    
    - baseline_ms = 1200.0 (ms)
    - Normalized Max Deviation = 5000 ms (deviation 5s = drift 1.0)
    """
    if baseline_ms <= 0:
        return 0.0
        
    deviation = abs(latency_ms - baseline_ms)
    # ใช้น้ำหนักที่กำหนด: normalize ให้อยู่ระหว่าง 0.0 ถึง 1.0
    score = deviation / 5000.0 
    
    return max(0.0, min(1.0, score))


def compute_pulse_drift(
    timestamp_prev: float,
    timestamp_now: float,
) -> Dict[str, object]:
    """
    entry หลัก: คำนวณ Temporal metrics
    """
    latency_ms = _compute_latency_ms(timestamp_prev, timestamp_now)
    pulse_state = _classify_pulse_state(latency_ms)
    drift_score = _compute_drift_score(latency_ms)
    
    # NOTE: จำลองค่า latency_percent_of_max ตาม Injection_Validation_Log.yaml
    # Max latency budget สมมติที่ 5000ms
    latency_vs_max_percent = (latency_ms / 5000.0) * 100.0
    latency_vs_max_percent = min(100.0, max(0.0, latency_vs_max_percent))

    return {
        "drift_score": round(drift_score, 4),
        "pulse_state": pulse_state,
        "latency_ms": round(latency_ms, 2),
        "latency_vs_max_percent": round(latency_vs_max_percent, 2), # เพิ่ม field นี้เพื่อความสมบูรณ์
    }