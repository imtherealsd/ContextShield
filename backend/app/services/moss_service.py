"""Moss Local Runtime semantic security-policy retrieval service."""

import os
import time
from typing import Any, List, Optional, Tuple
from dotenv import load_dotenv
from backend.app.models.responses import MossPolicyMatch

# Load environment variables from .env if present
load_dotenv()


class MossSecurityRetriever:
    """Abstraction for Moss Local Runtime semantic security-policy retrieval.
    
    Adheres strictly to the official Moss Python SDK:
        from moss import MossClient, QueryOptions
        client = MossClient(project_id, project_key)
        await client.load_index(index_name)
        results = await client.query(index_name, query, QueryOptions(top_k=top_k))
    
    Lifespan States:
    - not_configured: Missing MOSS_PROJECT_ID or MOSS_PROJECT_KEY.
    - loading: Client instantiated, index load in progress.
    - ready: Index successfully loaded into local runtime memory.
    - error: Index loading failed or SDK exception occurred.
    
    Guarantees:
    - Never silently reports ready.
    - Never fabricates retrieval results or latency numbers.
    - If unconfigured/unexecuted, returns moss_ms = None and matched_policy_ids = [].
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        project_key: Optional[str] = None,
        index_name: Optional[str] = None,
    ):
        load_dotenv()
        self.project_id = os.getenv("MOSS_PROJECT_ID") if project_id is None else project_id
        self.project_key = os.getenv("MOSS_PROJECT_KEY") if project_key is None else project_key
        self.index_name = os.getenv("MOSS_INDEX_NAME", "contextshield-security") if index_name is None else index_name
        self.client: Optional[Any] = None
        self.loaded: bool = False
        self.error_message: Optional[str] = None
        
        if not self.project_id or not self.project_key:
            self.status: str = "not_configured"
        else:
            self.status = "loading"

    async def initialize(self) -> None:
        """Initializes the Moss client and loads the security index on startup."""
        load_dotenv()
        if self.project_id is None:
            self.project_id = os.getenv("MOSS_PROJECT_ID")
        if self.project_key is None:
            self.project_key = os.getenv("MOSS_PROJECT_KEY")
        if self.index_name is None:
            self.index_name = os.getenv("MOSS_INDEX_NAME", "contextshield-security")

        if not self.project_id or not self.project_key:
            self.status = "not_configured"
            self.loaded = False
            return

        self.status = "loading"
        try:
            from moss import MossClient  # type: ignore
            self.client = MossClient(self.project_id, self.project_key)
            await self.client.load_index(self.index_name)
            self.loaded = True
            self.status = "ready"
            self.error_message = None
        except ImportError:
            self.status = "error"
            self.loaded = False
            self.error_message = "Moss SDK is not installed"
        except Exception as exc:
            self.status = "error"
            self.loaded = False
            self.error_message = str(exc)

    def get_status(self) -> dict:
        """Returns the current Moss health state without exposing credentials."""
        return {
            "status": self.status,
            "loaded": self.loaded,
            "index_name": self.index_name if self.status in ("loading", "ready", "error") else None
        }

    async def retrieve_policies(
        self,
        query: str,
        top_k: int = 5
    ) -> Tuple[List[MossPolicyMatch], Optional[float], bool]:
        """Queries the Moss security policy index using official SDK operations.
        
        Returns:
            Tuple of (matches_list, moss_ms, query_executed).
            - When unconfigured or not ready: ([], None, False).
            - When real query executes: (matches, time_taken_ms, True).
        """
        # When unconfigured, loading, or in error: NO query is executed
        if not self.loaded or self.client is None or self.status != "ready":
            return [], None, False

        start_time = time.perf_counter()
        try:
            try:
                from moss import QueryOptions  # type: ignore
                options = QueryOptions(top_k=top_k)
            except ImportError:
                options = type("QueryOptions", (), {"top_k": top_k})()

            results = await self.client.query(
                self.index_name,
                query,
                options
            )

            # Use SDK-exposed time_taken_ms where available, fallback to monotonic timer
            sdk_time = getattr(results, "time_taken_ms", None)
            if sdk_time is not None and isinstance(sdk_time, (int, float)):
                elapsed_ms = float(sdk_time)
            else:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            matches: List[MossPolicyMatch] = []
            docs = getattr(results, "docs", []) or []
            for doc in docs:
                meta = getattr(doc, "metadata", {}) or {}
                matches.append(
                    MossPolicyMatch(
                        id=doc.id,
                        text=getattr(doc, "text", ""),
                        score=float(getattr(doc, "score", 0.0)),
                        metadata=meta,
                        category=meta.get("category"),
                        severity=meta.get("severity"),
                        recommended_action=meta.get("recommended_action")
                    )
                )
            return matches, round(elapsed_ms, 3), True
        except Exception:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return [], round(elapsed_ms, 3), True


# Global singleton instance
moss_retriever = MossSecurityRetriever()
