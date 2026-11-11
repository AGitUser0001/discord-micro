# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class PreferredLocale(StrEnum):
    bg = 'bg'
    cs = 'cs'
    da = 'da'
    de = 'de'
    el = 'el'
    en_GB = 'en-GB'
    en_US = 'en-US'
    es_419 = 'es-419'
    es_ES = 'es-ES'
    fi = 'fi'
    fr = 'fr'
    hi = 'hi'
    hr = 'hr'
    hu = 'hu'
    id = 'id'
    it = 'it'
    ja = 'ja'
    ko = 'ko'
    lt = 'lt'
    nl = 'nl'
    no = 'no'
    pl = 'pl'
    pt_BR = 'pt-BR'
    ro = 'ro'
    ru = 'ru'
    sv_SE = 'sv-SE'
    th = 'th'
    tr = 'tr'
    uk = 'uk'
    vi = 'vi'
    zh_CN = 'zh-CN'
    zh_TW = 'zh-TW'
