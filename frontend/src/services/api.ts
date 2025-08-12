import axios from 'axios';
import type {ChatRequest, api_response, ErrorResponse} from '../types/chats' 
// When "verbatimModuleSyntax": true, TS will refuse to erase an import you wrote as a normal 
// import if that imported symbol is never used as a value, because it has 
// to preserve module syntax exactly as you wrote it. Since marked import type, the compiler knows it can completely drop that statement in the emitted JS, avoiding any runtime “undefined” errors 
// and satisfying the verbatim syntax rule.


// use nvm for managing the versions of node -- nvm install 22 (for latest version of node v22 as of today Aug 2025)

/*
This is the API client for the chat application. It connects the front end to the back end.
That is, it sends user messages to the server and receives responses from the server.
*/

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000, // it will timeout in 30 secs
});

export const chatApi = {
    sendMessage: async (message:string, session_id?:string | null): Promise<api_response> => {
        try {
            console.log('Sending message:', message, 'Session ID:', session_id);
            // session_id = "123"
            const request: ChatRequest = {message, session_id}
            const response = await apiClient.post<api_response | ErrorResponse>('/chat', request)

            if ('error' in response.data || 'internal server error' in response.data) {
                throw new Error(response.data.error || response.data['internal server error']);
            }

            return response.data as api_response;


        } catch (error:any) {
            throw new Error(error.message || 'Failed to send message');
        }
    }
};