from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: str
    supabase_url: str
    supabase_key: str
    notion_api_key: str
    notion_token: str
    notion_database_id: str
    voyage_api_key: str
    instagram_access_token: str = ""
    instagram_user_id: str = ""
    chroma_db_path: str = "./chroma_db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()  # type: ignore[call-arg]
