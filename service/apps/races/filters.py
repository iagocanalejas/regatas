from typing import Dict

from django.db.models import Q


def build_base_filters(params: Dict, prefix: str = '') -> Dict:
    filters = {}
    for key, value in params.items():
        if key == 'year':
            filters[f'{prefix}__date__year' if prefix else 'date__year'] = value
        if key == 'trophy':
            filters[f'{prefix}__trophy_id' if prefix else 'trophy_id'] = value
        if key == 'flag':
            filters[f'{prefix}__flag_id' if prefix else 'flag_id'] = value
        if key == 'league':
            filters[f'{prefix}__league_id' if prefix else 'league_id'] = value
    return filters


def build_keyword_filter(keywords: str, prefix: str = '') -> Q:
    return (
        Q(
            **{
                f'{prefix}__trophy__isnull' if prefix else 'trophy__isnull': False,
                f'{prefix}__trophy__name__unaccent__icontains' if prefix else 'trophy__name__unaccent__icontains': keywords
            }
        ) | Q(
            **{
                f'{prefix}__flag__isnull' if prefix else 'flag__isnull': False,
                f'{prefix}__flag__name__unaccent__icontains' if prefix else 'flag__name__unaccent__icontains': keywords
            }
        ) | Q(
            **{
                f'{prefix}__league__isnull' if prefix else 'league__isnull': False,
                f'{prefix}__league__name__unaccent__icontains' if prefix else 'league__name__unaccent__icontains': keywords
            }
        ) | Q(
            **{
                f'{prefix}__sponsor__isnull' if prefix else 'sponsor__isnull': False,
                f'{prefix}__sponsor__unaccent__icontains' if prefix else 'sponsor__unaccent__icontains': keywords
            }
        ) | Q(
            **{
                f'{prefix}__town__isnull' if prefix else 'town__isnull': False,
                f'{prefix}__town__unaccent__icontains' if prefix else 'town__unaccent__icontains': keywords
            }
        )
    )
