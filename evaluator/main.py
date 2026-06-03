import os
import sys
import argparse
import json
from evaluator.evaluator_logging import logger
from evaluator.configuration import Configuration
from evaluator.session_manager import SessionManager
from evaluator.state_machine import StateMachine, State
from evaluator.client import ChallengeClient
from evaluator.challenge_parser import ChallengeParser
from evaluator.validator_registry import ValidatorRegistry
from evaluator.result_aggregator import ResultAggregator
from evaluator.proof_generator import ProofGenerator
from evaluator.upload_client import UploadClient

# Make sure all validators are imported and registered
import evaluator.validators

def run_evaluation_flow(config: Configuration) -> int:
    """Executes the standard end-to-end local grading evaluation flow."""
    logger.info("==========================================================")
    logger.info("    Starting Artifact Validation Evaluator V2 (Local)    ")
    logger.info("==========================================================")

    # 1. Environment Prep
    session_mgr = SessionManager(config)
    session_mgr.prepare_environment()
    
    # 2. State Machine Init
    state_machine = StateMachine(config.state_file)
    
    try:
        # 3. Retrieve Challenge Package
        state_machine.transition_to(State.CHALLENGE_ISSUED, "Retrieving challenge configuration from backend API.")
        client = ChallengeClient(config)
        raw_challenge = client.fetch_challenge()
        
        challenge = ChallengeParser.parse(raw_challenge)
        logger.info(f"Loaded assignment: {challenge.title} ({challenge.slug}). Max Score: {challenge.max_score}")

        # 4. Evaluation Engine Running
        state_machine.transition_to(State.RUNNING, "Starting local validation execution.")
        aggregator = ResultAggregator()
        
        # Determine total rule scores and pass weight
        total_rules = len(challenge.rules)
        logger.info(f"Found {total_rules} validation rules to execute.")
        
        for index, rule in enumerate(challenge.rules, 1):
            logger.info(f"[{index}/{total_rules}] Processing rule '{rule.rule_id}' (Type: '{rule.type}')")
            
            validator_class = ValidatorRegistry.get_validator(rule.type)
            if not validator_class:
                logger.warning(f"No registered validator plugin found for type: '{rule.type}'. Rule marked as failed.")
                aggregator.add_result(
                    rule_id=rule.rule_id,
                    passed=False,
                    stdout=json.dumps({"status": "unsupported_rule_type", "passed": False, "reason": "No registered validator plugin found."}),
                    stderr="PluginMissing",
                    exit_code=-1,
                    score=0.0
                )
                continue
                
            # Instantiate and run validator plugin
            validator = validator_class()
            try:
                passed, stdout, stderr, exit_code = validator.validate(rule)
                
                # Deduce points scored
                points = rule.points if passed else 0.0
                aggregator.add_result(rule.rule_id, passed, stdout, stderr, exit_code, points)
                
                # Check for files and compute artifact hashes
                if rule.target:
                    # Target path relative to workspace or absolute
                    filepath = rule.target
                    if not os.path.isabs(filepath):
                        filepath = os.path.join(config.workspace_dir, filepath)
                    filename = os.path.basename(rule.target)
                    aggregator.record_artifact(filename, filepath)
                    
            except Exception as e:
                logger.error(f"Execution error on rule '{rule.rule_id}': {e}")
                aggregator.add_result(
                    rule_id=rule.rule_id,
                    passed=False,
                    stdout=json.dumps({"status": "runtime_error", "passed": False, "reason": str(e)}),
                    stderr=str(e),
                    exit_code=-1,
                    score=0.0
                )

        # 5. Proof Generation
        proof_gen = ProofGenerator(config)
        proof = proof_gen.generate_proof(challenge, aggregator)
        
        # Save signed proof locally
        proof_path = os.path.join(config.workspace_dir, "proof.json")
        with open(proof_path, "w") as f:
            json.dump(proof, f, indent=2)
        logger.info(f"Local signed proof written to: {proof_path}")
        
        state_machine.transition_to(State.PROOF_GENERATED, "Proof package successfully compiled and signed.")

        # 6. Upload Proof Package
        state_machine.transition_to(State.PROOF_SUBMITTED, "Uploading signed proof to grading platform.")
        uploader = UploadClient(config)
        upload_resp = uploader.upload_proof(proof)
        
        # 7. Verification Complete
        state_machine.transition_to(State.VERIFIED, f"Session verified. Score obtained: {upload_resp.get('final_score')}")
        
        # Clear temporary state
        session_mgr.clean_session()
        
        logger.info("==========================================================")
        logger.info("    Evaluation workflow completed successfully!    ")
        logger.info(f"    Final Score: {upload_resp.get('final_score')} / {challenge.max_score}")
        logger.info("==========================================================")
        return 0

    except KeyboardInterrupt:
        logger.warning("\nUser interrupted the evaluation. Aborting session...")
        try:
            client = ChallengeClient(config)
            client.abort_session()
        except Exception as abort_err:
            logger.warning(f"Could not notify backend of abortion: {abort_err}")
        state_machine.transition_to(State.ABORTED, "Aborted by user via keyboard interrupt.")
        session_mgr.clean_session()
        return 1
    except Exception as e:
        logger.error(f"Evaluator execution failed: {e}")
        state_machine.transition_to(State.FAILED, f"Execution failed: {str(e)}")
        return 1

def run_interactive_menu(config: Configuration) -> None:
    """Prompts the student to log in, lists assignments, and initializes a session interactively."""
    import getpass
    import httpx
    
    logger.info("==========================================================")
    logger.info("             EE-YANTRA SECURE GRADING PLATFORM            ")
    logger.info("==========================================================")
    logger.info("No session ID or token provided. Entering Interactive Mode.")
    
    # 1. Student Login
    roll = input("Enter Student Roll Number (e.g. 22BEC001): ").strip().upper()
    password = getpass.getpass("Enter Student Password: ")
    
    # Call student login endpoint
    login_url = f"{config.backend_url}/api/v1/auth/student/login"
    logger.info("Authenticating credentials...")
    try:
        resp = httpx.post(login_url, json={"roll_number": roll, "password": password}, timeout=15)
        if resp.status_code != 200:
            logger.error(f"Authentication failed (Status code: {resp.status_code}): {resp.json().get('detail', 'Unknown error')}")
            sys.exit(1)
            
        auth_data = resp.json()
        token = auth_data["access_token"]
        logger.info("Authentication successful!")
        config.student_token = token
        config.roll_number = roll
    except Exception as e:
        logger.error(f"Network error during login: {e}")
        sys.exit(1)
        
    # 2. Fetch published assignments
    headers = {"Authorization": f"Bearer {token}"}
    assignments_url = f"{config.backend_url}/api/v1/assignments/"
    logger.info("Fetching available published assignments...")
    try:
        resp = httpx.get(assignments_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            logger.error(f"Failed to fetch assignments: {resp.text}")
            sys.exit(1)
            
        assignments = resp.json()
        if not assignments:
            logger.warning("No published assignments are currently available.")
            sys.exit(0)
            
        logger.info("\nAvailable Assignments:")
        for idx, assign in enumerate(assignments, 1):
            print(f"  [{idx}] {assign['title']} (Slug: {assign['slug']}) - Max Score: {assign['max_score']}")
            
        # 3. Choose assignment
        choice = -1
        while choice < 1 or choice > len(assignments):
            try:
                choice_str = input(f"\nSelect assignment number [1-{len(assignments)}]: ").strip()
                choice = int(choice_str)
            except ValueError:
                print("Invalid integer. Please select a valid number.")
                
        selected_assignment = assignments[choice - 1]
        assignment_id = selected_assignment["id"]
        logger.info(f"Selected assignment: '{selected_assignment['title']}'")
        
        # 4. Open grading session on backend
        sessions_url = f"{config.backend_url}/api/v1/sessions/"
        logger.info("Opening a new grading session on the server...")
        resp = httpx.post(sessions_url, json={"assignment_id": assignment_id}, headers=headers, timeout=15)
        
        if resp.status_code == 409:
            # Student already has an active session. Let's retrieve it instead of blocking them!
            logger.info("An active session already exists for this assignment. Fetching active session details...")
            my_sessions_url = f"{config.backend_url}/api/v1/sessions/"
            active_resp = httpx.get(my_sessions_url, headers=headers, timeout=15)
            active_sessions = active_resp.json()
            # Find the active session for this assignment
            session_id = None
            for s in active_sessions:
                if str(s["assignment_id"]) == str(assignment_id) and s["status"] in ("CREATED", "CHALLENGE_ISSUED", "RUNNING", "PROOF_GENERATED", "STARTED", "IN_PROGRESS"):
                    session_id = s["session_id"]
                    break
            if not session_id:
                logger.error("Could not retrieve active session.")
                sys.exit(1)
        elif resp.status_code not in (200, 201):
            logger.error(f"Failed to open session: {resp.text}")
            sys.exit(1)
        else:
            session_id = resp.json()["session_id"]
            
        logger.info(f"Session started! Session ID: {session_id}")
        config.session_id = session_id
        
    except Exception as e:
        logger.error(f"Network error during assignment / session setup: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Artifact Validation Evaluator V2 Command Line Interface")
    parser.add_argument("--session-id", help="Session ID generated when assignment is opened")
    parser.add_argument("--token", help="Student's JWT token for authorization")
    parser.add_argument("--backend-url", default="http://localhost:8000", help="URL of the grading server")
    parser.add_argument("--roll", default="22BEC001", help="Student's roll number")
    
    args = parser.parse_args()
    
    # Load configuration
    config = Configuration()
    
    # Override defaults with CLI args if specified
    if args.session_id:
        os.environ["EEYAN_SESSION_ID"] = args.session_id
        config.session_id = args.session_id
    if args.token:
        os.environ["EEYAN_STUDENT_TOKEN"] = args.token
        config.student_token = args.token
    if args.backend_url:
        os.environ["EEYAN_BACKEND_URL"] = args.backend_url
        config.backend_url = args.backend_url
    if args.roll:
        os.environ["EEYAN_ROLL_NUMBER"] = args.roll
        config.roll_number = args.roll
        
    # Check if we should enter interactive menu mode
    if not config.session_id or not config.student_token:
        try:
            run_interactive_menu(config)
        except KeyboardInterrupt:
            logger.warning("\nMenu selection aborted by user. Exiting.")
            sys.exit(1)
        
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        parser.print_help()
        sys.exit(1)
        
    try:
        sys.exit(run_evaluation_flow(config))
    except KeyboardInterrupt:
        logger.warning("\nEvaluation interrupted by user. Exiting.")
        sys.exit(1)

if __name__ == "__main__":
    main()
