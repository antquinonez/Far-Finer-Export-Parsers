"""
Anthropic Chat Export Parser - Streamlined Message Format

Parses large Anthropic chat export JSON files and extracts conversations
with only essential message data: sender, text, and timestamp.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ConversationMetadata:
    """Metadata for a parsed conversation."""
    conversation_id: str
    name: str
    sanitized_filename: str
    message_count: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class MessageData:
    """Streamlined message data structure."""
    sender: str
    text: str
    created_at: Optional[str] = None


class MessageExtractor:
    """
    Extracts and normalizes message data from various Anthropic export formats.
    
    Handles different possible message structures and extracts only
    the essential information needed for AI processing.
    """
    
    def __init__(self):
        """Initialize the message extractor."""
        pass
    
    def extract_message_text(self, message: Dict[str, Any]) -> str:
        """
        Extract text content from a message, handling various formats.
        
        Args:
            message: Raw message data from export
            
        Returns:
            Extracted text content
        """
        # For Anthropic exports, text is directly in the 'text' field
        if 'text' in message and isinstance(message['text'], str):
            return message['text']
        
        # Try other possible text field names
        text_fields = ['content', 'body', 'message']
        
        for field in text_fields:
            if field in message:
                content = message[field]
                
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    # Handle structured content (like Claude's format)
                    text_parts = []
                    for part in content:
                        if isinstance(part, dict):
                            if 'text' in part:
                                text_parts.append(part['text'])
                            elif 'content' in part:
                                text_parts.append(str(part['content']))
                        elif isinstance(part, str):
                            text_parts.append(part)
                    return '\n'.join(text_parts)
                elif isinstance(content, dict):
                    # Handle nested content structures
                    if 'text' in content:
                        return content['text']
                    elif 'content' in content:
                        return str(content['content'])
        
        # Fallback: try to find any text-like content
        for key, value in message.items():
            if isinstance(value, str) and len(value) > 10:  # Assume substantial text
                return value
        
        return "[No text content found]"
    
    def extract_sender_info(self, message: Dict[str, Any]) -> str:
        """
        Extract sender information from message.
        
        Args:
            message: Raw message data from export
            
        Returns:
            Sender identifier (human, assistant, system, etc.)
        """
        # For Anthropic exports, sender is directly in the 'sender' field
        if 'sender' in message and isinstance(message['sender'], str):
            return message['sender'].lower()
        
        # Try other possible sender field names
        sender_fields = ['author', 'role', 'from', 'user']
        
        for field in sender_fields:
            if field in message:
                sender = message[field]
                
                if isinstance(sender, str):
                    return sender.lower()
                elif isinstance(sender, dict) and 'name' in sender:
                    return sender['name'].lower()
                elif isinstance(sender, dict) and 'role' in sender:
                    return sender['role'].lower()
        
        # Try to infer from message structure or content
        message_str = str(message).lower()
        if 'assistant' in message_str:
            return 'assistant'
        elif 'human' in message_str:
            return 'human'
        elif 'user' in message_str:
            return 'human'
        
        return 'unknown'
    
    def extract_timestamp(self, message: Dict[str, Any]) -> Optional[str]:
        """
        Extract timestamp from message.
        
        Args:
            message: Raw message data from export
            
        Returns:
            ISO format timestamp or None
        """
        timestamp_fields = ['created_at', 'timestamp', 'time', 'date']
        
        for field in timestamp_fields:
            if field in message and message[field]:
                return message[field]
        
        return None
    
    def process_message(self, message: Dict[str, Any]) -> MessageData:
        """
        Process a raw message into streamlined format.
        
        Args:
            message: Raw message data from export
            
        Returns:
            MessageData with essential information
        """
        return MessageData(
            sender=self.extract_sender_info(message),
            text=self.extract_message_text(message),
            created_at=self.extract_timestamp(message)
        )


class ConversationParser:
    """
    Parses Anthropic chat export data and extracts individual conversations
    with streamlined message format.
    """
    
    def __init__(self, max_filename_length: int = 100):
        """
        Initialize the parser.
        
        Args:
            max_filename_length: Maximum length for generated filenames
        """
        self.max_filename_length = max_filename_length
        self.message_extractor = MessageExtractor()
        
    def sanitize_filename(self, name: str) -> str:
        """
        Convert conversation name to safe filename.
        
        Args:
            name: Original conversation name
            
        Returns:
            Sanitized filename without extension
        """
        # Remove/replace problematic characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
        sanitized = re.sub(r'\s+', '_', sanitized.strip())
        sanitized = re.sub(r'_+', '_', sanitized)
        sanitized = sanitized.strip('_.')
        
        # Handle empty names
        if not sanitized:
            sanitized = "untitled_conversation"
            
        # Truncate if too long
        if len(sanitized) > self.max_filename_length:
            sanitized = sanitized[:self.max_filename_length].rstrip('_')
            
        return sanitized
    
    def extract_conversations(self, export_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract conversations from export data structure.
        
        Args:
            export_data: Parsed JSON export data
            
        Returns:
            List of conversation dictionaries
            
        Raises:
            KeyError: If expected data structure is not found
            ValueError: If no conversations found in export
        """
        # Handle different possible export structures
        conversations = None
        
        if 'conversations' in export_data:
            conversations = export_data['conversations']
        elif 'data' in export_data and 'conversations' in export_data['data']:
            conversations = export_data['data']['conversations']
        elif isinstance(export_data, list):
            conversations = export_data
        else:
            # Try to find conversation-like structures
            for key, value in export_data.items():
                if isinstance(value, list) and value and any(
                    field in str(value[0]) for field in ['messages', 'chat_messages']
                ):
                    conversations = value
                    break
        
        if not conversations:
            raise ValueError("No conversations found in export data")
            
        return conversations
    
    def get_conversation_metadata(self, conversation: Dict[str, Any], index: int) -> ConversationMetadata:
        """
        Extract metadata from a conversation object.
        
        Args:
            conversation: Single conversation data
            index: Conversation index for fallback naming
            
        Returns:
            ConversationMetadata object
        """
        # Extract conversation ID - handle both direct and nested structures
        conv_id = (
            conversation.get('id') or 
            conversation.get('uuid') or 
            (conversation.get('conversation', {}).get('uuid')) or
            f'conversation_{index:04d}'
        )
        
        # Extract conversation name with fallbacks - handle nested structure
        name = (
            conversation.get('name') or 
            conversation.get('title') or
            conversation.get('summary') or
            (conversation.get('conversation', {}).get('name')) or
            f"Conversation {index + 1}"
        )
        
        # Count messages - handle both 'messages' and 'chat_messages'
        messages = (
            conversation.get('messages', []) or 
            conversation.get('chat_messages', []) or
            conversation.get('conversation', {}).get('chat_messages', [])
        )
        message_count = len(messages) if isinstance(messages, list) else 0
        
        # Extract timestamps - handle nested structure
        created_at = (
            conversation.get('created_at') or
            conversation.get('conversation', {}).get('created_at')
        )
        updated_at = (
            conversation.get('updated_at') or
            conversation.get('conversation', {}).get('updated_at')
        )
        
        return ConversationMetadata(
            conversation_id=conv_id,
            name=name,
            sanitized_filename=self.sanitize_filename(name),
            message_count=message_count,
            created_at=created_at,
            updated_at=updated_at
        )
    
    def process_conversation_messages(self, conversation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process conversation messages into streamlined format.
        
        Args:
            conversation: Raw conversation data
            
        Returns:
            List of processed messages with only essential data
        """
        # Handle both direct and nested message structures
        messages = (
            conversation.get('messages', []) or 
            conversation.get('chat_messages', []) or
            conversation.get('conversation', {}).get('chat_messages', [])
        )
        
        processed_messages = []
        
        for message in messages:
            try:
                message_data = self.message_extractor.process_message(message)
                
                # Convert to dictionary for JSON serialization
                message_dict = {
                    'sender': message_data.sender,
                    'text': message_data.text
                }
                
                # Only include timestamp if available
                if message_data.created_at:
                    message_dict['created_at'] = message_data.created_at
                
                processed_messages.append(message_dict)
                
            except Exception as e:
                print(f"Warning: Failed to process message: {e}")
                # Include a placeholder for failed messages
                processed_messages.append({
                    'sender': 'unknown',
                    'text': '[Message processing failed]',
                    'error': str(e)
                })
        
        return processed_messages
    
    def find_latest_message_timestamp(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """
        Find the latest created_at timestamp from a list of messages.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Latest ISO format timestamp or None if no timestamps found
        """
        timestamps = []
        
        for message in messages:
            if 'created_at' in message and message['created_at']:
                timestamps.append(message['created_at'])
        
        if not timestamps:
            return None
        
        # Sort timestamps and return the latest one
        try:
            # Convert to datetime objects for proper sorting
            datetime_objects = []
            for ts in timestamps:
                try:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    datetime_objects.append((dt, ts))
                except (ValueError, AttributeError):
                    continue
            
            if datetime_objects:
                # Sort by datetime and return the original timestamp string
                datetime_objects.sort(key=lambda x: x[0])
                return datetime_objects[-1][1]  # Return the latest timestamp
            else:
                # Fallback to string sorting if datetime parsing fails
                return sorted(timestamps)[-1]
                
        except Exception:
            # If all else fails, just return the last timestamp
            return timestamps[-1] if timestamps else None


class ChatExportProcessor:
    """
    Main processor for handling Anthropic chat export files.
    
    Processes exports into streamlined conversation files containing
    only essential message data.
    """
    
    def __init__(self, export_file_path: str | Path):
        """
        Initialize processor with export file path.
        
        Args:
            export_file_path: Path to the Anthropic export JSON file
        """
        self.export_path = Path(export_file_path)
        # Get file creation date from filesystem
        file_stat = self.export_path.stat()
        file_creation_date = datetime.fromtimestamp(file_stat.st_ctime).strftime('%Y%m%d')
        
        self.output_dir = self.export_path.parent / f"{self.export_path.stem}_conversations_{file_creation_date}"
        self.parser = ConversationParser()
        
        if not self.export_path.exists():
            raise FileNotFoundError(f"Export file not found: {self.export_path}")
    
    def load_export_data(self) -> Dict[str, Any]:
        """
        Load and parse the export JSON file.
        
        Returns:
            Parsed JSON data
            
        Raises:
            json.JSONDecodeError: If file is not valid JSON
            MemoryError: If file is too large for available memory
        """
        print(f"Loading export file: {self.export_path}")
        print(f"File size: {self.export_path.stat().st_size / (1024*1024):.1f} MB")
        
        try:
            with open(self.export_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in export file: {e.msg}", 
                e.doc, 
                e.pos
            )
    
    def create_output_directory(self) -> None:
        """Create output directory for individual conversation files."""
        simple_output_dir = self.output_dir.parent / f"{self.output_dir.name}_simple"
        simple_output_dir.mkdir(exist_ok=True)
        print(f"Output directory: {simple_output_dir}")
    
    def save_conversation(
    self, 
    conversation: Dict[str, Any], 
    metadata: ConversationMetadata
    ) -> Path:
        """
        Save individual conversation to JSON file with streamlined format.
        
        Args:
            conversation: Raw conversation data
            metadata: Conversation metadata for naming
            
        Returns:
            Path to saved file
        """
        # Create simple output directory
        simple_output_dir = self.output_dir.parent / f"{self.output_dir.name}_simple"
        simple_output_dir.mkdir(exist_ok=True)
        
        # Process messages to streamlined format
        processed_messages = self.parser.process_conversation_messages(conversation)
        
        # Find the latest message timestamp
        latest_timestamp = self.parser.find_latest_message_timestamp(processed_messages)
        
        # Use latest message timestamp for filename, fallback to conversation metadata timestamp
        timestamp_for_filename = latest_timestamp or metadata.created_at
        
        # Create filename with timestamp prefix
        date_prefix = ""
        if timestamp_for_filename:
            try:
                # Parse ISO timestamp and format as YYYYMMDD_HHMMSS
                dt = datetime.fromisoformat(timestamp_for_filename.replace('Z', '+00:00'))
                date_prefix = dt.strftime('%Y%m%d_%H%M%S_')
            except (ValueError, AttributeError):
                # Fallback if timestamp parsing fails
                date_prefix = ""
        
        filename = f"{date_prefix}{metadata.sanitized_filename}.json"
        output_path = simple_output_dir / filename
        
        # Handle filename conflicts
        counter = 1
        while output_path.exists():
            base_name = f"{date_prefix}{metadata.sanitized_filename}"
            filename = f"{base_name}_{counter:02d}.json"
            output_path = simple_output_dir / filename
            counter += 1
        
        # Create streamlined conversation structure
        streamlined_conversation = {
            'conversation_id': metadata.conversation_id,
            'name': metadata.name,
            'messages': processed_messages
        }
        
        # Optionally include conversation timestamps if available
        if metadata.created_at:
            streamlined_conversation['created_at'] = metadata.created_at
        if metadata.updated_at:
            streamlined_conversation['updated_at'] = metadata.updated_at
        
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(streamlined_conversation, file, indent=2, ensure_ascii=False)
        
        return output_path
    
    def process_export(self) -> Dict[str, Any]:
        """
        Main processing method that orchestrates the entire operation.
        
        Returns:
            Summary statistics of the processing operation
        """
        print("Starting Anthropic chat export processing...")
        
        # Load export data
        export_data = self.load_export_data()
        
        # Extract conversations
        conversations = self.parser.extract_conversations(export_data)
        print(f"Found {len(conversations)} conversations")
        
        # Create output directory
        self.create_output_directory()
        
        # Process each conversation
        processed_count = 0
        skipped_count = 0
        total_messages = 0
        
        for index, conversation in enumerate(conversations):
            try:
                metadata = self.parser.get_conversation_metadata(conversation, index)
                output_path = self.save_conversation(conversation, metadata)
                
                processed_count += 1
                total_messages += metadata.message_count
                
                print(f"Saved: {output_path.name} ({metadata.message_count} messages)")
                
            except Exception as e:
                print(f"Warning: Failed to process conversation {index}: {e}")
                skipped_count += 1
                continue
        
        # Return summary
        simple_output_dir = self.output_dir.parent / f"{self.output_dir.name}_simple"
        summary = {
            'total_conversations': len(conversations),
            'processed_successfully': processed_count,
            'skipped_due_to_errors': skipped_count,
            'total_messages': total_messages,
            'output_directory': str(simple_output_dir)
        }
        
        print("\nProcessing completed!")
        print(f"Successfully processed: {processed_count} conversations")
        print(f"Total messages: {total_messages}")
        print(f"Output directory: {simple_output_dir}")
        
        if skipped_count > 0:
            print(f"Skipped due to errors: {skipped_count}")
        
        return summary


def main():
    """
    CLI entry point for the chat export processor.
    
    Usage:
        python chat_export_parser.py <path_to_export_file>
    """
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python chat_export_parser.py <path_to_export_file>")
        sys.exit(1)
    
    export_file_path = sys.argv[1]
    
    try:
        processor = ChatExportProcessor(export_file_path)
        summary = processor.process_export()
        
        # Save processing summary in the simple directory
        simple_output_dir = processor.output_dir.parent / f"{processor.output_dir.name}_simple"
        summary_path = simple_output_dir / "processing_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        print(f"Processing summary saved to: {summary_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()