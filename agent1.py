import asyncio
import logging
import os
import wave
import soundfile as sf
from datetime import datetime

from dotenv import load_dotenv

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    metrics,
    llm
)
from livekit.agents.pipeline import VoicePipelineAgent
# from livekit.plugins import cartesia, openai, deepgram, silero, turn_detector
from livekit.plugins.openai import stt 
from livekit.plugins.openai import llm as llm_groq
from livekit.plugins import silero, elevenlabs



load_dotenv(dotenv_path=".env.local")
logger = logging.getLogger("voice-agent")


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a voice assistant created by Sarvam-ai. Your interface with users will be voice. "
            "You should use short and concise responses, and avoiding usage of unpronouncable punctuation. "
            "You were created as a demo to showcase the capabilities of LiveKit's agents framework."
        ),
    )

    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"starting voice assistant for participant {participant.identity}")

    dg_model = "nova-2-general"
    if participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP:
        dg_model = "nova-2-phonecall"
    # https://docs.livekit.io/agents/plugins
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt = stt.STT.with_groq(
            model="whisper-large-v3-turbo",
            language="en",
        ),
        llm= llm_groq.LLM.with_groq(
            model="mixtral-8x7b-32768",
            temperature=0.8
        ),
        tts= elevenlabs.TTS(api_key="hello1234"),
        min_endpointing_delay=0.5,
        max_endpointing_delay=5.0,
        chat_ctx=initial_ctx,
    
    )

    # Debugging setup
    debug_dir = "debug_logs"
    os.makedirs(debug_dir, exist_ok=True)
    debug_prefix = datetime.now().strftime("%Y%m%d-%H%M%S")

    usage_collector = metrics.UsageCollector()

    @agent.on("metrics_collected")
    def on_metrics_collected(agent_metrics: metrics.AgentMetrics):
        metrics.log_metrics(agent_metrics)
        usage_collector.collect(agent_metrics)

    agent.start(ctx.room, participant)

    chat = rtc.ChatManager(ctx.room)

    async def answer_from_text(text: str):
        chat_ctx = agent.chat_ctx.copy()
        chat_ctx.append(role="user", text=text)
        stream = agent.llm.chat(chat_ctx = chat_ctx)
        await agent.say(stream)

    @chat.on("message_recieved")
    def on_chat_recieved(msg: rtc.ChatMessage):
        if msg.message:
            asyncio.create_task(answer_from_text(msg.message))
    
    await agent.say("Hey, how can I help you today?", allow_interruptions=True)

    
    
    # # The agent should be polite and greet the user when it joins
    # await agent.say("Hey, how can I help you today?", allow_interruptions=True, wait_for_end=True,add_to_chat_ctx=True)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )