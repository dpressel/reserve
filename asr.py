"""
Modified from:
https://github.com/nvidia-riva/sample-apps/blob/stable/virtual-assistant/riva/asr/asr.py
"""
import sys
import grpc
import riva_api.riva_audio_pb2 as ra
import riva_api.riva_asr_pb2 as rasr
import riva_api.riva_asr_pb2_grpc as rasr_srv
import queue
import logging

logging.basicConfig(level=logging.INFO)
# Default ASR parameters - Used in case config values not specified in the config.py file
SAMPLING_RATE = 16000
LANGUAGE_CODE = "en-US"
ENABLE_AUTOMATIC_PUNCTUATION = True
STREAM_INTERIM_RESULTS = True

logger = logging.getLogger("REServe")


class ASRPipe:
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, **config):
        self.asr_url = config.get("RIVA_SPEECH_API_URL", "localhost:50051")
        self.sampling_rate = config.get("SAMPLING_RATE", SAMPLING_RATE)
        self.language_code = config.get("LANGUAGE_CODE", LANGUAGE_CODE)
        self.enable_automatic_punctuation = config.get(
            "ENABLE_AUTOMATIC_PUNCTUATION", ENABLE_AUTOMATIC_PUNCTUATION
        )
        self.stream_interim_results = config.get(
            "STREAM_INTERIM_RESULTS", STREAM_INTERIM_RESULTS
        )
        self.chunk = int(self.sampling_rate / 10)  # 100ms
        self._buff = queue.Queue()
        self._transcript = queue.Queue()
        self.closed = False
        self.channel = None
        self.asr_client = None

    def start(self):
        logger.info("Creating Stream ASR channel: %s", self.asr_url)
        self.channel = grpc.insecure_channel(self.asr_url)
        self.asr_client = rasr_srv.RivaSpeechRecognitionStub(self.channel)

    def close(self):
        self.closed = True
        self._buff.queue.clear()
        self._buff.put(None)  # means the end
        del self.channel

    def empty_asr_buffer(self):
        """Clears the audio buffer."""
        if not self._buff.empty():
            self._buff.queue.clear()

    def fill_buffer(self, in_data):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)

    def get_transcript(self):
        """Generator returning chunks of audio transcript"""
        while True:  # not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            trans = self._transcript.get()
            if trans is None:
                return
            yield trans

    def build_request_generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)

    def listen_print_loop(self, responses):
        """Iterates through server responses and populates the audio
        transcription buffer (and prints the responses to stdout).

        The responses passed is a generator that will block until a response
        is provided by the server.

        Each response may contain multiple results, and each result may contain
        multiple alternatives; for details, see https://goo.gl/tjCPAU.  Here we
        print only the transcription for the top alternative of the top result.

        In this case, responses are provided for interim results as well. If the
        response is an interim one, print a line feed at the end of it, to allow
        the next result to overwrite it, until the response is a final one. For the
        final one, print a newline to preserve the finalized transcription.
        """
        num_chars_printed = 0
        for response in responses:
            if not response.results:
                continue

            # The `results` list is consecutive. For streaming, we only care about
            # the first result being considered, since once it's `is_final`, it
            # moves on to considering the next utterance.
            result = response.results[0]
            if not result.alternatives:
                continue

            # Display the transcription of the top alternative.
            transcript = result.alternatives[0].transcript

            # Display interim results, but with a carriage return at the end of the
            # line, so subsequent lines will overwrite them.
            #
            # If the previous result was longer than this one, we need to print
            # some extra spaces to overwrite the previous result
            overwrite_chars = " " * (num_chars_printed - len(transcript))

            if not result.is_final:
                sys.stdout.write(transcript + overwrite_chars + "\r")
                sys.stdout.flush()
                interm_trans = transcript + overwrite_chars + "\r"
                interm_str = (
                    f'event:{"intermediate-transcript"}\ndata: {interm_trans}\n\n'
                )
                # TODO?  Emit or not?
                logging.debug(interm_str)
            else:
                final_transcript = transcript + overwrite_chars
                logger.info("Transcript: %s", final_transcript)

                # final_str = f'event:{"finished-speaking"}\ndata: {final_transcript}\n\n'
                final_str = final_transcript
                self._transcript.put(final_str)
            num_chars_printed = 0
        logger.info("Exit")

    def main_asr(self):
        """Creates a gRPC channel (thread-safe) with RIVA API server for
        ASR Calls, and retrieves recognition/transcription responses."""
        # See http://g.co/cloud/speech/docs/languages
        # for a list of supported languages.
        self.start()
        config = rasr.RecognitionConfig(
            encoding=ra.AudioEncoding.LINEAR_PCM,
            sample_rate_hertz=self.sampling_rate,
            language_code=self.language_code,
            max_alternatives=1,
            enable_automatic_punctuation=self.enable_automatic_punctuation,
            verbatim_transcripts=True,
        )
        streaming_config = rasr.StreamingRecognitionConfig(
            config=config, interim_results=self.stream_interim_results
        )

        logger.info("Starting Background ASR process")
        self.request_generator = self.build_request_generator()
        requests = (
            rasr.StreamingRecognizeRequest(audio_content=content)
            for content in self.request_generator
        )

        def build_generator(cfg, gen):
            yield rasr.StreamingRecognizeRequest(streaming_config=cfg)
            for x in gen:
                yield x
            yield cfg

        logger.info("StreamingRecognize Start")
        responses = self.asr_client.StreamingRecognize(
            build_generator(streaming_config, requests)
        )
        # Now, put the transcription responses to use.
        self.listen_print_loop(responses)
