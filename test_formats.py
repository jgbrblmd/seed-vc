#!/usr/bin/env python3
"""Test script for audio format support."""

import sys
import os
sys.path.append('/home/wang/clean/seed-vc')

import numpy as np
import tempfile
from modules.v2.vc_wrapper import VoiceConversionWrapper
import torch

def test_audio_formats():
    """Test if all audio formats can be created properly."""

    # Create a dummy vc_wrapper instance for testing
    class DummyWrapper:
        def __init__(self):
            self.sr = 22050

        def save_audio(self, audio_array, output_path, format="wav", sr=None):
            if sr is None:
                sr = self.sr

            # Normalize audio to prevent clipping and improve quality
            audio_array_norm = audio_array / (np.abs(audio_array).max() + 1e-8) * 0.95
            audio_int16 = (audio_array_norm * 32767).astype(np.int16)

            from pydub import AudioSegment
            import torchaudio

            if format.lower() == "wav":
                torchaudio.save(output_path, torch.from_numpy(audio_int16).float().unsqueeze(0), sr)
            elif format.lower() == "mp3":
                audio_segment = AudioSegment(
                    audio_int16.tobytes(),
                    frame_rate=sr,
                    sample_width=audio_int16.dtype.itemsize,
                    channels=1
                )
                audio_segment.export(output_path, format="mp3", bitrate="320k")
            elif format.lower() == "ogg":
                audio_segment = AudioSegment(
                    audio_int16.tobytes(),
                    frame_rate=sr,
                    sample_width=audio_int16.dtype.itemsize,
                    channels=1
                )
                try:
                    audio_segment.export(output_path, format="ogg", codec="libvorbis")
                except Exception as e:
                    print(f"Failed to export OGG with libvorbis codec, trying fallback: {e}")
                    try:
                        audio_segment.export(output_path, format="ogg")
                    except Exception as e2:
                        print(f"OGG export failed completely: {e2}")
                        raise Exception(f"Could not save OGG file: {e2}")
            else:
                raise ValueError(f"Unsupported format: {format}")

    # Create test audio (1 second of sine wave)
    duration = 1.0  # seconds
    sample_rate = 22050
    frequency = 440  # Hz (A4 note)
    t = np.linspace(0, duration, int(sample_rate * duration))
    test_audio = np.sin(2 * np.pi * frequency * t)

    wrapper = DummyWrapper()

    # Test all formats
    formats = ["wav", "mp3", "ogg"]
    results = {}

    for fmt in formats:
        try:
            with tempfile.NamedTemporaryFile(suffix=f".{fmt}", delete=False) as tmp_file:
                wrapper.save_audio(test_audio, tmp_file.name, format=fmt)

                # Check if file was created and has content
                if os.path.exists(tmp_file.name) and os.path.getsize(tmp_file.name) > 0:
                    results[fmt] = {
                        "success": True,
                        "path": tmp_file.name,
                        "size": os.path.getsize(tmp_file.name)
                    }
                    print(f"✓ {fmt.upper()}: Successfully created, size: {results[fmt]['size']} bytes")

                    # Clean up
                    os.unlink(tmp_file.name)
                else:
                    results[fmt] = {
                        "success": False,
                        "error": "File not created or empty"
                    }
                    print(f"✗ {fmt.upper()}: {results[fmt]['error']}")

        except Exception as e:
            results[fmt] = {
                "success": False,
                "error": str(e)
            }
            print(f"✗ {fmt.upper()}: {results[fmt]['error']}")

    return results

if __name__ == "__main__":
    print("Testing audio format support...")
    results = test_audio_formats()

    success_count = sum(1 for r in results.values() if r["success"])
    total_count = len(results)

    print(f"\nSummary: {success_count}/{total_count} formats work correctly")

    if success_count == total_count:
        print("All formats are working! 🎉")
    else:
        print("Some formats have issues. Check the errors above.")