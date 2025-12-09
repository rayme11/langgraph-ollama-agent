# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Sports betting tools for NewsGenie.

This module provides:
  - get_sports_odds: fetch live odds (moneyline, spreads, totals)
    from The Odds API.
  - get_team_form: team performance over last N days/games
    from Sportsdata.io.
  - get_player_form: player performance over last N days/games
    from Sportsdata.io.

All tools are designed to be used by the LangGraph agent.
"""

from typing import Dict, Any, List, Optional, Tuple
import requests
from datetime import datetime, timedelta

from langchain.tools import tool

from app.config import get_settings

settings = get_settings()


# ---------------------------------------------------------------------------
# Helper: map (sport, league) -> The Odds API sport_key
# ---------------------------------------------------------------------------

def _get_odds_sport_key(sport: str, league: str) -> Optional[str]:
    """
    Map (sport, league) to The Odds API sport_key.

    Examples:
      ("basketball", "nba")   -> "basketball_nba"
      ("basketball", "cbb")   -> "basketball_ncaab"
      ("americanfootball", "nfl") -> "americanfootball_nfl"
      ("baseball", "mlb")     -> "baseball_mlb"
      ("hockey", "nhl")       -> "icehockey_nhl"
      ("soccer", "soccer")    -> "soccer"
    """
    key = (sport.lower(), league.lower())
    mapping: Dict[Tuple[str, str], str] = {
        ("basketball", "nba"): "basketball_nba",
        ("basketball", "cbb"): "basketball_ncaab",
        ("basketball", "ncaab"): "basketball_ncaab",
        ("americanfootball", "nfl"): "americanfootball_nfl",
        ("baseball", "mlb"): "baseball_mlb",
        ("hockey", "nhl"): "icehockey_nhl",
        ("soccer", "soccer"): "soccer",
    }
    return mapping.get(key)


# ---------------------------------------------------------------------------
# Helper: map league -> Sportsdata.io base URL
# ---------------------------------------------------------------------------

def _get_sportsdata_base_url(league: str) -> Optional[str]:
    """
    Map a league key to the correct Sportsdata.io base URL from settings.
    """
    key = league.lower()
    mapping: Dict[str, str] = {
        "nba": settings.sportsdata_nba_base_url,
        "nfl": settings.sportsdata_nfl_base_url,
        "mlb": settings.sportsdata_mlb_base_url,
        "nhl": settings.sportsdata_nhl_base_url,
        "cbb": settings.sportsdata_cbb_base_url,
        "ncaab": settings.sportsdata_cbb_base_url,
        "soccer": settings.sportsdata_soccer_base_url,
    }
    return mapping.get(key)


# ---------------------------------------------------------------------------
# Helper: compute implied probability from American odds
# ---------------------------------------------------------------------------

def compute_implied_probability(american_odds: int) -> float:
    """
    Compute implied probability from American odds.

    For positive odds (e.g. +150):
      p = 100 / (odds + 100)

    For negative odds (e.g. -180):
      p = -odds / (-odds + 100)

    Returns:
        Probability as a decimal (e.g. 0.40 == 40%).
    """
    if american_odds == 0:
        return 0.5

    if american_odds > 0:
        return 100.0 / (american_odds + 100.0)
    else:
        return (-american_odds) / ((-american_odds) + 100.0)


# ---------------------------------------------------------------------------
# Tool: get_sports_odds (The Odds API)
# ---------------------------------------------------------------------------

@tool("get_sports_odds", return_direct=False)
def get_sports_odds(
    sport: str,
    league: str,
    home_team: Optional[str] = None,
    away_team: Optional[str] = None,
    market_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Fetch live betting odds for a given sport/league and optional matchup.

    Uses The Odds API: https://the-odds-api.com/

    Args:
        sport: Friendly sport name ("basketball", "americanfootball",
               "baseball", "hockey", "soccer").
        league: League identifier ("nba", "nfl", "mlb", "nhl", "cbb", "soccer").
        home_team: Optional home team name to filter on.
        away_team: Optional away team name to filter on.
        market_types: Optional list of market types, e.g. ["h2h", "spreads", "totals"].

    Returns:
        dict with:
          - sport
          - league
          - games: list of games with normalized odds
          - error: optional error information
    """
    api_key = settings.odds_api_key
    base_url = settings.odds_api_base_url

    if not api_key:
        return {
            "sport": sport,
            "league": league,
            "games": [],
            "error": {
                "code": "missing_api_key",
                "message": "ODDS_API_KEY is not set in the environment.",
            },
        }

    sport_key = _get_odds_sport_key(sport, league)
    if not sport_key:
        return {
            "sport": sport,
            "league": league,
            "games": [],
            "error": {
                "code": "unsupported_sport_league",
                "message": "No sport_key mapping for (sport={}, league={}).".format(
                    sport, league
                ),
            },
        }

    if market_types is None or len(market_types) == 0:
        market_types = ["h2h", "spreads", "totals"]

    params = {
        "apiKey": api_key,
        "regions": "us",
        "markets": ",".join(market_types),
        "oddsFormat": "american",
    }

    url = "{}/sports/{}/odds".format(base_url, sport_key)

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        raw_games = resp.json()
    except Exception as e:
        return {
            "sport": sport,
            "league": league,
            "games": [],
            "error": {
                "code": "odds_api_error",
                "message": str(e),
            },
        }

    normalized_games: List[Dict[str, Any]] = []

    for g in raw_games:
        game_home = g.get("home_team")
        game_away = g.get("away_team")

        if home_team:
            if not game_home or home_team.lower() not in game_home.lower():
                continue
        if away_team:
            if not game_away or away_team.lower() not in game_away.lower():
                continue

        commence_time = g.get("commence_time")
        bookmakers = g.get("bookmakers", []) or []

        markets_normalized: List[Dict[str, Any]] = []

        for bk in bookmakers:
            bk_markets = bk.get("markets", []) or []
            for m in bk_markets:
                m_type = m.get("key")
                outcomes = m.get("outcomes", []) or []
                norm_outcomes: List[Dict[str, Any]] = []

                for o in outcomes:
                    entry: Dict[str, Any] = {
                        "name": o.get("name"),
                        "price": o.get("price"),
                    }
                    if "point" in o:
                        entry["point"] = o.get("point")

                    try:
                        price = o.get("price")
                        if isinstance(price, (int, float)):
                            entry["implied_probability"] = compute_implied_probability(int(price))
                    except Exception:
                        pass

                    norm_outcomes.append(entry)

                markets_normalized.append(
                    {
                        "type": m_type,
                        "bookmaker": bk.get("title") or bk.get("key"),
                        "outcomes": norm_outcomes,
                    }
                )

        normalized_games.append(
            {
                "home_team": game_home,
                "away_team": game_away,
                "commence_time": commence_time,
                "markets": markets_normalized,
            }
        )

    return {
        "sport": sport,
        "league": league,
        "games": normalized_games,
        "error": None,
    }


# ---------------------------------------------------------------------------
# Tool: get_team_form (Sportsdata.io)
# ---------------------------------------------------------------------------

@tool("get_team_form", return_direct=False)
def get_team_form(
    league: str,
    team: str,
    days_back: int = 5,
) -> Dict[str, Any]:
    """
    Retrieve recent team performance over the last N days using Sportsdata.io.
    """
    api_key = settings.sportsdata_api_key
    if not api_key:
        return {
            "league": league,
            "team": team,
            "games_analyzed": 0,
            "error": {
                "code": "missing_api_key",
                "message": "SPORTSDATA_API_KEY is not set in the environment.",
            },
        }

    base_url = _get_sportsdata_base_url(league)
    if not base_url:
        return {
            "league": league,
            "team": team,
            "games_analyzed": 0,
            "error": {
                "code": "unsupported_league",
                "message": "League '{}' is not supported for team form.".format(league),
            },
        }

    if days_back <= 0:
        days_back = 1

    today = datetime.utcnow().date()
    start_date = today - timedelta(days=days_back - 1)

    recent_games: List[Dict[str, Any]] = []

    headers = {
        "Ocp-Apim-Subscription-Key": api_key,
    }

    date_cursor = start_date
    while date_cursor <= today:
        date_str = date_cursor.isoformat()
        url = "{}/scores/json/TeamGameStatsByDate/{}".format(base_url, date_str)

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            day_stats = resp.json() or []
        except Exception:
            day_stats = []

        for rec in day_stats:
            rec_team = (
                rec.get("Team")
                or rec.get("Name")
                or rec.get("TeamKey")
            )
            if not rec_team:
                continue

            if team.lower() not in str(rec_team).lower():
                continue

            pts_for = (
                rec.get("Points")
                or rec.get("Score")
                or rec.get("PointsScored")
            )
            pts_against = (
                rec.get("OpponentScore")
                or rec.get("OpponentPoints")
                or rec.get("PointsAllowed")
            )

            try:
                pts_for_val = float(pts_for) if pts_for is not None else None
                pts_against_val = float(pts_against) if pts_against is not None else None
            except Exception:
                pts_for_val = None
                pts_against_val = None

            result = None
            margin = None
            if pts_for_val is not None and pts_against_val is not None:
                margin = pts_for_val - pts_against_val
                if pts_for_val > pts_against_val:
                    result = "W"
                elif pts_for_val < pts_against_val:
                    result = "L"
                else:
                    result = "T"

            opponent = rec.get("Opponent") or rec.get("OpponentName")
            game_date = rec.get("Day") or rec.get("Date") or date_str
            home_away = rec.get("HomeOrAway") or rec.get("HomeAway") or None

            recent_games.append(
                {
                    "date": game_date,
                    "opponent": opponent,
                    "home_away": home_away,
                    "points_for": pts_for_val,
                    "points_against": pts_against_val,
                    "margin": margin,
                    "result": result,
                    "raw": rec,
                }
            )

        date_cursor += timedelta(days=1)

    games_analyzed = len(recent_games)
    if games_analyzed == 0:
        return {
            "league": league,
            "team": team,
            "days_back": days_back,
            "games_analyzed": 0,
            "record": {"wins": 0, "losses": 0},
            "average_points_for": None,
            "average_points_against": None,
            "average_margin": None,
            "recent_games": [],
            "error": {
                "code": "no_games_found",
                "message": (
                    "No recent games found for team '{}' in league '{}' "
                    "over the last {} day(s).".format(team, league, days_back)
                ),
            },
        }

    wins = sum(1 for g in recent_games if g.get("result") == "W")
    losses = sum(1 for g in recent_games if g.get("result") == "L")

    pts_for_list = [g["points_for"] for g in recent_games if g["points_for"] is not None]
    pts_against_list = [g["points_against"] for g in recent_games if g["points_against"] is not None]
    margin_list = [g["margin"] for g in recent_games if g["margin"] is not None]

    avg_for = sum(pts_for_list) / len(pts_for_list) if pts_for_list else None
    avg_against = sum(pts_against_list) / len(pts_against_list) if pts_against_list else None
    avg_margin = sum(margin_list) / len(margin_list) if margin_list else None

    return {
        "league": league,
        "team": team,
        "days_back": days_back,
        "games_analyzed": games_analyzed,
        "record": {"wins": wins, "losses": losses},
        "average_points_for": avg_for,
        "average_points_against": avg_against,
        "average_margin": avg_margin,
        "recent_games": recent_games,
        "error": None,
    }


# ---------------------------------------------------------------------------
# Tool: get_player_form (Sportsdata.io)
# ---------------------------------------------------------------------------

@tool("get_player_form", return_direct=False)
def get_player_form(
    league: str,
    player_name: str,
    days_back: int = 5,
) -> Dict[str, Any]:
    """
    Retrieve recent player performance over the last N days using Sportsdata.io.
    """
    api_key = settings.sportsdata_api_key
    if not api_key:
        return {
            "league": league,
            "player_name": player_name,
            "games_analyzed": 0,
            "error": {
                "code": "missing_api_key",
                "message": "SPORTSDATA_API_KEY is not set in the environment.",
            },
        }

    base_url = _get_sportsdata_base_url(league)
    if not base_url:
        return {
            "league": league,
            "player_name": player_name,
            "games_analyzed": 0,
            "error": {
                "code": "unsupported_league",
                "message": "League '{}' is not supported for player form.".format(league),
            },
        }

    if days_back <= 0:
        days_back = 1

    today = datetime.utcnow().date()
    start_date = today - timedelta(days=days_back - 1)

    recent_games: List[Dict[str, Any]] = []

    headers = {
        "Ocp-Apim-Subscription-Key": api_key,
    }

    date_cursor = start_date
    while date_cursor <= today:
        date_str = date_cursor.isoformat()
        url = "{}/stats/json/PlayerGameStatsByDate/{}".format(base_url, date_str)

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            day_stats = resp.json() or []
        except Exception:
            day_stats = []

        for rec in day_stats:
            rec_name = rec.get("Name") or rec.get("PlayerName")
            if not rec_name:
                continue

            if player_name.lower() not in str(rec_name).lower():
                continue

            points = rec.get("Points")
            rebounds = rec.get("Rebounds")
            assists = rec.get("Assists")
            minutes = rec.get("Minutes") or rec.get("MinutesPlayed")

            passing_yards = rec.get("PassingYards")
            rushing_yards = rec.get("RushingYards")
            receiving_yards = rec.get("ReceivingYards")
            goals = rec.get("Goals")
            shots_on_goal = rec.get("ShotsOnGoal") or rec.get("ShotsOnTarget")

            game_date = rec.get("Day") or rec.get("Date") or date_str
            opponent = rec.get("Opponent") or rec.get("OpponentName") or None
            team = rec.get("Team") or rec.get("TeamName") or None

            recent_games.append(
                {
                    "date": game_date,
                    "team": team,
                    "opponent": opponent,
                    "player_name": rec_name,
                    "points": points,
                    "rebounds": rebounds,
                    "assists": assists,
                    "minutes": minutes,
                    "passing_yards": passing_yards,
                    "rushing_yards": rushing_yards,
                    "receiving_yards": receiving_yards,
                    "goals": goals,
                    "shots_on_goal": shots_on_goal,
                    "raw": rec,
                }
            )

        date_cursor += timedelta(days=1)

    games_analyzed = len(recent_games)
    if games_analyzed == 0:
        return {
            "league": league,
            "player_name": player_name,
            "days_back": days_back,
            "games_analyzed": 0,
            "averages": {},
            "recent_games": [],
            "error": {
                "code": "no_games_found",
                "message": (
                    "No recent games found for player '{}' in league '{}' "
                    "over the last {} day(s).".format(player_name, league, days_back)
                ),
            },
        }

    def _avg(field: str) -> Optional[float]:
        vals = [g[field] for g in recent_games if g.get(field) is not None]
        if not vals:
            return None
        return sum(float(v) for v in vals) / len(vals)

    averages = {
        "points": _avg("points"),
        "rebounds": _avg("rebounds"),
        "assists": _avg("assists"),
        "minutes": _avg("minutes"),
        "passing_yards": _avg("passing_yards"),
        "rushing_yards": _avg("rushing_yards"),
        "receiving_yards": _avg("receiving_yards"),
        "goals": _avg("goals"),
        "shots_on_goal": _avg("shots_on_goal"),
    }

    return {
        "league": league,
        "player_name": player_name,
        "days_back": days_back,
        "games_analyzed": games_analyzed,
        "averages": averages,
        "recent_games": recent_games,
        "error": None,
    }
