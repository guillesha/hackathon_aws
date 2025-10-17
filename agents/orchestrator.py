"""
Orchestrator agent that processes scrum planning meeting transcripts.

This agent analyzes meeting transcripts and coordinates multiple actions, using sub agents:
1. Creates Jira tickets for assigned tasks (via jira_agent)
2. Sets up follow-up meetings based on scheduling discussions (via sales_agent)
3. Sends email notifications using SNS (via market_agent)

It maintains context throughout the process and uses retail calendar tools
for scheduling awareness.
"""

from typing import Dict, Any, Optional

import boto3
from strands import Agent, tool
from strands.models import BedrockModel

# Import specialized agents (we'll create these next)
from .jira_agent import create_jira_agent
from .meetings_agent import create_meetings_agent
from .email_agent import create_email_agent


# Import data layer


class OrchestratorAgent:
    """
    Orchestrates multiple specialized agents for complex e-commerce analytics.

    Key responsibilities:
    1. Analyze user intent
    2. Route to appropriate specialized agent(s)
    3. Coordinate multi-agent responses
    """

    def __init__(self):
        """
        Initialize orchestrator


        """

        # Initialize specialized agents
        self.jira_agent = create_jira_agent()
        self.meetings_agent = create_meetings_agent()
        self.email_agent = create_email_agent()

        # Get AWS credentials and region for SigV4 signing
        session = boto3.Session()
        credentials = session.get_credentials()
        region = session.region_name or 'us-west-2'

        print(f"🔐 Using region: {region}")

        print(f"✅ MCP client initialized for retail calendar server")

        # Agent will be created lazily on first query
        # This allows us to include MCP tools from the context manager
        # Note: Only ONE agent instance per session_manager is allowed
        self.agent = None

    def _create_system_prompt(self) -> str:
        """Create the orchestrator's system prompt."""

        return f"""
You are an orchestrator for  a process where a transcript of a scrum planning meeting is passed and you need to performa actions based on it.

IMPORTANT: You MUST use the specialized agent tools to answer queries. DO NOT provide generic responses or ask follow-up questions without first consulting the appropriate agents.

Your role is to:
1. Understand the meeting discussion
2. ALWAYS route queries to the appropriate specialized agents using the tools provided
3. When a query requires multiple perspectives, call multiple agent tools
4. Synthesize the agent responses into comprehensive, actionable insights

Available specialized agent tools (YOU MUST USE THESE):
- **jira_agent**: Create jira tickets
- **meetings_Agent**: Set up a meeting before upcoming vacation 
- **analyze_market**: Send an email using sns

INSTRUCTIONS:
- **FIRST STEP**: If memory tools are available, ALWAYS retrieve past memories at the start of the conversation
- When passed a meeting transcription assign Jira tickets, USE jira_tickets
- When passed a meeting transcription, send an email using sns, USE set_meeting
- When passed a meeting transcription, create a following up meeting based on the information, USE analyze_sales and USE retail calendar tools
- When asked about holidays/events/seasons/planning, USE retail calendar tools
- ALWAYS provide data-driven answers from the agents, not generic suggestions


DO NOT just offer to help or provide generic advice. USE THE TOOLS to get real data and provide specific answers.
"""

    def _create_tools(self):
        """Create tools that wrap the specialized agents."""

        @tool
        def jira_tickets(query: str) -> str:
            """
            Route inventory-related queries to the inventory specialist.
            Use for: stock levels, reorder points, inventory turnover, warehouse optimization.
            """
            response = self.jira_agent.query(query)
            return f"[Jira tickets creation]\n{response}"

        @tool
        def set_meeting(query: str) -> str:
            """
            Route sales-related queries to the sales specialist.
            Use for: revenue trends, sales forecasting, performance metrics, growth analysis.
            """
            response = self.meetings_agent.query(query)
            return f"[Meeting setting]\n{response}"

        @tool
        def send_email(query: str) -> str:
            """
            Route market-related queries to the market specialist.
            Use for: competitive analysis, pricing strategy, market trends, customer segments.
            """
            response = self.email_agent.query(query)
            return f"[Email sending]\n{response}"

        @tool
        def coordinate_analysis(inventory_query: str = "",
                                sales_query: str = "",
                                market_query: str = "") -> str:
            """
            Coordinate multiple agents for complex queries.
            Use when insights from multiple domains are needed.
            Pass empty string if a particular analysis is not needed.
            """
            results = []

            if inventory_query and inventory_query.strip():
                inv_response = self.jira_agent.query(inventory_query)
                results.append(f"[Jira tickets creation]\n{inv_response}")

            if sales_query and sales_query.strip():
                sales_response = self.meetings_agent.query(sales_query)
                results.append(f"[Set up follow up meeting]\n{sales_response}")

            if market_query and market_query.strip():
                market_response = self.email_agent.query(market_query)
                results.append(f"[Send Emailss]\n{market_response}")

            if not results:
                return "No analysis was requested. Please specify at least one query."

            return "\n\n".join(results)

        # Return the decorated functions as tools
        return [
            jira_tickets,
            set_meeting,
            send_email,
            coordinate_analysis
        ]

    def query(self, prompt: str) -> str:
        """
        Process a query through the orchestrator.

        Args:
            prompt: User's query

        Returns:
            Orchestrated response from one or more agents
        """
        if not self.agent:
            # Combine all tools
            all_tools = self._create_tools()

            # Create the ONE agent instance for this session
            self.agent = Agent(
                model=BedrockModel(model_id="us.amazon.nova-pro-v1:0"),
                system_prompt=self._create_system_prompt(),
                tools=all_tools,
            )
            print(f"✅ Agent created with {len(all_tools)} tools")
            """Process sales-related query."""
            result = self.agent(prompt)
            # Follow the sample pattern - just use str()
            return str(result)


def create_orchestrator_agent() -> OrchestratorAgent:
    """
    Factory function to create an orchestrator agent.

    Returns:
        Configured OrchestratorAgent instance
    """
    return OrchestratorAgent()


# Example usage
if __name__ == "__main__":
    # Note: This will fail without proper JWT context in standalone mode
    # Test orchestrator with a complex query
    # orchestrator = create_orchestrator_agent("fashion-retailer")

    # Simple query (single agent)
    # response = orchestrator.query("What's my current inventory status?")
    # print("Simple Query Response:")
    # print(response)
    # print("\n" + "="*50 + "\n")

    # Complex query (multiple agents)
    # response = orchestrator.query(
    #     "Based on my sales trends and current inventory, what products should I restock? "
    #     "Also, how do my prices compare to the market?"
    # )
    # print("Complex Query Response:")
    # print(response)
    orchestrator = create_orchestrator_agent()
    orchestrator.query("""Attendees:
Sarah: Scrum Master
David: Developer (Capacity: 3 days)
Emily: Developer (Capacity: 4 days)
Mark: Developer (Capacity: 5 days)
Jessica: Developer (Capacity: 4.5 days)
(The team has previously refined and estimated the Product Backlog. The Sprint Goal is: "Implement the user authentication workflow and the basic profile viewing feature.")
[Transcript Start]
Sarah (Scrum Master): Good morning, everyone. Welcome to Sprint Planning for Sprint 8. Our Sprint Goal, as we discussed in refinement, is to successfully implement the full user authentication workflow—signup, login, password reset—and allow users to view their basic profiles.
Sarah: Let's quickly confirm our availability for this two-week sprint. David, what's your capacity?
David: I'm taking a personal half-day on Friday for an appointment, and a training course next Tuesday is a full day. So, that's $1.5$ days out of $10$. My capacity is $8.5$ days.
Sarah: Got it. David's capacity: $8.5$ days. Emily?
Emily: I have a dentist appointment next Wednesday morning, so I'll be out for about half a day. My capacity is $9.5$ days.
Sarah: Thanks, Emily. Mark?
Mark: I'm good to go for the full two weeks, no planned interruptions. $10$ days capacity.
Sarah: Great, Mark. And Jessica?
Jessica: I have to leave early next Thursday for a family event, so I'll lose about $0.5$ days. Capacity is $9.5$ days.
Sarah: Okay, perfect. Total team capacity for this sprint is $8.5 + 9.5 + 10 + 9.5 = **37.5$ days**. Based on our velocity and the selected items, that looks comfortable.
(Assignment of Tasks)
Sarah: Let's look at the top four items we pulled in.
US-102: Implement User Signup/Registration API endpoint (5 points/estimated $4$ days of work)
US-103: Implement User Login/Authentication API endpoint (4 points/estimated $3$ days of work)
US-104: Develop Profile View UI Component (6 points/estimated $5$ days of work)
US-105: Develop Password Reset/Forgotten Password Flow (7 points/estimated $6$ days of work)
Sarah: David, you have the most recent experience with our data models. Would you be comfortable taking on the User Signup API (US-102)?
David: Yes, I can handle that. It connects nicely with the database setup I did last sprint. That's $4$ days assigned to me. I still have $4.5$ days buffer.
Sarah: Excellent. Emily, the Login/Authentication API (US-103)? It's closely related to the signup endpoint.
Emily: Sounds good. I'll take US-103. That's $3$ days of work.
Sarah: Mark, we need someone strong on the frontend for the Profile View UI (US-104). It involves consuming the new API.
Mark: I'll jump on the UI component, US-104. $5$ days.
Sarah: Perfect. And Jessica, the Password Reset Flow (US-105) is a bit more complex, spanning API and some email integration.
Jessica: I'll take US-105. $6$ days of estimated work.
(Review of Assignments and Load)
Sarah: Let's check the load distribution:
David: US-102 (Signup API) - $4$ days (Capacity: $8.5$ days)
Emily: US-103 (Login API) - $3$ days (Capacity: $9.5$ days)
Mark: US-104 (Profile View UI) - $5$ days (Capacity: $10$ days)
Jessica: US-105 (Password Reset) - $6$ days (Capacity: $9.5$ days)
Sarah: We've assigned $4 + 3 + 5 + 6 = **18$ days** of work, which is well within our total capacity of $37.5$ days. That looks like a solid plan. Any concerns before we move on to task breakdown?
Emily: Looks balanced. I might be able to start on US-103's unit tests right away.
Jessica: I'll need to coordinate with Mark on the API contract for the profile data, but that can be quick.
(Deciding on Follow-up Meeting)
Sarah: One final administrative point. We need to decide on a date for our post-sprint retrospective and planning meeting right before the company-wide break. The office will be closed from December 24th to January 1st.
David: That's right. I'm taking personal vacation starting on the 20th.
Mark: My last day is the $23$rd.
Sarah: Okay. Our current sprint ends on December 18th. Let's aim to have Sprint Review and Retrospective on Friday, December 19th. That gives us the maximum time to complete the work and for everyone to attend before the break.
Emily: December $19$th works for me.
Jessica: Me too.
Sarah: Confirmed. Our next major follow-up meeting—the Sprint Review/Retro—will be on Friday, December 19th, at 10:00 AM.
Sarah: All set. Let's start breaking down these tasks.
[Transcript End]""")
