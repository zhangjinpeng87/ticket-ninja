import React, { useState } from 'react';
import { invoke } from '@forge/bridge';

interface Citation {
  title: string;
  url?: string;
  source_type?: string;
}

interface AnalyzeResult {
  answer: string;
  citations: Citation[];
  confidence: number;
  kb_suggestions?: Citation[];
}

export const App: React.FC = () => {
  const [text, setText] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResult | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // TODO: Upload file via Forge Media API once wired; use returned id
      const screenshotId = file ? 'placeholder-screenshot-id' : undefined;
      const response = await invoke('analyze', {
        queryText: text || undefined,
        screenshotId
      } as any);

      if (!response || response.ok === false) {
        throw new Error(response?.error || 'Unknown error');
      }
      setResult(response.data as AnalyzeResult);
    } catch (err: any) {
      setError(err?.message || String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ fontFamily: 'Inter, system-ui, Arial', padding: 16 }}>
      <h2>AI Assistant</h2>
      <form onSubmit={onSubmit} style={{ display: 'grid', gap: 12 }}>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter problem text or describe error logs"
          rows={5}
          style={{ width: '100%' }}
        />
        <input
          type="file"
          accept="image/*"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Analyzing…' : 'Submit'}
        </button>
      </form>

      {error && (
        <div style={{ color: 'red', marginTop: 12 }}>Error: {error}</div>
      )}

      {result && (
        <div style={{ marginTop: 16 }}>
          <h3>AI Answer</h3>
          <p>{result.answer}</p>
          <div>
            <strong>Confidence:</strong> {(result.confidence * 100).toFixed(0)}%
          </div>
          {!!result.citations?.length && (
            <div style={{ marginTop: 8 }}>
              <strong>Citations:</strong>
              <ul>
                {result.citations.map((c, idx) => (
                  <li key={idx}>
                    {c.url ? <a href={c.url}>{c.title}</a> : c.title}
                    {c.source_type ? ` (${c.source_type})` : ''}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {!!result.kb_suggestions?.length && (
            <div style={{ marginTop: 8 }}>
              <strong>KB Suggestions:</strong>
              <ul>
                {result.kb_suggestions.map((c, idx) => (
                  <li key={idx}>
                    {c.url ? <a href={c.url}>{c.title}</a> : c.title}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
