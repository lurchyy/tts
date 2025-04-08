import streamlit as st
import asyncio
import tempfile
import os
from pathlib import Path
from tts import EdgeTTSWithAccents
import time

# Initialize TTS engine
tts_engine = EdgeTTSWithAccents()

# Initialize session state
if 'last_text' not in st.session_state:
    st.session_state.last_text = ""
if 'last_audio_path' not in st.session_state:
    st.session_state.last_audio_path = None
if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False
if 'last_typing_time' not in st.session_state:
    st.session_state.last_typing_time = 0
if 'typing_timer' not in st.session_state:
    st.session_state.typing_timer = None
if 'auto_streaming' not in st.session_state:
    st.session_state.auto_streaming = False
if 'stream_progress' not in st.session_state:
    st.session_state.stream_progress = 0

# Page config
st.set_page_config(
    page_title="Text-to-Speech",
    page_icon="🎙️",
    layout="wide"
)

# Title and description
st.title("🎙️ Text-to-Speech")
st.markdown("""
Convert your text to speech with various English accents using Microsoft Edge TTS.
Select your preferred accent, gender, and voice to generate natural-sounding speech.
""")

# Sidebar for settings
with st.sidebar:
    st.header("Settings")
    
    # Accent selection
    accent = st.selectbox(
        "Select Accent",
        options=list(tts_engine.available_accents.keys()),
        index=0
    )
    
    # Gender selection
    gender = st.selectbox(
        "Select Gender",
        options=["Male", "Female"],
        index=1
    )
    
    # Voice selection
    voices = tts_engine.available_accents[accent][gender]
    voice = st.selectbox(
        "Select Voice",
        options=voices,
        index=0
    )
    
    # Mode selection
    mode = st.radio(
        "Select Mode",
        options=["Normal Mode", "Stream Mode"],
        index=0
    )

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    # Text input
    text = st.text_area(
        "Enter your text here",
        placeholder="Type or paste the text you want to convert to speech...",
        height=200,
        key="text_input"
    )
    
    # Progress bar
    progress_bar = st.progress(st.session_state.stream_progress / 100)
    
    # Status message
    status = st.empty()
    
    # Audio output
    audio_output = st.empty()

with col2:
    if mode == "Normal Mode":
        st.markdown("### Generate and Download")
        if st.button("Generate Speech", type="primary"):

            async def generate_speech():
                if text.strip():
                    with st.spinner("Generating speech..."):
                        try:
                            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                                temp_path = temp_file.name
                                st.session_state.last_audio_path = temp_path
                            
                            voice_index = voices.index(voice)
                            output_file = await tts_engine.convert_text_to_speech(
                                text=text,
                                accent=accent,
                                gender=gender,
                                voice_index=voice_index,
                                output_file=temp_path
                            )
                            
                            if output_file:
                                st.session_state.last_text = text
                                audio_output.audio(str(output_file))
                                status.success("Speech generated successfully!")
                            else:
                                status.error("Failed to generate speech. Please try again.")
                        except Exception as e:
                            status.error(f"An error occurred: {str(e)}")
                else:
                    status.warning("Please enter some text to convert to speech.")

            asyncio.run(generate_speech())
        
        if st.button("Download Audio"):
            if st.session_state.last_audio_path and os.path.exists(st.session_state.last_audio_path):
                with open(st.session_state.last_audio_path, 'rb') as f:
                    st.download_button(
                        label="Download Audio File",
                        data=f,
                        file_name="generated_speech.mp3",
                        mime="audio/mp3"
                    )
            else:
                status.warning("No audio file available to download")
    
    else:  # Stream Mode
        st.markdown("### Stream Audio")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Auto-Streaming", type="primary"):
                st.session_state.auto_streaming = True
                status.info("Auto-streaming started!")
        with col2:
            if st.button("Stop Auto-Streaming"):
                st.session_state.auto_streaming = False
                status.info("Auto-streaming stopped!")
        
        if st.button("Replay Last Audio"):

            async def replay_audio():
                if st.session_state.last_text:
                    try:
                        voice_index = voices.index(voice)
                        success = await tts_engine.stream_text_to_speech(
                            text=st.session_state.last_text,
                            accent=accent,
                            gender=gender,
                            voice_index=voice_index
                        )
                        if success:
                            status.success("Last audio replayed successfully!")
                        else:
                            status.error("Failed to replay audio. Please try again.")
                    except Exception as e:
                        status.error(f"An error occurred: {str(e)}")
                else:
                    status.warning("No previous text to replay.")

            asyncio.run(replay_audio())

# Auto-streaming logic
if mode == "Stream Mode" and text.strip() and st.session_state.auto_streaming:
    current_time = time.time()
    if current_time - st.session_state.last_typing_time >= 1:  # 1 second delay

        async def stream_with_progress(text, accent, gender, voice, progress_bar):
            try:
                voice_index = voices.index(voice)
                for i in range(100):
                    st.session_state.stream_progress = i + 1
                    progress_bar.progress(st.session_state.stream_progress / 100)
                    await asyncio.sleep(0.01)  # Simulate progress
                
                success = await tts_engine.stream_text_to_speech(
                    text=text,
                    accent=accent,
                    gender=gender,
                    voice_index=voice_index
                )
                
                if success:
                    status.success("Speech streamed successfully!")
                else:
                    status.error("Failed to stream speech. Please try again.")
            except Exception as e:
                status.error(f"An error occurred: {str(e)}")
            finally:
                st.session_state.stream_progress = 0
                progress_bar.progress(0)

        asyncio.run(stream_with_progress(text, accent, gender, voice, progress_bar))
    else:
        status.info("Typing detected...")
    
    st.session_state.last_typing_time = current_time

# Footer
st.markdown("---")
st.markdown("""
This app uses Microsoft Edge TTS to generate high-quality speech with various English accents.
The generated audio files are in MP3 format and can be downloaded for offline use.
""")
