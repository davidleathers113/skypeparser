# Skype Export Data Structure Analysis

## Overview

This document provides a comprehensive analysis of the Skype export data structure and how our ETL pipeline processes it. The analysis is based on examining sample data from the `messages.json` file extracted from a Skype export archive.

## Skype Export Data Structure

The Skype export data is stored in a JSON file with the following top-level structure:

```json
{
  "userId": "user-identifier",
  "exportDate": "timestamp",
  "conversations": [
    // Array of conversation objects
  ]
}
```

Each conversation object has this structure:

```json
{
  "id": "conversation-id",
  "displayName": "Conversation Name",
  "version": 1234567890123,
  "properties": {
    // Various conversation properties
    "conversationblocked": false,
    "lastimreceivedtime": "2025-03-01T20:34:52.072Z",
    "consumptionhorizon": "1740569134201;1740573743189;5051999092726992361",
    "conversationstatus": null
  },
  "MessageList": [
    // Array of message objects
  ]
}
```

Each message object has this structure:

```json
{
  "id": "message-id",
  "displayName": "Sender Name",
  "originalarrivaltime": "timestamp",
  "messagetype": "RichText", // or other message types
  "version": 1234567890123,
  "content": "Message content with HTML/XML tags",
  "conversationid": "conversation-id",
  "from": "sender-id",
  "properties": {
    // Various message properties including reactions
    "emotions": [
      {
        "key": "emoji_key",
        "users": [
          {
            "mri": "user-id",
            "time": 1234567890123,
            "value": "1234567890123"
          }
        ]
      }
    ],
    "urlpreviews": "JSON string with URL preview data"
  },
  "amsreferences": null
}
```

## File Format Challenges

### Single-Line JSON Files

Skype export files often come as a single-line JSON file, which presents several challenges:

1. **Parsing Complexity**: Standard JSON pretty-printing tools may fail due to the single-line format and large file size.
2. **Memory Usage**: Loading the entire file into memory can cause out-of-memory errors for large exports.
3. **Debugging Difficulty**: Examining the structure is difficult without proper formatting.

**Solution Approaches**:
- Use streaming JSON parsers like `ijson` for memory-efficient processing
- Implement chunked reading to process portions of the file at a time
- Add the `--skip-raw` flag to avoid saving the raw JSON when processing large files
- Use Python's built-in `json` module with context managers to ensure proper resource cleanup

### ContentExtractor Compatibility Issues

We've identified several issues with the `ContentExtractor` class:

1. **Missing Methods**: The `format_content_with_markup` method may be missing from the `ContentExtractor` class.
2. **Error Handling**: Inadequate error handling when processing message content.
3. **Type Safety**: Lack of type checking when dealing with content that may not be a string.

**Solutions Implemented**:
- Enhanced monkey patching to ensure the `format_content_with_markup` method exists
- Added robust error handling in the content processing functions
- Implemented type checking and conversion to handle non-string content
- Added comprehensive logging for debugging content processing issues

## Data Volume

The sample file contains:
- 1,138 conversations
- One conversation has 6,052 messages
- This indicates a large dataset that requires efficient processing
- The `messages.json` file can be over 100MB in size, often as a single line of JSON

## Message Types

I've identified several message types in the sample data:
- `RichText`: Standard text messages
- `RichText/UriObject`: Messages with images or attachments
- `Poll`: Poll messages
- `ThreadActivity/AddMember`: System messages about adding members

Our codebase has a default configuration for handling these message types:

```json
{
  "message_types": {
    "Event/Call": "***A call started/ended***",
    "Poll": "***Created a poll***",
    "RichText/Media_Album": "***Sent an album of images***",
    "RichText/Media_AudioMsg": "***Sent a voice message***",
    "RichText/Media_CallRecording": "***Sent a call recording***",
    "RichText/Media_Card": "***Sent a media card***",
    "RichText/Media_FlikMsg": "***Sent a moji***",
    "RichText/Media_GenericFile": "***Sent a file***",
    "RichText/Media_Video": "***Sent a video message***",
    "RichText/UriObject": "***Sent a photo***",
    "RichText/ScheduledCallInvite": "***Scheduled a call***",
    "RichText/Location": "***Sent a location***",
    "RichText/Contacts": "***Sent a contact***"
  },
  "default_message_format": "***Sent a {message_type}***"
}
```

## ETL Pipeline Process

Our ETL pipeline processes this data in three phases:

1. **Extraction**: Reads the JSON file from a Skype export archive
2. **Transformation**: Processes the raw data into a structured format
3. **Loading**: Stores the data in a database

### Extraction Process

The extraction phase:
1. Validates the input file (exists, is a valid JSON file)
2. Reads the file content
3. Parses the JSON data
4. Validates the data structure
5. Returns the raw data for transformation

#### Handling Large JSON Files

For large export files, we recommend:
1. Using the `--skip-raw` flag to avoid saving the entire raw JSON to disk
2. Ensuring adequate memory is available for processing
3. Using a step-by-step approach for extremely large files:
   - Extract the tar file to a temporary directory
   - Process the `messages.json` file directly with streaming parsers if needed
   - Clean up temporary files after processing

### Transformation Process

The transformation phase:
1. Validates the raw data structure
2. Processes metadata (user ID, export date)
3. Creates a mapping of user IDs to display names
4. Processes each conversation:
   - Extracts conversation metadata
   - Processes each message:
     - Parses timestamps
     - Handles different message types
     - Cleans message content (removes HTML tags)
   - Sorts messages by timestamp
   - Updates conversation timespan information
5. Saves the transformed data to a file if an output directory is specified

### Message Processing

For each message, the pipeline:
1. Extracts metadata (timestamp, sender, content, type)
2. Parses the timestamp into a datetime object
3. Creates a structured message object
4. Handles special message types using the `type_parser` function
5. Cleans message content using the `content_parser` function
6. Checks if the message has been edited

### Content Parsing

The `content_parser` function:
1. Uses BeautifulSoup to parse HTML/XML content if available
2. Falls back to regex-based tag stripping if BeautifulSoup is not available
3. Formats quoted messages for better readability
4. Replaces straight quotes with curly quotes

#### Content Parsing Challenges

We've identified several challenges with content parsing:

1. **HTML/XML Tags**: Messages often contain complex HTML tags that require careful parsing.
2. **Monkey Patching**: The `format_content_with_markup` method needs to be added to the `ContentExtractor` class.
3. **Type Safety**: Content may not always be a string, requiring type checking and conversion.
4. **Error Handling**: Robust error handling is needed to prevent crashes during parsing.

**Improved Implementation**:
- Enhanced the monkey patching to include better error handling and logging
- Added type checking to ensure content is always processed as a string
- Implemented fallback mechanisms when content formatting fails
- Added comprehensive testing of the patched methods

### Loading Process

The loading phase:
1. Stores the raw data in the `raw_skype_exports` table
2. Stores the transformed data in the clean storage tables:
   - `clean_skype_conversations`
   - `clean_skype_messages`

## Database Structure

The clean storage database has two main tables:

1. `clean_skype_conversations`: Stores conversation metadata
   - `id`: Primary key
   - `conversation_id`: Unique conversation identifier
   - `display_name`: Conversation name
   - `raw_export_id`: Reference to the raw export
   - `first_message_time`: Timestamp of the first message
   - `last_message_time`: Timestamp of the last message
   - `message_count`: Number of messages in the conversation

2. `clean_skype_messages`: Stores message data
   - `id`: Primary key
   - `message_id`: Unique message identifier
   - `conversation_id`: Reference to the conversation
   - `timestamp`: Message timestamp
   - `sender_id`: Sender identifier
   - `sender_name`: Sender display name
   - `message_type`: Type of message
   - `content`: Cleaned message content
   - `raw_content`: Original message content
   - `is_edited`: Flag indicating if the message was edited

## Special Features

1. **Reactions/Emotions**: Messages can have reactions from users, stored in the `emotions` property
2. **URL Previews**: Links in messages have preview data stored in the `urlpreviews` property
3. **Mentions**: Messages can contain mentions of users with `<at id="user-id">user-name</at>` tags
4. **HTML Content**: Message content can contain HTML tags for formatting, links, etc.
5. **Edited Messages**: Messages that have been edited have a `skypeeditedid` property

## Observations and Recommendations

1. **Data Volume**: The large number of conversations and messages requires efficient processing and storage.
   - **New**: Implement chunked processing for extremely large files
   - **New**: Add support for memory-efficient streaming parsers

2. **Message Types**: The system should handle all message types present in the data, including those not in the default configuration.

3. **Content Formatting**: Message content includes HTML tags, mentions, and links that need proper parsing.
   - **New**: Enhanced error handling for content formatting failures
   - **New**: Improved type safety for non-string content

4. **Timestamp Handling**: The timestamps in the data are in ISO format with timezone information, which our parser handles correctly.

5. **Special Properties**: Messages have properties like reactions ("emotions") that could be extracted for additional insights.

6. **Performance Considerations**: Given the large volume of data, batch processing and efficient database operations are important.
   - **New**: Added the `--skip-raw` flag to avoid saving large raw JSON files
   - **New**: Enhanced memory management for processing large files

7. **Error Handling**: The pipeline should handle edge cases like missing fields, invalid timestamps, and malformed content.
   - **New**: Comprehensive error handling in content processing
   - **New**: Improved logging for debugging issues

8. **Validation**: Thorough validation of the data structure is essential to ensure reliable processing.
   - **New**: Added type checking throughout the processing pipeline

9. **Monkey Patching**: The dependency on monkey patching requires careful implementation and testing.
   - **New**: Enhanced monkey patching with better error handling and logging
   - **New**: Added unit testing for patched methods

## Next Steps

1. **Validate Data Models**: Ensure our data models can accommodate all the fields and properties in the Skype export data.

2. **Enhance Message Type Handling**: Update the message type configuration to handle all types present in the data.

3. **Optimize Performance**: Implement batch processing and other optimizations for handling large datasets.
   - **New**: Consider implementing streaming JSON parsing for very large files
   - **New**: Add incremental processing options for extremely large datasets

4. **Extract Additional Insights**: Consider extracting and storing additional data like reactions and URL previews.

5. **Improve Error Handling**: Enhance error handling to gracefully handle edge cases and malformed data.
   - **New**: Continue refining error handling in content processing
   - **New**: Add more comprehensive recovery mechanisms

6. **Add Comprehensive Logging**: Implement detailed logging to track the processing of each conversation and message.
   - **New**: Expand logging to include performance metrics
   - **New**: Add structured logging for easier analysis

7. **Implement Data Validation**: Add validation checks to ensure the integrity of the processed data.
   - **New**: Add schema validation for processed data
   - **New**: Implement consistency checks between raw and processed data

8. **Reduce Dependency on Monkey Patching**: Consider refactoring the code to reduce or eliminate the need for monkey patching.
   - **New**: Design a more flexible content processing architecture
   - **New**: Implement proper inheritance and composition instead of monkey patching
