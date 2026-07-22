from foundry_local_sdk import Configuration, FoundryLocalManager
from app.config import embedding_model_name, chat_model_name


def initialize_foundry():
    # Boots up the Foundry Local runtime once, so models can be loaded locally afterwards
    config = Configuration(app_name="local_rag_ai_assistant")
    FoundryLocalManager.initialize(config)
    return FoundryLocalManager.instance


def load_embedding_model(manager):
    # Fetch the embedding model from the local catalog (downloads it if not present yet)
    embedding_model = manager.catalog.get_model(embedding_model_name)
    if embedding_model is None:
        print("Embedding model is not found!")
        print("Use model name that is listed above")
        return

    # Download shows a live progress percentage in the console
    embedding_model.download(
        lambda p: print(f"\rEmbedding download: {p:.1f}%", end="", flush=True))
    print()

    embedding_model.load()
    return embedding_model.get_embedding_client()


def load_chat_client(manager):
    # Fetch the local chat/generation model (Qwen3-4B) the same way
    chat_model = manager.catalog.get_model("qwen3-4b")
    if chat_model is None:
        print("Chat model is not found!")
        return

    chat_model.download(lambda p: print(f"\rDownloading chat model: {p:.1f}%", end="", flush=True))
    print()

    chat_model.load()
    return chat_model.get_chat_client()