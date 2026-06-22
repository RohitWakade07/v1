import json
import os
import sys

def grade():
    breakdown = {
        "package_structure": 0,
        "process_corpus": 0
    }
    feedback_messages = []

    # 1. Package Structure
    if os.path.isdir("metadata_organizer") and os.path.exists(os.path.join("metadata_organizer", "__init__.py")):
        breakdown["package_structure"] = 40
        feedback_messages.append("Package Structure (40/40): Valid metadata_organizer Python package found.")
    else:
        feedback_messages.append("Package Structure (0/40): metadata_organizer directory or __init__.py missing.")
        print(json.dumps({"breakdown": breakdown, "feedback": feedback_messages}))
        return

    # 2. Process Corpus Execution
    try:
        from metadata_organizer import process_corpus
        
        # Assume process_corpus takes a directory and returns a dict with 'document_count'
        result = process_corpus("test_corpus")
        
        if isinstance(result, dict) and "document_count" in result:
            if result["document_count"] == 1:
                breakdown["process_corpus"] = 60
                feedback_messages.append("Process Corpus (60/60): Correctly processed test_corpus.")
            else:
                breakdown["process_corpus"] = 30
                feedback_messages.append(f"Process Corpus (30/60): Processed but incorrect document_count. Expected 1, got {result.get('document_count')}.")
        else:
            feedback_messages.append("Process Corpus (0/60): process_corpus did not return a dictionary with 'document_count'.")
            
    except ImportError as e:
        feedback_messages.append(f"Process Corpus (0/60): Failed to import process_corpus from metadata_organizer: {e}")
    except Exception as e:
        feedback_messages.append(f"Process Corpus (0/60): Execution failed with error: {e}")

    print(json.dumps({"breakdown": breakdown, "feedback": feedback_messages}))

if __name__ == "__main__":
    grade()
