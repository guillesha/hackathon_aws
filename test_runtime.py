#!/usr/bin/env python3
"""
Test script for Phase 1 AgentCore Runtime - Direct IAM Authentication.

This script tests the AgentCore runtime directly using IAM authentication,
which is consistent with Phase 1's simplified approach.

Modes:
- Interactive: Ask your own questions (default)
- Auto: Run predefined tests (--auto flag)
- Single prompt: Pass a question as argument
"""

import boto3
import json
from pathlib import Path
import sys
import time


def load_configuration():
    """Load configuration from .env files."""
    config = {}

    # Check deployment directory first
    deployment_env = Path(__file__).parent / 'deployment' / '.env.deployment'
    cognito_env = Path(__file__).parent / 'deployment' / '.env.cognito'

    # Also check parent directory and current directory
    parent_env = Path(__file__).parent.parent / '.env'
    current_env = Path(__file__).parent / '.env'

    # Load from deployment directory
    for env_file in [deployment_env, cognito_env]:
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        line = line.strip()
                        if line.startswith('export '):
                            _, rest = line.split('export ', 1)
                            key, value = rest.split('=', 1)
                        else:
                            key, value = line.split('=', 1)
                        config[key] = value

    # Load from parent and current directory if exists (may override)
    for env_file in [parent_env, current_env]:
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        line = line.strip()
                        if line.startswith('export '):
                            _, rest = line.split('export ', 1)
                            key, value = rest.split('=', 1)
                        else:
                            key, value = line.split('=', 1)
                        config[key] = value

    return config


def get_runtime_client():
    """Get configured bedrock-agentcore client and runtime ARN."""
    config = load_configuration()

    agent_arn = config.get('AGENTCORE_RUNTIME_ARN_SIMPLE') or config.get('AGENTCORE_RUNTIME_ARN_SHARED')
    if not agent_arn:
        print("\n❌ ERROR: No runtime deployment found.")
        print("Please run: python3 deployment/02_deploy_runtime.py")
        return None, None

    try:
        region = agent_arn.split(':')[3]
        client = boto3.client('bedrock-agentcore', region_name=region)
        return client, agent_arn
    except Exception as e:
        print(f"❌ Failed to create bedrock-agentcore client: {e}")
        print("Make sure you have valid AWS credentials configured")
        return None, None


def invoke_runtime(prompt, customer_id="sarah.manager", show_details=False):
    """Invoke the runtime with a prompt."""
    client, agent_arn = get_runtime_client()
    if not client:
        return None

    try:
        session_id = f"test-session-{int(time.time())}-{int(time.time() * 1000000)}"

        payload = {
            "prompt": prompt,
            "customer_id": customer_id
        }

        if show_details:
            print(f"\n🔧 Request Details:")
            print(f"   Runtime: {agent_arn}")
            print(f"   Customer: {customer_id}")
            print(f"   Session: {session_id}")

        response = client.invoke_agent_runtime(
            agentRuntimeArn=agent_arn,
            qualifier='DEFAULT',
            runtimeSessionId=session_id,
            payload=json.dumps(payload)
        )

        if 'response' in response:
            stream = response['response']
            response_text = stream.read().decode('utf-8')
            return response_text

        return None

    except Exception as e:
        print(f"❌ Error invoking runtime: {e}")
        return None


def interactive_mode():
    """Interactive mode - user asks their own questions."""
    print("🎯 INTERACTIVE MODE")
    print("=" * 80)
    print("Ask questions to your AgentCore Runtime. Type 'quit' to exit.")
    print()
    print("💡 Available commands:")
    print("   - Type your question to get an answer")
    print("   - 'switch' to change tenant (fashion-retailer ↔ electronics-store)")
    print("   - 'quit' to exit")
    print()



    print()

    while True:
        try:
            user_input = input("❓ Your prompt: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break

            if not user_input:
                continue

            print(f"\n🚀 Sending to Scrum Master Agent...")

            result = invoke_runtime(user_input)

            if result:
                print("\n" + "=" * 80)
                print("✅ RESPONSE:")
                print("=" * 80)
                print(result)
                print("=" * 80)

            print()

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")



def test_runtime_with_iam():
    """Legacy test function - runs predefined scenarios."""

    print("="*80)
    print("PHASE 1 RUNTIME TESTING - IAM AUTHENTICATION")
    print("="*80)

    client, agent_arn = get_runtime_client()
    if not client:
        return 1

    print(f"\nTesting runtime: {agent_arn}")
    region = agent_arn.split(':')[3]
    print(f"Region: {region}")
    print(f"Using IAM authentication with current AWS credentials")

    # Define test scenarios
    test_scenarios = [
        {
            "name": "Task Review - Authorized Access",
            "description": "Review assigned tasks and capacity",
            "payload": {
                "prompt": "Summarize the workload distribution of my team",
                "tenant_id": "project-team",
                "customer_id": "sarah.manager"
            },
            "expected_result": "✅ Should return task assignments and capacity details"
        },
        {
            "name": "Sprint Planning Analysis",
            "description": "Analyze sprint capacity and workload",
            "payload": {
                "prompt": "Show sprint capacity vs assigned work analysis",
                "tenant_id": "project-team",
                "customer_id": "sarah.manager"
            },
            "expected_result": "✅ Should return sprint planning analysis"
        },
        {
            "name": "Team Member Access",
            "description": "Testing user access level control",
            "payload": {
                "prompt": "Show me team members and capacity",
                "tenant_id": "project-team",
                "customer_id": "sarah.manager"
            },
            "expected_result": "🔒 Should return authorized team member information"
        }
    ]

    # Run tests
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}/{len(test_scenarios)}: {scenario['name']}")
        print(f"Description: {scenario['description']}")
        print(f"Expected: {scenario['expected_result']}")
        print("-"*80)

        print(f"Tenant: {scenario['payload']['tenant_id']}")
        print(f"Customer: {scenario['payload']['customer_id']}")
        print(f"Query: {scenario['payload']['prompt']}")

        try:
            print("\nMaking IAM-authenticated request to AgentCore...")

            # Use boto3 client to invoke the runtime
            # Session ID must be at least 33 characters
            session_id = f"test-session-{i}-{int(time.time())}-{int(time.time() * 1000000)}"
            response = client.invoke_agent_runtime(
                agentRuntimeArn=agent_arn,
                qualifier='DEFAULT',
                runtimeSessionId=session_id,
                payload=json.dumps(scenario['payload'])
            )

            print(f"Response status: Success")

            # Read the streaming response body
            if 'response' in response:
                stream = response['response']
                response_text = stream.read().decode('utf-8')

                print(f"\n{'='*80}")
                print("AGENT RESPONSE:")
                print('='*80)
                print(response_text)
                print('='*80)

                # Also show metadata
                if 'runtimeSessionId' in response:
                    print(f"\nSession ID: {response['runtimeSessionId']}")
                if 'traceId' in response:
                    print(f"Trace ID: {response['traceId']}")
            else:
                print(f"\nFull response:\n{json.dumps(response, indent=2, default=str)}")

        except client.exceptions.ValidationException as e:
            print(f"\nValidation Error: {e}")
        except client.exceptions.AccessDeniedException as e:
            print(f"\nAccess Denied: {e}")
            print("Make sure your AWS credentials have permission to invoke bedrock-agentcore")
        except client.exceptions.ResourceNotFoundException as e:
            print(f"\nResource Not Found: {e}")
            print("Make sure the runtime ARN is correct and the runtime is deployed")
        except Exception as e:
            print(f"\nError: {type(e).__name__}: {e}")

    # Summary
    print("\n" + "="*80)
    print("PHASE 1 ARCHITECTURE SUMMARY")
    print("="*80)
    print("\n🔐 Authentication Pattern:")
    print("   - AgentCore Runtime: IAM authentication (SigV4)")
    print("   - Frontend: Cognito ID tokens → AWS credentials → IAM calls")
    print("   - Test Script: Direct IAM authentication")

    print("\n🏢 Multi-Tenancy Pattern:")
    print("   - Tenant Isolation: Application-level (payload-based)")
    print("   - Trust Boundary: Backend trusts tenant_id from request payload")
    print("   - Security Model: Frontend responsible for tenant extraction")

    print("\n💡 Phase 1 Simplicity:")
    print("   - No JWT validation at runtime level")
    print("   - No infrastructure-level tenant claims")
    print("   - Simplified payload-based tenant isolation")
    print("="*80)

    return 0


def show_usage():
    """Show usage examples."""
    print("\n💡 USAGE EXAMPLES")
    print("=" * 80)
    print("📝 Sample Questions to Try:")
    print("   • What are my underperforming products?")
    print("   • Show me my inventory status")
    print("   • Analyze product performance")
    print("   • Check inventory for low stock items")
    print()
    print("🏢 Available Tenants:")
    print("   • fashion-retailer (Fashion Forward Co.)")
    print("   • electronics-store (TechHub Electronics)")
    print()
    print("🔧 Phase 1 Architecture:")
    print("   • Authentication: IAM (SigV4)")
    print("   • Multi-tenancy: Payload-based tenant_id")
    print("   • Agent: Product analytics with tenant-scoped data")
    print()


def main():
    """Main function."""
    print("🎯 PHASE 1 AGENTCORE RUNTIME TESTER")
    print("=" * 80)
    print("Test your deployed AgentCore Runtime with IAM authentication.")
    print()

    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--help", "-h"]:
            # Show help
            print("Usage:")
            print("  python3 test_runtime.py              # Interactive mode (default)")
            print("  python3 test_runtime.py --auto       # Run automated tests")
            print("  python3 test_runtime.py <prompt>     # Single prompt mode")
            print()
            show_usage()
            return 0
        else:
            # Single prompt mode
            prompt = " ".join(sys.argv[1:])
            print(f"🚀 Single Prompt Mode")
            print("=" * 80)
            print(f"Prompt: {prompt}")
            print()

            result = invoke_runtime(prompt, show_details=True)
            if result:
                print("\n" + "=" * 80)
                print("✅ RESPONSE:")
                print("=" * 80)
                print(result)
                print("=" * 80)

                show_usage()
                return 0
            else:
                return 1
    else:
        # Interactive mode (default)
        interactive_mode()
        return 0


if __name__ == "__main__":
    sys.exit(main())
