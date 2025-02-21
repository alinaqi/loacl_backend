Streaming
Beta
Stream the result of executing a Run or resuming a Run after submitting tool outputs. You can stream events from the Create Thread and Run, Create Run, and Submit Tool Outputs endpoints by passing "stream": true. The response will be a Server-Sent events stream. Our Node and Python SDKs provide helpful utilities to make streaming easy. Reference the Assistants API quickstart to learn more.

The message delta object
Beta
Represents a message delta i.e. any changed fields on a message during streaming.

id
string

The identifier of the message, which can be referenced in API endpoints.

object
string

The object type, which is always thread.message.delta.

delta
object

The delta containing the fields that have changed on the Message.


Show properties
OBJECT The message delta object
{
  "id": "msg_123",
  "object": "thread.message.delta",
  "delta": {
    "content": [
      {
        "index": 0,
        "type": "text",
        "text": { "value": "Hello", "annotations": [] }
      }
    ]
  }
}
The run step delta object
Beta
Represents a run step delta i.e. any changed fields on a run step during streaming.

id
string

The identifier of the run step, which can be referenced in API endpoints.

object
string

The object type, which is always thread.run.step.delta.

delta
object

The delta containing the fields that have changed on the run step.


Show properties
OBJECT The run step delta object
{
  "id": "step_123",
  "object": "thread.run.step.delta",
  "delta": {
    "step_details": {
      "type": "tool_calls",
      "tool_calls": [
        {
          "index": 0,
          "id": "call_123",
          "type": "code_interpreter",
          "code_interpreter": { "input": "", "outputs": [] }
        }
      ]
    }
  }
}
Assistant stream events
Beta
Represents an event emitted when streaming a Run.

Each event in a server-sent events stream has an event and data property:

event: thread.created
data: {"id": "thread_123", "object": "thread", ...}
We emit events whenever a new object is created, transitions to a new state, or is being streamed in parts (deltas). For example, we emit thread.run.created when a new run is created, thread.run.completed when a run completes, and so on. When an Assistant chooses to create a message during a run, we emit a thread.message.created event, a thread.message.in_progress event, many thread.message.delta events, and finally a thread.message.completed event.

We may add additional events over time, so we recommend handling unknown events gracefully in your code. See the Assistants API quickstart to learn how to integrate the Assistants API with streaming.

thread.created
data is a thread

Occurs when a new thread is created.

thread.run.created
data is a run

Occurs when a new run is created.

thread.run.queued
data is a run

Occurs when a run moves to a queued status.

thread.run.in_progress
data is a run

Occurs when a run moves to an in_progress status.

thread.run.requires_action
data is a run

Occurs when a run moves to a requires_action status.

thread.run.completed
data is a run

Occurs when a run is completed.

thread.run.incomplete
data is a run

Occurs when a run ends with status incomplete.

thread.run.failed
data is a run

Occurs when a run fails.

thread.run.cancelling
data is a run

Occurs when a run moves to a cancelling status.

thread.run.cancelled
data is a run

Occurs when a run is cancelled.

thread.run.expired
data is a run

Occurs when a run expires.

thread.run.step.created
data is a run step

Occurs when a run step is created.

thread.run.step.in_progress
data is a run step

Occurs when a run step moves to an in_progress state.

thread.run.step.delta
data is a run step delta

Occurs when parts of a run step are being streamed.

thread.run.step.completed
data is a run step

Occurs when a run step is completed.

thread.run.step.failed
data is a run step

Occurs when a run step fails.

thread.run.step.cancelled
data is a run step

Occurs when a run step is cancelled.

thread.run.step.expired
data is a run step

Occurs when a run step expires.

thread.message.created
data is a message

Occurs when a message is created.

thread.message.in_progress
data is a message

Occurs when a message moves to an in_progress state.

thread.message.delta
data is a message delta

Occurs when parts of a Message are being streamed.

thread.message.completed
data is a message

Occurs when a message is completed.

thread.message.incomplete
data is a message

Occurs when a message ends before it is completed.

error
data is an error

Occurs when an error occurs. This can happen due to an internal server error or a timeout.


Occurs when a stream ends.
