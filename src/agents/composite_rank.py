#!/usr/bin/env python
"""
Composite Rank Agent: aggregate all agent signals/confidences into a single score
"""
from src.graph.state import AgentState, show_agent_reasoning
from langchain_core.messages import HumanMessage
import json

# Map signal to numeric
_signal_map = {"bullish": 1, "neutral": 0, "bearish": -1}

def composite_rank_agent(state: AgentState) -> dict:
    """Aggregate signals from other agents into a composite score."""
    scores = []
    details = {}
    result = {}
    
    # Extract analyst signals from state data
    analyst_signals = {}
    
    # Look for analyst signals in the state
    if 'data' in state and 'analyst_signals' in state['data']:
        analyst_signals = state['data']['analyst_signals']
    
    # Look for direct agent signals in state data (e.g., from Ben Graham)
    for agent_name, agent_data in state.get('data', {}).items():
        if agent_name != 'analyst_signals' and isinstance(agent_data, dict):
            # Check if this agent has signal data directly
            for ticker, signal_data in agent_data.items():
                if isinstance(signal_data, dict) and 'signal' in signal_data and 'confidence' in signal_data:
                    # This is a valid signal, create/update the analyst_signals structure
                    if agent_name not in analyst_signals:
                        analyst_signals[agent_name] = {}
                    analyst_signals[agent_name][ticker] = signal_data
    
    # Process signals
    if not analyst_signals:
        result = {"composite_score": 0.0, "components": {}, "message": "No analyst signals found"}
    else:
        # Process signals if they exist
        for agent_name, agent_signals in analyst_signals.items():
            for ticker, signal_data in agent_signals.items():
                if isinstance(signal_data, dict) and 'signal' in signal_data and 'confidence' in signal_data:
                    sig = signal_data.get('signal', '').lower()
                    conf = signal_data.get('confidence', 0)
                    val = _signal_map.get(sig, 0)
                    weighted = val * conf / 100.0  # Convert percentage to decimal
                    
                    # Store by ticker and agent
                    if ticker not in details:
                        details[ticker] = {}
                    details[ticker][agent_name] = weighted
                    scores.append(weighted)
        
        # Calculate composite score
        composite = sum(scores) / len(scores) if scores else 0.0
        result = {
            "composite_score": composite,
            "components": details,
            "ticker_scores": {
                ticker: sum(agent_scores.values()) / len(agent_scores)
                for ticker, agent_scores in details.items()
                if agent_scores
            }
        }
    
    # Optionally show reasoning
    if state["metadata"].get("show_reasoning"):
        show_agent_reasoning(result, "Composite Rank")
    
    # Return updated state with the message and data
    message = HumanMessage(content=json.dumps(result), name="composite_rank")
    
    # Update the state with our composite rank data
    state["data"]["composite_rank"] = result
    
    return {"messages": [message], "data": state["data"]} 