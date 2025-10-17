"""
Jira ticket creation agent.

This agent focuses on creating Jira tickets with appropriate assignees
based on context from meeting transcripts and conversations.
"""

import random

from strands import Agent, tool
from strands.models import BedrockModel


class JiraAgent:
    def __init__(self):

        # Create specialized agent
        self.agent = Agent(
            model=BedrockModel(model_id="us.amazon.nova-pro-v1:0"),
            system_prompt=self._create_system_prompt(),
            tools=self._create_tools()
        )

    def _create_system_prompt(self) -> str:
        """Create jira-focused system prompt."""
        return f"""
                Create a Jira Ticket
                The Creator shall always be Automation Bot 
                Also Asigne the Ticket to a random name 
                """

    def _create_tools(self):
        @tool
        def create_jira_ticket(summary: str, description: str, tenant_id: str = "default") -> dict:
            """Mock Jira ticket creation with realistic API-like response."""

            # Generate fake but consistent-looking Jira data
            issue_id = str(random.randint(30000, 99999))
            project_key = random.choice(["DEV", "OPS", "TEST", "PROD", "SEC"])
            issue_number = random.randint(100, 999)
            ticket_key = f"{project_key}-{issue_number}"

            base_url = "http://localhost:8080/rest/api/2/issue"
            self_url = f"{base_url}/{issue_id}"

            print(f"[Tenant {tenant_id}] Creating Jira ticket...")
            print(f"Summary: {summary}")
            print(f"Description: {description}\n")

            # Mock Jira response
            response = {
                "id": issue_id,
                "key": ticket_key,
                "self": self_url,
                "fields": {
                    "summary": summary,
                    "description": description,
                    "status": {"name": random.choice(["To Do", "In Progress", "Done"])},
                    "priority": {"name": random.choice(["Low", "Medium", "High"])},
                    "creator": {
                        "displayName": random.choice(["System Agent", "Automation Bot"]),
                        "active": True
                    }
                }
            }

            return response

        return [
            create_jira_ticket
        ]

    def query(self, prompt: str) -> str:
        """Process jira-related query."""
        result = self.agent(prompt)
        return str(result)


def create_jira_agent() -> JiraAgent:
    """Factory function to create jira agent."""
    return JiraAgent()


# Example usage
if __name__ == "__main__":
    agent = create_jira_agent()
    query = """Attendees:
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
[Transcript End]
    """

    # Test various queries
    print(agent.query(query))
