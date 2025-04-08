import gradio as gr
import asyncio
import tempfile
import os
from pathlib import Path
from tts import EdgeTTSWithAccents
import time

# Initialize TTS engine
tts_engine = EdgeTTSWithAccents()

# Global variables to store state
last_text = ""
last_audio_path = None
is_processing = False
last_typing_time = 0
typing_timer = None


async def process_text(text, accent, gender, voice, progress=gr.Progress()):
    """Process text to speech and return the audio file path"""
    global last_text, last_audio_path, is_processing, last_typing_time
    
    if not text.strip():
        return None, "Please enter some text to convert to speech."
    
    try:
        is_processing = True
        last_text = text
        last_typing_time = time.time()
        
        # Create a temporary file for the audio
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_path = temp_file.name
            last_audio_path = temp_path
        
        # Get available voices for the selected accent and gender
        voices = tts_engine.available_accents[accent][gender]
        voice_index = voices.index(voice)
        
        # Show progress
        for i in progress.tqdm(range(100)):
            time.sleep(0.01)  # Simulate processing time
        
        # Convert text to speech
        output_file = await tts_engine.convert_text_to_speech(
            text=text,
            accent=accent,
            gender=gender,
            voice_index=voice_index,
            output_file=last_audio_path
        )
        
        if output_file:
            return str(output_file), "Speech generated successfully!"
        else:
            return None, "Failed to generate speech. Please try again."
            
    except Exception as e:
        return None, f"An error occurred: {str(e)}"
    finally:
        is_processing = False


async def stream_text_with_delay(text, accent, gender, voice, delay=1, progress=gr.Progress()):
    """Stream text to speech directly with a delay."""
    global last_text, is_processing

    if not text.strip():
        return None, "Please enter some text to convert to speech."

    try:
        is_processing = True
        last_text = text

        # Get available voices for the selected accent and gender
        voices = tts_engine.available_accents[accent][gender]
        voice_index = voices.index(voice)

        # Show progress
        for i in progress.tqdm(range(100)):
            time.sleep(0.01)  # Simulate processing time

        # Stream text to speech
        success = await tts_engine.stream_text_to_speech(
            text=text,
            accent=accent,
            gender=gender,
            voice_index=voice_index
        )

        if success:
            return None, "Speech streamed successfully!"
        else:
            return None, "Failed to stream speech. Please try again."

    except Exception as e:
        return None, f"An error occurred: {str(e)}"
    finally:
        is_processing = False


def get_voices(accent, gender):
    """Get available voices for the selected accent and gender"""
    return tts_engine.available_accents[accent][gender]


async def replay_last_audio(accent, gender, voice):
    """Replay the last generated audio"""
    global last_text
    
    if not last_text:
        return None, "No previous text to replay."
    
    try:
        # Get available voices for the selected accent and gender
        voices = tts_engine.available_accents[accent][gender]
        voice_index = voices.index(voice)
        
        # Stream text to speech
        success = await tts_engine.stream_text_to_speech(
            text=last_text,
            accent=accent,
            gender=gender,
            voice_index=voice_index
        )
        
        if success:
            return None, "Last audio replayed successfully!"
        else:
            return None, "Failed to replay audio. Please try again."
            
    except Exception as e:
        return None, f"An error occurred: {str(e)}"


async def handle_typing(text, accent, gender, voice):
    """Handle typing detection and streaming"""
    global last_typing_time, typing_timer
    
    if not text.strip():
        return None, "Please enter some text to convert to speech."
    
    # Update last typing time
    last_typing_time = time.time()
    
    # Cancel any existing timer
    if typing_timer:
        typing_timer.cancel()
    
    # Create a new timer
    typing_timer = asyncio.create_task(wait_and_stream(text, accent, gender, voice))
    
    return None, "Typing detected..."


async def wait_and_stream(text, accent, gender, voice):
    """Wait for delay and then stream"""
    await asyncio.sleep(1)
    if time.time() - last_typing_time >= 1:
        return await stream_text_with_delay(text, accent, gender, voice)
    return None, "Typing resumed..."


async def download_audio():
    """Download the last generated audio file"""
    global last_audio_path
    
    if not last_audio_path or not os.path.exists(last_audio_path):
        return None, "No audio file available to download"
    
    try:
        return str(last_audio_path), "Audio file ready for download"
    except Exception as e:
        return None, f"Failed to prepare audio for download: {str(e)}"


# Create Gradio interface
with gr.Blocks(title="Text-to-Speech", theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🎙️ Text-to-Speech")
    gr.Markdown("""
    Convert your text to speech with various English accents using Microsoft Edge TTS.
    Select your preferred accent, gender, and voice to generate natural-sounding speech.
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            # Text input
            text_input = gr.Textbox(
                label="Enter your text here",
                placeholder="Type or paste the text you want to convert to speech...",
                lines=5
            )
            
            # Status message
            status = gr.Textbox(label="Status", value="Enter text and select options to generate speech", interactive=False)
            
            # Audio output
            audio_output = gr.Audio(label="Generated Audio", type="filepath", interactive=False)
            
        with gr.Column(scale=1):
            # Settings
            accent_dropdown = gr.Dropdown(
                choices=list(tts_engine.available_accents.keys()),
                label="Select Accent",
                value=list(tts_engine.available_accents.keys())[0]
            )
            
            gender_dropdown = gr.Dropdown(
                choices=["Male", "Female"],
                label="Select Gender",
                value="Female"
            )
            
            voice_dropdown = gr.Dropdown(
                label="Select Voice",
                choices=get_voices(accent_dropdown.value, gender_dropdown.value),
                value=get_voices(accent_dropdown.value, gender_dropdown.value)[0]
            )
            
            # Update voice dropdown when accent or gender changes
            accent_dropdown.change(
                fn=lambda accent, gender: gr.update(choices=get_voices(accent, gender), value=get_voices(accent, gender)[0] if get_voices(accent, gender) else None),
                inputs=[accent_dropdown, gender_dropdown],
                outputs=voice_dropdown
            )
            gender_dropdown.change(
                fn=lambda accent, gender: gr.update(choices=get_voices(accent, gender), value=get_voices(accent, gender)[0] if get_voices(accent, gender) else None),
                inputs=[accent_dropdown, gender_dropdown],
                outputs=voice_dropdown
            )
            
            # Tabs for different modes
            with gr.Tabs():
                with gr.Tab("Normal Mode"):
                    gr.Markdown("Generate and download audio files")
                    generate_btn = gr.Button("Generate Speech", variant="primary")
                    download_btn = gr.Button("Download Audio", variant="secondary")
                
                with gr.Tab("Stream Mode"):
                    gr.Markdown("Stream audio directly")
                    stream_btn = gr.Button("Start Auto-Streaming", variant="primary")
                    replay_btn = gr.Button("Replay Last Audio", variant="secondary")
    
    # Connect buttons to functions
    generate_btn.click(
        fn=process_text,
        inputs=[text_input, accent_dropdown, gender_dropdown, voice_dropdown],
        outputs=[audio_output, status]
    )
    
    download_btn.click(
        fn=download_audio,
        inputs=None,
        outputs=[audio_output, status]
    )
    
    # Set up auto-streaming after text input changes
    text_input.change(
        fn=handle_typing,
        inputs=[text_input, accent_dropdown, gender_dropdown, voice_dropdown],
        outputs=[audio_output, status]
    )
    
    # Start auto-streaming button
    stream_btn.click(
        fn=lambda: gr.update(value="Auto-streaming started!"),
        inputs=None,
        outputs=status
    )
    
    replay_btn.click(
        fn=replay_last_audio,
        inputs=[accent_dropdown, gender_dropdown, voice_dropdown],
        outputs=[audio_output, status]
    )
    
    # Footer
    gr.Markdown("---")
    gr.Markdown("""
    This app uses Microsoft Edge TTS to generate high-quality speech with various English accents.
    The generated audio files are in MP3 format and can be downloaded for offline use.
    """)

# Launch the app
if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
