#!/usr/bin/env python3
"""
Proxy that converts streaming chat completion requests to non-streaming,
then converts the response back to SSE format with COMPLETE tool call arguments.

Why: vLLM's hermes streaming parser sends cumulative (not incremental)
argument deltas, causing OpenCode to execute tools with partial arguments
like {"filePath":"/"}. By using non-streaming on the backend, we get the
full tool call, then synthesize SSE chunks with complete arguments.
"""
import json
import os
import sys
import time

# Clear proxy env vars BEFORE importing requests
for k in ('HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy'):
    os.environ.pop(k, None)

import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

VLLM_BASE = "http://localhost:8000"

SESSION = requests.Session()
SESSION.trust_env = False


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def _proxy_get(self):
        try:
            resp = SESSION.get(f"{VLLM_BASE}{self.path}", timeout=30)
            content = resp.content
            self.send_response(resp.status_code)
            self.send_header('Content-Type', resp.headers.get('Content-Type', 'application/json'))
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(502, f"Proxy error: {e}")

    def do_GET(self):
        self._proxy_get()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            if '/chat/completions' not in self.path:
                # Pass through other POSTs
                resp = SESSION.post(
                    f"{VLLM_BASE}{self.path}",
                    data=body,
                    headers={'Content-Type': 'application/json'},
                    timeout=600
                )
                content = resp.content
                self.send_response(resp.status_code)
                self.send_header('Content-Type', resp.headers.get('Content-Type', 'application/json'))
                self.send_header('Content-Length', str(len(content)))
                self.send_header('Connection', 'close')
                self.end_headers()
                self.wfile.write(content)
                return

            self._handle_chat_completions(body)
        except Exception as e:
            try:
                self.send_error(500, f"Proxy error: {e}")
            except Exception:
                pass

    def _handle_chat_completions(self, body: bytes):
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        was_streaming = data.get('stream', False)
        # Always use non-streaming on the backend
        data['stream'] = False
        data.pop('stream_options', None)

        # Debug: log key request fields
        try:
            n_msgs = len(data.get('messages', []))
            n_tools = len(data.get('tools', []))
            tc = data.get('tool_choice', 'unset')
            temp = data.get('temperature', 'unset')
            mt = data.get('max_tokens', 'unset')
            sys.stderr.write(f"[proxy] req msgs={n_msgs} tools={n_tools} tc={tc} temp={temp} mt={mt}\n")
            sys.stderr.flush()
        except Exception:
            pass

        try:
            resp = SESSION.post(
                f"{VLLM_BASE}{self.path}",
                json=data,
                timeout=600
            )
        except Exception as e:
            self.send_error(502, f"vLLM request failed: {e}")
            return

        if not was_streaming:
            content = resp.content
            self.send_response(resp.status_code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(content)
            return

        # Build SSE response from non-streaming result
        try:
            result = resp.json()
        except Exception:
            self.send_error(502, "Invalid response from vLLM")
            return

        sse_body = self._build_sse_body(result)
        sse_bytes = sse_body.encode('utf-8')

        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Content-Length', str(len(sse_bytes)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(sse_bytes)
        self.wfile.flush()

    def _build_sse_body(self, result: dict) -> str:
        """Convert non-streaming response to SSE format."""
        lines = []
        chunk_id = result.get('id', 'chatcmpl-proxy')
        model = result.get('model', '')
        created = result.get('created', int(time.time()))

        def emit(chunk):
            lines.append(f"data: {json.dumps(chunk)}\n\n")

        for choice in result.get('choices', []):
            msg = choice.get('message', {})
            index = choice.get('index', 0)
            finish_reason = choice.get('finish_reason') or 'stop'

            tool_calls = msg.get('tool_calls') or []
            content = msg.get('content')
            role = msg.get('role', 'assistant')

            # Emit role first
            role_chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{
                    "index": index,
                    "delta": {"role": role, "content": ""},
                    "finish_reason": None
                }]
            }
            emit(role_chunk)

            if tool_calls:
                for i, tc in enumerate(tool_calls):
                    fn = tc.get('function', {})
                    # Single chunk with name + complete arguments
                    tc_chunk = {
                        "id": chunk_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": model,
                        "choices": [{
                            "index": index,
                            "delta": {
                                "tool_calls": [{
                                    "index": i,
                                    "id": tc.get('id', f'call_{i}'),
                                    "type": "function",
                                    "function": {
                                        "name": fn.get('name', ''),
                                        "arguments": fn.get('arguments', '')
                                    }
                                }]
                            },
                            "finish_reason": None
                        }]
                    }
                    emit(tc_chunk)

            if content:
                content_chunk = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [{
                        "index": index,
                        "delta": {"content": content},
                        "finish_reason": None
                    }]
                }
                emit(content_chunk)

            # Final chunk with finish_reason
            final_chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{
                    "index": index,
                    "delta": {},
                    "finish_reason": finish_reason
                }]
            }
            usage = result.get('usage')
            if usage:
                final_chunk['usage'] = usage
            emit(final_chunk)

        lines.append("data: [DONE]\n\n")
        return ''.join(lines)

    def log_message(self, format, *args):
        sys.stderr.write(f"[proxy] {' '.join(str(a) for a in args)}\n")
        sys.stderr.flush()


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    server = ThreadingHTTPServer(('0.0.0.0', port), ProxyHandler)
    print(f"vLLM proxy listening on port {port}, forwarding to {VLLM_BASE}")
    sys.stdout.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nProxy stopped.")


if __name__ == '__main__':
    main()
