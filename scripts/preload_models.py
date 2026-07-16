import asyncio

from app.services.embedding_service import EmbeddingService


async def main() -> None:
    await EmbeddingService().embed_query("prechargement du modele")
    print("Embedding provider ready.")


if __name__ == "__main__":
    asyncio.run(main())
