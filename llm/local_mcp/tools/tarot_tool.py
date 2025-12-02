"""Tarot tool implementation for Local MCP Server.

Provides mystical guidance through tarot card readings for incident operations.
"""

import logging
import random
from typing import Any, Dict, Optional

logger = logging.getLogger("LocalMCPServer")

# Major Arcana Tarot Deck (22 cards)
TAROT_DECK = [
    {
        "name": "The Fool",
        "meaning": "New beginnings, innocence, spontaneity, free spirit",
        "risk_alignment": "opportunity",
        "omen_message": "Embrace the unknown. New approaches may reveal unexpected solutions to persistent issues."
    },
    {
        "name": "The Magician",
        "meaning": "Manifestation, resourcefulness, power, inspired action",
        "risk_alignment": "opportunity",
        "omen_message": "You have all the tools needed. Channel your resources wisely to transform challenges into victories."
    },
    {
        "name": "The High Priestess",
        "meaning": "Intuition, sacred knowledge, divine feminine, subconscious mind",
        "risk_alignment": "caution",
        "omen_message": "Trust your instincts. Hidden patterns in your systems may reveal themselves through careful observation."
    },
    {
        "name": "The Empress",
        "meaning": "Abundance, nurturing, fertility, nature",
        "risk_alignment": "stability",
        "omen_message": "Systems flourish under care. Nurture your infrastructure and it will sustain you through turbulent times."
    },
    {
        "name": "The Emperor",
        "meaning": "Authority, structure, control, father figure",
        "risk_alignment": "stability",
        "omen_message": "Strong foundations prevent collapse. Enforce structure and governance to maintain order."
    },
    {
        "name": "The Hierophant",
        "meaning": "Tradition, conformity, morality, ethics",
        "risk_alignment": "stability",
        "omen_message": "Follow established protocols. Proven practices exist for a reason—deviation invites chaos."
    },
    {
        "name": "The Lovers",
        "meaning": "Harmony, relationships, alignment, choices",
        "risk_alignment": "opportunity",
        "omen_message": "Integration brings strength. Align your systems and teams for harmonious operations."
    },
    {
        "name": "The Chariot",
        "meaning": "Control, willpower, success, determination",
        "risk_alignment": "transformation",
        "omen_message": "Seize control of runaway processes. Direct your momentum toward resolution with unwavering focus."
    },
    {
        "name": "Strength",
        "meaning": "Courage, patience, control, compassion",
        "risk_alignment": "stability",
        "omen_message": "Gentle persistence overcomes resistance. Address incidents with patience rather than force."
    },
    {
        "name": "The Hermit",
        "meaning": "Introspection, solitude, inner guidance, withdrawal",
        "risk_alignment": "caution",
        "omen_message": "Look inward for answers. Deep analysis of logs and metrics will illuminate the path forward."
    },
    {
        "name": "Wheel of Fortune",
        "meaning": "Cycles, destiny, turning point, good luck",
        "risk_alignment": "transformation",
        "omen_message": "Change is inevitable. Prepare for shifts in system behavior—fortune favors the prepared."
    },
    {
        "name": "Justice",
        "meaning": "Fairness, truth, cause and effect, law",
        "risk_alignment": "stability",
        "omen_message": "Every action has consequences. Root causes must be addressed to prevent recurring incidents."
    },
    {
        "name": "The Hanged Man",
        "meaning": "Suspension, letting go, new perspective, sacrifice",
        "risk_alignment": "caution",
        "omen_message": "Sometimes inaction is wisdom. Pause before deploying—perspective reveals hidden risks."
    },
    {
        "name": "Death",
        "meaning": "Endings, transformation, transition, letting go",
        "risk_alignment": "transformation",
        "omen_message": "Old systems must die for new ones to thrive. Embrace necessary deprecation and migration."
    },
    {
        "name": "Temperance",
        "meaning": "Balance, moderation, patience, purpose",
        "risk_alignment": "stability",
        "omen_message": "Seek equilibrium in all things. Balanced load distribution prevents cascading failures."
    },
    {
        "name": "The Devil",
        "meaning": "Bondage, materialism, playfulness, addiction",
        "risk_alignment": "caution",
        "omen_message": "Beware of technical debt. Dependencies and shortcuts bind you—break free before they consume you."
    },
    {
        "name": "The Tower",
        "meaning": "Sudden change, upheaval, chaos, revelation, awakening",
        "risk_alignment": "disruption",
        "omen_message": "Beware of cascading failures. Systems built on unstable foundations may crumble. Prepare for unexpected incidents."
    },
    {
        "name": "The Star",
        "meaning": "Hope, inspiration, serenity, renewal",
        "risk_alignment": "opportunity",
        "omen_message": "Light pierces darkness. Even in crisis, opportunities for improvement shine through."
    },
    {
        "name": "The Moon",
        "meaning": "Illusion, intuition, uncertainty, subconscious",
        "risk_alignment": "caution",
        "omen_message": "Not all is as it seems. False positives and misleading metrics may cloud your judgment."
    },
    {
        "name": "The Sun",
        "meaning": "Success, vitality, confidence, joy",
        "risk_alignment": "opportunity",
        "omen_message": "Clarity and success await. Your systems are aligned—trust in your monitoring and automation."
    },
    {
        "name": "Judgement",
        "meaning": "Reflection, reckoning, inner calling, absolution",
        "risk_alignment": "transformation",
        "omen_message": "Time for retrospection. Review past incidents to inform future decisions and prevent recurrence."
    },
    {
        "name": "The World",
        "meaning": "Completion, accomplishment, travel, fulfillment",
        "risk_alignment": "opportunity",
        "omen_message": "A cycle completes. Celebrate resolved incidents and prepare for the next phase of operations."
    }
]


def tarot_draw(arguments: Dict[str, Any], request_id: Optional[Any] = None) -> Dict[str, Any]:
    """
    Draw a tarot card *influenced by incident insights*.
    
    Args:
        arguments: {
            "insights": {
                "trend_summary": [...],
                "risk_trend": [...],
                "category_hotspots": [...],
                "anomaly_detection": [...]
            }
        }
    Returns:
        dict: {
            "card_name": str,           # e.g., "The Tower"
            "meaning": str,             # Card interpretation
            "risk_alignment": str,      # e.g., "disruption", "stability"
            "omen_message": str         # Contextual message for incident ops
        }
    """
    logger.info(
        f"[request_id={request_id}] [tool=tarot.draw] Tarot request received"
    )

    # -----------------------------------------
    # Extract insights (supports legacy empty {})
    # -----------------------------------------
    insights = {}
    if isinstance(arguments, dict):
        insights = arguments.get("insights", {}) or {}

    trend_text = " ".join(insights.get("trend_summary", [])).lower()
    risk_text = " ".join(insights.get("risk_trend", [])).lower()
    hotspot_list = insights.get("category_hotspots", [])
    anomaly_text = " ".join(insights.get("anomaly_detection", [])).lower()

    logger.info(
        f"[request_id={request_id}] [tool=tarot.draw] Insight context extracted: "
        f"trend='{trend_text[:60]}', risk='{risk_text[:60]}', hotspots={hotspot_list}, anomalies='{anomaly_text[:60]}'"
    )

    # -----------------------------------------
    # Determine symbolic risk theme
    # -----------------------------------------
    theme = "neutral"

    if any(w in risk_text for w in ["critical", "severe", "high risk", "spiking", "escalat"]):
        theme = "disruption"
    elif any(w in trend_text for w in ["increase", "rising", "unstable", "decline"]):
        theme = "caution"
    elif any(w in anomaly_text for w in ["unusual", "unexpected", "anomal"]):
        theme = "transformation"
    elif any(w in trend_text for w in ["stable", "improved", "recover"]):
        theme = "stability"
    else:
        theme = "opportunity"

    logger.info(
        f"[request_id={request_id}] [tool=tarot.draw] Derived tarot theme: {theme}"
    )

    # -----------------------------------------
    # Map themes → candidate cards
    # -----------------------------------------
    theme_cards = {
        "disruption": ["The Tower", "The Devil", "Death"],
        "caution": ["The Moon", "The Hanged Man", "The Hermit"],
        "transformation": ["Judgement", "Wheel of Fortune", "Death"],
        "stability": ["The Sun", "Strength", "Justice", "Temperance"],
        "opportunity": ["The Star", "The Magician", "The World", "The Fool"]
    }

    candidate_names = theme_cards.get(theme, ["Wheel of Fortune"])

    # Find card objects matching candidate names
    candidates = [c for c in TAROT_DECK if c["name"] in candidate_names]

    # Fallback to random if something unexpected happens
    if not candidates:
        candidates = TAROT_DECK

    # -----------------------------------------
    # Draw one deterministic-themed card
    # -----------------------------------------
    card = random.choice(candidates)

    logger.info(
        f"[request_id={request_id}] [tool=tarot.draw] Selected card={card['name']} (theme={theme})"
    )

    # -----------------------------------------
    # Build contextual omen message
    # -----------------------------------------
    hotspot_text = ""
    if hotspot_list:
        hotspot_text = f" Hotspots detected in: {', '.join(hotspot_list)}."

    anomaly_hint = ""
    if "anomal" in anomaly_text or "unusual" in anomaly_text:
        anomaly_hint = " Unusual patterns suggest deeper underlying volatility."

    omen_message = (
        f"{card['omen_message']} "
        f"This card aligns with {theme} themes in your incident data."
        f"{hotspot_text}{anomaly_hint}"
    )

    # -----------------------------------------
    # Return same schema as before
    # -----------------------------------------
    return {
        "card_name": card["name"],
        "meaning": card["meaning"],
        "risk_alignment": theme,
        "omen_message": omen_message
    }
