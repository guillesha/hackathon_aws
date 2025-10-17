# Hackathon AWS – Multi-Agent Orchestrator Runtime
A Python 3.11.9 application that runs an AWS Bedrock AgentCore runtime server and orchestrates multiple specialized agents (Jira ticketing, meeting scheduling, email notifications) through a single entrypoint. It is designed to process scrum planning meeting transcripts and coordinate actions via sub-agents.
## Key Features
- Bedrock AgentCore runtime server (HTTP on port 8080).
- Orchestrator agent that routes and coordinates tasks across specialized agents.
- Health check endpoint for platform readiness.
- AWS-friendly setup using boto3 and SigV4 context.
- Simple JSON-based invocation with a single prompt.

## Architecture Overview
- Runtime app: starts the AgentCore HTTP server and exposes:
    - Agent invocation entrypoint for processing prompts
    - Health check endpoint

- Orchestrator agent:
    - Analyzes the input prompt (e.g., a meeting transcript)
    - Invokes specialized sub-agents for:
        - Creating Jira tickets
        - Scheduling follow-up meetings (ICS)
        - Sending email notifications (e.g., via SNS)

    - Synthesizes results into a single response string

## Prerequisites
- Python 3.11.9
- AWS account credentials configured locally (for boto3/Bedrock usage)
- Access to Amazon Bedrock models referenced by the agents
- Network access to run a local HTTP server on port 8080

## Setup
1. Create and activate a virtual environment

- macOS/Linux:
``` bash
python3.11 -m venv .venv
source .venv/bin/activate
```
- Windows (PowerShell):
``` powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```
1. Install dependencies
``` bash
pip install --upgrade pip
pip install -r requirements.txt
```
1. Configure AWS credentials

- Ensure your default AWS credentials are available via one of the standard methods:
    - ~/.aws/credentials and ~/.aws/config
    - Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN (if needed), AWS_REGION

- Recommended region: us-west-2 (override with AWS_REGION if desired)

1. Optional environment variables

- AWS_REGION: defaults to us-west-2 if not provided

You can set environment variables locally:
- macOS/Linux:
``` bash
export AWS_REGION=us-west-2
```
```
- Windows (PowerShell):
``` powershell
$env:AWS_REGION = "us-west-2"
```
## Run the Server
``` bash
python app.py
```
What to expect:
- Server binds to port 8080.
- Logs will show startup messages, region detection, and tool setup when agents are used.

## Endpoints
- Health check
    - Method: GET
    - Path: /ping
    - Response: HEALTHY (via Bedrock AgentCore PingStatus)

- Agent invocation
    - Method: POST
    - Path: /invocations (default AgentCore entrypoint path)
    - Body: JSON with a prompt field

Request body format:
``` json
{
  "prompt": "Your scrum planning transcript or query goes here"
}
```
Response format:
- Plain text string containing the orchestrated result.

## Usage Examples
- Health check:
``` bash
curl -i http://localhost:8080/ping
```
- Invoke the orchestrator:
``` bash
curl -s -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Summarize this planning transcript and create Jira tickets, schedule a review meeting, and notify the team via email: ..."}'
```
- Python example:
``` python
import requests

url = "http://localhost:8080/invocations"
payload = {"prompt": "Process this sprint planning transcript ..."}
resp = requests.post(url, json=payload, timeout=120)
print(resp.text)
```
## Project Structure (high level)
- Runtime app entrypoint
- Orchestrator agent that delegates to:
    - Jira agent (ticket creation)
    - Meetings agent (generate ICS)
    - Email agent (e.g., SNS notification)

- requirements.txt (workshop and runtime dependencies)

## Development Tips
- Use autopep8 for formatting if desired:
``` bash
autopep8 -ir .
```
- Keep your virtual environment active in the shell where you run the server/tests.
- When modifying agents, ensure tool signatures and names align with their usage in the orchestrator.

## Troubleshooting
- Model access or authorization errors
    - Ensure your IAM principal has permissions to invoke the target Bedrock model(s).
    - Verify AWS_REGION matches a region where the model is available.

- AWS credential errors
    - Confirm credentials via aws sts get-caller-identity.
    - If using temporary credentials, ensure AWS_SESSION_TOKEN is set.

- HTTP errors or no response
    - Confirm the server is running on port 8080 and not blocked by a firewall.
    - Validate JSON request structure includes a prompt field.

## Security Notes
- Authentication and authorization for incoming requests should be enforced by your deployment environment or gateway. The server assumes trusted traffic in local development.
- Do not log sensitive data (e.g., PII, secrets) in production.

## License
- Add your license information here.

## Contributing
- Open issues and pull requests are welcome. Please include clear reproduction steps for bugs and keep changes focused per PR.

