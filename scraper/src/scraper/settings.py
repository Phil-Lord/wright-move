import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    '''
    Runtime settings loaded from the environment.

    Attributes:
        supabase_url (str): Supabase project URL.
        supabase_service_key (str): Service-role key — write access. Never expose to frontend.
    '''

    supabase_url: str
    supabase_service_key: str


def load_settings() -> Settings:
    ''' Load settings from environment (and `.env` if present). '''
    load_dotenv()
    return Settings(
        supabase_url=os.environ['SUPABASE_URL'],
        supabase_service_key=os.environ['SUPABASE_SERVICE_KEY'],
    )
