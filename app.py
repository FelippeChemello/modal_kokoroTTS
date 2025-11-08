import modal

image = modal.Image.debian_slim(python_version="3.10").apt_install(
        "espeak-ng",
        "portaudio19-dev"
    ).uv_pip_install(
        "fastapi",
        "uvicorn[standard]",
        "python-dotenv",
        "requests",
        "numpy",
        "kokoro",
        "pyaudio",
        "soundfile"
    )

app = modal.App('kokoro')

with image.imports():
    import os
    import tempfile
    import json
    from fastapi import Header, Request
    from fastapi.responses import FileResponse, JSONResponse
    from pydantic import BaseModel
    from kokoro import KPipeline
    import soundfile as sf
    import torch
    import numpy as np

class TTSRequest(BaseModel):
    text: str
    voice: str
        
@app.cls(gpu='L40S', image=image, timeout=60, secrets=[modal.Secret.from_name("kokoro-secret")])
class Model:
    @modal.enter()
    def load_model(self):
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Loading Kokoro model on device: {device}")

        self.pipeline = KPipeline(lang_code="p", device=device)

    def inference(self, text: str, voice: str):
        print(f"Generating text to speech for '{text}' with voice '{voice}'")

        generator = self.pipeline(text, voice, 1.5)

        audio_chunks = []
        for i, (gs, ps, audio) in enumerate(generator):
            print(f"Generated chunk {i} with gs: {gs}, ps: {ps}")
            audio_chunks.append(audio)

        if audio_chunks:
            combined_audio = np.concatenate(audio_chunks)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
                sf.write(tmpfile, combined_audio, samplerate=22050)
                tmpfile.seek(0)
                audio_bytes = tmpfile.read()
                tmpfile_path = tmpfile.name

                os.remove(tmpfile_path)

            return audio_bytes
        else:
            print("No audio chunks were generated.")
            return None
    
    @modal.method()
    def _inference(self, text: str, voice: str):
        return self.inference(text, voice)
    
    @modal.fastapi_endpoint(docs=True, method="POST")
    def web_inference(self, request: TTSRequest, x_api_key: str = Header(None)):
        api_key = os.getenv("API_KEY")
        if x_api_key != api_key:
            return JSONResponse(status_code=401, content={"message": "Unauthorized"})

        audio = self.inference(request.text, request.voice)
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
            tmpfile.write(audio)
            tmpfile_path = tmpfile.name
        
        return FileResponse(
            path=tmpfile_path,
            media_type="audio/wav",
            filename="output.wav"
        )
    
@app.local_entrypoint()
def main():
    text = "Olá, este é um exemplo de síntese de fala usando Kokoro."
    lang = "p"
    voice = "pf_dora"

    audio = Model()._inference.remote(text, lang, voice)
    with open("output.wav", "wb") as f:
        f.write(audio)

