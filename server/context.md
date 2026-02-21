AgriAssist – Express Backend
============================

AI Agent Context File (Prototype – Full Updated Version)
--------------------------------------------------------

1\. System Overview
===================

AgriAssist is a voice-first AI agriculture platform.

The system is divided into two major services:

*   **Express.js Backend** → Governance Layer (See Section 17 for API list)
    
*   **FastAPI Service** → AI Intelligence Layer
    

PostgreSQL is the single source of truth.

Object storage holds heavy media (audio, image, documents).

2\. Architectural Separation
============================

### Express Backend (Law Authority)

Responsible for:

*   Identity
    
*   Authorization
    
*   Land & Field ownership
    
*   Crop lifecycle
    
*   Conversation retrieval
    
*   Audit logging
    

Express does NOT:

*   Run AI models
    
*   Stream responses
    
*   Store raw media
    
*   Generate AI output
    

### FastAPI (AI Compute)

Responsible for:

*   Text & Voice AI processing
    
*   Streaming responses
    
*   Storing AI chat messages
    
*   Storing image/audio paths
    
*   Writing metadata into Postgres
    

FastAPI does NOT:

*   Enforce ownership
    
*   Modify governance tables
    
*   Manage user roles
    

3\. Data Ownership Model
========================

Postgres stores:

*   User identity
    
*   Land & field structure
    
*   Crop assignments
    
*   AI conversation metadata
    
*   AI message metadata
    
*   Audit logs
    

Object storage stores:

*   Images
    
*   Voice recordings
    
*   Documents
    

Postgres never stores binary data.

4\. Domain Model (Prototype Scope)
==================================

The system supports:

*   One Land per Farmer
    
*   Multiple Fields per Land
    
*   Multiple CropAssignments per Field (over time)
    
*   AI conversations per user / field / crop cycle
    

5\. Core Domain Relationships
=============================

User→ Farmer→ Land (single)→ Field (multiple)→ CropAssignment (multiple over time)→ Crop (reference)

Important:

A Field does not permanently own a Crop.It hosts multiple CropAssignments across seasons.

CropAssignment represents:

*   One crop
    
*   In one field
    
*   During one time period
    

6\. Authentication Model
========================

User logs in via OTP.

Express issues short-lived JWT containing:

*   userId
    
*   role
    
*   interface
    
*   expiry
    

FastAPI validates JWT signature only.

Express enforces ownership.

7\. Interface Awareness
=======================

Each user has an interface type:

*   HELPLINE
    
*   SOFTWARE
    
*   SOFTWARE\_WITH\_HARDWARE
    

Interface determines:

*   Allowed features
    
*   Media permissions
    
*   AI behavior limits
    

8\. AI Conversation Model (Industry-Grade Prototype)
====================================================

FastAPI inserts chat data.Express retrieves chat history.

AIConversation
--------------

Tracks a logical session.

Fields:

*   id
    
*   userId
    
*   fieldId
    
*   cropAssignmentId
    
*   status
    
*   startedAt
    
*   endedAt
    

Purpose:

*   Groups messages
    
*   Maintains farming context
    
*   Enables scoped retrieval
    

AIChatMessage
-------------

Single unified message table.

Supports:

*   Text
    
*   Image
    
*   Document
    
*   Voice
    

Fields:

*   id
    
*   conversationId
    
*   sender (USER / AI / SYSTEM)
    
*   messageType (TEXT / IMAGE / DOCUMENT / VOICE)
    
*   textContent
    
*   filePath
    
*   fileName
    
*   mimeType
    
*   fileSizeBytes
    
*   createdAt
    

All media stored in object storage.Only file paths saved in database.

9\. Chat Flow
=============

### New Message Flow

1.  Client sends message to FastAPI
    
2.  FastAPI:
    
    *   Stores media (if any)
        
    *   Inserts AIChatMessage
        
    *   Streams response
        
3.  Express retrieves conversation later via REST
    

### Retrieval Flow

1.  Client requests history via Express
    
2.  Express:
    
    *   Validates JWT
        
    *   Verifies conversation ownership
        
    *   Retrieves messages ordered by createdAt
        
    *   Returns paginated results
        

10. AI Interaction Model (Folder & Messages)
========================================

The chat system is structured as a hierarchical relationship between sessions and their content.

### 10.1 AIConversation (The Folder)
Think of `AIConversation` as a WhatsApp chat thread or a file folder. It acts as a session container that groups messages together.
*   **Purpose**: Prevents message mixing and provides farming context.
*   **Links**: Links the interaction to a specific **User**, **Field**, and **CropAssignment**.
*   **Tracking**: Records `startedAt`, `endedAt`, and session `status` (ACTIVE/CLOSED).

### 10.2 AIChatMessage (The Messages Inside)
Think of `AIChatMessage` as the individual lines of text or media inside the thread. 
*   **Content**: Stores text snippets, image paths, voice notes, or documents.
*   **Metadata**: Tracks the `sender` (USER/AI), `messageType`, and `createdAt` timestamp.

*   **Relationship**: One `AIConversation` (Folder) has many `AIChatMessage` entries (Messages).

11\. Prototype Prisma Schema Context
====================================

The schema includes:

*   User
    
*   Farmer
    
*   Land (single per farmer)
    
*   Field
    
*   Crop
    
*   CropAssignment
    
*   AIConversation
    
*   AIChatMessage
    
*   AuditLog
    

Relationships are strictly enforced.

AIConversation links to:

*   User
    
*   Field (optional)
    
*   CropAssignment (optional)
    

AIChatMessage links to:

*   AIConversation
    

11\. Business Rules (Express Enforced)
======================================

*   One ACTIVE CropAssignment per Field
    
*   Farmer accesses only their land
    
*   Conversation must belong to user
    
*   CropAssignment must belong to field
    
*   Interface restrictions applied
    

12\. Performance Rules
======================

*   Paginate chat messages
    
*   Index conversationId + createdAt
    
*   Never load entire chat history
    
*   Never store large media in DB
    
*   Keep Postgres metadata-only
    

13\. What This Backend Must Never Do
====================================

*   Never perform AI reasoning
    
*   Never store raw media
    
*   Never maintain WebSockets
    
*   Never allow FastAPI to control governance
    

14\. System Guarantees
======================

This design ensures:

*   Clean separation of law vs intelligence
    
*   Scalable chat system
    
*   AI-safe storage model
    
*   Governance traceability
    
*   Future extensibility
    

15\. Mental Model
=================

Express governs.FastAPI thinks.Postgres stores truth.Object storage stores weight.

Field hosts crop cycles.Conversations are contextual to farming state.

16. Current Implementation Status
==============================

### Completed Components
*   **Authentication**: OTP-based login via Twilio Verify.
*   **Authorization**: JWT-based Access and Refresh tokens.
*   **Infrastructure**: Prisma ORM with PostgreSQL.
*   **Governance APIs**: CRUD operations for Land, Fields, and Crops with area conversion (Hectares).
*   **Chat Retrieval**: Secure, paginated APIs to fetch conversation history.
*   **Audit Logging**: Integrated system tracking all governance actions in `AuditLog`.
*   **Profile Management**:
    *   **Name Updates**: Seamless editing of user names.
    *   **Secure Mobile Updates**: Two-step verification (Request -> OTP -> Update) for changing phone numbers.
    *   **Automated Token Re-issuance**: New JWTs are issued upon phone number updates to ensure session continuity.
*   **Validation & Error Handling**: Global Zod validation middleware and standardized error responses.
*   **Governance Refinements**: Automated harvest date calculation, field area defaulting, and enhanced location tracking (Lat/Lng/District/State).

17. API Reference (Express Governance Layer)
========================================

### Auth
*   `POST /api/request-otp`: Sends a login/signup code to a phone number.
*   `POST /api/verify-otp`: Verifies code and issues Access/Refresh JWTs.
*   `POST /api/refresh`: Re-issues access token using the refresh cookie.

### User Profile
*   `GET /api/user/profile`: Retrieves the authenticated user's profile details.
*   `PATCH /api/user/profile`: Updates user name or interface settings.
*   `POST /api/user/request-mobile-update`: Sends OTP to a new phone number for verification.
*   `POST /api/user/verify-mobile-update`: Finalizes phone number update and re-issues tokens.

### Governance - Land
*   `POST /api/governance/land`: Registers the primary farm land for a farmer.
*   `GET /api/governance/land`: Retrieves land details and associated fields.
*   `PATCH /api/governance/land`: Updates land boundaries or metadata.

### Governance - Fields
*   `POST /api/governance/field`: Adds a specific field section to the land.
*   `GET /api/governance/field`: Lists all fields and their active crop cycles.
*   `DELETE /api/governance/field/:id`: Removes a field section from the land.

### Governance - Crops & Assignments
*   `GET /api/governance/crops`: Lists available crop types (seeds) and durations.
*   `POST /api/governance/assignment`: Starts a cultivation cycle in a specific field.
*   `PATCH /api/governance/assignment/:id`: Marks a cycle as COMPLETED or FAILED.
*   `GET /api/governance/active-assignments`: Lists current ongoing cultivation cycles.

### AI Conversations (Retrieval)
*   `POST /api/chat/conversations`: Initializes a new session linked to land/crop.
*   `GET /api/chat/conversations`: Retrieves paginated session history for the user.
*   `GET /api/chat/messages/:conversationId`: Fetches sorted messages from a session.
*   `POST /api/chat/conversations/:conversationId/messages`: Appends a user or AI message to history.

18. Roadmap / Future Enhancements
================================

1.  **AI-Driven Harvest Prediction**: Use real-time weather data to adjust calculated harvest dates.
2.  **Notification Engine**: Automated alerts when real-world time exceeds the calculated harvest date.
3.  **Swagger/OpenAPI**: Implement automated API documentation.
4.  **Multi-Farmer Collaboration**: Enable sharing Land access.

19. Prototype Status
====================

This schema and core infrastructure are:

*   **Production-Ready**
*   **Fully Implemented**: All core Governance, Auth, and Chat APIs are live.
*   **Verified**: Logic and area conversion bugs have been resolved.
*   **Documented**: Integrated API reference is available in Section 17.

End of AI Agent Context File.
