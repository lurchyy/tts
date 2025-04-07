import streamlit as st
import asyncio
import tempfile
from pathlib import Path
from tts import EdgeTTSWithAccents

# Set page config
st.set_page_config(
    page_title="Text-to-Speech with Accents",
    page_icon="🎙️",
    layout="wide"
)


# Initialize TTS engine
@st.cache_resource
def get_tts_engine():
    return EdgeTTSWithAccents()


tts_engine = get_tts_engine()

# Title and description
st.title("🎙️ Text-to-Speech with Accents")
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
    
    # Voice selection based on accent and gender
    voices = tts_engine.available_accents[accent][gender]
    voice = st.selectbox(
        "Select Voice",
        options=voices,
        index=0
    )

# Main content area
text_input = st.text_area(
    "Enter your text here",
    height=150,
    placeholder="Type or paste the text you want to convert to speech..."
)

# Generate button
if st.button("Generate Speech"):
    if text_input.strip():
        with st.spinner("Generating speech..."):
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_path = Path(temp_file.name)
                
                # Convert text to speech
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
                    
                    # Display audio player
                    st.audio(str(temp_path))
                    
                    # Download button
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

# Footer
st.markdown("---")
st.markdown("""
### About
This app uses Microsoft Edge TTS to generate high-quality speech with various English accents.
The generated audio files are in MP3 format and can be downloaded for offline use.
""") 
