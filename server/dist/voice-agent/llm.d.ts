import WebSocket from 'ws';
export declare function connectToElevenLabs(agentId: string, apiKey: string): WebSocket;
export interface OllamaMessage {
    role: 'system' | 'user' | 'assistant';
    content: string;
}
/**
 * Send a conversation history to a local Ollama model and get a text reply.
 *
 * @param messages - Full conversation history (system + user + assistant turns)
 * @param model    - Ollama model name (defaults to OLLAMA_MODEL env var or qwen2.5:7b)
 * @returns The assistant's reply string
 */
export declare function chatWithOllama(messages: OllamaMessage[], model?: string): Promise<string>;
//# sourceMappingURL=llm.d.ts.map