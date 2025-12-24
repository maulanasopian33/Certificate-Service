from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_KEY: str = "dev-secret"
    STORAGE_PATH: str = "app/storage"
    TEMPLATE_PATH: str = "app/templates/certificate.docx"

settings = Settings()
