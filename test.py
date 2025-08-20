from openai import OpenAI

client = OpenAI(
    base_url="http://v-dev-busi1004-11179700-vllm-wl0101-vtraining.vmic.xyz/v1/",
    api_key="empty",
)

response = client.chat.completions.create(
    model="qwen2.5-vl",
    messages=[
        {"role": "user", "content": "hi"},
    ],
)

print(response.choices[0].message)
