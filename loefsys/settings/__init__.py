"""The settings for Django are defined here.

Before the settings are loaded, a file named ``.env`` located in the root of the project
is loaded to populate the environment variables.
"""

from dotenv import load_dotenv

from .storage import StorageSettings

# fmt: off
# isort: off
from .test import TestSettings
from .templates import TemplateSettings
# from .email import EmailSettings
from .base import BaseSettings
from .auth import AuthSettings
# from .security import SecuritySettings
from .admin import AdminSettings
from .database import DatabaseSettings
# from .locale import LocaleSettings
# from .logging import LoggingSettings
# from .storage import StorageSettings
# isort: on
# fmt: on


load_dotenv()


# In principle all individual settings modules work without errors. However, settings
# were directly copied from the old configuration and it may not be correct. That is
# why currently a number of modules are disabled. They can be enabled once we get to
# the part of the app that requires the specific module and we need to set up the
# configuration correctly.
class Settings(
    DatabaseSettings,
    StorageSettings,
    # LocaleSettings,
    AdminSettings,
    # SecuritySettings,
    AuthSettings,
    # EmailSettings,
    # LoggingSettings,
    TemplateSettings,
    BaseSettings,
    TestSettings,
):
    """Composite settings class containing the complete configuration.

    This class inherits the settings classes with specific configurations. In principle,
    all individual configuration classes work without errors. However, parts of the
    configuration were directly copied from the old configuration, and thus it is not
    tested whether this works correctly. Some configurations may be disabled because of
    that reason. They can be enabled once that part of the site requires configuration,
    so that we can properly set up that configuration.
    """


__getattr__, __dir__ = Settings.use()
