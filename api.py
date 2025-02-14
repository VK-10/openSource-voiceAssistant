from livekit.agents import llm
# from livekit.plugins.openai import llm

# groq_llm = llm.LLM.with_groq(
#     model = "llama3-70b-8192",
#     temperature = 0.8,
# )

class AssistantFnc(llm.FunctionContext):
    def __init__(self):
        super().__init__()