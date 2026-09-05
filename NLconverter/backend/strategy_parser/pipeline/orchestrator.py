from typing import Dict, Any, Optional

from .blocker_detector import BlockerDetector
from .semantic_resolver import SemanticResolver
from .compiler import StrategyCompiler
from .schema_validator import SchemaValidator
from .ast_generator import ASTGenerator
from .ast_validator import ASTValidatorStep
from .auditor import Auditor


class PipelineOrchestrator:
    """
    Ties the compilation stages together according to the target architecture.
    """

    def __init__(
        self,
        blocker_detector: BlockerDetector,
        semantic_resolver: SemanticResolver,
        compiler: StrategyCompiler,
        schema_validator: SchemaValidator,
        ast_generator: ASTGenerator,
        ast_validator: ASTValidatorStep,
        auditor: Auditor,
    ):
        self.blocker_detector = blocker_detector
        self.semantic_resolver = semantic_resolver
        self.compiler = compiler
        self.schema_validator = schema_validator
        self.ast_generator = ast_generator
        self.ast_validator = ast_validator
        self.auditor = auditor

    def run(self, strategy_text: str, strategy_id: str, deterministic_schema: Optional[Dict[str, Any]] = None, headless: bool = False):
        """
        Executes the full pipeline.
        Includes interactive CLI prompts for the Clarification Loop and User Approval.
        Returns (ast_node, canonical_json, final_status)
        """
        print("\n--- STAGE 1: BLOCKER DETECTOR ---")
        current_strategy = strategy_text
        while True:
            blocker_result = self.blocker_detector.detect(current_strategy)
            if blocker_result.status == "CLEAR":
                print("Status: CLEAR")
                break
            
            print("Status: BLOCKED")
            print("The following issues must be resolved before compilation:")
            
            if headless:
                for b in blocker_result.blockers:
                    print(f"- Reason: {b.reason}")
                    print(f"  Question: {b.question}")
                raise RuntimeError("Strategy is blocked and requires clarification, but running in headless mode.")
                
            # Clarification Loop
            print("\nPlease provide additional information for each issue (or type 'abort' to cancel):")
            
            clarifications_made = False
            for i, b in enumerate(blocker_result.blockers, 1):
                print(f"\nIssue {i}/{len(blocker_result.blockers)}:")
                print(f"Reason: {b.reason}")
                print(f"Question: {b.question}")
                
                user_input = input("Answer > ")
                if user_input.strip().lower() == "abort":
                    raise RuntimeError("Pipeline aborted by user during Clarification Loop.")
                
                if user_input.strip():
                    # Link the answer explicitly to the question to prevent LLM hallucination loops
                    current_strategy += f"\n\nClarification regarding '{b.question}': {user_input.strip()}"
                    clarifications_made = True
            
            if not clarifications_made:
                print("\nNo clarifications provided. Aborting to prevent infinite loops.")
                raise RuntimeError("No clarifications provided by user.")
                
            print("\nRe-evaluating...")

        print("\n--- STAGE 2: SEMANTIC RESOLVER ---")
        resolver_result = self.semantic_resolver.resolve(current_strategy)
        approved_interpretations = []

        if resolver_result.approval_items:
            print("The Semantic Resolver identified ambiguous terms that require your approval.")
            for item in resolver_result.approval_items:
                print(f"\nTerm: '{item.source}'")
                print("Candidates:")
                for i, cand in enumerate(item.candidates):
                    if i == 0:
                        print(f"  {i+1}. {cand} [Default]")
                    else:
                        print(f"  {i+1}. {cand}")
                
                if headless:
                    print("  [Auto-selecting Default in Headless Mode]")
                    user_input = ""
                else:
                    print("Enter the number of the correct interpretation, type your own, or press Enter to use the [Default]:")
                    user_input = input("> ").strip()
                
                if not user_input:
                    resolution = item.candidates[0]
                elif user_input.isdigit() and 1 <= int(user_input) <= len(item.candidates):
                    resolution = item.candidates[int(user_input)-1]
                else:
                    resolution = user_input
                
                approved_interpretations.append({
                    "source": item.source,
                    "resolution": resolution
                })
        else:
            print("No ambiguous terms detected.")

        print("\n--- STAGE 3: COMPILER ---")
        canonical_json = self.compiler.compile(current_strategy, approved_interpretations)
        print("Canonical JSON generated.")

        print("\n--- STAGE 4: SCHEMA VALIDATION ---")
        is_valid, schema_errors = self.schema_validator.validate(canonical_json)
        if not is_valid:
            print("Schema Validation FAILED:")
            for err in schema_errors:
                print(f"- {err}")
            raise RuntimeError("Schema validation failed.")
        print("Schema Validation PASS")

        print("\n--- STAGE 5: AST GENERATION ---")
        ast = self.ast_generator.generate(canonical_json, strategy_id, deterministic_schema)
        print("AST Generated.")

        print("\n--- STAGE 6: AST VALIDATION ---")
        is_ast_valid, ast_errors = self.ast_validator.validate(ast)
        if not is_ast_valid:
            print("AST Validation FAILED:")
            for err in ast_errors:
                print(f"- {err}")
            raise RuntimeError("AST validation failed.")
        print("AST Validation PASS")

        print("\n--- STAGE 7: AUDITOR ---")
        audit_result = self.auditor.audit(ast)
        if audit_result.status == "FAIL":
            print("Auditor FAILED:")
            for msg in audit_result.messages:
                print(f"- {msg}")
            raise RuntimeError("Auditor failed.")
        print("Auditor PASS")

        return ast, canonical_json, "SUCCESS"
