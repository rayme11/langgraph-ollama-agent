# -*- coding: utf-8 -*-
"""
Simple sports betting smoke test for NewsGenie.

This script:
  - Calls run_agent_turn() with a sports betting question.
  - Prints the assistant's response.

Requirements:
  - ODDS_API_KEY set in .env (The Odds API).
  - SPORTSDATA_API_KEY set in .env (Sportsdata.io).
  - Database migrations already run (so app.db schema exists).
"""

from app.agent.graph import run_agent_turn


def main():
    # You can change this to any identifier you want
    external_user_id = "sports-smoke-tester@example.com"

    # Start with a fresh conversation (None)
    conversation_id = None

    # Example question:
    # Adjust the teams / sport / league wording as you like
    user_question = (
        "For the NBA today, is Lakers -3.5 a good bet? "
        "Give me a low, medium, or high recommendation and explain why."
    )

    print("User:", user_question)
    print("----")

    result = run_agent_turn(
        external_user_id=external_user_id,
        conversation_id=conversation_id,
        user_text=user_question,
    )

    new_conversation_id = result["conversation_id"]
    assistant_text = result["assistant"]

    print(f"[conversation_id={new_conversation_id}]")
    print("Assistant:")
    print(assistant_text)


if __name__ == "__main__":
    main()
