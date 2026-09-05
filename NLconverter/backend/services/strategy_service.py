import json
import time
import uuid
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import HTTPException
from sqlalchemy.orm import Session
import jsonschema

from backend.api.schemas import StrategyRequest, SCHEMA_CONFIG
from backend.db.models import StrategyRecord
from backend.strategy_parser.utils import load_dotenv
from backend.strategy_parser.parser.llm_client import LLMClient
from backend.strategy_parser.parser.strategy_parser import StrategyParser
from backend.strategy_parser.parser.validator import StrategyValidator
from backend.strategy_parser.ast import ASTBuilder, ASTSerializer
from backend.strategy_parser.pipeline import (
    SemanticResolver,
    StrategyCompiler,
    SchemaValidator,
    ASTGenerator,
    ASTValidatorStep,
    Auditor,
)

logger = logging.getLogger("nlconverter")

class StrategyRecordRepository:
    """Handles all database interactions for Strategy Records."""
    def __init__(self, db: Session, user_id: Optional[str] = None):
        self.db = db
        self.user_id = user_id

    def save(self, prompt: str, status: str, logs: str, **kwargs) -> StrategyRecord:
        record = StrategyRecord(
            prompt=prompt, 
            status=status, 
            logs=logs, 
            user_id=self.user_id, 
            **kwargs
        )
        self.db.add(record)
        self.db.commit()
        return record


class ExecutionSchemaValidator:
    """Handles schema file loading and validation."""
    @staticmethod
    def validate(payload: StrategyRequest, config: dict) -> Optional[Dict[str, Any]]:
        if not payload.execution_context:
            return None

        try:
            with open(config["execution_context"], "r", encoding="utf-8") as f:
                exec_schema = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load execution schema: {e}")
            raise HTTPException(status_code=500, detail="Internal configuration error.")

        try:
            jsonschema.validate(instance={"execution_context": payload.execution_context}, schema=exec_schema)
        except jsonschema.exceptions.ValidationError as e:
            logger.error(f"Execution context validation failed for payload {payload.execution_context}. Error: {e.message}")
            raise HTTPException(status_code=422, detail=f"Execution context validation failed: {e.message}")
            
        return {"execution_context": payload.execution_context}


class StrategyGenerationService:
    """Orchestrates the strategy compilation pipeline."""
    
    def __init__(self, repository: StrategyRecordRepository, llm_client: Optional[LLMClient] = None):
        self.repository = repository
        self.llm_client = llm_client or LLMClient()
        self.stage_logs: list[str] = []
        self.stage_timings: dict[str, float] = {}
        self.request_id = str(uuid.uuid4())[:8]

    def _save_record(self, prompt: str, status: str, **kwargs) -> StrategyRecord:
        log_text = "\n".join(self.stage_logs)
        return self.repository.save(prompt, status, log_text, **kwargs)

    def _run_stage(self, stage_name: str, func, *args, **kwargs):
        t0 = time.time()
        logger.info(f"[{self.request_id}] {stage_name} — starting")
        try:
            result = func(*args, **kwargs)
            elapsed = round(time.time() - t0, 3)
            self.stage_timings[stage_name] = elapsed
            logger.info(f"[{self.request_id}] {stage_name} — completed ({elapsed}s)")
            self.stage_logs.append(f"[{self.request_id}] {stage_name} — completed ({elapsed}s)")
            return result
        except Exception as e:
            elapsed = round(time.time() - t0, 3)
            logger.warning(f"[{self.request_id}] {stage_name} error: {e}")
            self.stage_logs.append(f"[{self.request_id}] {stage_name} — error ({elapsed}s): {e}")
            raise

    def process_strategy(self, payload: StrategyRequest) -> dict:
        backend_dir = Path(__file__).parent.parent
        load_dotenv(str(backend_dir / ".env"))

        config = SCHEMA_CONFIG[payload.market_type]
        deterministic_schema = ExecutionSchemaValidator.validate(payload, config)
        strategy_schema_path = config["strategy"]

        context_str = f"Execution Context:\n{json.dumps(payload.execution_context, indent=2)}\n\n" if payload.execution_context else ""
        prompt_to_analyze = f"{context_str}User Strategy: {payload.prompt}"

        try:
            # Stage 2: Semantic Resolver
            approved_interpretations = []
            if payload.semantic_resolutions is not None:
                from backend.strategy_parser.rag.retriever import HybridRetriever
                retriever = HybridRetriever()
                
                with retriever:
                    for r in payload.semantic_resolutions:
                        results, _ = retriever.retrieve(r.resolution, top_n=1)
                        full_context = r.resolution
                        if results and results[0].get("canonical_name") == r.resolution:
                            full_context = results[0].get("embedding_text", r.resolution)
                            
                        approved_interpretations.append({
                            "source": r.source, 
                            "resolution": full_context
                        })
                self.stage_logs.append(f"[{self.request_id}] Stage 2: Semantic Resolver — {len(approved_interpretations)} resolution(s) provided by user")
            else:
                semantic_resolver = SemanticResolver(self.llm_client)
                resolver_result = self._run_stage("Stage 2: Semantic Resolver", semantic_resolver.resolve, prompt_to_analyze)
                unresolved_items = [{"type": item.type, "source": item.source, "candidates": item.candidates, "confidence": item.confidence} for item in resolver_result.approval_items]
                if unresolved_items:
                    self._save_record(payload.prompt, "semantic_approval", name=payload.name, tag=payload.tag, description=payload.description)
                    return {"status": "semantic_approval", "approval_items": unresolved_items, "current_strategy": payload.prompt}

            # Stage 3: Compiler
            strategy_parser = StrategyParser(strategy_schema_path=strategy_schema_path)
            compiler = StrategyCompiler(strategy_parser)
            canonical_json = self._run_stage("Stage 3: Compiler", compiler.compile, payload.prompt, approved_interpretations)

            # Stage 4: Schema Validation
            schema_validator = SchemaValidator(StrategyValidator())
            is_valid, schema_errors = self._run_stage("Stage 4: Schema Validation", schema_validator.validate, canonical_json)
            if not is_valid:
                raise HTTPException(status_code=400, detail={"type": "schema_validation", "messages": schema_errors})

            # Stage 5: AST Generation
            ast_generator = ASTGenerator(ASTBuilder())
            ast = self._run_stage("Stage 5: AST Generation", ast_generator.generate, canonical_json, "frontend_strategy", deterministic_schema)

            # Stage 6: AST Validation
            ast_validator = ASTValidatorStep()
            is_ast_valid, ast_errors = self._run_stage("Stage 6: AST Validation", ast_validator.validate, ast)
            if not is_ast_valid:
                raise HTTPException(status_code=400, detail={"type": "ast_validation", "messages": ast_errors})

            # Stage 7: Auditor
            auditor = Auditor()
            audit_result = self._run_stage("Stage 7: Auditor", auditor.audit, ast)
            if audit_result.status == "FAIL":
                raise HTTPException(status_code=400, detail={"type": "auditor_validation", "messages": audit_result.messages})

            ast_json = ASTSerializer.to_json(ast, include_version=True)
            token_usage = canonical_json.pop("_token_usage", None)
            
            db_record = self._save_record(
                prompt=payload.prompt, status="ok", canonical_json=canonical_json,
                ast_json=json.loads(ast_json), execution_context=payload.execution_context,
                name=payload.name, tag=payload.tag, description=payload.description
            )

            return {
                "status": "ok", "id": db_record.id, "prompt": payload.prompt,
                "canonical_json": canonical_json, "ast_json": json.loads(ast_json),
                "_meta": {"request_id": self.request_id, "stage_timings": self.stage_timings, "token_usage": token_usage},
            }
        except Exception as exc:
            try:
                self._save_record(payload.prompt, "error", name=payload.name, tag=payload.tag, description=payload.description)
            except Exception as db_exc:
                logger.error(f"[{self.request_id}] Failed to save error to db: {db_exc}")
            raise exc


def generate_strategy_response(payload: StrategyRequest, db: Session, user_id: Optional[str] = None) -> dict:
    repository = StrategyRecordRepository(db, user_id)
    service = StrategyGenerationService(repository)
    return service.process_strategy(payload)
