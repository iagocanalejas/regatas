def is_play_off(name: str) -> bool:
    return 'PLAY' in name and 'OFF' in name


def is_branch_club(name: str, letter: str = 'B') -> bool:
    return any(e == letter for e in name.upper().split())
