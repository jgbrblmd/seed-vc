import gradio as gr
import torch
import yaml

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

dtype = torch.float16
def load_models(args):
    from hydra.utils import instantiate
    from omegaconf import DictConfig
    cfg = DictConfig(yaml.safe_load(open("configs/v2/vc_wrapper.yaml", "r")))
    vc_wrapper = instantiate(cfg)
    vc_wrapper.load_checkpoints(ar_checkpoint_path=args.ar_checkpoint_path,
                                cfm_checkpoint_path=args.cfm_checkpoint_path)
    vc_wrapper.to(device)
    vc_wrapper.eval()

    vc_wrapper.setup_ar_caches(max_batch_size=1, max_seq_len=32768, dtype=dtype, device=device)

    if args.compile:
        torch._inductor.config.coordinate_descent_tuning = True
        torch._inductor.config.triton.unique_kernel_names = True

        if hasattr(torch._inductor.config, "fx_graph_cache"):
            # Experimental feature to reduce compilation times, will be on by default in future
            torch._inductor.config.fx_graph_cache = True
        vc_wrapper.compile_ar()
        # vc_wrapper.compile_cfm()

    return vc_wrapper

def main(args):
    vc_wrapper = load_models(args)
    
    # Set up Gradio interface
    description = ("Zero-shot voice conversion with in-context learning. For local deployment please check [GitHub repository](https://github.com/Plachtaa/seed-vc) "
                   "for details and updates.<br>Note that reference audio is recommended to be within 120s for best performance.<br> "
                   "Supports processing up to 240s of source audio with intelligent splitting at speech boundaries.<br> "
                   "无需训练的 zero-shot 语音/歌声转换模型，若需本地部署查看[GitHub页面](https://github.com/Plachtaa/seed-vc)<br>"
                   "请注意，参考音频建议不超过 120 秒以获得最佳效果。<br>支持最长 240 秒的源音频处理，会在语音边界智能分割以保持连贯性。")
    
    inputs = [
        gr.Audio(type="filepath", label="Source Audio / 源音频"),
        gr.Audio(type="filepath", label="Reference Audio / 参考音频"),
        gr.Slider(minimum=1, maximum=200, value=30, step=1, label="Diffusion Steps / 扩散步数",
                 info="30 by default, 50~100 for best quality / 默认为 30，50~100 为最佳质量"),
        gr.Slider(minimum=0.5, maximum=2.0, step=0.1, value=1.0, label="Length Adjust / 长度调整",
                 info="<1.0 for speed-up speech, >1.0 for slow-down speech / <1.0 加速语速，>1.0 减慢语速"),
        gr.Slider(minimum=0.0, maximum=1.0, step=0.1, value=0.5, label="Intelligibility CFG Rate",
                 info="has subtle influence / 有微小影响"),
        gr.Slider(minimum=0.0, maximum=1.0, step=0.1, value=0.5, label="Similarity CFG Rate",
                  info="has subtle influence / 有微小影响"),
        gr.Slider(minimum=0.1, maximum=1.0, step=0.1, value=0.9, label="Top-p",
                 info="Controls diversity of generated audio / 控制生成音频的多样性"),
        gr.Slider(minimum=0.1, maximum=2.0, step=0.1, value=1.0, label="Temperature",
                 info="Controls randomness of generated audio / 控制生成音频的随机性"),
        gr.Slider(minimum=1.0, maximum=3.0, step=0.1, value=1.0, label="Repetition Penalty",
                 info="Penalizes repetition in generated audio / 惩罚生成音频中的重复"),
        gr.Checkbox(label="convert style", value=False),
        gr.Checkbox(label="anonymization only", value=False),
        gr.Radio(choices=["wav", "mp3", "ogg"], value="wav", label="Full Output Format / 完整输出格式",
                 info="Choose output format for the full audio / 选择完整输出的音频格式"),
    ]
    
    examples = [
        ["examples/source/yae_0.wav", "examples/reference/dingzhen_0.wav", 50, 1.0, 0.5, 0.5, 0.9, 1.0, 1.0, False, False, "wav"],
        ["examples/source/jay_0.wav", "examples/reference/azuma_0.wav", 50, 1.0, 0.5, 0.5, 0.9, 1.0, 1.0, False, False, "mp3"],
    ]
    
    outputs = [
        gr.Audio(label="Stream Output Audio / 流式输出", streaming=True, format='mp3'),
        gr.Audio(label="Full Output Audio / 完整输出", streaming=False)
    ]
    
    def process_with_format(source_audio, reference_audio, diffusion_steps, length_adjust,
                        intelligibility_cfg, similarity_cfg, top_p, temperature,
                        repetition_penalty, convert_style, anonymization_only, output_format):
        """Wrapper function to handle format selection."""

        import tempfile

        # Process audio only once with streaming enabled
        full_audio_array = None
        last_streaming_data = None

        print(f"Starting audio processing with output format: {output_format}")

        # Run the conversion with streaming enabled to get both outputs in one pass
        results = vc_wrapper.convert_voice_with_streaming(
            source_audio_path=source_audio,
            target_audio_path=reference_audio,
            diffusion_steps=diffusion_steps,
            length_adjust=length_adjust,
            intelligebility_cfg_rate=intelligibility_cfg,
            similarity_cfg_rate=similarity_cfg,
            top_p=top_p,
            temperature=temperature,
            repetition_penalty=repetition_penalty,
            convert_style=convert_style,
            anonymization_only=anonymization_only,
            device=device,
            dtype=dtype,
            stream_output=True,  # Use streaming to get progressive results
            output_format="mp3"  # Always use MP3 for streaming
        )

        # Collect all results during processing
        for streaming_data, full_audio in results:
            if streaming_data:
                last_streaming_data = streaming_data
            if full_audio is not None:
                full_audio_array = full_audio[1]  # Extract the audio array

        # Handle full output in the requested format
        if full_audio_array is not None:
            if output_format.lower() == "wav":
                # For WAV, use the audio array directly
                full_output = (22050, full_audio_array)
            else:
                # For MP3/OGG, save to temp file
                with tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False) as tmp_file:
                    print(f"Saving audio as {output_format} format to {tmp_file.name}")
                    try:
                        vc_wrapper.save_audio(full_audio_array, tmp_file.name, format=output_format)
                        # Verify file was created and has content
                        import os
                        if os.path.exists(tmp_file.name) and os.path.getsize(tmp_file.name) > 0:
                            print(f"Successfully created {output_format} file, size: {os.path.getsize(tmp_file.name)} bytes")
                            full_output = tmp_file.name
                        else:
                            print(f"Failed to create {output_format} file or file is empty")
                            # Fallback to MP3 if OGG fails
                            fallback_format = "mp3"
                            with tempfile.NamedTemporaryFile(suffix=f".{fallback_format}", delete=False) as fallback_file:
                                vc_wrapper.save_audio(full_audio_array, fallback_file.name, format=fallback_format)
                                full_output = fallback_file.name
                                print(f"Fallback: Saved as {fallback_format} instead")
                    except Exception as e:
                        print(f"Error saving {output_format}: {e}")
                        # Fallback to MP3
                        fallback_format = "mp3"
                        with tempfile.NamedTemporaryFile(suffix=f".{fallback_format}", delete=False) as fallback_file:
                            vc_wrapper.save_audio(full_audio_array, fallback_file.name, format=fallback_format)
                            full_output = fallback_file.name
                            print(f"Fallback: Saved as {fallback_format} due to error")

            # Handle streaming output (save last streaming chunk to temp file)
            streaming_path = None
            if last_streaming_data:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_stream:
                    tmp_stream.write(last_streaming_data)
                    streaming_path = tmp_stream.name

            # Final verification
            if output_format.lower() != "wav":
                import os
                if isinstance(full_output, str) and os.path.exists(full_output):
                    actual_size = os.path.getsize(full_output)
                    print(f"Final {output_format.upper()} file: {full_output}, size: {actual_size} bytes")
                else:
                    print(f"Warning: {output_format.upper()} file verification failed")

            return streaming_path, full_output
        else:
            return None, None

    # Launch the Gradio interface
    gr.Interface(
        fn=process_with_format,
        description=description,
        inputs=inputs,
        outputs=outputs,
        title="Seed Voice Conversion V2",
        examples=examples,
        cache_examples=False,
    ).launch()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--compile", action="store_true", help="Compile the model using torch.compile")
    # V2 custom checkpoints
    parser.add_argument("--ar-checkpoint-path", type=str, default=None,
                        help="Path to custom checkpoint file")
    parser.add_argument("--cfm-checkpoint-path", type=str, default=None,
                        help="Path to custom checkpoint file")
    args = parser.parse_args()
    main(args)