from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"

    INGEST_API_KEY: str | None = None
    ENCRYPTION_KEY: str = ""  # base64 32 bytes

    DROPBOX_APP_KEY: str = ""
    DROPBOX_APP_SECRET: str = ""
    DROPBOX_REDIRECT_URL: str = ""
    KB_DROPBOX_ROOT: str = "/ChatGPT-KB"

    EMBEDDINGS_PROVIDER: str = "fallback"  # fallback|openai
    OPENAI_API_KEY: str | None = None
    OPENAI_EMBEDDINGS_MODEL: str = "text-embedding-3-small"

    AUTOTAG_RULES: str = "ClimSystems:ClimSystems,CS;ISSB_ASRS:ISSB,ASRS,AASB S2;Theology:Holy Word,CWWL,New Testament"

settings = Settings()
