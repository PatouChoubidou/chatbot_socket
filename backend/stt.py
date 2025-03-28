import whisper

async def transcribe(filename) -> str:
    """
        Transcribe text using whisper model
        Params:
            ?filename - audiofile
        Returns:
            the transcribed text
    """ 
    model = whisper.load_model("whisper/medium.pt")
    result = model.transcribe(filename, fp16=False)
    print(result["text"])
    return result["text"]