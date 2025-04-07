#!pip install edge-tts
#!pip install nltk
import os
import sys
import argparse
import asyncio
from pathlib import Path
import tempfile

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress
from rich.table import Table

console = Console()


class EdgeTTSWithAccents:

    def __init__(self):
        self.output_dir = Path("generated_audio")
        self.output_dir.mkdir(exist_ok=True)
        
        if not self._ensure_edge_tts():
            console.print("[bold red]Failed to install edge-tts. Please install it manually with: pip install edge-tts[/bold red]")
            sys.exit(1)
            
        import edge_tts
        self.edge_tts = edge_tts
        
        self.available_accents = {
            "American": {
                "Male": ["en-US-ChristopherNeural", "en-US-GuyNeural"],
                "Female": ["en-US-JennyNeural", "en-US-AriaNeural"]
            },
            "British": {
                "Male": ["en-GB-RyanNeural", "en-GB-ThomasNeural"],
                "Female": ["en-GB-SoniaNeural", "en-GB-LibbyNeural"]
            },
            "Indian": {
                "Male": ["en-IN-PrabhatNeural"],
                "Female": ["en-IN-NeerjaNeural"]
            },
            "Australian": {
                "Male": ["en-AU-WilliamNeural"],
                "Female": ["en-AU-NatashaNeural", "en-AU-AnnetteNeural"]
            },
            "Irish": {
                "Male": ["en-IE-ConnorNeural"],
                "Female": ["en-IE-EmilyNeural"]
            },
            "Canadian": {
                "Male": ["en-CA-LiamNeural"],
                "Female": ["en-CA-ClaraNeural"]
            },
            "South African": {
                "Male": ["en-ZA-LukeNeural"],
                "Female": ["en-ZA-LeahNeural"]
            }
        }
        
        self.voice_gender = {
            voice: "Male" if "Guy" in voice or "Christopher" in voice or "Ryan" in voice or 
                             "Thomas" in voice or "Prabhat" in voice or "William" in voice or
                             "Connor" in voice or "Liam" in voice or "Luke" in voice else "Female"
            for accent, voices in self.available_accents.items()
            for voice in voices
        }
        
    def _ensure_edge_tts(self):
        """Check if edge-tts is installed, install if not"""
        try:
            import edge_tts
            return True
        except ImportError:
            console.print("[yellow]edge-tts not installed. Installing...[/yellow]")
            try:
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "edge-tts"])
    
                try:
                    import edge_tts
                    return True
                except ImportError:
                    return False
            except Exception as e:
                console.print(f"[bold red]Error installing edge-tts: {str(e)}[/bold red]")
                return False
                
    def _ensure_player(self):
        """Check if audio player dependencies are installed"""
        try:
            import pygame
            return True
        except ImportError:
            try:
                import playsound
                return True
            except ImportError:
                console.print("[yellow]Audio player not installed. Installing pygame...[/yellow]")
                try:
                    import subprocess
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame"])
                    return True
                except Exception as e:
                    console.print(f"[bold red]Error installing pygame: {str(e)}[/bold red]")
                    return False
                    
    async def get_available_voices(self):
        """Get all available voices from Edge TTS"""
        voices = await self.edge_tts.VoicesManager.create()
        return voices.voices
        
    async def list_available_accents(self, detailed=False):
        """Display available accent options"""
        if not detailed:
            console.print(Panel("\n".join([f"- {accent}" for accent in self.available_accents.keys()]),
                              title="Available Accents", style="blue"))
        else:

            voices = await self.get_available_voices()
            

            table = Table(title="Available Accents and Voices")
            table.add_column("Accent", style="cyan")
            table.add_column("Voice", style="green")
            table.add_column("Gender", style="magenta")
            
            for accent, voice_list in self.available_accents.items():
                for i, voice_name in enumerate(voice_list):
        
                    voice_details = next((v for v in voices if v["ShortName"] == voice_name), None)
                    
                    if voice_details:
            
                        accent_display = accent if i == 0 else ""
                        table.add_row(
                            accent_display,
                            voice_name,
                            self.voice_gender.get(voice_name, "Unknown")
                        )
            
            console.print(table)
            
    async def list_all_available_voices(self):
        """List all available voices from Edge TTS"""
        voices = await self.get_available_voices()
        
        english_voices = [v for v in voices if v["Locale"].startswith("en")]
        
        table = Table(title="All Available English Voices")
        table.add_column("Locale", style="cyan")
        table.add_column("Voice Name", style="green")
        table.add_column("Short Name", style="magenta")
        table.add_column("Gender", style="blue")
        
        for voice in english_voices:
            table.add_row(
                voice["Locale"],
                voice["FriendlyName"],
                voice["ShortName"],
                voice["Gender"]
            )
        
        console.print(table)
        
    async def convert_text_to_speech(self, text, accent, gender=None, voice_index=0, output_file=None):
        """Convert text to speech with the specified accent and gender"""
        if accent not in self.available_accents:
            console.print(f"[bold red]Error:[/bold red] Invalid accent '{accent}'. Please choose from available accents.")
            await self.list_available_accents()
            return False
            
        if gender:
            voices = self.available_accents[accent].get(gender, [])
            if not voices:
                console.print(f"[bold red]Error:[/bold red] No voices available for {gender} in {accent} accent.")
                return False
        else:

            voices = []
            for gender_voices in self.available_accents[accent].values():
                voices.extend(gender_voices)
            
        if voice_index >= len(voices):
            voice_index = 0
            
        voice = voices[voice_index]
        
        if not output_file:
            output_file = self.output_dir / f"output_{accent.lower().replace(' ', '_')}.mp3"
        else:
            output_file = Path(output_file)
            
        console.print(f"Converting text to speech with [bold]{accent}[/bold] accent (Voice: {voice})...")
        
        try:

            communicate = self.edge_tts.Communicate(text, voice)
            

            with Progress() as progress:
                task = progress.add_task("[green]Generating speech...", total=100)
                progress.update(task, advance=30)
                
                await communicate.save(str(output_file))
                progress.update(task, advance=70)
                
            console.print(f"[bold green]Success![/bold green] Audio saved to: {output_file}")
            return str(output_file)
            
        except Exception as e:
            console.print(f"[bold red]Error generating speech: {str(e)}[/bold red]")
            return False
            
    async def play_audio(self, file_path):
        """Play the generated audio file"""
        if not self._ensure_player():
            console.print(f"[yellow]Audio playback not available. File saved to: {file_path}[/yellow]")
            return
            
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            

            console.print("Playing audio... Press Ctrl+C to stop.")
            try:
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
            except KeyboardInterrupt:
                pygame.mixer.music.stop()
                
        except ImportError:
            try:
    
                from playsound import playsound
                import os
    
                abs_path = os.path.abspath(file_path)
    
                normalized_path = abs_path.replace('\\', '/')
                console.print("Playing audio...")
                playsound(normalized_path)
            except Exception as e:
                console.print(f"[bold red]Error playing audio: {str(e)}[/bold red]")
                console.print(f"[green]Audio file saved to: {file_path}[/green]")
                
    async def replay_audio(self, file_path):
        """Replay the audio file"""
        replay = True
        while replay:
            await self.play_audio(file_path)
            replay_choice = Prompt.ask("[bold]Replay the audio?[/bold]", choices=["y", "n"], default="n")
            replay = replay_choice.lower() == "y"


async def main_async():
    parser = argparse.ArgumentParser(description="Text-to-Speech with multiple English accents using Edge TTS")
    parser.add_argument("--text", type=str, help="Text to convert to speech")
    parser.add_argument("--accent", type=str, help="Accent to use for speech generation")
    parser.add_argument("--gender", type=str, choices=["Male", "Female"], help="Gender of the voice")
    parser.add_argument("--voice", type=int, default=0, help="Voice index for the selected accent (default: 0)")
    parser.add_argument("--output", type=str, help="Output audio file path (optional)")
    parser.add_argument("--list-accents", action="store_true", help="List available accents")
    parser.add_argument("--detailed", action="store_true", help="Show detailed voice information")
    parser.add_argument("--list-all", action="store_true", help="List all available voices")
    parser.add_argument("--play", action="store_true", help="Play the generated audio after conversion")
    
    args = parser.parse_args()
    
    tts_engine = EdgeTTSWithAccents()
    
    if args.list_accents:
        await tts_engine.list_available_accents(args.detailed)
        return
        
    if args.list_all:
        await tts_engine.list_all_available_voices()
        return
        
    if args.text and args.accent:
        output_file = await tts_engine.convert_text_to_speech(args.text, args.accent, args.gender, args.voice, args.output)
        if output_file and args.play:
            await tts_engine.replay_audio(output_file)
    else:
        console.print(Panel("Welcome to Edge TTS with Accents!",
                           title="Edge TTS Accent Generator", style="green"))
        
        await tts_engine.list_available_accents()
        
        show_details = Prompt.ask("[bold]Show detailed voice information?[/bold]", choices=["y", "n"], default="n")
        if show_details.lower() == "y":
            await tts_engine.list_available_accents(detailed=True)
        
        while True:
            text = Prompt.ask("[bold]Enter text to convert[/bold] (or 'q' to quit)")
            
            if text.lower() == 'q':
                break
                
            accent = Prompt.ask("[bold]Choose an accent[/bold]",
                                choices=list(tts_engine.available_accents.keys()))
                
            gender = Prompt.ask("[bold]Choose voice gender[/bold]",
                               choices=["Male", "Female"],
                               default="Female")
                

            voices = tts_engine.available_accents[accent][gender]
            console.print(f"[cyan]Available voices for {accent} ({gender}):[/cyan]")
            for i, voice in enumerate(voices):
                console.print(f"  {i}: {voice}")
                
            voice_idx = Prompt.ask("[bold]Choose voice index[/bold]",
                                  choices=[str(i) for i in range(len(voices))],
                                  default="0")
                
            output_file = await tts_engine.convert_text_to_speech(text, accent, gender, int(voice_idx))
            
            if output_file:
                play_choice = Prompt.ask("[bold]Play the audio?[/bold]", choices=["y", "n"], default="y")
                if play_choice.lower() == "y":
                    await tts_engine.replay_audio(output_file)
            
            continue_choice = Prompt.ask("[bold]Continue with another conversion?[/bold]",
                                        choices=["y", "n"], default="y")
            if continue_choice.lower() != "y":
                break
                
    console.print(Panel("Thank you for using Edge TTS with Accents!",
                        title="Goodbye", style="green"))


def main():
    """Entry point for the script that handles asyncio loop"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        console.print("\n[yellow]Program interrupted by user. Exiting...[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]Error: {str(e)}[/bold red]")


if __name__ == "__main__":
    main()
