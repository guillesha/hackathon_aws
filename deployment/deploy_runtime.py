#!/usr/bin/env python3
"""
Deploy Phase 1 AgentCore Runtime

This script demonstrates how to deploy an AI Agent to AgentCore and uses IAM-based authentication (no JWT validation needed).
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Deploy Phase 1 AgentCore Runtime"""

    print("="*60)
    print("AGENTCORE DEPLOYMENT - PHASE 1")
    print("="*60)

    # Check if we're in the right directory
    if not Path("app.py").exists():
        print("❌ app.py not found")
        print("💡 Please run from the root directory:")
        print("   cd /workshop/phase1-mvp")
        print("   python3 deployment/02_deploy_runtime.py")
        sys.exit(1)

    # Step 1: Check AgentCore CLI
    print("📋 Step 1: Verify AgentCore CLI")
    try:
        result = subprocess.run(["agentcore", "--version"], capture_output=True, text=True)
        print(f"   ✅ AgentCore CLI ready: {result.stdout.strip()}")
    except:
        print("   ❌ Install AgentCore: pip install bedrock-agentcore-starter-toolkit")
        sys.exit(1)

    # Step 2: Configure the runtime
    print("\n🔧 Step 2: Configure AgentCore Runtime")
    print("   💻 Running: agentcore configure --entrypoint app.py --requirements-file requirements.txt --disable-memory")
    print("   📝 Configuration:")
    print("      • Entrypoint: app.py (at project root)")
    print("      • Requirements: requirements.txt")
    print("      • Supporting modules: agents/, data/, utils/")
    print("      • Memory: Disabled (Phase 1 simplicity)")
    print("   🔐 Using IAM authentication (default - no OAuth config)")
    print("\n   You will be prompted for:")
    print("      • Agent name (choose a unique name)")
    print("      • Execution role (press Enter to auto-create)")
    print("      • ECR repository (press Enter to auto-create)")

    configure_result = subprocess.run([
        "agentcore", "configure",
        "--entrypoint", "app.py",
        "--requirements-file", "requirements.txt",
        "--disable-memory"
    ], text=True)

    if configure_result.returncode != 0:
        print(f"   ❌ Configuration failed")
        sys.exit(1)
    print("   ✅ Runtime configured")

    # Step 3: Launch runtime
    print("\n🚀 Step 3: Launch Runtime")
    print("   💻 Running: agentcore launch --auto-update-on-conflict")
    print("   ⏳ This may take a few minutes...")

    launch_result = subprocess.run([
        "agentcore", "launch",
        "--auto-update-on-conflict"
    ], text=True)  # Show output directly

    if launch_result.returncode != 0:
        print("   ❌ Launch failed")
        sys.exit(1)

    # Get runtime status
    print("\n📊 Getting Runtime Status...")
    status_result = subprocess.run([
        "agentcore", "status"
    ], capture_output=True, text=True)

    # Extract runtime ARN from status
    runtime_arn = None
    for line in status_result.stdout.split('\n'):
        if "arn:aws:bedrock-agentcore:" in line:
            # Extract just the ARN part, removing any formatting characters
            import re
            arn_match = re.search(r'(arn:aws:bedrock-agentcore:[^│\s]+)', line)
            if arn_match:
                runtime_arn = arn_match.group(1)
                break

    print("\n" + "="*60)
    print("DEPLOYMENT COMPLETE")
    print("="*60)
    if runtime_arn:
        print(f"Runtime ARN: {runtime_arn}")

        # Save to environment
        from env_utils import update_env_section
        env_path = Path(".env")  # Save to current directory
        runtime_content = [
            "# Phase 1 AgentCore Runtime",
            f"export AGENTCORE_RUNTIME_ARN_SIMPLE={runtime_arn}",
            "export AGENTCORE_AUTH_TYPE=iam"
        ]
        update_env_section(env_path, "PHASE1_RUNTIME", runtime_content)
        print(f"✅ Configuration saved to {env_path}")

    print("\nWhat was created:")
    print("   • AgentCore managed runtime")
    print("   • HTTPS API endpoint")

    print("\nNext Steps:")
    print("   1. Test runtime: python3 test_runtime.py")

if __name__ == "__main__":
    main()
