from ai_django.ai_core.utils.strings import remove_symbols


def is_play_off(name: str) -> bool:
    return 'PLAY' in name and 'OFF' in name


def is_branch_club(name: str, letter: str = 'B') -> bool:
    clean_name = remove_symbols(name)
    return any(e == letter for e in clean_name.upper().split())
