# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class ConnectedAccountProviders(StrEnum):
    BATTLENET = 'battlenet'
    BLUESKY = 'bluesky'
    BUNGIE = 'bungie'
    EBAY = 'ebay'
    EPIC_GAMES = 'epicgames'
    FACEBOOK = 'facebook'
    GITHUB = 'github'
    INSTAGRAM = 'instagram'
    LETTERBOXD = 'letterboxd'
    MASTODON = 'mastodon'
    LEAGUE_OF_LEGENDS = 'leagueoflegends'
    PAYPAL = 'paypal'
    PLAYSTATION = 'playstation'
    REDDIT = 'reddit'
    RIOT_GAMES = 'riotgames'
    ROBLOX = 'roblox'
    SKYPE = 'skype'
    SPOTIFY = 'spotify'
    STEAM = 'steam'
    TIKTOK = 'tiktok'
    TWITCH = 'twitch'
    TWITTER = 'twitter'
    XBOX = 'xbox'
    YOUTUBE = 'youtube'
    DOMAIN = 'domain'
