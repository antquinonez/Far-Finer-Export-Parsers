"""
Anthropic Chat Export Parser

Parses large Anthropic chat export JSON files and organizes conversations
into separate files with proper naming conventions.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
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
    latest_message_at: Optional[str] = None


class ConversationParser:
    """
    Parses Anthropic chat export data and extracts individual conversations.
    
    Handles large JSON files efficiently and provides clean separation
    of parsing logic from file operations.
    """
    
    def __init__(self, max_filename_length: int = 100):
        """
        Initialize the parser.
        
        Args:
            max_filename_length: Maximum length for generated filenames
        """
        self.max_filename_length = max_filename_length
        
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
    
    def find_latest_message_timestamp(self, conversation: Dict[str, Any]) -> Optional[str]:
        """
        Find the latest created_at timestamp from messages in a conversation.
        
        Args:
            conversation: Conversation data
            
        Returns:
            Latest ISO format timestamp or None if no timestamps found
        """
        # Extract messages - handle both direct and nested structures
        messages = (
            conversation.get('messages', []) or 
            conversation.get('chat_messages', []) or
            conversation.get('conversation', {}).get('chat_messages', [])
        )
        
        if not isinstance(messages, list):
            return None
        
        timestamps = []
        
        # Extract timestamps from messages
        for message in messages:
            if isinstance(message, dict):
                # Try various timestamp field names
                timestamp_fields = ['created_at', 'timestamp', 'time', 'date']
                for field in timestamp_fields:
                    if field in message and message[field]:
                        timestamps.append(message[field])
                        break
        
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
        
        # Find latest message timestamp
        latest_message_at = self.find_latest_message_timestamp(conversation)
        
        return ConversationMetadata(
            conversation_id=conv_id,
            name=name,
            sanitized_filename=self.sanitize_filename(name),
            message_count=message_count,
            created_at=created_at,
            updated_at=updated_at,
            latest_message_at=latest_message_at
        )


class ChatExportProcessor:
    """
    Main processor for handling Anthropic chat export files.
    
    Coordinates file I/O, parsing, and conversation extraction with
    proper error handling and progress reporting.
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
        self.output_dir.mkdir(exist_ok=True)
        print(f"Output directory: {self.output_dir}")
    
    def save_conversation(
    self, 
    conversation: Dict[str, Any], 
    metadata: ConversationMetadata
    ) -> Path:
        """
        Save individual conversation to JSON file.
        
        Args:
            conversation: Conversation data to save
            metadata: Conversation metadata for naming
            
        Returns:
            Path to saved file
        """
        # Use latest message timestamp for filename, fallback to conversation created_at
        timestamp_for_filename = metadata.latest_message_at or metadata.created_at
        
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
        output_path = self.output_dir / filename
        
        # Handle filename conflicts
        counter = 1
        while output_path.exists():
            base_name = f"{date_prefix}{metadata.sanitized_filename}"
            filename = f"{base_name}_{counter:02d}.json"
            output_path = self.output_dir / filename
            counter += 1
        
        # Add metadata to conversation data
        conversation_with_metadata = {
            'metadata': {
                'conversation_id': metadata.conversation_id,
                'original_name': metadata.name,
                'message_count': metadata.message_count,
                'created_at': metadata.created_at,
                'updated_at': metadata.updated_at,
                'latest_message_at': metadata.latest_message_at,
                'exported_at': datetime.now().isoformat()
            },
            'conversation': conversation
        }
        
        with open(output_path, 'w', encoding='utf-8') as file:
            json.dump(conversation_with_metadata, file, indent=2, ensure_ascii=False)
        
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
        summary = {
            'total_conversations': len(conversations),
            'processed_successfully': processed_count,
            'skipped_due_to_errors': skipped_count,
            'total_messages': total_messages,
            'output_directory': str(self.output_dir)
        }
        
        print("\nProcessing completed!")
        print(f"Successfully processed: {processed_count} conversations")
        print(f"Total messages: {total_messages}")
        print(f"Output directory: {self.output_dir}")
        
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
        
        # Optionally save processing summary
        summary_path = processor.output_dir / "processing_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        print(f"Processing summary saved to: {summary_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()