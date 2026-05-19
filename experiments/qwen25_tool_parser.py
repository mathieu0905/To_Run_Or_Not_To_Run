"""
Custom tool parser for Qwen2.5-Coder models.

Qwen2.5-Coder outputs tool calls as raw JSON (no XML tags), e.g.:
  {"name": "read_file", "arguments": {"filePath": "/etc/hostname"}}

Strategy for streaming:
  - Suppress all output while accumulating JSON
  - When we detect a complete tool call (name + arguments both present),
    emit the tool call delta
  - Track what we've already sent to avoid duplicates
"""
import json
from collections.abc import Sequence
from typing import Union

import partial_json_parser
from partial_json_parser.core.options import Allow

from vllm.entrypoints.chat_utils import make_tool_call_id
from vllm.entrypoints.openai.engine.protocol import (
    DeltaFunctionCall,
    DeltaMessage,
    DeltaToolCall,
    ExtractedToolCallInformation,
    FunctionCall,
    ToolCall,
)
from vllm.logger import init_logger
from vllm.tokenizers import TokenizerLike
from vllm.tool_parsers.abstract_tool_parser import ToolParser, ToolParserManager

logger = init_logger(__name__)


@ToolParserManager.register_module("qwen25")
class Qwen25ToolParser(ToolParser):

    def __init__(self, tokenizer: TokenizerLike):
        super().__init__(tokenizer)
        self.current_tool_name_sent: bool = False
        self.prev_tool_call_arr: list[dict] = []
        self.current_tool_id: int = -1
        self.streamed_args_for_tool: list[str] = []
        self._tool_call_name: str = ""
        self._sent_name: bool = False
        self._last_args_sent: str = ""

    def extract_tool_calls(
        self, model_output: str, request=None
    ) -> ExtractedToolCallInformation:
        """Non-streaming: parse complete model output for tool calls."""
        text = model_output.strip()
        if not text:
            return ExtractedToolCallInformation(
                tools_called=False, tool_calls=[], content=text
            )

        parsed = self._try_parse(text)
        if parsed is None:
            return ExtractedToolCallInformation(
                tools_called=False, tool_calls=[], content=model_output
            )

        if isinstance(parsed, dict):
            parsed = [parsed]
        if not isinstance(parsed, list):
            return ExtractedToolCallInformation(
                tools_called=False, tool_calls=[], content=model_output
            )

        tool_calls = []
        for tc in parsed:
            name = tc.get("name", "")
            if not name:
                continue
            args = tc.get("arguments", {})
            args_str = json.dumps(args) if not isinstance(args, str) else args
            tool_calls.append(
                ToolCall(
                    type="function",
                    function=FunctionCall(name=name, arguments=args_str),
                    id=make_tool_call_id(),
                )
            )

        if tool_calls:
            return ExtractedToolCallInformation(
                tools_called=True, tool_calls=tool_calls, content=None
            )
        return ExtractedToolCallInformation(
            tools_called=False, tool_calls=[], content=model_output
        )

    def _strip_xml_tags(self, text: str) -> str:
        """Strip known XML wrapper tags from tool call output."""
        import re
        for tag in ['calls', 'tool_call', 'tool_calls', 'tools',
                     'function_call']:
            m = re.search(rf'<{tag}>\s*(.*)', text, re.DOTALL)
            if m:
                inner = m.group(1)
                # Remove closing tag if present
                inner = re.sub(rf'\s*</{tag}>\s*$', '', inner)
                return inner.strip()
        return text

    def extract_tool_calls_streaming(
        self,
        previous_text: str,
        current_text: str,
        delta_text: str,
        previous_token_ids: Sequence[int],
        current_token_ids: Sequence[int],
        delta_token_ids: Sequence[int],
        request=None,
    ) -> Union[DeltaMessage, None]:
        current_stripped = current_text.strip()

        if not current_stripped:
            return None

        # Strip XML wrapper tags (e.g. <calls>, <tool_call>)
        current_stripped = self._strip_xml_tags(current_stripped)

        # Not a tool call pattern - pass through as content
        if current_stripped and current_stripped[0] not in ('{', '[', '<'):
            return DeltaMessage(content=delta_text)

        # If still starts with '<', it's an incomplete XML tag - suppress
        if not current_stripped or current_stripped[0] == '<':
            return None

        # Looks like JSON - try partial parsing
        try:
            parsed = partial_json_parser.loads(
                current_stripped, Allow.ALL
            )
        except Exception:
            # Can't parse yet, suppress output
            return None

        # Normalize
        if isinstance(parsed, dict):
            tc_list = [parsed]
        elif isinstance(parsed, list):
            tc_list = [x for x in parsed if isinstance(x, dict)]
        else:
            return None

        # Filter to entries with a name
        tc_list = [tc for tc in tc_list if tc.get("name")]
        if not tc_list:
            return None

        # Get the latest tool call
        tc = tc_list[-1]
        name = tc.get("name", "")
        args = tc.get("arguments")

        # We need to wait until arguments are present AND have actual content
        if args is None:
            # Name is there but no arguments yet - suppress
            return None

        args_str = json.dumps(args) if not isinstance(args, str) else args

        # Don't send empty arguments - wait for actual content
        if args_str in ('{}', '""', ''):
            return None

        # First time sending this tool call?
        if not self._sent_name or name != self._tool_call_name:
            self._sent_name = True
            self._tool_call_name = name
            self._last_args_sent = args_str
            self.current_tool_id += 1

            return DeltaMessage(
                tool_calls=[
                    DeltaToolCall(
                        index=self.current_tool_id,
                        type="function",
                        id=make_tool_call_id(),
                        function=DeltaFunctionCall(
                            name=name,
                            arguments=args_str,
                        ),
                    )
                ]
            )
        else:
            # Send argument updates
            if args_str != self._last_args_sent:
                # Find the new portion
                old = self._last_args_sent
                if args_str.startswith(old):
                    delta = args_str[len(old):]
                else:
                    delta = args_str
                self._last_args_sent = args_str
                if delta:
                    return DeltaMessage(
                        tool_calls=[
                            DeltaToolCall(
                                index=self.current_tool_id,
                                type="function",
                                function=DeltaFunctionCall(
                                    arguments=delta,
                                ),
                            )
                        ]
                    )

        return None

    def _try_parse(self, text: str):
        """Try to parse text as tool call(s).

        Qwen2.5-Coder under complex SWE-bench prompts hallucinates several
        non-conforming formats. Recognise and normalise:

        1. <tool_call>{"name":..,"arguments":{..}}</tool_call>  (chat template)
        2. {"name":"read","arguments":{"filePath":"/x"}}        (raw JSON)
        3. read {"filePath":"/x"}                                (func + JSON)
        4. [read filePath="/x" key="val"]                        (bracket)
        5. [bash command="ls -la"]                               (bracket)
        """
        import re
        text = text.strip()
        if not text:
            return None

        # 1. Strip XML wrapper tags
        for tag in ['tool_call', 'tool_calls', 'calls', 'tools',
                     'function_call']:
            m = re.search(rf'<{tag}>\s*(.*?)\s*</{tag}>', text, re.DOTALL)
            if m:
                text = m.group(1).strip()
                break

        # 2. Direct JSON
        try:
            obj = json.loads(text)
            if isinstance(obj, dict) and 'name' in obj:
                return obj
            if isinstance(obj, list) and obj and isinstance(obj[0], dict) and 'name' in obj[0]:
                return obj
        except json.JSONDecodeError:
            pass

        # 2b. Multiple JSON objects separated by whitespace/newlines
        # Use raw_decode to consume one object at a time.
        try:
            decoder = json.JSONDecoder()
            objs = []
            idx = 0
            while idx < len(text):
                # Skip whitespace
                while idx < len(text) and text[idx].isspace():
                    idx += 1
                if idx >= len(text):
                    break
                if text[idx] != '{':
                    break
                obj, end = decoder.raw_decode(text, idx)
                if isinstance(obj, dict) and 'name' in obj:
                    objs.append(obj)
                else:
                    break
                idx = end
            if objs:
                return objs if len(objs) > 1 else objs[0]
        except (json.JSONDecodeError, ValueError):
            pass

        # 3. funcname {"...": "..."}  (e.g. `read {"filePath": "/x"}`)
        m = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s+(\{.*\})\s*$', text, re.DOTALL)
        if m:
            try:
                args = json.loads(m.group(2))
                return {"name": m.group(1), "arguments": args}
            except json.JSONDecodeError:
                pass

        # 4. [funcname key="value" key2="value2"]  bracket pseudo-syntax
        m = re.match(r'^\[\s*([a-zA-Z_][a-zA-Z0-9_]*)\s+(.*?)\s*\]\s*$', text, re.DOTALL)
        if m:
            name = m.group(1)
            args_str = m.group(2)
            args = {}
            # Match key="value" or key='value'
            for k, v in re.findall(r'(\w+)\s*=\s*"((?:[^"\\]|\\.)*)"', args_str):
                args[k] = v.encode().decode('unicode_escape') if '\\' in v else v
            for k, v in re.findall(r"(\w+)\s*=\s*'((?:[^'\\]|\\.)*)'", args_str):
                if k not in args:
                    args[k] = v
            if args:
                return {"name": name, "arguments": args}

        # 5. JSON object(s) embedded inside prose. Find every '{"name"' offset
        # and try raw_decode from there. Collect every successful decode.
        decoder = json.JSONDecoder()
        embedded = []
        for m in re.finditer(r'\{\s*"name"\s*:', text):
            try:
                obj, _ = decoder.raw_decode(text, m.start())
                if isinstance(obj, dict) and 'name' in obj:
                    embedded.append(obj)
            except (json.JSONDecodeError, ValueError):
                continue
        if embedded:
            return embedded if len(embedded) > 1 else embedded[0]

        return None
