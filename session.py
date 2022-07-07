from asr import ASRPipe
from shortid import ShortId
import logging

# Generate a key for this session
SHORT_ID = ShortId()
# A map of sessions.  TODO: handle this better
SESSION_MAP = {}


logger = logging.getLogger("REServe")


def generate_shortid() -> str:
    """Generate a short ID

    :return:
    """
    return SHORT_ID.generate()


class Session:
    """A session object.  Currently only includes the ASR object and a pause variable"""

    def __init__(self, key: str, asr: ASRPipe):
        """Initialize our session.  We need an ID and the ASR pipe

        :param key:
        :param asr:
        """
        self.key = key
        self.asr = asr
        self.pause_asr_flag = False

    def fill_asr_buffer(self, audio_in):
        """The ASR buffer is for input data, we want to allow filling this buffer unless we are paused

        :param audio_in:
        :return:
        """
        if not self.pause_asr_flag:
            self.asr.fill_buffer(audio_in)

    def get_asr_transcript(self):
        """Proxy for accessing ASR transcript

        :return:
        """
        return self.asr.get_transcript()

    def pause_asr(self):
        """Signal to stop collecting audio input to the ASR buffer.  Sent packets will be dropped

        :return:
        """
        self.pause_asr_flag = True

    def unpause_asr(self):
        """Signal to start collecting audio input from the ASR Buffer.

        :return:
        """
        self.pause_asr_flag = False


class SessionManager:
    """Generates and manages the dialog state for each session"""

    @staticmethod
    def create_session(asr: ASRPipe):
        """Create a new session

        :param asr:
        :return:
        """
        key = generate_shortid()
        session = Session(key, asr)

        SESSION_MAP[key] = session

        return session

    @staticmethod
    def get_session(key: str):
        return SESSION_MAP.get(key)

    @staticmethod
    def delete_session(key: str):
        del SESSION_MAP[key]
