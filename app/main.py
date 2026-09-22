import argparse
import os

from dotenv import load_dotenv
from openai import OpenAI

from app.tools.read import read

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


local_tools = {"read": read}


def call_tool(tool):
    func = tool.function
    name = func.name
    arguments = eval(func.arguments)
    callable = local_tools.get(name)
    if callable:
        return callable(**arguments)


def call_tools(tools):
    results = []
    for tool in tools:
        res = call_tool(tool)
        print(res)
        results.append(res)
    return results


class Agent:
    def __init__(self, tools, model="anthropic/claude-haiku-4.5"):
        self.client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
        self.tools = tools
        self.model = model

    def call_api(self, messages):
        chat = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools,
        )
        return chat

    def agent_loop(self, messages):
        while True:
            response = self.call_api(messages)
            messages.append(response.choices[0].message)

            if not response.choices[0].message.tool_calls:
                print(response.choices[0].message.content)
                break

            for tool in response.choices[0].message.tool_calls:
                result = call_tool(tool)
                messages.append(
                    {"role": "tool", "tool_call_id": tool.id, "content": result}
                )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    tools = [
        {
            "type": "function",
            "function": {
                "name": "read",
                "description": "Read and return the contents of a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "The path to the file to read",
                        }
                    },
                    "required": ["file_path"],
                },
            },
        }
    ]

    messages = [{"role": "user", "content": args.p}]

    # chat = client.chat.completions.create(
    #     model="anthropic/claude-haiku-4.5",
    #     messages=messages,
    #     tools=tools,
    # )

    # if not chat.choices or len(chat.choices) == 0:
    #     raise RuntimeError("no choices in response")

    # # You can use print statements as follows for debugging, they'll be visible when running tests.
    # print("Logs from your program will appear here!", file=sys.stderr)

    # # TODO: Uncomment the following line to pass the first stage
    # choice = chat.choices[0].message
    # if choice.tool_calls:
    #     if len(choice.tool_calls) > 1:
    #         res = call_tools(choice.tool_calls)
    #     elif len(choice.tool_calls) == 1:
    #         res = call_tool(choice.tool_calls[0])
    #         print(res)
    # else:
    #     print(chat.choices[0].message.content)

    agent = Agent(tools)
    agent.agent_loop(messages)


if __name__ == "__main__":
    main()
# ChatCompletion(
#     id="gen-1790070615-YMKfj03z6epPt9Nmnhyl",
#     choices=[
#         Choice(
#             finish_reason="tool_calls",
#             index=0,
#             logprobs=None,
#             message=ChatCompletionMessage(
#                 content=None,
#                 refusal=None,
#                 role="assistant",
#                 annotations=None,
#                 audio=None,
#                 function_call=None,
#                 tool_calls=[
#                     ChatCompletionMessageFunctionToolCall(
#                         id="toolu_bdrk_01Eqc3YZ1LMqYK5vUyuFfRkS",
#                         function=Function(
#                             arguments='{"file_path": "README.md"}', name="read"
#                         ),
#                         type="function",
#                         index=0,
#                     )
#                 ],
#                 reasoning=None,
#             ),
#             native_finish_reason="tool_use",
#         )
#     ],
#     created=1790070615,
#     model="anthropic/claude-haiku-4.5",
#     object="chat.completion",
#     service_tier="default",
#     system_fingerprint=None,
#     usage=CompletionUsage(
#         completion_tokens=56,
#         prompt_tokens=595,
#         total_tokens=651,
#         completion_tokens_details=CompletionTokensDetails(
#             accepted_prediction_tokens=None,
#             audio_tokens=0,
#             reasoning_tokens=0,
#             rejected_prediction_tokens=None,
#             image_tokens=0,
#         ),
#         prompt_tokens_details=PromptTokensDetails(
#             audio_tokens=0, cached_tokens=0, cache_write_tokens=0, video_tokens=0
#         ),
#         cost=0.00086625,
#         is_byok=False,
#         cost_details={
#             "upstream_inference_cost": 0.000875,
#             "upstream_inference_prompt_cost": 0.000595,
#             "upstream_inference_completions_cost": 0.00028,
#         },
#     ),
#     provider="Amazon Bedrock",
# )
