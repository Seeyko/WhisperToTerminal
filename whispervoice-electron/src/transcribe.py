#!/usr/bin/env python3
"""Transcribe audio using faster-whisper"""
import sys
import os

def transcribe(audio_path, model_name="medium"):
    from faster_whisper import WhisperModel

    # Map model names to faster-whisper compatible names
    model_map = {
        "distil-large-v3": "Systran/faster-distil-whisper-large-v3",
        "distil-large-v2": "Systran/faster-distil-whisper-large-v2",
    }
    actual_model = model_map.get(model_name, model_name)

    # Check if CUDA libs are actually available
    cuda_available = os.path.exists("C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.6/bin/cublas64_12.dll") or \
                     os.path.exists("C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA/v12.0/bin/cublas64_12.dll")

    if cuda_available:
        try:
            print(f"[INFO] Using CUDA with {model_name}...", file=sys.stderr)
            model = WhisperModel(actual_model, device="cuda", compute_type="float16")
        except Exception as e:
            print(f"[INFO] CUDA failed ({e}), using CPU...", file=sys.stderr)
            model = WhisperModel(actual_model, device="cpu", compute_type="int8")
    else:
        print(f"[INFO] Using CPU with {model_name}...", file=sys.stderr)
        model = WhisperModel(actual_model, device="cpu", compute_type="int8")

    segments, info = model.transcribe(audio_path, beam_size=5)
    text = " ".join([segment.text for segment in segments])
    return text.strip()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python transcribe.py <audio_file> [model]", file=sys.stderr)
        sys.exit(1)

    audio_file = sys.argv[1]
    model_name = sys.argv[2] if len(sys.argv) > 2 else "medium"

    result = transcribe(audio_file, model_name)
    print(result)
