#!/usr/bin/env python3
"""
Seed Voice Conversion V2 API

This API provides programmatic access to all voice conversion features available in the web interface.
Supports multiple audio formats (WAV, MP3, OGG) for both input and output.
"""

import argparse
import os
import sys
import json
import tempfile
import uuid
import base64
from pathlib import Path
from typing import Dict, Any, Optional, Union
import warnings
warnings.filterwarnings("ignore")

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import torch
import numpy as np
import gradio as gr
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import the voice conversion wrapper
from modules.v2.vc_wrapper import VoiceConversionWrapper

# Initialize FastAPI app
app = FastAPI(
    title="Seed Voice Conversion V2 API",
    description="Zero-shot voice conversion with in-context learning",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
vc_wrapper = None
device = None
dtype = None

class VoiceConversionRequest(BaseModel):
    """Request model for voice conversion."""

    # Required parameters
    source_audio_path: Optional[str] = Field(None, description="Path to source audio file (alternative to source_audio_base64)")
    target_audio_path: Optional[str] = Field(None, description="Path to reference audio file (alternative to target_audio_base64)")
    source_audio_base64: Optional[str] = Field(None, description="Base64 encoded source audio (alternative to source_audio_path)")
    target_audio_base64: Optional[str] = Field(None, description="Base64 encoded reference audio (alternative to target_audio_path)")

    # Model parameters
    diffusion_steps: int = Field(30, ge=1, le=200, description="Number of diffusion steps")
    length_adjust: float = Field(1.0, ge=0.5, le=2.0, description="Length adjustment factor")

    # Control parameters
    intelligibility_cfg_rate: float = Field(0.5, ge=0.0, le=1.0, description="CFG rate for intelligibility")
    similarity_cfg_rate: float = Field(0.5, ge=0.0, le=1.0, description="CFG rate for similarity")
    top_p: float = Field(0.9, ge=0.1, le=1.0, description="Top-p sampling parameter")
    temperature: float = Field(1.0, ge=0.1, le=2.0, description="Temperature for sampling")
    repetition_penalty: float = Field(1.0, ge=1.0, le=3.0, description="Repetition penalty")

    # Processing options
    convert_style: bool = Field(False, description="Enable style conversion")
    anonymization_only: bool = Field(False, description="Enable anonymization only mode")

    # Output format
    output_format: str = Field("wav", pattern="^(wav|mp3|ogg)$", description="Output audio format")

    # Advanced options
    return_base64: bool = Field(False, description="Return output as base64 encoded string")
    cleanup_temp_files: bool = Field(True, description="Clean up temporary files")

class VoiceConversionResponse(BaseModel):
    """Response model for voice conversion."""

    success: bool = Field(..., description="Whether the conversion was successful")
    message: str = Field(..., description="Status message")

    # Output data
    streaming_output_path: Optional[str] = Field(None, description="Path to streaming output file")
    full_output_path: Optional[str] = Field(None, description="Path to full output file")
    streaming_output_base64: Optional[str] = Field(None, description="Base64 encoded streaming output")
    full_output_base64: Optional[str] = Field(None, description="Base64 encoded full output")

    # Metadata
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    output_format: str = Field(..., description="Actual output format used")
    input_info: Optional[Dict[str, Any]] = Field(None, description="Input audio information")

def setup_device():
    """Setup device and data type."""
    global device, dtype

    if torch.cuda.is_available():
        device = torch.device("cuda")
        dtype = torch.float16
        print(f"Using CUDA device: {torch.cuda.get_device_name()}")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
        dtype = torch.float16
        print("Using MPS device")
    else:
        device = torch.device("cpu")
        dtype = torch.float32
        print("Using CPU device")

    return device, dtype

def load_models(ar_checkpoint_path=None, cfm_checkpoint_path=None, compile=False):
    """Load the voice conversion models."""
    global vc_wrapper

    try:
        print("Loading voice conversion models...")

        # Load models
        from hydra.utils import instantiate
        from omegaconf import DictConfig

        cfg = DictConfig({
            "_target_": "modules.v2.vc_wrapper.VoiceConversionWrapper",
            "sr": 22050,
            "hop_size": 256,
            "mel_fn": {
                "_target_": "modules.audio.mel_spectrogram",
                "_partial_": True,
                "n_fft": 1024,
                "win_size": 1024,
                "hop_size": 256,
                "num_mels": 80,
                "sampling_rate": 22050,
                "fmin": 0,
                "fmax": None,
                "center": False
            },
            "cfm": {
                "_target_": "modules.v2.cfm.CFM",
                "estimator": {
                    "_target_": "modules.v2.dit_wrapper.DiT",
                    "time_as_token": True,
                    "style_as_token": True,
                    "uvit_skip_connection": False,
                    "block_size": 8192,
                    "depth": 13,
                    "num_heads": 8,
                    "hidden_dim": 512,
                    "in_channels": 80,
                    "content_dim": 512,
                    "style_encoder_dim": 192,
                    "class_dropout_prob": 0.1,
                    "dropout_rate": 0.0,
                    "attn_dropout_rate": 0.0
                }
            },
            "cfm_length_regulator": {
                "_target_": "modules.v2.length_regulator.InterpolateRegulator",
                "channels": 512,
                "is_discrete": True,
                "codebook_size": 2048,
                "sampling_ratios": [1, 1, 1, 1],
                "f0_condition": False
            },
            "ar": {
                "_target_": "modules.v2.ar.NaiveWrapper",
                "model": {
                    "_target_": "modules.v2.ar.NaiveTransformer",
                    "config": {
                        "_target_": "modules.v2.ar.NaiveModelArgs",
                        "dropout": 0.0,
                        "rope_base": 10000.0,
                        "dim": 768,
                        "head_dim": 64,
                        "n_local_heads": 2,
                        "intermediate_size": 2304,
                        "n_head": 12,
                        "n_layer": 12,
                        "vocab_size": 2049
                    }
                }
            },
            "ar_length_regulator": {
                "_target_": "modules.v2.length_regulator.InterpolateRegulator",
                "channels": 768,
                "is_discrete": True,
                "codebook_size": 32,
                "sampling_ratios": [],
                "f0_condition": False
            },
            "style_encoder": {
                "_target_": "modules.campplus.DTDNN.CAMPPlus",
                "feat_dim": 80,
                "embedding_size": 192
            },
            "content_extractor_narrow": {
                "_target_": "modules.astral_quantization.default_model.AstralQuantizer",
                "tokenizer_name": "openai/whisper-small",
                "ssl_model_name": "facebook/hubert-large-ll60k",
                "ssl_output_layer": 18,
                "skip_ssl": True,
                "encoder": {
                    "_target_": "modules.astral_quantization.convnext.ConvNeXtV2Stage",
                    "dim": 512,
                    "num_blocks": 12,
                    "intermediate_dim": 1536,
                    "dilation": 1,
                    "input_dim": 1024
                },
                "quantizer": {
                    "_target_": "modules.astral_quantization.bsq.BinarySphericalQuantize",
                    "codebook_size": 32,
                    "dim": 512,
                    "entropy_loss_weight": 0.1,
                    "diversity_gamma": 1.0,
                    "spherical": True,
                    "enable_entropy_loss": True,
                    "soft_entropy_loss": True
                }
            },
            "content_extractor_wide": {
                "_target_": "modules.astral_quantization.default_model.AstralQuantizer",
                "tokenizer_name": "openai/whisper-small",
                "ssl_model_name": "facebook/hubert-large-ll60k",
                "ssl_output_layer": 18,
                "encoder": {
                    "_target_": "modules.astral_quantization.convnext.ConvNeXtV2Stage",
                    "dim": 512,
                    "num_blocks": 12,
                    "intermediate_dim": 1536,
                    "dilation": 1,
                    "input_dim": 1024
                },
                "quantizer": {
                    "_target_": "modules.astral_quantization.bsq.BinarySphericalQuantize",
                    "codebook_size": 2048,
                    "dim": 512,
                    "entropy_loss_weight": 0.1,
                    "diversity_gamma": 1.0,
                    "spherical": True,
                    "enable_entropy_loss": True,
                    "soft_entropy_loss": True
                }
            },
            "vocoder": {
                "_target_": "modules.bigvgan.bigvgan.BigVGAN.from_pretrained",
                "pretrained_model_name_or_path": "nvidia/bigvgan_v2_22khz_80band_256x",
                "use_cuda_kernel": False
            }
        })

        vc_wrapper = instantiate(cfg)

        # Load checkpoints
        if ar_checkpoint_path is None or cfm_checkpoint_path is None:
            from hf_utils import load_custom_model_from_hf
            DEFAULT_REPO_ID = "Plachta/Seed-VC"
            DEFAULT_CFM_CHECKPOINT = "v2/cfm_small.pth"
            DEFAULT_AR_CHECKPOINT = "v2/ar_base.pth"

            if cfm_checkpoint_path is None:
                cfm_checkpoint_path = load_custom_model_from_hf(
                    repo_id=DEFAULT_REPO_ID,
                    model_filename=DEFAULT_CFM_CHECKPOINT,
                )
            if ar_checkpoint_path is None:
                ar_checkpoint_path = load_custom_model_from_hf(
                    repo_id=DEFAULT_REPO_ID,
                    model_filename=DEFAULT_AR_CHECKPOINT,
                )

        vc_wrapper.load_checkpoints(ar_checkpoint_path=ar_checkpoint_path, cfm_checkpoint_path=cfm_checkpoint_path)
        vc_wrapper.to(device)
        vc_wrapper.eval()

        # Setup AR caches with increased size for long audio support
        vc_wrapper.setup_ar_caches(max_batch_size=1, max_seq_len=32768, dtype=dtype, device=device)

        # Optional compilation
        if compile:
            print("Enabling model compilation...")
            torch._inductor.config.coordinate_descent_tuning = True
            torch._inductor.config.triton.unique_kernel_names = True

            if hasattr(torch._inductor.config, "fx_graph_cache"):
                torch._inductor.config.fx_graph_cache = True

            vc_wrapper.compile_ar()

        print("Models loaded successfully!")
        return True

    except Exception as e:
        print(f"Failed to load models: {str(e)}")
        return False

def base64_to_audio(base64_data: str, output_path: str) -> str:
    """Convert base64 encoded audio data to file."""
    try:
        # Decode base64
        audio_data = base64.b64decode(base64_data)

        # Write to file
        with open(output_path, "wb") as f:
            f.write(audio_data)

        return output_path
    except Exception as e:
        raise ValueError(f"Failed to decode base64 audio: {str(e)}")

def audio_to_base64(file_path: str) -> str:
    """Convert audio file to base64 encoded string."""
    try:
        with open(file_path, "rb") as f:
            audio_data = f.read()
        return base64.b64encode(audio_data).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to encode audio to base64: {str(e)}")

def validate_audio_file(file_path: str) -> Dict[str, Any]:
    """Validate audio file and return metadata."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    try:
        import librosa
        # Load audio to get metadata
        audio, sr = librosa.load(file_path, sr=None)

        return {
            "duration": len(audio) / sr,
            "sample_rate": sr,
            "channels": 1,
            "file_size": os.path.getsize(file_path),
            "file_format": os.path.splitext(file_path)[1].lower().lstrip('.')
        }
    except Exception as e:
        raise ValueError(f"Invalid audio file: {str(e)}")

def process_voice_conversion(request: VoiceConversionRequest) -> VoiceConversionResponse:
    """Process voice conversion request."""
    import time
    import tempfile

    start_time = time.time()
    temp_files = []

    try:
        # Validate models are loaded
        if vc_wrapper is None:
            raise RuntimeError("Models not loaded. Please check initialization.")

        # Handle input audio
        source_audio_path = None
        target_audio_path = None

        if request.source_audio_base64 and not request.source_audio_path:
            # Handle base64 encoded source audio
            temp_source = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_files.append(temp_source.name)
            source_audio_path = base64_to_audio(request.source_audio_base64, temp_source.name)
        elif request.source_audio_path:
            source_audio_path = request.source_audio_path
        else:
            raise ValueError("Either source_audio_path or source_audio_base64 must be provided")

        if request.target_audio_base64 and not request.target_audio_path:
            # Handle base64 encoded target audio
            temp_target = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_files.append(temp_target.name)
            target_audio_path = base64_to_audio(request.target_audio_base64, temp_target.name)
        elif request.target_audio_path:
            target_audio_path = request.target_audio_path
        else:
            raise ValueError("Either target_audio_path or target_audio_base64 must be provided")

        # Validate input files
        source_info = validate_audio_file(source_audio_path)
        target_info = validate_audio_file(target_audio_path)

        print(f"Processing audio conversion:")
        print(f"  Source: {source_info['duration']:.2f}s, {source_info['file_format']}")
        print(f"  Target: {target_info['duration']:.2f}s, {target_info['file_format']}")
        print(f"  Output format: {request.output_format}")

        # Process conversion
        full_audio_array = None
        last_streaming_data = None

        results = vc_wrapper.convert_voice_with_streaming(
            source_audio_path=source_audio_path,
            target_audio_path=target_audio_path,
            diffusion_steps=request.diffusion_steps,
            length_adjust=request.length_adjust,
            intelligebility_cfg_rate=request.intelligibility_cfg_rate,
            similarity_cfg_rate=request.similarity_cfg_rate,
            top_p=request.top_p,
            temperature=request.temperature,
            repetition_penalty=request.repetition_penalty,
            convert_style=request.convert_style,
            anonymization_only=request.anonymization_only,
            device=device,
            dtype=dtype,
            stream_output=True,
            output_format="mp3"  # Always use MP3 for streaming
        )

        # Collect results
        for streaming_data, full_audio in results:
            if streaming_data:
                last_streaming_data = streaming_data
            if full_audio is not None:
                full_audio_array = full_audio[1]

        if full_audio_array is None:
            raise RuntimeError("No audio was generated")

        # Handle output based on request format
        streaming_output_path = None
        full_output_path = None
        streaming_output_base64 = None
        full_output_base64 = None

        # Handle full output
        if request.output_format.lower() == "wav":
            # Save as WAV
            full_output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            temp_files.append(full_output_path)
            vc_wrapper.save_audio(full_audio_array, full_output_path, format="wav")
        else:
            # Save as MP3/OGG
            full_output_path = tempfile.NamedTemporaryFile(delete=False, suffix=f".{request.output_format}").name
            temp_files.append(full_output_path)
            vc_wrapper.save_audio(full_audio_array, full_output_path, format=request.output_format)

        # Handle streaming output
        if last_streaming_data:
            streaming_output_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
            temp_files.append(streaming_output_path)
            with open(streaming_output_path, "wb") as f:
                f.write(last_streaming_data)

        # Convert to base64 if requested
        if request.return_base64:
            if streaming_output_path:
                streaming_output_base64 = audio_to_base64(streaming_output_path)
                if request.cleanup_temp_files:
                    os.unlink(streaming_output_path)
                    streaming_output_path = None
                    temp_files.remove(streaming_output_path)

            if full_output_path:
                full_output_base64 = audio_to_base64(full_output_path)
                if request.cleanup_temp_files:
                    os.unlink(full_output_path)
                    full_output_path = None
                    temp_files.remove(full_output_path)

        # Calculate processing time
        processing_time = time.time() - start_time

        # Prepare response
        response = VoiceConversionResponse(
            success=True,
            message="Voice conversion completed successfully",
            streaming_output_path=streaming_output_path,
            full_output_path=full_output_path,
            streaming_output_base64=streaming_output_base64,
            full_output_base64=full_output_base64,
            processing_time=processing_time,
            output_format=request.output_format,
            input_info={
                "source": source_info,
                "target": target_info
            }
        )

        print(f"Conversion completed in {processing_time:.2f}s")
        return response

    except Exception as e:
        print(f"Error during voice conversion: {str(e)}")

        # Clean up temp files on error
        if request.cleanup_temp_files:
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except:
                    pass

        return VoiceConversionResponse(
            success=False,
            message=f"Voice conversion failed: {str(e)}",
            processing_time=time.time() - start_time,
            output_format=request.output_format
        )

# API Endpoints

@app.get("/", response_model=Dict[str, Any])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Seed Voice Conversion V2 API",
        "version": "2.0.0",
        "description": "Zero-shot voice conversion with in-context learning",
        "features": [
            "Multiple audio format support (WAV, MP3, OGG)",
            "Intelligent audio splitting for long files",
            "Style conversion and anonymization",
            "Configurable generation parameters",
            "Base64 encoding support"
        ],
        "endpoints": {
            "health": "/health",
            "convert": "/convert",
            "docs": "/docs"
        }
    }

@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "models_loaded": vc_wrapper is not None,
        "device": str(device) if device else None,
        "cuda_available": torch.cuda.is_available(),
        "gpu_memory": torch.cuda.get_device_properties(0).total_memory if torch.cuda.is_available() else None
    }

@app.post("/convert", response_model=VoiceConversionResponse)
async def convert_voice(request: VoiceConversionRequest):
    """Convert voice using the specified parameters."""
    try:
        response = process_voice_conversion(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/convert/files", response_model=VoiceConversionResponse)
async def convert_voice_with_files(
    source_audio: UploadFile = File(..., description="Source audio file"),
    target_audio: UploadFile = File(..., description="Reference audio file"),
    diffusion_steps: int = Form(30, ge=1, le=200),
    length_adjust: float = Form(1.0, ge=0.5, le=2.0),
    intelligibility_cfg_rate: float = Form(0.5, ge=0.0, le=1.0),
    similarity_cfg_rate: float = Form(0.5, ge=0.0, le=1.0),
    top_p: float = Form(0.9, ge=0.1, le=1.0),
    temperature: float = Form(1.0, ge=0.1, le=2.0),
    repetition_penalty: float = Form(1.0, ge=1.0, le=3.0),
    convert_style: bool = Form(False),
    anonymization_only: bool = Form(False),
    output_format: str = Form("wav"),
    return_base64: bool = Form(False)
):
    """Convert voice using uploaded files."""
    import tempfile

    # Validate output format
    if output_format not in ["wav", "mp3", "ogg"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid output format: {output_format}. Must be one of: wav, mp3, ogg"
        )

    temp_files = []

    try:
        # Save uploaded files
        source_suffix = os.path.splitext(source_audio.filename)[1]
        target_suffix = os.path.splitext(target_audio.filename)[1]

        source_path = tempfile.NamedTemporaryFile(delete=False, suffix=source_suffix).name
        target_path = tempfile.NamedTemporaryFile(delete=False, suffix=target_suffix).name

        temp_files.extend([source_path, target_path])

        # Write uploaded files
        with open(source_path, "wb") as f:
            f.write(await source_audio.read())

        with open(target_path, "wb") as f:
            f.write(await target_audio.read())

        # Create request
        request = VoiceConversionRequest(
            source_audio_path=source_path,
            target_audio_path=target_path,
            diffusion_steps=diffusion_steps,
            length_adjust=length_adjust,
            intelligibility_cfg_rate=intelligibility_cfg_rate,
            similarity_cfg_rate=similarity_cfg_rate,
            top_p=top_p,
            temperature=temperature,
            repetition_penalty=repetition_penalty,
            convert_style=convert_style,
            anonymization_only=anonymization_only,
            output_format=output_format,
            return_base64=return_base64,
            cleanup_temp_files=True
        )

        response = process_voice_conversion(request)

        # Clean up temp files if not returning paths
        if return_base64:
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                except:
                    pass

        return response

    except Exception as e:
        # Clean up temp files on error
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass

        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """Download generated audio file."""
    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        # Get filename from path
        filename = os.path.basename(file_path)

        return FileResponse(
            file_path,
            media_type="application/octet-stream",
            filename=filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cleanup/{file_path:path}")
async def cleanup_file(file_path: str):
    """Clean up temporary files."""
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            return {"message": f"File {file_path} deleted successfully"}
        else:
            return {"message": f"File {file_path} not found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def main():
    """Main function to run the API server."""
    parser = argparse.ArgumentParser(description="Seed Voice Conversion V2 API")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--compile", action="store_true", help="Enable model compilation")
    parser.add_argument("--ar-checkpoint-path", type=str, default=None, help="Path to AR checkpoint")
    parser.add_argument("--cfm-checkpoint-path", type=str, default=None, help="Path to CFM checkpoint")

    args = parser.parse_args()

    print("=" * 60)
    print("Seed Voice Conversion V2 API")
    print("=" * 60)

    # Setup device and load models
    device, dtype = setup_device()

    if not load_models(
        ar_checkpoint_path=args.ar_checkpoint_path,
        cfm_checkpoint_path=args.cfm_checkpoint_path,
        compile=args.compile
    ):
        print("Failed to load models. Exiting.")
        sys.exit(1)

    print(f"Starting API server on {args.host}:{args.port}")
    print(f"Documentation available at: http://{args.host}:{args.port}/docs")
    print(f"ReDoc available at: http://{args.host}:{args.port}/redoc")
    print("=" * 60)

    # Run the server
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()