from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
client = OpenAI()

client.batches.cancel("batch_68ce45c0a90c8190b3a3b74f9fd2c038")