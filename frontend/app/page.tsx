// frontend/app/page.tsx
"use client";

import { useState, useEffect, useRef, FormEvent } from "react";
// We no longer need react-player
// import ReactPlayer from 'react-player';

// --- Types ---
type Message = {
  role: "user" | "agent";
  text: string;
  audioUrl?: string;
  timestamps?: string[];
};

// --- YouTube Player State ---
// This will hold the official YouTube Player object
const ytPlayer: any = null;

// --- SVG Icon Components (Unchanged) ---
const UserIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className="w-6 h-6 text-gray-400"
  >
    <path
      fillRule="evenodd"
      d="M7.5 6a4.5 4.5 0 1 1 9 0 4.5 4.5 0 0 1-9 0ZM3.751 20.105a8.25 8.25 0 0 1 16.498 0 .75.75 0 0 1-.437.695A18.683 18.683 0 0 1 12 22.5c-2.786 0-5.433-.608-7.812-1.7a.75.75 0 0 1-.437-.695Z"
      clipRule="evenodd"
    />
  </svg>
);
const AgentIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className="w-6 h-6 text-blue-400"
  >
    <path
      fillRule="evenodd"
      d="M15.75 1.5a6.75 6.75 0 0 0-6.651 7.906c.067.39-.036.784-.278 1.087C6.64 12.983 6 14.63 6 16.5V19.5a.75.75 0 0 0 .75.75h10.5a.75.75 0 0 0 .75-.75v-3c0-1.87-.64-3.517-1.829-4.992a2.454 2.454 0 0 1-.278-1.087A6.75 6.75 0 0 0 15.75 1.5Zm-3 0a.75.75 0 0 1 .75.75V3a.75.75 0 0 1-1.5 0V2.25a.75.75 0 0 1 .75-.75Zm0 13.5a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"
      clipRule="evenodd"
    />
  </svg>
);
const SendIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className="w-5 h-5"
  >
    <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.98.75.75 0 0 0 0-1.298A60.519 60.519 0 0 0 3.478 2.404Z" />
  </svg>
);

// --- Main App Component ---
export default function Home() {
  // --- State Variables ---
  const [videoUrl, setVideoUrl] = useState<string>("");
  const [currentVideoId, setCurrentVideoId] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [videoStatus, setVideoStatus] = useState<string>("idle");
  const [statusMessage, setStatusMessage] = useState<string>("");

  const [messages, setMessages] = useState<Message[]>([]);
  const [currentQuery, setCurrentQuery] = useState<string>("");
  const [isChatLoading, setIsChatLoading] = useState<boolean>(false);

  // Ref for scrolling the chat area
  const chatEndRef = useRef<HTMLDivElement>(null);
  // Ref to store the player object
  const playerRef = useRef<any>(null);

  // --- YouTube API Loading ---
  useEffect(() => {
    // Check if script is already loaded
    if (!window.YT) {
      const tag = document.createElement("script");
      tag.src = "https://www.youtube.com/iframe_api";
      document.head.appendChild(tag);

      // This global function is CALLED BY THE YOUTUBE SCRIPT
      (window as any).onYouTubeIframeAPIReady = () => {
        console.log("YouTube IFrame API Ready");
        // We don't create the player here, we do it in the handleVideoUpload
      };
    }
  }, []); // Run only once on component mount

  // --- F1.3: Client-side logic for video upload status (Unchanged) ---
  useEffect(() => {
    if (!jobId || videoStatus === "completed" || videoStatus === "failed") {
      return;
    }
    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/video-status/${jobId}`);
        if (!res.ok) throw new Error(`Polling failed: ${res.statusText}`);
        const data = await res.json();
        setVideoStatus(data.status);
        if (data.status === "completed") {
          setStatusMessage("Video processed. Ready for questions!");
          setMessages((prev) => [
            {
              role: "agent",
              text: "Video processed! You can now ask questions about it.",
            },
          ]);
          clearInterval(pollInterval);
        } else if (data.status === "failed") {
          setStatusMessage(
            `Processing failed: ${data.message || "Unknown error"}`
          );
          clearInterval(pollInterval);
        } else {
          setStatusMessage(`Processing... (Status: ${data.status})`);
        }
      } catch (error: any) {
        console.error("Polling error:", error);
        setStatusMessage(
          `Error polling status: ${error.message}. Please refresh.`
        );
        setVideoStatus("failed");
        clearInterval(pollInterval);
      }
    }, 2500);
    return () => clearInterval(pollInterval);
  }, [jobId, videoStatus]);

  // --- Auto-scroll chat (Unchanged) ---
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isChatLoading]);

  // --- YouTube Video ID Parser ---
  function extractVideoId(url: string): string | null {
    // Regex for youtu.be/VIDEO_ID or youtube.com/watch?v=VIDEO_ID
    const regex =
      /(?:https?:\/\/)?(?:www\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})/;
    const match = url.match(regex);
    return match ? match[1] : null;
  }

  // --- F1.1 & F1.2: Handle Video URL Submission ---
  const handleVideoUpload = async (e: FormEvent) => {
    e.preventDefault();
    if (!videoUrl) return;

    // Reset state
    setMessages([]);
    setJobId(null);
    setCurrentVideoId(null);

    // Destroy previous player if it exists
    if (playerRef.current) {
      playerRef.current.destroy();
      playerRef.current = null;
    }

    // Try to get video ID for the player
    const videoId = extractVideoId(videoUrl);
    if (videoId && (window as any).YT && (window as any).YT.Player) {
      setCurrentVideoId(videoId); // This will trigger the player to be created
      // We create the player using a useEffect hook that watches currentVideoId
    } else {
      // It's not a YouTube URL, maybe a direct MP4?
      // For now, we'll just log this. The official IFrame API only supports YouTube.
      console.log(
        "Not a YouTube URL or API not ready, player will not be loaded."
      );
      // We can still process it, though.
    }

    setVideoStatus("pending");
    setStatusMessage("Submitting video...");

    try {
      const res = await fetch("/api/upload-video-url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ video_url: videoUrl }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `Error: ${res.statusText}`);
      }

      const data = await res.json();
      setJobId(data.job_id);
      setVideoStatus(data.status);
      setStatusMessage("Processing video... this may take several minutes.");
    } catch (error: any) {
      console.error("Upload error:", error);
      setStatusMessage(`Failed to submit video: ${error.message}`);
      setVideoStatus("failed");
    }
  };

  // --- This effect creates the YouTube player when the videoId is set ---
  useEffect(() => {
    if (currentVideoId && (window as any).YT && (window as any).YT.Player) {
      if (playerRef.current) {
        playerRef.current.destroy(); // Destroy old one first
      }
      playerRef.current = new (window as any).YT.Player("youtube-player-div", {
        videoId: currentVideoId,
        width: "100%",
        height: "100%",
        playerVars: {
          playsinline: 1,
          origin: window.location.origin, // Important for security
        },
        events: {
          onReady: () => console.log("YouTube Player is ready."),
        },
      });
    }
  }, [currentVideoId]); // This hook runs when currentVideoId changes

  // --- F4.1: Handle Chat Query Submission (Unchanged) ---
  const handleChatSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!currentQuery || !jobId || videoStatus !== "completed" || isChatLoading)
      return;
    const userMessage: Message = { role: "user", text: currentQuery };
    setMessages((prev) => [...prev, userMessage]);
    setCurrentQuery("");
    setIsChatLoading(true);
    try {
      const res = await fetch("/api/query-video", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId, query: currentQuery }),
      });
      if (!res.ok) {
        let errorMsg = `Error: ${res.statusText}`;
        try {
          const errorData = await res.json();
          errorMsg = errorData.detail || errorMsg;
        } catch (jsonError) {
          const errorText = await res.text();
          console.error("Server Error Response:", errorText);
          errorMsg = `Error ${res.status}: ${res.statusText}`;
        }
        throw new Error(errorMsg);
      }
      const data = await res.json();
      const fullAudioUrl = `http://localhost:8000${data.audio_url}`;
      const agentMessage: Message = {
        role: "agent",
        text: data.explanation_text,
        audioUrl: fullAudioUrl,
        timestamps: data.referenced_timestamps,
      };
      setMessages((prev) => [...prev, agentMessage]);
    } catch (error: any) {
      console.error("Query error:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          text: `Sorry, I encountered an error: ${error.message}`,
        },
      ]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // --- F6.5: Handle Timestamp Clicks (FIXED!) ---
  const handleTimestampClick = (timestamp: string) => {
    // We now check our ref for the official player object
    const player = playerRef.current;

    if (player && typeof player.seekTo === "function") {
      const parts = timestamp.split(":").map(Number);
      let seconds = 0;
      if (parts.length === 3)
        seconds = parts[0] * 3600 + parts[1] * 60 + parts[2];
      else if (parts.length === 2) seconds = parts[0] * 60 + parts[1];

      // Call the official IFrame API function
      player.seekTo(seconds, true); // true = allowSeekAhead

      if (typeof player.playVideo === "function") {
        player.playVideo();
      }
    } else {
      console.error(
        "YouTube player ref not ready or seekTo method not available."
      );
    }
  };

  const isChatReady = videoStatus === "completed" && !isChatLoading;

  // --- F6.1: Main Web Application Layout (Unchanged UI) ---
  return (
    <main className="flex h-screen w-full bg-gray-900 text-gray-100">
      {/* --- Sidebar --- */}
      <section className="w-96 flex-shrink-0 bg-gray-950 flex flex-col border-r border-gray-700/50">
        <div className="p-4 border-b border-gray-700/50">
          <h1 className="text-xl font-semibold">VidExplainAgent</h1>
          <p className="text-sm text-gray-400">
            Accessible STEM Video Explanations
          </p>
        </div>

        {/* Video Upload */}
        <form onSubmit={handleVideoUpload} className="p-4 space-y-3">
          <label
            htmlFor="video-url"
            className="block text-sm font-medium text-gray-300"
          >
            Video URL (MP4 or YouTube)
          </label>
          <input
            id="video-url"
            type="text"
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
            placeholder="https://..."
            className="block w-full rounded-md border-gray-600 bg-gray-800 p-2 shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-sm"
          />
          <button
            type="submit"
            disabled={
              !videoUrl ||
              (!!jobId &&
                videoStatus !== "completed" &&
                videoStatus !== "failed")
            }
            className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-gray-950 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {jobId && videoStatus !== "completed" && videoStatus !== "failed"
              ? "Processing..."
              : "Process Video"}
          </button>
          {statusMessage && (
            <p
              aria-live="polite"
              className="mt-2 text-sm text-gray-400 font-medium"
            >
              {statusMessage}
            </p>
          )}
        </form>

        {/* Video Player Area */}
        <div className="flex-grow p-4 mt-auto">
          <div className="aspect-video w-full">
            {/* This div is what the YouTube API will replace */}
            <div
              id="youtube-player-div"
              className="w-full h-full bg-black rounded-lg shadow-lg flex items-center justify-center text-gray-500 text-sm"
            >
              {currentVideoId
                ? "Loading player..."
                : "YouTube player will appear here"}
            </div>
          </div>
        </div>
      </section>

      {/* --- Main Chat Area (Unchanged UI) --- */}
      <section className="flex-1 flex flex-col bg-gray-900">
        {/* Chat Messages */}
        <div className="flex-grow overflow-y-auto">
          <div className="max-w-3xl mx-auto py-6 px-4 space-y-8">
            {messages.map((msg, index) => (
              <div key={index} className="flex items-start gap-4">
                <div
                  className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    msg.role === "agent" ? "bg-gray-700" : "bg-blue-700"
                  }`}
                >
                  {msg.role === "user" ? <UserIcon /> : <AgentIcon />}
                </div>
                <div
                  className={`flex-1 ${
                    msg.role === "agent"
                      ? "bg-gray-700/80 rounded-lg p-4 shadow"
                      : "pt-1"
                  }`}
                >
                  <p className="text-gray-100 whitespace-pre-wrap leading-relaxed">
                    {msg.text}
                  </p>
                  {msg.audioUrl && (
                    <audio
                      controls
                      src={msg.audioUrl}
                      className="mt-3 w-full max-w-sm rounded"
                    >
                      Your browser does not support the audio element.
                    </audio>
                  )}
                  {msg.timestamps && msg.timestamps.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2 items-center">
                      <span className="text-xs text-gray-400 font-medium">
                        Jump to:
                      </span>
                      {msg.timestamps.map((ts) => (
                        <button
                          key={ts}
                          onClick={() => handleTimestampClick(ts)}
                          className="rounded-full bg-gray-600 px-2.5 py-1 text-xs text-white hover:bg-gray-500 transition-colors duration-150 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:ring-offset-1 focus:ring-offset-gray-700"
                        >
                          {ts}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isChatLoading && (
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center animate-pulse">
                  <AgentIcon />
                </div>
                <div className="flex-1 bg-gray-700/80 rounded-lg p-4 shadow">
                  <div className="h-4 bg-gray-600 rounded w-1/4 animate-pulse"></div>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>
        </div>

        {/* Chat Input Bar (Unchanged UI) */}
        <div className="w-full max-w-3xl mx-auto p-4 border-t border-gray-700/50">
          <form
            onSubmit={handleChatSubmit}
            className="relative flex items-center"
          >
            <label htmlFor="chat-input" className="sr-only">
              Ask a question
            </label>
            <input
              id="chat-input"
              type="text"
              value={currentQuery}
              onChange={(e) => setCurrentQuery(e.target.value)}
              disabled={!isChatReady}
              placeholder={
                isChatReady
                  ? "Ask a question about the video..."
                  : "Please process a video first."
              }
              className="flex-grow rounded-lg border-gray-600 bg-gray-700 p-3 pr-12 shadow-sm text-gray-100 placeholder-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:opacity-60"
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleChatSubmit(e);
                }
              }}
            />
            <button
              type="submit"
              disabled={!isChatReady || !currentQuery.trim()}
              aria-label="Send message"
              className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-gray-400 bg-gray-600 hover:bg-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50 transition-colors duration-150"
            >
              <SendIcon />
            </button>
          </form>
        </div>
      </section>
    </main>
  );
}
