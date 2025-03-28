import pyttsx3
import subprocess


async def convertAiffToWave():
    """
    Convert an aiff file to wave using ffmpeg
    -y: override true
    """
    cmd2 = f"ffmpeg -y -i output.aiff -ac 2 output.wav" 
    subprocess.call(cmd2, shell=True)


async def generateAiff(txt):
    """
        Convert text to speech using pytssx3
         # choose engine by system espeak, nsss, avspeech
        Params:
            txt
        Returns:
            saves an audio file as aiff
    """
    
    engine = pyttsx3.init("nsss")
    engine.setProperty('rate', 200 - 20)
    
    # solid german voice
    # engine.setProperty('voice', 'com.apple.speech.synthesis.voice.anna')
    
    # nearly solid english
    engine.setProperty('voice', 'com.apple.speech.synthesis.voice.samantha')
    
    # engine.setProperty("pitch", 75)  # Set the pitch (default 50) to 75 out of 100 - doesnt work with nsss
    engine.say(" ") # this is a workaround for pyttsx3 not beeing able to save files 
    engine.save_to_file(txt, 'output.aiff') # says it can save as wav but actually is aiff Format
    engine.runAndWait()
    await convertAiffToWave()
   