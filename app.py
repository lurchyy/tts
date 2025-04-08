import streamlit as st
import asyncio
import tempfile
import os
from pathlib import Path
from tts import EdgeTTSWithAccents
import time

st.set_page_config(
    page_title="Text-to-Speech",
    page_icon="🎙️",
    layout="wide"
)


@st.cache_resource
def get_tts_engine():
    return EdgeTTSWithAccents()


tts_engine = get_tts_engine()

# Initialize session state for streaming control
if 'is_playing' not in st.session_state:
    st.session_state.is_playing = False
if 'stop_playback' not in st.session_state:
    st.session_state.stop_playback = False
if 'last_text' not in st.session_state:
    st.session_state.last_text = ""
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'last_processed' not in st.session_state:
    st.session_state.last_processed = 0
if 'last_audio_path' not in st.session_state:
    st.session_state.last_audio_path = None
if 'trigger_process' not in st.session_state:
    st.session_state.trigger_process = False
if 'text_changed' not in st.session_state:
    st.session_state.text_changed = False


def trigger_processing():
    st.session_state.trigger_process = True


# Force processing even without window change
def force_processing():
    st.session_state.trigger_process = True
    st.session_state.last_processed = 0  # Reset timer to force immediate processing


# Detect text changes in real-time
def on_text_change():
    st.session_state.text_changed = True
    st.session_state.trigger_process = True


st.title(" Text-to-Speech")
st.markdown("""
Convert your text to speech with various English accents using Microsoft Edge TTS.
Select your preferred accent, gender, and voice to generate natural-sounding speech.
""")

# Add mode selection
mode = st.radio(
    "Select Mode",
    ["Normal", "Stream"],
    horizontal=True,
    help="Normal mode saves the audio file, Stream mode plays audio immediately"
)

with st.sidebar:
    st.header("Settings")

    accent = st.selectbox(
        "Select Accent",
        options=list(tts_engine.available_accents.keys()),
        index=0
    )

    gender = st.selectbox(
        "Select Gender",
        options=["Male", "Female"],
        index=1
    )

    voices = tts_engine.available_accents[accent][gender]
    voice = st.selectbox(
        "Select Voice",
        options=voices,
        index=0
    )

    # Add auto-play toggle
    auto_play = st.toggle(
        "Auto-play",
        value=True,
        help="Automatically play audio as you type"
    )

    # Delay slider removed as requested

if mode == "Stream":
    st.markdown("### 🎙️ Streaming Mode")
    st.info("Type your text and it will be automatically converted to speech.")
    
    # Create a text input with on_change callback
    text_input = st.text_area(
        "Enter your text here",
        height=100,
        placeholder="Type or paste the text you want to convert to speech...",
        key="text_input",
        on_change=on_text_change
    )
    
    # Add control buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Stop Playback"):
            st.session_state.stop_playback = True
            st.session_state.is_playing = False
            st.warning("Playback stopped!")
    with col2:
        if st.button("Process Now", on_click=force_processing):
            pass  # Processing handled by on_click
    with col3:
        if st.button("Replay Last Audio"):
            if st.session_state.last_audio_path and os.path.exists(st.session_state.last_audio_path):
                try:
                    st.success("Replaying last audio!")
                    # Fix for replay functionality - use stream_text_to_speech with the cached text
                    if st.session_state.last_text:
                        asyncio.run(
                            tts_engine.stream_text_to_speech(
                                text=st.session_state.last_text,
                                accent=accent,
                                gender=gender,
                                voice_index=voices.index(voice)
                            )
                        )
                    else:
                        st.warning("No previous text to replay")
                except Exception as e:
                    st.error(f"Failed to replay audio: {str(e)}")
            else:
                st.warning("No previous text to replay")
    
    # Check if text has changed and auto-play is enabled
    current_time = time.time()
    should_process = (
        (auto_play and 
         text_input != st.session_state.last_text and 
         not st.session_state.processing) or
        st.session_state.trigger_process or
        st.session_state.text_changed
    )
    
    if should_process and text_input.strip():
        st.session_state.last_text = text_input
        st.session_state.processing = True
        st.session_state.last_processed = current_time
        st.session_state.trigger_process = False
        st.session_state.text_changed = False
        
        # Create a progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Start streaming
        try:
            # Show processing status
            for i in range(101):
                if st.session_state.stop_playback:
                    break
                progress_bar.progress(i)
                status_text.text(f"Processing: {i}%")
                time.sleep(0.01)  # Reduced time to make processing faster
            
            if not st.session_state.stop_playback and text_input.strip():
                # Create a temporary file for the audio
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                    temp_path = temp_file.name
                    st.session_state.last_audio_path = temp_path
                
                # Use the streaming function
                success = asyncio.run(
                    tts_engine.stream_text_to_speech(
                        text=text_input,
                        accent=accent,
                        gender=gender,
                        voice_index=voices.index(voice)
                    )
                )
                
                if success:
                    st.success("Speech generated and played!")
                else:
                    st.error("Failed to generate speech. Please try again.")
            
            st.session_state.is_playing = False
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.session_state.is_playing = False
        
        finally:
            progress_bar.empty()
            status_text.empty()
            st.session_state.processing = False
            st.session_state.stop_playback = False
else:
    st.markdown("### 📁 Normal Mode")
    st.info("Enter text and generate an audio file that you can download.")
    
    text_input = st.text_area(
        "Enter your text here",
        height=150,
        placeholder="Type or paste the text you want to convert to speech..."
    )

    if st.button("Generate Speech"):
        if text_input.strip():
            with st.spinner("Generating speech..."):
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                    temp_path = Path(temp_file.name)
                    st.session_state.last_audio_path = str(temp_path)
                    st.session_state.last_text = text_input  # Save the text for potential replay
                
                    output_file = asyncio.run(
                        tts_engine.convert_text_to_speech(
                            text=text_input,
                            accent=accent,
                            gender=gender,
                            voice_index=voices.index(voice),
                            output_file=str(temp_path)
                        )
                    )
                    
                    if output_file:
                        st.success("Speech generated successfully!")
                    
                        st.audio(str(temp_path))
                    
                        with open(str(temp_path), "rb") as f:
                            st.download_button(
                                label="Download Audio",
                                data=f,
                                file_name=f"tts_{accent.lower().replace(' ', '_')}.mp3",
                                mime="audio/mp3"
                            )
                    else:
                        st.error("Failed to generate speech. Please try again.")
        else:
            st.warning("Please enter some text to convert to speech.")

st.markdown("---")
st.markdown("""
This app uses Microsoft Edge TTS to generate high-quality speech with various English accents.
The generated audio files are in MP3 format and can be downloaded for offline use.
""")
