"""
Phase 2 Runtime Application with Memory Integration.

This extends the Phase 1 runtime to add:
1. AgentCore Memory integration
2. Multi-agent orchestration
3. Two-level tenant/customer isolation
"""

import json
import logging
import os
import sys
from typing import Dict, Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our agents
from agents.orchestrator import create_orchestrator_agent

# Import tenant security

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the runtime app
app = BedrockAgentCoreApp()

# Get region from environment or use default
REGION = os.environ.get("AWS_REGION", "us-west-2")


def import_orchestrator_agent():
    """
    Create an orchestrator agent with memory capabilities using SessionManager.

    Returns:
        Agent's orchestrator
    """

    # Create the orchestrator agent
    orchestrator = create_orchestrator_agent()

    return orchestrator


@app.entrypoint
def agent_invocation(payload: Dict[str, Any], context) -> str:
    """
    Main entry point for agent invocation.

    Secure Implementation:
    - JWT validation handled by infrastructure

    Args:
        payload: Request payload containing customer_id (optional) and prompt
        context: Runtime context (includes JWT validation info)

    Returns:
        JSON response with agent's answer
    """
    try:
        # Log the invocation
        logger.info(f"Agent invocation received")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")

        # Extract customer ID from payload

        # Get the user's prompt
        user_input = payload.get("prompt", "")
        if not user_input:
            # Return error as plain string for AgentCore
            return "Error: No prompt provided in payload"

        # Check if this is a customer-specific query


        orchestrator = import_orchestrator_agent()

        # Add customer context to prompt if available
        enhanced_prompt = user_input

        # Process the query through the orchestrator
        logger.info(f"Processing prompt: {enhanced_prompt[:100]}...")
        response = orchestrator.query(enhanced_prompt)

        # Return response as plain string for AgentCore
        # AgentCore expects a string response, not JSON-wrapped
        logger.info(f"Returning response of length: {len(response)}")
        return str(response)

    except Exception as e:
        logger.error(f"Authentication/processing error: {e}", exc_info=True)
        # Return error as plain string for AgentCore
        return f"Error: {str(e)}"


# Health check endpoint (required for runtime)
@app.ping
def health_check():
    """Health check endpoint for the runtime."""
    from bedrock_agentcore.runtime import PingStatus
    # Return PingStatus enum, not string
    return PingStatus.HEALTHY


if __name__ == "__main__":
    # Start the AgentCore runtime server
    print("Starting Phase 2 Runtime Application")
    print(f"Environment check: {os.environ.get('AGENTCORE_MEMORY_ID_SHARED')}")
    print(f"Region: {REGION}")

    # Run the app - this starts the HTTP server on port 8080
    # The BedrockAgentCoreApp handles all the server setup
    app.run()
