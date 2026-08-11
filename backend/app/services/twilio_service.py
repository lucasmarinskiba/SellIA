from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
import os
from typing import Optional


class TwilioVoiceService:
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID', 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN', 'your_auth_token')
        self.phone_number = os.getenv('TWILIO_PHONE_NUMBER', '+1234567890')
        self.client = Client(self.account_sid, self.auth_token)

    def make_outbound_call(
        self,
        to_number: str,
        agent_persona_id: str,
        call_id: str,
    ) -> dict:
        """Make outbound call via Twilio."""
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=self.phone_number,
                url=f'http://api.example.com/api/v1/voice/twiml/{call_id}',
                record=True,
                recordingStatusCallback=f'http://api.example.com/api/v1/voice/webhooks/recording/{call_id}',
                statusCallback=f'http://api.example.com/api/v1/voice/webhooks/status/{call_id}',
                statusCallbackEvent=['initiated', 'ringing', 'answered', 'completed'],
                statusCallbackMethod='POST',
            )

            return {
                'success': True,
                'twilio_call_id': call.sid,
                'status': call.status,
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }

    def generate_twiml(
        self,
        agent_persona_id: str,
        call_id: str,
        system_prompt: str,
        voice_id: str = 'Alice',
    ) -> str:
        """Generate TwiML for IVR."""
        response = VoiceResponse()

        response.say(
            f'Hello, connecting you to our AI agent.',
            voice='alice',
            language='en-US',
        )

        response.gather(
            num_digits=1,
            action=f'http://api.example.com/api/v1/voice/twiml/{call_id}',
            method='POST',
            timeout=5,
            speech_timeout='auto',
            max_speech_time=60,
            speech_model='default',
            hints='yes, no, help',
        ).say(
            'Press 1 for sales, 2 for support, or speak your request.',
            voice='alice',
        )

        response.redirect(f'http://api.example.com/api/v1/voice/twiml/{call_id}')

        return str(response)

    def end_call(self, twilio_call_id: str) -> dict:
        """End active call."""
        try:
            call = self.client.calls(twilio_call_id).update(status='completed')
            return {
                'success': True,
                'status': call.status,
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }

    def transfer_call(
        self,
        twilio_call_id: str,
        transfer_to: str,
    ) -> dict:
        """Transfer call to another number."""
        try:
            response = VoiceResponse()
            response.dial(transfer_to)

            return {
                'success': True,
                'transfer_to': transfer_to,
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }

    def get_call_recording(self, recording_sid: str) -> dict:
        """Get recording details."""
        try:
            recording = self.client.recordings(recording_sid).fetch()

            return {
                'success': True,
                'sid': recording.sid,
                'duration': recording.duration,
                'channels': recording.channels,
                'media_url': recording.media_url,
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }

    def transcribe_recording(self, recording_sid: str) -> dict:
        """Transcribe recording via Twilio."""
        try:
            transcription = self.client.transcriptions.create(recording_sid)

            return {
                'success': True,
                'sid': transcription.sid,
                'status': transcription.status,
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
