import json
from functools import lru_cache
from pathlib import Path

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from app.core.config import Config
from app.services.chunking import chunk_profile_pages
from app.services.pdf_sources import extract_pdf_pages
from app.services.retrieval import ProfileRetriever


mcp_server = MCPServer("AI Profile Assistant")


@lru_cache(maxsize=1)
def get_profile_retriever() -> ProfileRetriever:
	"""Build the small in-memory PDF index on first tool use, then reuse it."""
	pages = []
	for source, pdf_path in Config.get_profile_source_paths().items():
		pages.extend(extract_pdf_pages(pdf_path, source=source))

	chunks = chunk_profile_pages(pages)
	return ProfileRetriever.from_chunks(chunks)


@mcp_server.tool()
def search_profile(query: str, top_k: int = Config.PROFILE_RETRIEVAL_TOP_K) -> str:
	"""Find relevant excerpts in the LinkedIn profile and resume PDFs.

	Returns JSON results containing excerpt text, source, page number, and similarity score.
	"""
	if not query.strip():
		raise ValueError("query must not be empty.")
	if top_k < 1 or top_k > 8:
		raise ValueError("top_k must be between 1 and 8.")

	results = get_profile_retriever().search(query, top_k=top_k)
	citations = [
		{
			"source": result.chunk.source,
			"page_number": result.chunk.page_number,
			"text": result.chunk.text,
			"score": round(result.score, 4),
		}
		for result in results
	]
	return json.dumps(citations, ensure_ascii=True)


def create_mcp_http_app():
	transport_security = TransportSecuritySettings(
		allowed_hosts=Config.get_profile_mcp_allowed_hosts()
	)
	return mcp_server.streamable_http_app(transport_security=transport_security)