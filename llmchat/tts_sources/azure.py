import asyncio

from . import TTSSource
import azure.cognitiveservices.speech as speechsdk
from discord import User, Client
from llmchat.config import Config
from llmchat.persistence import PersistentData
from llmchat.logger import logger
import io


class Azure(TTSSource):
    synthesizer: speechsdk.speech.SpeechSynthesizer

    def __init__(self, client: Client, config: Config, db: PersistentData):
        super(Azure, self).__init__(client, config, db)
        logger.info("Logging into Azure...")
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.config.azure_key, region=self.config.azure_region
        )
        fake_stream = speechsdk.audio.PushAudioOutputStreamCallback()  # I tried to make a stream callback that wrote to a io.BytesIO but that didn't work for some reason
        stream = speechsdk.audio.PushAudioOutputStream(fake_stream)
        self.audio_config = speechsdk.audio.AudioOutputConfig(stream=stream)
        self.synthesizer = speechsdk.speech.SpeechSynthesizer(self.speech_config, self.audio_config)

    async def generate_speech(self, content: str) -> io.BufferedIOBase:
        self.speech_config.speech_synthesis_voice_name = self.config.azure_voice
        self.synthesizer = speechsdk.speech.SpeechSynthesizer(self.speech_config, self.audio_config)
        result: speechsdk.SpeechSynthesisResult = self.synthesizer.speak_text(content)
        buf = io.BytesIO(result.audio_data)
        return buf

    @property
    def current_voice_name(self) -> str:
        return self.config.azure_voice

    def set_voice(self, voice_id: str):
        self.config.azure_voice = voice_id

    def list_voices(self) -> list[str]:
        res: speechsdk.speech.SynthesisVoicesResult = self.synthesizer.get_voices_async("en-US").get()
        return [v.short_name for v in res.voices]
