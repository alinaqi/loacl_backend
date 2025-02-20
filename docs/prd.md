# LOACL: Lightweight OpenAI Assistants ChatBot Library

## Overview
LOACL is a lightweight, embeddable, and fully customizable chatbot library built with React. It is designed to integrate seamlessly with the OpenAI Assistants API by simply providing an assistant ID. LOACL is optimized for third-party websites, offering a standardized and dynamic conversational experience—complete with guided starting questions and auto-generated follow-up queries based on the last chatbot response.

## Objectives
- **Plug-and-Play Integration:**
  Initialize the chatbot with a single parameter (assistant ID) and be ready for embedding.
- **Embeddability & Modularity:**
  Provide a self-contained React component that can be easily integrated into any website.
- **Customizable UI & Theming:**
  Offer a fully customizable interface with a lightweight theming system built on React’s Context API and Tailwind CSS.
- **Dynamic Conversation Flow:**
  Support guided starting questions and intelligent, auto-defined follow-up questions based on user interaction.
- **Mobile-Friendly Design:**
  Ensure full responsiveness for seamless usage on mobile devices, including optimized touch interactions and adaptive layouts.
- **Voice Support:**
  Provide built-in voice input and output functionality using Web Speech API or an alternative speech-to-text and text-to-speech solution.
- **Developer Flexibility:**
  Expose event hooks, API callbacks, and customization options to allow deep integration and tailored behavior.
- **Supabase Integration:**
  Utilize Supabase as the database layer for storing conversations, user preferences, and configurations.
- **Environment Variables:**
  Allow users to configure OpenAI assistant ID and API key via environment variables for secure access.
- **Streaming Support:**
  Enable streaming of chatbot responses by default to improve real-time interaction experience.
- **File Upload Support:**
  Provide functionality for users to upload files that can be processed by the assistant.
- **Assistant API Response Review & Follow-Up Suggestions:**
  Analyze responses from the OpenAI Assistants API and dynamically generate suggested follow-up questions for the user.

## Target Audience
- **Web Developers** seeking to integrate an AI-powered chatbot quickly and effortlessly.
- **Third-Party Website Owners** who require a customizable chat solution that matches their brand identity.
- **Agencies & Startups** looking for a scalable, modular solution that can be extended with custom features over time.

## Core Features
1. **Assistant ID Integration:**
   - The chatbot initializes by accepting an assistant ID, which configures the integration with the OpenAI Assistants API.

2. **Embeddable Component:**
   - A self-contained React component that can be embedded directly or via iframes in third-party websites.

3. **Customizable UI & Theming:**
   - **Theming Provider:**
     - Build a lightweight, flexible theming system using React Context API and Tailwind CSS.
     - Provide a central configuration for design tokens (colors, fonts, spacing) that all components reference.
   - **Styling Overrides:**
     - Allow developers to pass custom class names or override component defaults via props.

4. **Dynamic Conversation Flow:**
   - **Guided Starting Questions:**
     - Pre-configured prompts to help users begin interacting with the chatbot.
   - **Auto-Defined Follow-Up Questions:**
     - Based on the last message from the chatbot, dynamically generate a set of follow-up queries or suggestions.
   - **Branching Logic:**
     - Support advanced conversation flows that can branch depending on user responses.

5. **Session Management & History:**
   - Track conversation history and optionally persist session data via Supabase or an external API.
   - Provide easy restoration of previous sessions.

6. **API & Event Hooks:**
   - Expose callbacks (e.g., `onMessageSend`, `onResponseReceived`, `onError`) to allow custom handling of chat events.
   - Support middleware for pre- and post-processing of messages.

7. **Analytics & Logging:**
   - Built-in hooks for integrating with analytics platforms and logging interactions.
   - Provide error handling and debugging tools to assist in monitoring performance.

8. **Accessibility & Internationalization:**
   - Ensure components meet accessibility standards (keyboard navigation, ARIA labels).
   - Offer support for internationalization (i18n) so the chatbot can be easily localized.

9. **Mobile-Friendly Design:**
   - Fully responsive layout with adaptive UI scaling for mobile, tablet, and desktop.
   - Optimized touch interactions and mobile-friendly animations.
   - Configurable viewport adjustments for better mobile usability.

10. **Voice Support:**
   - **Speech-to-Text:**
     - Use Web Speech API or an alternative voice recognition engine to allow users to speak instead of typing.
   - **Text-to-Speech:**
     - Provide spoken responses using a synthesized voice engine.
   - **Customizable Voice Options:**
     - Allow developers to modify voice tone, speed, and other attributes.
   - **Fallback to Text:**
     - Ensure smooth degradation when voice support is unavailable.

11. **File Upload Support:**
   - Enable users to upload files to be processed by the chatbot or stored in Supabase.
   - Allow OpenAI Assistants to analyze and respond based on uploaded content.

12. **Assistant API Response Review & Follow-Up Suggestions:**
   - Review OpenAI API responses and generate relevant follow-up questions.
   - Improve engagement by predicting the next set of user queries based on context.

## Technical Stack
- **Frontend:**
  - React for building the interactive UI.
  - Tailwind CSS for utility-first styling.
- **Theming:**
  - A custom ThemeProvider using React’s Context API to expose theme variables (potentially tied to Tailwind’s configuration).
- **API Integration:**
  - OpenAI Assistants API integration via a dynamic assistant ID.
- **State Management:**
  - React Hooks (useState, useContext) for managing session data and dynamic conversation state.
- **Database Layer:**
  - Supabase for storing user preferences, conversation history, and assistant configurations.
- **Voice Handling:**
  - Web Speech API or third-party voice recognition APIs.
- **Embedding:**
  - Designed to be integrated via module import or iframe with clear documentation.

## Non-Functional Requirements
- **Performance:**
  - Optimized for fast load times and minimal rendering overhead.
- **Security:**
  - Secure handling of API keys (with guidance for safe storage) and data integrity.
- **Scalability:**
  - Modular architecture to allow future enhancements and plugins.
- **Documentation:**
  - Comprehensive guides, examples, and API documentation for seamless developer integration.
