/**
 * H6 — Streaming Generation UI
 *
 * EventSource-based client for the SSE streaming regeneration endpoint.
 * Provides a typed event model and a clean callback-driven API so components
 * can display live section-by-section progress without polling.
 *
 * Usage:
 *   const source = streamRegenerate(sessionId, {
 *     onStart: (total) => setTotalSections(total),
 *     onSectionComplete: (id, title) => addCompletedSection(id, title),
 *     onDone: (sid) => refetchSession(sid),
 *     onError: (msg) => showError(msg),
 *   });
 *   // To cancel: source.close();
 */

import { useState, useRef, useCallback } from "react";

import { env } from "../config/env";

// ------------------------------------------------------------------ //
// Event payload types                                                  //
// ------------------------------------------------------------------ //

export type StreamStartEvent = {
  event: "start";
  session_id: string;
  total_sections: number;
};

export type StreamSectionCompleteEvent = {
  event: "section_complete";
  section_id: string;
  title: string;
};

export type StreamSectionErrorEvent = {
  event: "section_error";
  section_id: string;
  error: string;
};

export type StreamDoneEvent = {
  event: "done";
  session_id: string;
};

export type StreamErrorEvent = {
  event: "error";
  message: string;
};

export type StreamEvent =
  | StreamStartEvent
  | StreamSectionCompleteEvent
  | StreamSectionErrorEvent
  | StreamDoneEvent
  | StreamErrorEvent;

// ------------------------------------------------------------------ //
// Callback interface                                                   //
// ------------------------------------------------------------------ //

export type StreamRegenerateCallbacks = {
  /** Called once when the server acknowledges the stream start. */
  onStart?: (totalSections: number, sessionId: string) => void;

  /** Called each time a section finishes generating. */
  onSectionComplete?: (sectionId: string, title: string) => void;

  /** Called when a single section fails (stream continues for others). */
  onSectionError?: (sectionId: string, error: string) => void;

  /** Called once when all sections, metadata, and FAQs are done.
   *  Fetch the updated session via GET /v1/review/session/{sessionId}. */
  onDone?: (sessionId: string) => void;

  /** Called on fatal stream errors (connection lost, server error). */
  onError?: (message: string) => void;
};

// ------------------------------------------------------------------ //
// Public API                                                           //
// ------------------------------------------------------------------ //

/**
 * Open an SSE stream to regenerate all editorial sections for an existing
 * review session.  Returns the underlying EventSource so the caller can
 * close it early if needed (e.g. component unmount).
 *
 * @param sessionId - The review session to regenerate
 * @param callbacks - Lifecycle hooks called as events arrive
 * @param persistSession - Whether the backend should save the updated session
 * @returns The EventSource instance (close it on unmount)
 */
export function streamRegenerate(
  sessionId: string,
  callbacks: StreamRegenerateCallbacks,
  persistSession = true,
): EventSource {
  const params = new URLSearchParams({ persist_session: String(persistSession) });
  const url = `${env.apiBaseUrl}/v1/review/session/${encodeURIComponent(sessionId)}/stream-regenerate?${params}`;

  const source = new EventSource(url);

  source.onmessage = (rawEvent: MessageEvent) => {
    let parsed: StreamEvent;
    try {
      parsed = JSON.parse(rawEvent.data as string) as StreamEvent;
    } catch {
      return; // ignore malformed frames
    }

    switch (parsed.event) {
      case "start":
        callbacks.onStart?.(parsed.total_sections, parsed.session_id);
        break;

      case "section_complete":
        callbacks.onSectionComplete?.(parsed.section_id, parsed.title);
        break;

      case "section_error":
        callbacks.onSectionError?.(parsed.section_id, parsed.error);
        break;

      case "done":
        callbacks.onDone?.(parsed.session_id);
        source.close();
        break;

      case "error":
        callbacks.onError?.(parsed.message);
        source.close();
        break;
    }
  };

  source.onerror = () => {
    callbacks.onError?.("Lost connection to generation stream. Please try again.");
    source.close();
  };

  return source;
}

// ------------------------------------------------------------------ //
// React hook                                                           //
// ------------------------------------------------------------------ //

/**
 * React hook for streaming regeneration progress.
 *
 * Automatically closes the EventSource on component unmount.
 *
 * @example
 * const { isStreaming, completedSections, totalSections, startStream } =
 *   useStreamRegenerate(sessionId, { onDone: refetchSession });
 */

export type UseStreamRegenerateState = {
  isStreaming: boolean;
  completedSections: string[];
  failedSections: string[];
  totalSections: number;
  error: string | null;
};

export type UseStreamRegenerateReturn = UseStreamRegenerateState & {
  startStream: () => void;
  cancelStream: () => void;
};

export function useStreamRegenerate(
  sessionId: string,
  callbacks?: Pick<StreamRegenerateCallbacks, "onDone" | "onError">,
  persistSession = true,
): UseStreamRegenerateReturn {
  const [state, setState] = useState<UseStreamRegenerateState>({
    isStreaming: false,
    completedSections: [],
    failedSections: [],
    totalSections: 0,
    error: null,
  });

  const sourceRef = useRef<EventSource | null>(null);

  const cancelStream = useCallback(() => {
    sourceRef.current?.close();
    sourceRef.current = null;
    setState((prev) => ({ ...prev, isStreaming: false }));
  }, []);

  const startStream = useCallback(() => {
    // Close any previous stream
    sourceRef.current?.close();

    setState({
      isStreaming: true,
      completedSections: [],
      failedSections: [],
      totalSections: 0,
      error: null,
    });

    const source = streamRegenerate(
      sessionId,
      {
        onStart: (total) => {
          setState((prev) => ({ ...prev, totalSections: total }));
        },
        onSectionComplete: (sectionId) => {
          setState((prev) => ({
            ...prev,
            completedSections: [...prev.completedSections, sectionId],
          }));
        },
        onSectionError: (sectionId) => {
          setState((prev) => ({
            ...prev,
            failedSections: [...prev.failedSections, sectionId],
          }));
        },
        onDone: (sid) => {
          setState((prev) => ({ ...prev, isStreaming: false }));
          callbacks?.onDone?.(sid);
        },
        onError: (message) => {
          setState((prev) => ({ ...prev, isStreaming: false, error: message }));
          callbacks?.onError?.(message);
        },
      },
      persistSession,
    );

    sourceRef.current = source;
  }, [sessionId, persistSession, callbacks]);

  return { ...state, startStream, cancelStream };
}
