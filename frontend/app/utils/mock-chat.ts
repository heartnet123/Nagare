export type Source = {
  title: string
  snippet: string
  score: number
}

export type MockReply = {
  content: string
  sources: Source[]
}

const genericSources: Source[] = [
  {
    title: 'rag-architecture-guide.pdf',
    snippet:
      'A retrieval-augmented generation pipeline combines a dense retriever with a generative model to ground responses in an external corpus.',
    score: 0.94
  },
  {
    title: 'evaluation-methodology.md',
    snippet:
      'Faithfulness, answer relevance, and context precision are the three core metrics tracked across every evaluation run.',
    score: 0.89
  },
  {
    title: 'internal-benchmarks-q3.csv',
    snippet:
      'The reranked hybrid retriever improved context precision by 8.4% over the baseline BM25 configuration.',
    score: 0.82
  }
]

export function mockReply(prompt: string): MockReply {
  const p = prompt.toLowerCase()

  if (p.includes('agent')) {
    return {
      content:
        'All 12 agents are currently healthy. The retrieval, reranking, and synthesis agents are operating within nominal latency budgets (p95 under 340ms). No restarts have occurred in the last 24 hours, and the orchestration queue depth is stable at 3 pending tasks.',
      sources: [
        {
          title: 'agent-health-snapshot.json',
          snippet: 'status: healthy · agents_online: 12/12 · queue_depth: 3 · restarts_24h: 0',
          score: 0.97
        },
        genericSources[1]!
      ]
    }
  }

  if (p.includes('analytic') || p.includes('metric') || p.includes('performance')) {
    return {
      content:
        'Over the last 7 days you processed 24.8K queries with a 98.6% success rate. Average end-to-end latency was 320ms (down 8.4%), and retrieval precision held steady at 0.91. Peak load occurred Tuesday at 14:00 UTC with 1.9K queries/hour.',
      sources: [genericSources[2]!, genericSources[1]!]
    }
  }

  if (p.includes('eval')) {
    return {
      content:
        'The latest evaluation on the legal-docs dataset scored 0.91 faithfulness, 0.88 answer relevance, and 0.86 context precision across 240 test cases. Twelve cases regressed versus the previous run, mostly on multi-hop questions requiring more than three retrieved chunks.',
      sources: [genericSources[1]!, genericSources[0]!]
    }
  }

  return {
    content:
      'Retrieval-augmented generation (RAG) grounds a language model in an external knowledge base. At query time the system embeds the question, retrieves the most relevant document chunks from a vector store, optionally reranks them, and passes the top results to the model as context. This keeps answers factual, current, and traceable back to their sources.',
    sources: genericSources
  }
}
