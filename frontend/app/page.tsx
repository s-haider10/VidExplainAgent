// pages/index.tsx or app/page.tsx
"use client";

import { useState, useEffect, useRef, FormEvent } from "react";
import Head from "next/head"; // For adding Google Fonts link

// --- Types ---
type Message = {
  role: "user" | "agent";
  text: string;
  audioUrl?: string;
  timestamps?: string[];
};

type VideoSegment = {
  timestamp_start_str: string;
  timestamp_end_str: string;
  transcript_snippet: string;
  visual_description: string;
  key_concepts: string[];
};

// --- Icon Components ---
const UserIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className="w-6 h-6"
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
    className="w-6 h-6"
  >
    <path
      fillRule="evenodd"
      d="M9 4.5a.75.75 0 0 1 .721.544l.813 2.846a3.75 3.75 0 0 0 2.57 2.57l2.846.813a.75.75 0 0 1 0 1.442l-2.846.813a3.75 3.75 0 0 0-2.57 2.57l-.813 2.846a.75.75 0 0 1-1.442 0l-.813-2.846a3.75 3.75 0 0 0-2.57-2.57l-2.846-.813a.75.75 0 0 1 0-1.442l2.846-.813A3.75 3.75 0 0 0 7.466 5.04l.813-2.846A.75.75 0 0 1 9 4.5ZM18 9.75a.75.75 0 0 1 .721.544l.625 2.187a1.5 1.5 0 0 0 1.03 1.03l2.187.625a.75.75 0 0 1 0 1.442l-2.187.625a1.5 1.5 0 0 0-1.03 1.03l-.625 2.187a.75.75 0 0 1-1.442 0l-.625-2.187a1.5 1.5 0 0 0-1.03-1.03l-2.187-.625a.75.75 0 0 1 0-1.442l2.187-.625a1.5 1.5 0 0 0 1.03-1.03l.625-2.187A.75.75 0 0 1 18 9.75Z"
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

const SparklesIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className="w-4 h-4"
  >
    <path
      fillRule="evenodd"
      d="M9 4.5a.75.75 0 0 1 .721.544l.813 2.846a3.75 3.75 0 0 0 2.576 2.576l2.846.813a.75.75 0 0 1 0 1.442l-2.846.813a3.75 3.75 0 0 0-2.576 2.576l-.813 2.846a.75.75 0 0 1-1.442 0l-.813-2.846a3.75 3.75 0 0 0-2.576-2.576l-2.846-.813a.75.75 0 0 1 0-1.442l2.846-.813A3.75 3.75 0 0 0 7.466 7.89l.813-2.846A.75.75 0 0 1 9 4.5ZM18 1.5a.75.75 0 0 1 .728.568l.258 1.036c.236.94.97 1.674 1.91 1.91l1.036.258a.75.75 0 0 1 0 1.456l-1.036.258c-.94.236-1.674.97-1.91 1.91l-.258 1.036a.75.75 0 0 1-1.456 0l-.258-1.036a2.625 2.625 0 0 0-1.91-1.91l-1.036-.258a.75.75 0 0 1 0-1.456l1.036-.258a2.625 2.625 0 0 0 1.91-1.91l.258-1.036A.75.75 0 0 1 18 1.5ZM16.5 15a.75.75 0 0 1 .712.513l.394 1.183c.15.447.5.799.948.948l1.183.395a.75.75 0 0 1 0 1.422l-1.183.395c-.447.15-.799.5-.948.948l-.395 1.183a.75.75 0 0 1-1.422 0l-.395-1.183a1.5 1.5 0 0 0-.948-.948l-1.183-.395a.75.75 0 0 1 0-1.422l1.183-.395c.447-.15.799.5.948.948l.395-1.183A.75.75 0 0 1 16.5 15Z"
      clipRule="evenodd"
    />
  </svg>
);

const PlayIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className="w-6 h-6"
  >
    <path
      fillRule="evenodd"
      d="M4.5 5.653c0-1.427 1.529-2.33 2.779-1.643l11.54 6.347c1.295.712 1.295 2.573 0 3.286L7.28 19.99c-1.25.687-2.779-.217-2.779-1.643V5.653Z"
      clipRule="evenodd"
    />
  </svg>
);

const PauseIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className="w-6 h-6"
  >
    <path
      fillRule="evenodd"
      d="M6.75 5.25a.75.75 0 0 1 .75.75V18a.75.75 0 0 1-1.5 0V6a.75.75 0 0 1 .75-.75Zm6 0a.75.75 0 0 1 .75.75V18a.75.75 0 0 1-1.5 0V6a.75.75 0 0 1 .75-.75Z"
      clipRule="evenodd"
    />
  </svg>
);

const SpeakerWaveIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className="w-5 h-5 text-teal-400"
  >
    <path
      fillRule="evenodd"
      d="M8.25 4.5a.75.75 0 0 1 .75.75v13.5a.75.75 0 0 1-1.5 0V5.25a.75.75 0 0 1 .75-.75Z"
      clipRule="evenodd"
    />
    <path
      fillRule="evenodd"
      d="M12.75 3a.75.75 0 0 1 .75.75v16.5a.75.75 0 0 1-1.5 0V3.75a.75.75 0 0 1 .75-.75Z"
      clipRule="evenodd"
    />
    <path
      fillRule="evenodd"
      d="M17.25 6.75a.75.75 0 0 1 .75.75v9a.75.75 0 0 1-1.5 0v-9a.75.75 0 0 1 .75-.75Z"
      clipRule="evenodd"
    />
    <path
      fillRule="evenodd"
      d="M3.75 9a.75.75 0 0 1 .75.75v4.5a.75.75 0 0 1-1.5 0v-4.5a.75.75 0 0 1 .75-.75Z"
      clipRule="evenodd"
    />
    <path
      fillRule="evenodd"
      d="M21.75 9.75a.75.75 0 0 1 .75.75v3a.75.75 0 0 1-1.5 0v-3a.75.75 0 0 1 .75-.75Z"
      clipRule="evenodd"
    />
  </svg>
);

const LoadingIcon = () => (
  <svg
    className="animate-spin h-5 w-5 text-white"
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
  >
    <circle
      className="opacity-25"
      cx="12"
      cy="12"
      r="10"
      stroke="currentColor"
      strokeWidth="4"
    ></circle>
    <path
      className="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
    ></path>
  </svg>
);

const MicrophoneIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className="w-5 h-5"
  >
    <path d="M8.25 4.5a3.75 3.75 0 1 1 7.5 0v8.25a3.75 3.75 0 1 1-7.5 0V4.5Z" />
    <path d="M6 10.5a.75.75 0 0 1 .75.75v1.5a5.25 5.25 0 1 0 10.5 0v-1.5a.75.75 0 0 1 1.5 0v1.5a6.751 6.751 0 0 1-6 6.709v2.291h3a.75.75 0 0 1 0 1.5h-7.5a.75.75 0 0 1 0-1.5h3v-2.291a6.751 6.751 0 0 1-6-6.709v-1.5A.75.75 0 0 1 6 10.5Z" />
  </svg>
);

const StopIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className="w-5 h-5"
  >
    <path
      fillRule="evenodd"
      d="M4.5 7.5a3 3 0 0 1 3-3h9a3 3 0 0 1 3 3v9a3 3 0 0 1-3 3h-9a3 3 0 0 1-3-3v-9Z"
      clipRule="evenodd"
    />
  </svg>
);

// NEW: Icon for closing the controls panel
const ChevronDownIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className="w-5 h-5"
  >
    <path
      fillRule="evenodd"
      d="M12.53 16.28a.75.75 0 0 1-1.06 0l-7.5-7.5a.75.75 0 0 1 1.06-1.06L12 14.69l6.97-6.97a.75.75 0 1 1 1.06 1.06l-7.5 7.5Z"
      clipRule="evenodd"
    />
  </svg>
);

// NEW: Icon for "Add Video" button
const PlusIcon = () => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className="w-5 h-5 mr-1"
  >
    <path
      fillRule="evenodd"
      d="M12 5.25a.75.75 0 0 1 .75.75v6h6a.75.75 0 0 1 0 1.5h-6v6a.75.75 0 0 1-1.5 0v-6h-6a.75.75 0 0 1 0-1.5h6v-6a.75.75 0 0 1 .75-.75Z"
      clipRule="evenodd"
    />
  </svg>
);

// --- Loading Progress Bar Component ---
const LoadingProgressBar = ({ status }: { status: string }) => {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Simulate progress based on status
    let targetProgress = 0;
    if (status === "pending") targetProgress = 10;
    else if (status === "processing_video") targetProgress = 50;
    else if (status === "indexing_data") targetProgress = 85;
    else if (status === "completed") targetProgress = 100;

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= targetProgress) return prev;
        return Math.min(prev + 1, targetProgress);
      });
    }, 50);

    return () => clearInterval(interval);
  }, [status]);

  const getStatusText = (status: string) => {
    switch (status) {
      case "pending":
        return "Initializing...";
      case "processing_video":
        return "Extracting video content with AI...";
      case "indexing_data":
        return "Indexing data for semantic search...";
      case "completed":
        return "Ready!";
      default:
        return "Processing...";
    }
  };

  return (
    <div className="mt-4 space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-teal-400 font-medium">
          {getStatusText(status)}
        </span>
        <span className="text-teal-300 font-semibold">{progress}%</span>
      </div>
      <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-teal-500 to-emerald-500 rounded-full transition-all duration-300 ease-out relative overflow-hidden"
          style={{ width: `${progress}%` }}
        >
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
        </div>
      </div>
      <p className="text-xs text-gray-400">
        This may take a few minutes depending on video length
      </p>
    </div>
  );
};

// --- Custom Audio Player Component ---
const CustomAudioPlayer = ({
  src,
  "aria-label": ariaLabel,
}: {
  src: string;
  "aria-label": string;
}) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isReady, setIsReady] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    setIsReady(false);
    setIsPlaying(false);
    setIsLoading(true);
    setIsError(false);

    audio.src = src;

    const handleCanPlay = () => {
      setIsReady(true);
      setIsLoading(false);
      setIsError(false);
    };
    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);
    const handleWaiting = () => setIsLoading(true);
    const handlePlaying = () => setIsLoading(false);
    const handleError = () => {
      setIsError(true);
      setIsLoading(false);
      setIsPlaying(false);
    };

    audio.addEventListener("canplaythrough", handleCanPlay);
    audio.addEventListener("play", handlePlay);
    audio.addEventListener("pause", handlePause);
    audio.addEventListener("waiting", handleWaiting);
    audio.addEventListener("playing", handlePlaying);
    audio.addEventListener("error", handleError);
    audio.addEventListener("ended", handlePause);

    return () => {
      audio.removeEventListener("canplaythrough", handleCanPlay);
      audio.removeEventListener("play", handlePlay);
      audio.removeEventListener("pause", handlePause);
      audio.removeEventListener("waiting", handleWaiting);
      audio.removeEventListener("playing", handlePlaying);
      audio.removeEventListener("error", handleError);
      audio.removeEventListener("ended", handlePause);
    };
  }, [src]);

  const togglePlayPause = () => {
    const audio = audioRef.current;
    if (!audio || (!isReady && !isError)) return;

    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
  };

  let buttonContent;
  let buttonAriaLabel;
  let statusText;

  if (isError) {
    buttonContent = <span>❌</span>;
    buttonAriaLabel = "Error playing audio";
    statusText = "Error";
  } else if (isLoading) {
    buttonContent = <LoadingIcon />;
    buttonAriaLabel = "Loading audio...";
    statusText = "Loading...";
  } else if (isPlaying) {
    buttonContent = <PauseIcon />;
    buttonAriaLabel = "Pause audio explanation";
    statusText = "Playing";
  } else {
    buttonContent = <PlayIcon />;
    buttonAriaLabel = "Play audio explanation";
    statusText = "Audio Explanation";
  }

  return (
    <div className="mt-4 flex items-center gap-3">
      <audio ref={audioRef} src={src} className="sr-only" />
      <button
        onClick={togglePlayPause}
        disabled={!isReady && !isError}
        className="flex-shrink-0 w-12 h-12 rounded-full bg-emerald-600 text-white flex items-center justify-center transition-all shadow-lg hover:bg-emerald-700 disabled:bg-gray-600 disabled:opacity-70 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:ring-offset-gray-800"
        aria-label={buttonAriaLabel}
        type="button"
      >
        {buttonContent}
      </button>
      <div
        className="flex items-center gap-2 px-4 py-3 bg-gray-700/50 rounded-lg border border-gray-600/50"
        aria-hidden="true"
      >
        <SpeakerWaveIcon />
        <span className="text-sm font-medium text-gray-300">{statusText}</span>
      </div>
    </div>
  );
};

// --- Main App Component ---
export default function Home() {
  // --- State Variables ---
  const [videoUrl, setVideoUrl] = useState<string>("");
  const [currentVideoId, setCurrentVideoId] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [videoStatus, setVideoStatus] = useState<string>("idle");
  const [statusMessage, setStatusMessage] = useState<string>("");
  // const [videoSegments, setVideoSegments] = useState<VideoSegment[]>([]); // This state is not used in the provided code
  const [ttsProvider, setTtsProvider] = useState<"macos" | "gemini">("macos");

  const [messages, setMessages] = useState<Message[]>([]);
  const [currentQuery, setCurrentQuery] = useState<string>("");
  const [isChatLoading, setIsChatLoading] = useState<boolean>(false);

  // Voice input state
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [isVoiceSupported, setIsVoiceSupported] = useState<boolean>(true);
  const recognitionRef = useRef<any>(null);

  // --- MODIFIED: Controls panel visibility state ---
  const [isControlsOpen, setIsControlsOpen] = useState<boolean>(false);

  const chatEndRef = useRef<HTMLDivElement>(null);
  const playerRef = useRef<any>(null);

  const querySuggestions = [
    "What is this video about?",
    "Explain the main concepts",
    "What happens at the beginning?",
    "Describe the visual elements",
    "What are the key takeaways?",
  ];

  // --- YouTube API Loading ---
  useEffect(() => {
    if (!window.YT) {
      const tag = document.createElement("script");
      tag.src = "https://www.youtube.com/iframe_api";
      document.head.appendChild(tag);
      (window as any).onYouTubeIframeAPIReady = () => {
        console.log("YouTube IFrame API Ready");
      };
    }
  }, []);

  // --- Voice Recognition Setup ---
  useEffect(() => {
    // Only run on client side
    if (typeof window === "undefined") return;

    try {
      // Check if Web Speech API is supported
      const SpeechRecognition =
        (window as any).SpeechRecognition ||
        (window as any).webkitSpeechRecognition;

      if (!SpeechRecognition) {
        console.log("Speech Recognition not supported in this browser");
        setIsVoiceSupported(false);
        return;
      }

      // Initialize speech recognition
      const recognition = new SpeechRecognition();
      recognition.continuous = false; // Stop after one result
      recognition.interimResults = false; // Only final results
      recognition.lang = "en-US"; // Set language

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setCurrentQuery(transcript);
        setIsRecording(false);
      };

      recognition.onerror = (event: any) => {
        console.log("Speech recognition error:", event.error);
        setIsRecording(false);

        // Show user-friendly error messages
        if (event.error === "not-allowed") {
          alert(
            "Microphone access denied. Please allow microphone access in your browser settings."
          );
        } else if (event.error === "no-speech") {
          alert("No speech detected. Please try again.");
        }
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = recognition;

      return () => {
        if (recognitionRef.current) {
          try {
            recognitionRef.current.stop();
          } catch (e) {
            // Ignore errors when stopping recognition during cleanup
          }
        }
      };
    } catch (error) {
      console.log("Failed to initialize speech recognition:", error);
      setIsVoiceSupported(false);
    }
  }, []);

  // --- Voice Recording Handler ---
  const handleVoiceInput = () => {
    if (!isVoiceSupported || !recognitionRef.current) {
      alert(
        "Voice input is not supported in your browser. Please use Chrome, Edge, or Safari."
      );
      return;
    }

    if (isRecording) {
      // Stop recording
      recognitionRef.current.stop();
      setIsRecording(false);
    } else {
      // Start recording
      try {
        setCurrentQuery(""); // Clear existing query
        recognitionRef.current.start();
        setIsRecording(true);
      } catch (error) {
        console.error("Error starting speech recognition:", error);
        setIsRecording(false);
      }
    }
  };

  // --- Poll video status ---
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
          setStatusMessage("Video processed! Ready for questions.");
          setMessages([
            {
              role: "agent",
              text: "Video processed successfully! You can now ask me questions about the video content.",
            },
          ]);
          clearInterval(pollInterval);
        } else if (data.status === "failed") {
          setStatusMessage(
            `Processing failed: ${data.message || "Unknown error"}`
          );
          clearInterval(pollInterval);
        } else {
          setStatusMessage(`Processing video... (${data.status})`);
        }
      } catch (error: any) {
        console.error("Polling error:", error);
        setStatusMessage(`Error: ${error.message}`);
        setVideoStatus("failed");
        clearInterval(pollInterval);
      }
    }, 2500);
    return () => clearInterval(pollInterval);
  }, [jobId, videoStatus]);

  // --- Auto-scroll chat ---
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isChatLoading]);

  // --- Extract YouTube video ID ---
  function extractVideoId(url: string): string | null {
    const regex =
      /(?:https?:\/\/)?(?:www\.)?(?:youtu\.be\/|youtube.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})/;
    const match = url.match(regex);
    return match ? match[1] : null;
  }

  // --- Handle Video Upload ---
  const handleVideoUpload = async (e: FormEvent) => {
    e.preventDefault();
    if (!videoUrl) return;

    setMessages([]);
    setJobId(null);
    setCurrentVideoId(null);
    // setVideoSegments([]); // State is not used

    if (playerRef.current) {
      playerRef.current.destroy();
      playerRef.current = null;
    }

    const videoId = extractVideoId(videoUrl);
    if (videoId) {
      setCurrentVideoId(videoId); // This will trigger the useEffect to create the player
    } else {
      console.warn(
        "Could not extract a valid YouTube video ID. Player will not load."
      );
    }

    setVideoStatus("pending");
    setStatusMessage("Submitting video for processing...");

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

  // --- Create YouTube player when videoId is set ---
  useEffect(() => {
    // Only create player if ID is valid and API is ready
    if (currentVideoId && (window as any).YT && (window as any).YT.Player) {
      if (playerRef.current) {
        playerRef.current.destroy();
      }

      const playerElement = document.getElementById("youtube-player-div");
      if (playerElement) {
        playerRef.current = new (window as any).YT.Player(
          "youtube-player-div",
          {
            videoId: currentVideoId,
            width: "100%",
            height: "100%",
            playerVars: { playsinline: 1, origin: window.location.origin },
            events: { onReady: () => console.log("YouTube Player ready") },
          }
        );
      }
    }
  }, [currentVideoId]);

  // --- Handle Chat Query ---
  const handleChatSubmit = async (e: FormEvent, customQuery?: string) => {
    e.preventDefault();
    const query = customQuery || currentQuery;

    if (!query || !query.trim()) return;
    if (!jobId) {
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          text: "⚠️ Please upload a YouTube video first before asking questions.",
        },
      ]);
      return;
    }
    if (videoStatus !== "completed") {
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          text: `⚠️ Please wait for the video to finish processing. Current status: ${videoStatus}`,
        },
      ]);
      return;
    }
    if (isChatLoading) return;

    const userMessage: Message = { role: "user", text: query };
    setMessages((prev) => [...prev, userMessage]);
    setCurrentQuery("");
    setIsChatLoading(true);

    try {
      const res = await fetch("/api/query-video", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          job_id: jobId,
          query: query,
          tts_provider: ttsProvider,
        }),
      });

      if (!res.ok) {
        let errorMsg = `Error: ${res.statusText}`;
        try {
          const errorData = await res.json();
          errorMsg = errorData.detail || errorMsg;
        } catch {
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
      const errorMessage = error.message || "An unexpected error occurred";
      setMessages((prev) => [
        ...prev,
        { role: "agent", text: `❌ ${errorMessage}` },
      ]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // --- Handle Timestamp Click ---
  const handleTimestampClick = (timestamp: string) => {
    const player = playerRef.current;
    if (player && typeof player.seekTo === "function") {
      const parts = timestamp.split(":").map(Number);
      let seconds = 0;
      if (parts.length === 3)
        seconds = parts[0] * 3600 + parts[1] * 60 + parts[2];
      else if (parts.length === 2) seconds = parts[0] * 60 + parts[1];
      player.seekTo(seconds, true);
      if (typeof player.playVideo === "function") player.playVideo();
    } else {
      console.warn("Player not ready or seekTo function unavailable.");
    }
  };

  // --- Handle Suggestion Click ---
  const handleSuggestionClick = (suggestion: string) => {
    setCurrentQuery(suggestion);
    handleChatSubmit(new Event("submit") as any, suggestion);
  };

  // const isChatReady = videoStatus === "completed" && !isChatLoading; // Not used in footer, so commented out

  // --- Main Layout ---
  return (
    <>
      <Head>
        <title>Vid Explain Agent</title>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap"
          rel="stylesheet"
        />
      </Head>

      {/* --- MODIFIED: Main wrapper, 2-column flex layout --- */}
      <div className="relative flex h-screen w-full overflow-hidden bg-gradient-to-br from-stone-900 via-stone-900 to-neutral-950 text-gray-100">
        <a
          href="#chat-input"
          className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:top-2 focus:left-2 focus:px-4 focus:py-2 focus:from-slate-900 to-teal-950 focus:text-white focus:rounded-lg"
        >
          Skip to chat
        </a>

        {/* --- Headers (remain fixed) --- */}
        <h1
          className="absolute top-6 left-6 text-xl font-bold text-gray-200 z-10 leading-tight"
          style={{ fontFamily: "'Space Mono', monospace" }}
        >
          Vid
          <br />
          Explain
          <br />
          Agent
        </h1>
        <h2 className="absolute top-6 right-6 text-sm font-medium tracking-widest text-gray-400 z-10">
          TALK TO YOUR VIDEOS
        </h2>

        {/* --- MODIFIED: Left Column (Video Player) --- */}
        <div className="w-3/5 h-screen flex items-center justify-center p-6 pt-28">
          {/* This container will respect the padding and center the video box */}
          <div className="w-full max-w-full">
            {/* This div provides the 16:9 aspect ratio box.
              'relative' is needed for the child to be 'absolute'.
            */}
            <div className="aspect-video relative">
              {/* This is the div the YouTube API will replace.
                It's 'absolute' to fill the parent 'aspect-video' box.
                This is the key fix for the vertical sizing.
              */}
              <div
                id="youtube-player-div"
                className="absolute top-0 left-0 w-full h-full bg-black rounded-xl shadow-2xl flex items-center justify-center text-gray-500 text-sm overflow-hidden"
              >
                {currentVideoId
                  ? "Loading player..."
                  : "Add a video using the button below"}
              </div>
            </div>
          </div>
        </div>

        {/* --- MODIFIED: Right Column (Chat) --- */}
        <main
          className="w-2/5 flex flex-col bg-transparent h-screen pt-28" // pt-28 to clear header
          aria-label="Chat Conversation"
        >
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto">
            <div className="w-full max-w-3xl mx-auto py-8 px-6 space-y-6">
              {/* --- Welcome / Suggestion Messages --- */}
              {messages.length === 0 && videoStatus === "idle" && (
                <div className="text-center space-y-6 py-12">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-teal-500/20 mb-4">
                    <SparklesIcon />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-200">
                    Welcome to Vid Explain Agent
                  </h2>
                  <p className="text-gray-400 max-w-md mx-auto">
                    Click the "Add Video" button to process a YouTube URL and
                    start asking questions.
                  </p>
                </div>
              )}
              {messages.length === 0 && videoStatus === "completed" && (
                <div className="text-center space-y-6 py-12">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-teal-500/20 mb-4">
                    <SparklesIcon />
                  </div>
                  <h2 className="text-2xl font-bold text-gray-200">
                    Ask me anything about the video
                  </h2>
                  <p className="text-gray-400 max-w-md mx-auto">
                    I can explain concepts, describe visuals, and answer
                    questions about the content.
                  </p>
                </div>
              )}
              {messages.length === 0 && videoStatus === "completed" && (
                <div className="flex flex-wrap gap-3 justify-center">
                  {querySuggestions.map((suggestion, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSuggestionClick(suggestion)}
                      className="px-4 py-2 rounded-full bg-gray-800 hover:bg-gray-700 text-sm text-gray-300 transition-all transform hover:scale-105 active:scale-95 border border-gray-700 hover:border-gray-600"
                      aria-label={`Ask: ${suggestion}`}
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              )}

              {/* --- Chat Message Map --- */}
              {messages.map((msg, index) => (
                <div
                  key={index}
                  className={`flex items-start gap-4 ${
                    msg.role === "user" ? "justify-end" : ""
                  }`}
                >
                  {msg.role === "agent" && (
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-zinc-900 to-slate-900 flex items-center justify-center shadow-lg">
                      <AgentIcon />
                    </div>
                  )}
                  <div
                    className={`flex-1 ${
                      msg.role === "agent"
                        ? "bg-gray-800/80 rounded-2xl p-5 shadow-lg border border-gray-700/50"
                        : "bg-gradient-to-r from-stone-600 to-stone-700 rounded-2xl p-5 shadow-lg text-right"
                    }`}
                  >
                    <p className="text-gray-100 whitespace-pre-wrap leading-relaxed">
                      {msg.text}
                    </p>
                    {msg.audioUrl && (
                      <CustomAudioPlayer
                        src={msg.audioUrl}
                        aria-label="Audio explanation for agent's message"
                      />
                    )}
                    {msg.timestamps && msg.timestamps.length > 0 && (
                      <div className="mt-4 flex flex-wrap gap-2 items-center">
                        <span className="text-xs text-gray-400 font-medium">
                          Referenced times:
                        </span>
                        {msg.timestamps.map((ts) => (
                          <button
                            key={ts}
                            onClick={() => handleTimestampClick(ts)}
                            className="rounded-full bg-teal-600/20 px-3 py-1.5 text-xs font-medium text-teal-400 hover:bg-teal-600/30 transition-all transform hover:scale-105 active:scale-95 border border-teal-500/30"
                            aria-label={`Jump to timestamp ${ts}`}
                          >
                            {ts}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  {msg.role === "user" && (
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center shadow-lg">
                      <UserIcon />
                    </div>
                  )}
                </div>
              ))}
              {isChatLoading && (
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-zinc-900 to-slate-900 flex items-center justify-center animate-pulse shadow-lg">
                    <AgentIcon />
                  </div>
                  <div className="flex-1 bg-gray-800/80 rounded-2xl p-5 shadow-lg border border-gray-700/50">
                    <div className="flex items-center gap-2">
                      <div
                        className="h-3 w-3 from-slate-900 to-teal-950 rounded-full animate-bounce"
                        style={{ animationDelay: "0ms" }}
                      ></div>
                      <div
                        className="h-3 w-3 from-slate-900 to-teal-950 rounded-full animate-bounce"
                        style={{ animationDelay: "150ms" }}
                      ></div>
                      <div
                        className="h-3 w-3 from-slate-900 to-teal-950 rounded-full animate-bounce"
                        style={{ animationDelay: "300ms" }}
                      ></div>
                      <span className="text-gray-400 text-sm ml-2">
                        Thinking...
                      </span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          </div>

          {/* --- Chat Input Bar --- */}
          <footer className="w-full border-t border-gray-700/50 bg-transparent">
            <div className="w-full max-w-3xl mx-auto p-6">
              <form
                onSubmit={(e) => handleChatSubmit(e)}
                className="relative flex items-center gap-3"
              >
                <label htmlFor="chat-input" className="sr-only">
                  Ask a question about the video
                </label>
                <input
                  id="chat-input"
                  type="text"
                  value={currentQuery}
                  onChange={(e) => setCurrentQuery(e.target.value)}
                  disabled={isRecording} // Only disable for recording
                  placeholder={
                    isRecording
                      ? "Listening..."
                      : "Ask a question about the video..."
                  }
                  className={`flex-grow rounded-xl border-gray-600 bg-gray-800 p-4 pr-28 shadow-lg text-gray-100 placeholder-gray-500 focus:border-teal-500 focus:ring-2 focus:ring-teal-500 disabled:opacity-60 transition-all ${
                    isRecording ? "animate-pulse border-red-500" : ""
                  }`}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleChatSubmit(e as any);
                    }
                  }}
                  aria-label="Type your question here"
                />
                {/* Microphone Button */}
                <button
                  type="button"
                  onClick={handleVoiceInput}
                  disabled={!isVoiceSupported}
                  aria-label={
                    isRecording ? "Stop recording" : "Start voice input"
                  }
                  className={`absolute right-20 top-1/2 -translate-y-1/2 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-teal-500 disabled:cursor-not-allowed disabled:opacity-50 transition-all transform hover:scale-110 active:scale-95 shadow-lg ${
                    isRecording
                      ? "bg-red-600 hover:bg-red-700 text-white animate-pulse"
                      : "bg-gray-700 hover:bg-gray-600 text-gray-300"
                  }`}
                  title={
                    !isVoiceSupported
                      ? "Voice input not supported in this browser"
                      : isRecording
                      ? "Click to stop recording"
                      : "Click to start voice input"
                  }
                >
                  {isRecording ? <StopIcon /> : <MicrophoneIcon />}
                </button>
                {/* Send Button */}
                <button
                  type="submit"
                  disabled={!currentQuery.trim()}
                  aria-label="Send message"
                  className="absolute right-8 top-1/2 -translate-y-1/2 rounded-lg p-3 text-white from-slate-900 to-teal-950 hover:from-slate-900 to-teal-900 focus:outline-none focus:ring-2 focus:ring-teal-500 disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-gray-700 transition-all transform hover:scale-110 active:scale-95 shadow-lg"
                >
                  <SendIcon />
                </button>
              </form>
              <p className="text-xs text-gray-500 mt-3 text-center">
                Press{" "}
                <kbd className="px-2 py-0.5 rounded bg-gray-800 border border-gray-700">
                  Enter
                </kbd>
                to send • Click 🎤 for voice input • Using{" "}
                {ttsProvider === "macos"
                  ? "macOS TTS (free)"
                  : "Gemini TTS (premium)"}
              </p>
            </div>
          </footer>
        </main>

        {/* --- MODIFIED: Collapsible Controls Panel --- */}
        {!isControlsOpen && (
          <button
            onClick={() => setIsControlsOpen(true)}
            className="fixed bottom-6 left-6 z-30 flex items-center px-6 py-3 rounded-full bg-black/50 backdrop-blur-md text-white font-semibold shadow-lg hover:bg-black/70 transition-all transform hover:scale-105"
            aria-label="Add a new video"
          >
            <PlusIcon />
            Add Video
          </button>
        )}

        <div
          className={`fixed bottom-6 left-6 z-30 w-[450px] bg-gray-900/80 backdrop-blur-md border border-gray-700/50 rounded-lg shadow-2xl p-6 transition-all duration-300 ease-in-out ${
            isControlsOpen
              ? "opacity-100 translate-y-0"
              : "opacity-0 translate-y-10 pointer-events-none"
          }`}
          aria-label="Video Upload and Controls"
        >
          <button
            onClick={() => setIsControlsOpen(false)}
            className="absolute top-3 right-3 z-40 p-2 rounded-full text-gray-400 bg-gray-800/50 hover:bg-gray-700 transition-all"
            aria-label="Hide video controls"
          >
            <ChevronDownIcon />
          </button>

          <form onSubmit={handleVideoUpload} className="space-y-4">
            <div>
              <label
                htmlFor="video-url"
                className="block text-sm font-medium text-gray-300 mb-2"
              >
                YouTube Video URL
              </label>
              <input
                id="video-url"
                type="text"
                value={videoUrl}
                onChange={(e) => setVideoUrl(e.target.value)}
                placeholder="https://youtube.com/watch?v=..."
                className="block w-full rounded-lg border-gray-600 bg-gray-800 p-3 shadow-sm focus:border-teal-500 focus:ring-2 focus:ring-teal-500 text-sm transition-all"
                aria-label="Enter YouTube video URL"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Voice Provider
                <span className="ml-2 text-xs text-gray-500 font-normal">
                  (for audio responses)
                </span>
              </label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setTtsProvider("macos")}
                  className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    ttsProvider === "macos"
                      ? "bg-teal-600 text-white shadow-lg"
                      : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                  }`}
                  aria-label="Use macOS native TTS (Siri quality, free, instant)"
                >
                  <div className="flex items-center justify-center gap-2">
                    <span>🍎 macOS</span>
                    <span className="text-xs from-gray-950 to-emerald-900 text-green-400 px-2 py-0.5 rounded">
                      FREE
                    </span>
                  </div>
                </button>
                <button
                  type="button"
                  onClick={() => setTtsProvider("gemini")}
                  className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    ttsProvider === "gemini"
                      ? "bg-teal-600 text-white shadow-lg"
                      : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                  }`}
                  aria-label="Use Gemini TTS (premium quality, rate limited)"
                >
                  <div className="flex items-center justify-center gap-2">
                    <SparklesIcon />
                    <span>Gemini</span>
                  </div>
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {ttsProvider === "macos"
                  ? "Native Mac TTS (Siri quality, instant, unlimited)"
                  : "Premium quality, 3 RPM limit"}
              </p>
            </div>
            <button
              type="submit"
              disabled={
                !videoUrl ||
                (!!jobId &&
                  videoStatus !== "completed" &&
                  videoStatus !== "failed")
              }
              className="w-full rounded-lg bg-gradient-to-r from-zinc-900 to-slate-900 px-4 py-3 text-sm font-semibold text-white shadow-lg hover:from-neutral-950 to-neutral-900 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:cursor-not-allowed disabled:opacity-60 transition-all transform hover:scale-[1.02] active:scale-[0.98]"
              aria-label="Process video"
            >
              {jobId && videoStatus !== "completed" && videoStatus !== "failed"
                ? "Processing..."
                : "Process Video"}
            </button>
            {statusMessage && (
              <div role="status" aria-live="polite">
                {videoStatus === "completed" ? (
                  <div className="mt-4 text-sm font-medium px-4 py-3 rounded-lg from-gray-950 to-emerald-900 text-emerald-600 border border-green-500/30 flex items-center gap-2">
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    {statusMessage}
                  </div>
                ) : videoStatus === "failed" ? (
                  <div className="mt-4 text-sm font-medium px-4 py-3 rounded-lg bg-red-500/20 text-red-400 border border-red-500/30 flex items-center gap-2">
                    <svg
                      className="w-5 h-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    {statusMessage}
                  </div>
                ) : (
                  <LoadingProgressBar status={videoStatus} />
                )}
              </div>
            )}
          </form>
        </div>
      </div>
    </>
  );
}
