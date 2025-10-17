#!/usr/bin/env python3
"""
Setup Cognito user pool for  agentic AI authentication.

Creates a simple authentication system with:
- ID tokens containing  for frontend use
"""

import boto3
import json
from pathlib import Path
from boto3.session import Session


def setup_cognito_user_pool():
    """
    Create Cognito resources for  agentic AI authentication.

    Creates:
    - User Pool
    - App Client for secure authentication
    - Identity Pool for AWS credentials
    - IAM role for AgentCore runtime access
    """
    boto_session = Session()
    region = boto_session.region_name or 'us-west-2'
    account_id = boto3.client('sts').get_caller_identity()['Account']

    # Initialize AWS clients
    cognito_client = boto3.client('cognito-idp', region_name=region)
    cognito_identity_client = boto3.client('cognito-identity', region_name=region)
    iam_client = boto3.client('iam')

    try:
        # Create User Pool with custom attributes (no Lambda needed for Phase 1)
        user_pool_response = cognito_client.create_user_pool(
            PoolName='Phase1AgenticSaaSPool',
            Policies={
                'PasswordPolicy': {
                    'MinimumLength': 8,
                    'RequireUppercase': True,
                    'RequireLowercase': True,
                    'RequireNumbers': True,
                    'RequireSymbols': True
                }
            },
            Schema=[
                # Standard attributes
                {
                    'Name': 'email',
                    'AttributeDataType': 'String',
                    'Required': True,
                    'Mutable': True
                },
                {
                    'Name': 'tier',
                    'AttributeDataType': 'String',
                    'DeveloperOnlyAttribute': False,
                    'Mutable': True,
                    'Required': False,
                    'StringAttributeConstraints': {
                        'MinLength': '1',
                        'MaxLength': '50'
                    }
                },
                {
                    'Name': 'role',
                    'AttributeDataType': 'String',
                    'DeveloperOnlyAttribute': False,
                    'Mutable': True,
                    'Required': False,
                    'StringAttributeConstraints': {
                        'MinLength': '1',
                        'MaxLength': '50'
                    }
                },
                {
                    'Name': 'display_name',
                    'AttributeDataType': 'String',
                    'DeveloperOnlyAttribute': False,
                    'Mutable': True,
                    'Required': False,
                    'StringAttributeConstraints': {
                        'MinLength': '1',
                        'MaxLength': '100'
                    }
                }
            ]
        )
        pool_id = user_pool_response['UserPool']['Id']
        print(f"✅ Created User Pool: {pool_id}")

        # Create App Client (no Lambda triggers for Phase 1)
        app_client_response = cognito_client.create_user_pool_client(
            UserPoolId=pool_id,
            ClientName='Phase1AgenticSaaSClient',
            GenerateSecret=False,
            ExplicitAuthFlows=[
                'ALLOW_USER_PASSWORD_AUTH',
                'ALLOW_REFRESH_TOKEN_AUTH',
                'ALLOW_USER_SRP_AUTH'
            ],
            # Configure which attributes appear in ID tokens
            ReadAttributes=[
                'email',
                'custom:tier',
                'custom:role',
                'custom:display_name'
            ],
            # Set token validity
            TokenValidityUnits={
                'AccessToken': 'hours',
                'IdToken': 'hours',
                'RefreshToken': 'days'
            },
            AccessTokenValidity=2,
            IdTokenValidity=2,
            RefreshTokenValidity=30
        )
        client_id = app_client_response['UserPoolClient']['ClientId']
        print(f"✅ Created App Client: {client_id}")

        # Create Identity Pool for AWS credentials
        print(f"⏳ Creating Cognito Identity Pool...")

        # Check if identity pool already exists and delete it to ensure clean state
        try:
            existing_pools = cognito_identity_client.list_identity_pools(MaxResults=60)
            for pool in existing_pools.get('IdentityPools', []):
                if pool['IdentityPoolName'] == 'Phase1AgenticSaaSIdentityPool':
                    print(f"   Deleting existing Identity Pool: {pool['IdentityPoolId']}")
                    cognito_identity_client.delete_identity_pool(IdentityPoolId=pool['IdentityPoolId'])
        except Exception as e:
            print(f"   Note: Could not check for existing pools: {e}")

        identity_pool_response = cognito_identity_client.create_identity_pool(
            IdentityPoolName='Phase1AgenticSaaSIdentityPool',
            AllowUnauthenticatedIdentities=False,
            CognitoIdentityProviders=[
                {
                    'ProviderName': f'cognito-idp.{region}.amazonaws.com/{pool_id}',
                    'ClientId': client_id,
                    'ServerSideTokenCheck': False
                }
            ]
        )
        identity_pool_id = identity_pool_response['IdentityPoolId']
        print(f"✅ Created Identity Pool: {identity_pool_id}")

        # Create IAM role for authenticated users
        print(f"⏳ Creating IAM role for AgentCore access...")

        # Trust policy for Cognito Identity Pool
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": "cognito-identity.amazonaws.com"
                    },
                    "Action": "sts:AssumeRoleWithWebIdentity",
                    "Condition": {
                        "StringEquals": {
                            "cognito-identity.amazonaws.com:aud": identity_pool_id
                        },
                        "ForAnyValue:StringLike": {
                            "cognito-identity.amazonaws.com:amr": "authenticated"
                        }
                    }
                }
            ]
        }

        role_name = 'Phase1AgenticSaaSAuthenticatedRole'

        # Delete existing role if it exists (to ensure clean state with new Identity Pool)
        try:
            # First detach all policies
            attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
            for policy in attached_policies.get('AttachedPolicies', []):
                iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policy['PolicyArn'])
                print(f"   Detached policy: {policy['PolicyName']}")

            # Delete the role
            iam_client.delete_role(RoleName=role_name)
            print(f"   Deleted existing IAM role to recreate with new Identity Pool")
        except iam_client.exceptions.NoSuchEntityException:
            pass  # Role doesn't exist, that's fine
        except Exception as e:
            print(f"   Note: Could not delete existing role: {e}")

        # Create the role with correct trust policy
        try:
            iam_role_response = iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Role for authenticated users to access AgentCore runtime'
            )
            role_arn = iam_role_response['Role']['Arn']
            print(f"✅ Created IAM role: {role_arn}")
        except Exception as e:
            # If creation fails, use the existing role ARN
            role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
            print(f"⚠️  Could not create role, using existing: {role_arn}")
            print(f"   Error: {e}")

        # Attach policy for AgentCore runtime access
        # Note: We'll use a wildcard for now since runtime ARN isn't created yet
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "bedrock-agentcore:InvokeAgentRuntime"
                    ],
                    "Resource": f"arn:aws:bedrock-agentcore:{region}:{account_id}:runtime/*"
                }
            ]
        }

        policy_name = 'Phase1AgentCoreRuntimeAccess'
        try:
            policy_response = iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document),
                Description='Allow access to AgentCore runtime'
            )
            policy_arn = policy_response['Policy']['Arn']
            print(f"✅ Created IAM policy: {policy_arn}")
        except iam_client.exceptions.EntityAlreadyExistsException:
            policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
            print(f"✅ Using existing IAM policy: {policy_arn}")

        # Attach policy to role
        try:
            iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn=policy_arn
            )
            print(f"✅ Attached policy to role")
        except Exception as e:
            print(f"⚠️  Policy already attached or error: {e}")

        # Set Identity Pool roles
        cognito_identity_client.set_identity_pool_roles(
            IdentityPoolId=identity_pool_id,
            Roles={
                'authenticated': role_arn
            }
        )
        print(f"✅ Configured Identity Pool with IAM role")

        print(f"⏳ Creating test users for Phase 1 authentication...")

        # Create test users (same as Phase 2 for consistency)
        test_users = [
            # Fashion Retailer Users
            {
                'username': 'sarah.manager',
                'email': 'sarah@fashion-retailer.com',
                'tier': 'basic',
                'role': 'Scrum Master',
                'display_name': 'Sarah Wilson'
            },


            # Electronics Store Users
            {
                'username': 'mike.admin',
                'email': 'mike@electronics-store.com',
                'tier': 'basic',
                'role': 'Developer',
                'display_name': 'Mike Rodriguez'
            },
            {
                'username': 'david.chen',
                'email': 'david@customer.electronics-store.com',
                'tier': 'basic',
                'role': 'Developer',
                'display_name': 'David Chen'
            }
        ]

        # Dictionary to store ID tokens (Phase 1 only needs ID tokens)
        id_tokens = {}

        for user in test_users:
            print(f"  📝 Creating user: {user['username']} ")

            # Create user with email verification bypass
            cognito_client.admin_create_user(
                UserPoolId=pool_id,
                Username=user['username'],
                UserAttributes=[
                    {'Name': 'email', 'Value': user['email']},
                    {'Name': 'email_verified', 'Value': 'true'},
                    {'Name': 'custom:tier', 'Value': user['tier']},
                    {'Name': 'custom:role', 'Value': user['role']},
                    {'Name': 'custom:display_name', 'Value': user['display_name']}
                ],
                TemporaryPassword='TempPass123!',
                MessageAction='SUPPRESS'
            )

            # Set permanent password
            cognito_client.admin_set_user_password(
                UserPoolId=pool_id,
                Username=user['username'],
                Password='MyPassword123!',
                Permanent=True
            )

            # Authenticate and get ID token
            auth_response = cognito_client.initiate_auth(
                ClientId=client_id,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={
                    'USERNAME': user['username'],
                    'PASSWORD': 'MyPassword123!'
                }
            )

            # Store ID token for frontend authentication
            id_tokens[user['username']] = {
                'id_token': auth_response['AuthenticationResult']['IdToken'],
                'role': user['role'],
                'display_name': user['display_name']
            }

            print(f"  ✅ Created and authenticated successfully")

        # Discovery URL for OAuth configuration
        discovery_url = f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/openid-configuration"

        # Output configuration
        config = {
            'pool_id': pool_id,
            'client_id': client_id,
            'identity_pool_id': identity_pool_id,
            'discovery_url': discovery_url,
            'region': region,
            'role_arn': role_arn,
            'id_tokens': id_tokens
        }

        print("\n" + "="*60)
        print("COGNITO CONFIGURATION COMPLETE")
        print("="*60)
        print(f"User Pool ID: {pool_id}")
        print(f"Client ID: {client_id}")
        print(f"Identity Pool ID: {identity_pool_id}")
        print(f"IAM Role ARN: {role_arn}")
        print(f"Discovery URL: {discovery_url}")
        print(f"\n🎫 Generated ID Tokens for Frontend Authentication:")
        print(f"   Password for all test users: MyPassword123!")
        for username, token_info in id_tokens.items():
            print(f"  ├── {username} ({token_info['display_name']}):")
            print(f"  │   ├── Role: {token_info['role']}")
            print(f"  │   └── ID Token: {token_info['id_token'][:50]}...")

        print("\n" + "="*60)
        print("SETUP COMPLETE")
        print("="*60)

        # Save configuration using env_utils
        from env_utils import update_env_section

        # Use absolute path to ensure we write to the correct location
        env_path = Path(__file__).parent.parent / ".env"
        print(f"\n💾 Saving configuration to: {env_path.absolute()}")
        auth_content = [
            "# Cognito Configuration",
            f"export COGNITO_USER_POOL_ID={pool_id}",
            f"export COGNITO_CLIENT_ID={client_id}",
            f"export COGNITO_IDENTITY_POOL_ID={identity_pool_id}",
            f"export COGNITO_DISCOVERY_URL={discovery_url}",
            f"export COGNITO_REGION={region}",
            f"export COGNITO_IAM_ROLE_ARN={role_arn}",
            "",
            "# Test users (development only)",
            "export TEST_USER_PASSWORD=MyPassword123!",
            "",
            "# ID tokens for frontend authentication"
        ]

        # Add ID tokens for each user
        for username, token_info in id_tokens.items():
            id_env_key = f"TEST_ID_TOKEN_{username.upper().replace('.', '_')}"
            auth_content.append(f"export {id_env_key}={token_info['id_token']}")

        auth_content.extend([
            "",
            "# Authentication configuration",
            "export AUTH_TYPE=id_token_based",
            "export TENANT_ISOLATION=application_level"
        ])

        update_env_section(env_path, "AUTHENTICATION", auth_content)
        print(f"✅ Configuration saved to {env_path}")

        # Verify the configuration was saved correctly
        print(f"\n🔍 Verifying saved configuration...")
        if env_path.exists():
            print(f"   File exists at: {env_path.absolute()}")
            with open(env_path, 'r') as f:
                content = f.read()
                if pool_id in content and identity_pool_id in content:
                    print(f"✅ Verified: User Pool ID and Identity Pool ID saved correctly")
                    print(f"   User Pool ID: {pool_id}")
                    print(f"   Identity Pool ID: {identity_pool_id}")
                else:
                    print(f"⚠️  WARNING: Configuration NOT saved correctly!")
                    print(f"   Expected User Pool: {pool_id}")
                    print(f"   Expected Identity Pool: {identity_pool_id}")
                    print(f"\n   Actual content of COGNITO_IDENTITY_POOL_ID line:")
                    for line in content.split('\n'):
                        if 'COGNITO_IDENTITY_POOL_ID' in line:
                            print(f"   {line}")
        else:
            print(f"⚠️  ERROR: .env file not found at {env_path.absolute()}")

        return config

    except Exception as e:
        print(f"\n❌ Error setting up Cognito: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Setup Phase 1 Cognito authentication."""
    print("="*60)
    print("PHASE 1 COGNITO SETUP")
    print("="*60)

    config = setup_cognito_user_pool()

    if config:
        print("\n" + "="*60)
        print("NEXT STEPS")
        print("="*60)
        print("1. Load the configuration into your shell:")
        print("   cd /workshop/phase1-mvp")
        print("   source .env")
        print("")
        print("2. Deploy the AgentCore runtime:")
        print("   python3 deployment/02_deploy_runtime.py")
        print("")
        print("⚠️  IMPORTANT: Always run 'source .env' after this script")
        print("   to load the new configuration into your shell!")
    else:
        print("\n❌ Setup failed")
        return False

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
