export interface ChatMessage {
    id: string;
    message: string;
    sender: 'user'| 'bot';
    timestamp: Date;
}

export interface api_response {
    answer: string;
    source_doc: SourceDocument[];
    session_id: string;
}

export interface SourceDocument {
    relevant_doc: string;
    [key:string]: any;
}

export interface ChatRequest {
    message: string;
    session_id?: string | null; // optional, if not provided, a new chat session will be created
}

export interface ErrorResponse {
    "internal server error" ?: string;
    error?: string;
}

export interface ChatSession {
    session_id: string | null;
    messages: ChatMessage[];
}