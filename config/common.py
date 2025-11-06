import os
import sys

from environs import Env


def load_env() -> Env:
    is_docker = os.environ.get("DOCKER", False)
    env = Env()
    if not is_docker:
        import logging

        logger = logging.getLogger(__name__)

        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        env.read_env(env_file, override=True)
        logger.info(f"Using env: {env_file}")

    if "test" in sys.argv:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".testenv")
        env.read_env(env_file, override=True)
    return env
