"use client";

import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useTheme } from "next-themes";
import axios from "axios";
import { 
  Bot, User, Mic, ArrowUp, Loader2, ChevronLeft, ChevronRight, 
  Maximize2, Minimize2, Sparkles, FileText, CheckCircle2 
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";

import SidebarLeft, { DocumentItem } from "@/components/dashboard/SidebarLeft";
import SidebarRight, { StudioType } from "@/components/dashboard/SidebarRight";
import CommandPalette from "@/components/dashboard/CommandPalette";
import LandingPage from "@/components/landing/LandingPage";
import { COMMANDS, Command } from "@/lib/commands";
import { API_BASE, getApiErrorMessage } from "@/lib/api";
import { ToastContainer, ToastMessage } from "@/components/ui/toast";

const DEFAULT_KEY = process.env.NEXT_PUBLIC_GEMINI_KEY || "";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface StudioCacheEntry {
  podcastScript: any[];
  flashcards: any[];
  debateTranscript: any[];
  vaultAudit: any;
  quizQuestions: any[];
  summaryText: string;
}

const emptyStudioCache = (): StudioCacheEntry => ({
  podcastScript: [],
  flashcards: [],
  debateTranscript: [],
  vaultAudit: null,
  quizQuestions: [],
  summaryText: "",
});

export default function RootPage() {
  const { setTheme, theme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [hasEntered, setHasEntered] = useState(false);

  // --- CORE STATE ---
  const [apiKey, setApiKey] = useState(DEFAULT_KEY);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [activeDoc, setActiveDoc] = useState<DocumentItem | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [chatStatus, setChatStatus] = useState("");

  // --- APPLICATION SETTINGS ---
  const [appSettings, setAppSettings] = useState({
    focusMode: false,
    autoAudit: false,
    spacedRepetition: false,
  });

  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const toastIdRef = useRef(0);

  const showToast = (message: string, type: ToastMessage["type"] = "info") => {
    const id = ++toastIdRef.current;
    setToasts((prev) => [...prev, { id, message, type }]);
  };

  const dismissToast = (id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  // --- STUDIO STATES ---
  const [activeStudio, setActiveStudio] = useState<StudioType>("none");
  const [podcastScript, setPodcastScript] = useState<any[]>([]);
  const [isGeneratingPodcast, setIsGeneratingPodcast] = useState(false);
  const [flashcards, setFlashcards] = useState<any[]>([]);
  const [isGeneratingFlashcards, setIsGeneratingFlashcards] = useState(false);
  const [debateTranscript, setDebateTranscript] = useState<any[]>([]);
  const [isDebating, setIsDebating] = useState(false);
  const [vaultAudit, setVaultAudit] = useState<any>(null);
  const [isAuditing, setIsAuditing] = useState(false);
  const [quizQuestions, setQuizQuestions] = useState<any[]>([]);
  const [isGeneratingQuiz, setIsGeneratingQuiz] = useState(false);
  const [summaryText, setSummaryText] = useState("");
  const [isGeneratingSummary, setIsGeneratingSummary] = useState(false);
  const [studioCache, setStudioCache] = useState<Record<string, StudioCacheEntry>>({});

  // --- UI STATES ---
  const [showLeftSidebar, setShowLeftSidebar] = useState(true);
  const [showRightSidebar, setShowRightSidebar] = useState(true);
  const [leftSidebarWide, setLeftSidebarWide] = useState(false);
  const [rightSidebarWide, setRightSidebarWide] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [filteredCommands, setFilteredCommands] = useState<Command[]>([]);
  const [selectedCommandIndex, setSelectedCommandIndex] = useState(0);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll chat to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Load persistence
  useEffect(() => {
    setMounted(true);
    const savedKey = localStorage.getItem("notewave_gemini_key");
    if (savedKey) setApiKey(savedKey);

    const savedDocs = localStorage.getItem("notewave_docs");
    if (savedDocs) {
      try {
        const parsed = JSON.parse(savedDocs);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setDocuments(parsed);
          setActiveDoc(parsed[0]);
          setHasEntered(true);
        }
      } catch (e) {
        console.error("Failed to load documents from storage", e);
      }
    }

    const savedSettings = localStorage.getItem("notewave_settings");
    if (savedSettings) {
      try {
        setAppSettings(JSON.parse(savedSettings));
      } catch (e) {
        console.error("Failed to load settings", e);
      }
    }

    // Sync documents from backend
    axios.get(`${API_BASE}/api/documents`)
      .then((res) => {
        const backendDocs = res.data?.documents;
        if (Array.isArray(backendDocs) && backendDocs.length > 0) {
          setDocuments(backendDocs);
          setActiveDoc(backendDocs[0]);
          setHasEntered(true);
          localStorage.setItem("notewave_docs", JSON.stringify(backendDocs));
        }
      })
      .catch(() => {});
  }, []);

  // Sync settings
  useEffect(() => {
    if (mounted) {
      localStorage.setItem("notewave_settings", JSON.stringify(appSettings));
    }
  }, [appSettings, mounted]);

  // Keep per-document studio cache in sync
  useEffect(() => {
    if (!activeDoc) return;
    setStudioCache((prev) => ({
      ...prev,
      [activeDoc.name]: {
        podcastScript,
        flashcards,
        debateTranscript,
        vaultAudit,
        quizQuestions,
        summaryText,
      },
    }));
  }, [activeDoc, podcastScript, flashcards,  debateTranscript, vaultAudit, quizQuestions, summaryText]);

  const updateApiKey = (key: string) => {
    setApiKey(key);
    localStorage.setItem("notewave_gemini_key", key);
  };

  const cacheCurrentStudios = (docName: string) => {
    if (!docName) return;
    setStudioCache((prev) => ({
      ...prev,
      [docName]: {
        podcastScript,
        flashcards,
        debateTranscript,
        vaultAudit,
        quizQuestions,
        summaryText,
      },
    }));
  };

  const applyStudioCache = (docName: string) => {
    const cached = studioCache[docName] || emptyStudioCache();
    setPodcastScript(cached.podcastScript);
    setFlashcards(cached.flashcards);
        setDebateTranscript(cached.debateTranscript);
    setVaultAudit(cached.vaultAudit);
    setQuizQuestions(cached.quizQuestions);
    setSummaryText(cached.summaryText);
  };

  // --- STUDIO API HANDLERS ---
  const handleGeneratePodcast = async () => {
    if (!activeDoc) return;
    setIsGeneratingPodcast(true);
    try {
      const res = await axios.post(`${API_BASE}/api/podcast`, {
        fileId: activeDoc.name,
        api_key: apiKey,
      });
      if (res.data?.script) {
        setPodcastScript(res.data.script);
        showToast("Podcast script generated!", "success");
      }
    } catch (err) {
      showToast(getApiErrorMessage(err), "error");
    } finally {
      setIsGeneratingPodcast(false);
    }
  };

  const handleGenerateFlashcards = async () => {
    if (!activeDoc) return;
    setIsGeneratingFlashcards(true);
    try {
      const res = await axios.post(`${API_BASE}/api/flashcards`, {
        fileId: activeDoc.name,
        api_key: apiKey,
      });
      if (res.data?.flashcards) setFlashcards(res.data.flashcards);
    } catch (err) {
      showToast(getApiErrorMessage(err), "error");
    } finally {
      setIsGeneratingFlashcards(false);
    }
  };


  const handleStartDebate = async () => {
    if (!activeDoc) return;
    setIsDebating(true);
    try {
      const res = await axios.post(`${API_BASE}/api/debate`, {
        fileId: activeDoc.name,
        api_key: apiKey,
      });
      if (res.data?.transcript) setDebateTranscript(res.data.transcript);
    } catch (err) {
      showToast(getApiErrorMessage(err), "error");
    } finally {
      setIsDebating(false);
    }
  };

  const handleVaultAudit = async () => {
    if (!activeDoc) return;
    setIsAuditing(true);
    try {
      const res = await axios.post(`${API_BASE}/api/vault`, {
        fileId: activeDoc.name,
        api_key: apiKey,
      });
      setVaultAudit(res.data);
    } catch (err) {
      showToast(getApiErrorMessage(err), "error");
    } finally {
      setIsAuditing(false);
    }
  };

  const handleGenerateQuiz = async (count: number = 5) => {
    if (!activeDoc) return;
    setIsGeneratingQuiz(true);
    try {
      const res = await axios.post(`${API_BASE}/api/quiz`, {
        fileId: activeDoc.name,
        count,
        api_key: apiKey,
      });
      if (res.data?.questions) setQuizQuestions(res.data.questions);
    } catch (err) {
      showToast(getApiErrorMessage(err), "error");
    } finally {
      setIsGeneratingQuiz(false);
    }
  };

  const handleGenerateSummary = async () => {
    if (!activeDoc) return;
    setIsGeneratingSummary(true);
    try {
      const res = await axios.post(`${API_BASE}/api/summary`, {
        fileId: activeDoc.name,
        api_key: apiKey,
      });
      if (res.data?.summary) setSummaryText(res.data.summary);
    } catch (err) {
      showToast(getApiErrorMessage(err), "error");
    } finally {
      setIsGeneratingSummary(false);
    }
  };

  // --- UPLOAD HANDLER ---
  const processUpload = async (file: File) => {
    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("api_key", apiKey);

    try {
      const res = await axios.post(`${API_BASE}/api/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      const newDoc: DocumentItem = {
        id: Date.now(),
        name: res.data.filename,
        filename: res.data.filename,
        date: "Just now",
        chunks: res.data.chunks || 1,
        mastery: 85,
      };

      const updatedDocs = [newDoc, ...documents.filter((d) => d.name !== newDoc.name)];
      setDocuments(updatedDocs);
      setActiveDoc(newDoc);
      localStorage.setItem("notewave_docs", JSON.stringify(updatedDocs));

      setMessages([
        {
          role: "assistant",
          content: `**${file.name}** is indexed and ready! Ask questions, or type \`/\` to launch any intelligence studio.`,
        },
      ]);

      setHasEntered(true);
      setIsUploadOpen(false);
      showToast(`Indexed ${res.data.chunks} chunks. Studios generate on demand.`, "success");

      if (appSettings.autoAudit) {
        handleVaultAudit();
      }
    } catch (err: unknown) {
      showToast(getApiErrorMessage(err), "error");
    } finally {
      setIsUploading(false);
    }
  };

  // --- SWITCH / DELETE DOCUMENT ---
  const handleSwitchFile = (doc: DocumentItem) => {
    if (activeDoc) {
      cacheCurrentStudios(activeDoc.name);
    }
    setActiveDoc(doc);
    setMessages([
      {
        role: "assistant",
        content: `Switched context to **${doc.name}**. Ready for research questions.`,
      },
    ]);
    setActiveStudio("none");
    applyStudioCache(doc.name);
  };

  const handleDeleteFile = async (e: React.MouseEvent, doc: DocumentItem) => {
    e.stopPropagation();
    try {
      await axios.delete(`${API_BASE}/api/documents/${encodeURIComponent(doc.name)}`, {
        params: { api_key: apiKey },
      });
    } catch (err) {
      console.error(err);
    }
    setStudioCache((prev) => {
      const next = { ...prev };
      delete next[doc.name];
      return next;
    });
    const updated = documents.filter((d) => d.id !== doc.id);
    setDocuments(updated);
    localStorage.setItem("notewave_docs", JSON.stringify(updated));
    if (activeDoc?.id === doc.id) {
      setActiveDoc(updated.length > 0 ? updated[0] : null);
      setMessages([]);
    }
  };

  // --- COMMAND PALETTE ---
  const executeCommand = (cmd: Command) => {
    setFilteredCommands([]);
    setInput("");
    setShowRightSidebar(true);

    if (cmd.id === "podcast") {
      setActiveStudio("podcast");
      if (podcastScript.length === 0) handleGeneratePodcast();
    } else if (cmd.id === "flashcards") {
      setActiveStudio("flashcards");
      if (flashcards.length === 0) handleGenerateFlashcards();
    } else if (cmd.id === "") {
      setActiveStudio("");
      if (!Data?.nodes?.length) handleGenerateGraph();
    } else if (cmd.id === "debate") {
      setActiveStudio("debate");
      if (debateTranscript.length === 0) handleStartDebate();
    } else if (cmd.id === "vault") {
      setActiveStudio("vault");
      if (!vaultAudit) handleVaultAudit();
    } else if (cmd.id === "quiz") {
      setActiveStudio("quiz");
      if (quizQuestions.length === 0) handleGenerateQuiz();
    } else if (cmd.id === "summary") {
      setActiveStudio("summary");
      if (!summaryText) handleGenerateSummary();
    } else if (cmd.id === "voice") {
      setActiveStudio("voice");
    } else if (cmd.id === "settings") {
      setActiveStudio("settings");
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setInput(val);
    if (val.startsWith("/")) {
      const query = val.slice(1).toLowerCase();
      setFilteredCommands(
        COMMANDS.filter((c) => c.id.includes(query) || c.label.includes(query))
      );
      setSelectedCommandIndex(0);
    } else {
      setFilteredCommands([]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (filteredCommands.length > 0) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedCommandIndex((prev) => (prev + 1) % filteredCommands.length);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedCommandIndex((prev) => (prev - 1 + filteredCommands.length) % filteredCommands.length);
      } else if (e.key === "Enter") {
        e.preventDefault();
        executeCommand(filteredCommands[selectedCommandIndex]);
      } else if (e.key === "Escape") {
        setFilteredCommands([]);
      }
    }
  };

  // --- SEND CHAT MESSAGE ---
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const query = input.trim();
    if (!query || !activeDoc) return;

    const newMessages: ChatMessage[] = [...messages, { role: "user", content: query }];
    setMessages([...newMessages, { role: "assistant", content: "" }]);
    setInput("");
    setIsLoading(true);
    setChatStatus("Connecting...");

    const finalize = (content: string) => {
      setMessages((prev) => {
        const copy = prev.slice();
        copy[copy.length - 1] = { role: "assistant", content } as ChatMessage;
        return copy;
      });
    };

    try {
      const res = await axios.post(`${API_BASE}/api/chat`, {
        messages: newMessages,
        fileId: activeDoc.name,
        api_key: apiKey,
      });

      const jobId = res.data?.job_id;
      if (!jobId) {
        const reply = res.data?.content || res.data?.text || "Answer synthesized.";
        finalize(reply);
        return;
      }

      const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
      const deadline = Date.now() + 300000; // 5 min max
      for (;;) {
        if (Date.now() > deadline) throw new Error("Timed out waiting for the answer.");
        await sleep(1200);
        let reply: string | null = null;
        try {
          const statusRes = await axios.get(`${API_BASE}/api/chat/status/${jobId}`);
          if (statusRes.data?.status === "done") {
            reply = statusRes.data?.content || statusRes.data?.text || "Answer synthesized.";
          } else {
            setChatStatus(statusRes.data?.message || "Working...");
          }
        } catch (pollErr: any) {
          if (pollErr.response?.status === 500) {
            throw new Error(pollErr.response?.data?.detail || "Chat generation failed.");
          }
          setChatStatus("Contacting server...");
        }
        if (reply !== null) {
          finalize(reply);
          break;
        }
      }
    } catch (err: any) {
      console.error("Chat error:", err);
      finalize(`Error communicating with the backend: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsLoading(false);
      setChatStatus("");
    }
  };

  if (!mounted) return null;

  // Render Landing Page if user has no documents or chooses to land
  if (!hasEntered) {
    return (
      <LandingPage
        onEnter={() => setHasEntered(true)}
        onUploadFile={processUpload}
        isUploading={isUploading}
        apiKey={apiKey}
        onUpdateApiKey={updateApiKey}
      />
    );
  }

  return (
    <div
      className={`h-screen flex bg-white dark:bg-black overflow-hidden font-sans transition-all duration-700 ${
        appSettings.focusMode ? "grayscale-[0.8] brightness-90" : ""
      }`}
    >
      {/* LEFT SIDEBAR: SOURCES & LIBRARY */}
      <SidebarLeft
        documents={documents}
        activeDoc={activeDoc}
        isUploading={isUploading}
        isUploadOpen={isUploadOpen}
        setIsUploadOpen={setIsUploadOpen}
        handleUploadForm={processUpload}
        handleSwitchFile={handleSwitchFile}
        handleDeleteFile={handleDeleteFile}
        setTheme={setTheme}
        theme={theme}
        showLeftSidebar={showLeftSidebar}
        isWide={leftSidebarWide}
        toggleSidebar={() => setShowLeftSidebar(!showLeftSidebar)}
        onOpenSettings={() => {
          setActiveStudio("settings");
          setShowRightSidebar(true);
        }}
      />

      {/* CENTER STAGE: COPILOT CHAT */}
      <div className="flex-1 flex flex-col h-full bg-white dark:bg-black relative overflow-hidden transition-all duration-300 min-w-0">
        {/* HEADER BAR */}
        <header className="h-16 flex-none flex items-center justify-between px-6 border-b border-zinc-200 dark:border-zinc-800 z-30">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setShowLeftSidebar(!showLeftSidebar)}
              className="h-8 w-8 icon-btn"
            >
              <ChevronLeft className={`h-4 w-4 transition-transform ${!showLeftSidebar ? "rotate-180" : ""}`} />
            </Button>
            {showLeftSidebar && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setLeftSidebarWide(!leftSidebarWide)}
                className="h-8 w-8 icon-btn"
              >
                {leftSidebarWide ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
              </Button>
            )}
            {!showLeftSidebar && (
              <span className="font-bold text-sm tracking-tight text-zinc-900 dark:text-white ml-1">
                NoteWave
              </span>
            )}
          </div>

          {/* ACTIVE CONTEXT PILL */}
          <div className="flex items-center gap-2.5 px-4 py-1.5 rounded-full bg-zinc-100 dark:bg-zinc-900/90 border border-zinc-200 dark:border-zinc-800 shadow-sm">
            <span className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">Context</span>
            <div className="h-3 w-px bg-zinc-300 dark:bg-zinc-700" />
            <span className="text-xs font-semibold truncate max-w-[200px] text-zinc-800 dark:text-zinc-200">
              {activeDoc?.name || "No Document Active"}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {showRightSidebar && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setRightSidebarWide(!rightSidebarWide)}
                className="h-8 w-8 icon-btn"
              >
                {rightSidebarWide ? <Minimize2 className="h-3.5 w-3.5" /> : <Maximize2 className="h-3.5 w-3.5" />}
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setShowRightSidebar(!showRightSidebar)}
              className="h-8 w-8 icon-btn"
            >
              <ChevronRight className={`h-4 w-4 transition-transform ${showRightSidebar ? "" : "rotate-180"}`} />
            </Button>
          </div>
        </header>

        {/* CHAT SCROLL AREA */}
        <div className={`flex-1 overflow-hidden relative ${appSettings.focusMode ? "opacity-75" : "opacity-100"}`}>
          <ScrollArea className="h-full w-full">
            <div className="max-w-3xl mx-auto px-6 py-10 space-y-8">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-24 text-center space-y-4 opacity-40">
                  <div className="h-12 w-12 rounded-2xl bg-zinc-100 dark:bg-zinc-900 flex items-center justify-center">
                    <Bot className="w-6 h-6" />
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-semibold">AI Research Copilot</p>
                    <p className="text-xs text-zinc-500 max-w-sm">
                      Ask anything about your document or type <code className="font-mono text-purple-400">/</code> to launch specialized studios.
                    </p>
                  </div>
                </div>
              ) : (
                messages.map((m, i) => {
                  const isUser = m.role === "user";
                  return (
                    <div
                      key={i}
                      className={`flex gap-4 animate-in fade-in duration-300 ${
                        isUser ? "flex-row-reverse" : "flex-row"
                      }`}
                    >
                      <Avatar className={`h-8 w-8 mt-1 shrink-0 ${isUser ? "bg-zinc-800" : "bg-zinc-900 dark:bg-white"}`}>
                        <AvatarFallback className="text-xs">
                          {isUser ? (
                            <User className="w-4 h-4 text-white" />
                          ) : (
                            <Bot className="w-4 h-4 text-black dark:text-black" />
                          )}
                        </AvatarFallback>
                      </Avatar>

                      <div className={`flex-1 min-w-0 ${isUser ? "text-right" : ""}`}>
                        <div
                          className={`inline-block text-left ${
                            isUser
                              ? "bg-zinc-100 dark:bg-zinc-900 px-4 py-2.5 rounded-2xl text-zinc-900 dark:text-zinc-100 text-sm shadow-sm"
                              : "markdown-content w-full"
                          }`}
                        >
                          {isUser ? (
                            <p>{m.content}</p>
                          ) : (
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {m.content}
                            </ReactMarkdown>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}

              {isLoading && (
                <div className="flex items-center gap-3 text-xs text-zinc-400">
                  <Loader2 className="w-4 h-4 animate-spin text-purple-400" />
                  <span>{chatStatus || "Synthesizing answer with Gemini..."}</span>
                </div>
              )}
              <div ref={messagesEndRef} className="h-10" />
            </div>
          </ScrollArea>
        </div>

        {/* BOTTOM INPUT BAR WITH COMMAND PALETTE */}
        <footer className="flex-none p-6 pt-2">
          <div className="max-w-3xl mx-auto relative">
            <CommandPalette
              commands={filteredCommands}
              selectedIndex={selectedCommandIndex}
              onSelect={executeCommand}
            />

            <form onSubmit={handleSubmit} className="relative group">
              <Input
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder="Ask about document or type / for studios..."
                className="h-14 pl-12 pr-14 rounded-2xl border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 shadow-2xl text-zinc-900 dark:text-zinc-100 text-sm focus-visible:ring-1 focus-visible:ring-purple-500"
              />
              <button
                type="button"
                onClick={() => {
                  setActiveStudio("voice");
                  setShowRightSidebar(true);
                }}
                className="absolute left-4 top-4 icon-btn transition-colors"
              >
                <Mic className="w-5 h-5" />
              </button>
              <Button
                type="submit"
                disabled={isLoading || !input.trim()}
                size="icon"
                className="absolute right-2.5 top-2.5 h-9 w-9 rounded-xl bg-black dark:bg-white text-white dark:text-black hover:opacity-90 transition-opacity"
              >
                <ArrowUp className="w-4 h-4" />
              </Button>
            </form>
          </div>
        </footer>
      </div>

      {/* RIGHT SIDEBAR: INTELLIGENCE STUDIOS */}
      <SidebarRight
        activeStudio={activeStudio}
        showRightSidebar={showRightSidebar}
        isWide={rightSidebarWide}
        onSelectStudio={(studio) => {
          setActiveStudio(studio);
          setShowRightSidebar(true);
          if (studio === "podcast" && podcastScript.length === 0) handleGeneratePodcast();
          if (studio === "flashcards" && flashcards.length === 0) handleGenerateFlashcards();
          if (studio === "" && !Data?.nodes?.length) handleGenerateGraph();
          if (studio === "debate" && debateTranscript.length === 0) handleStartDebate();
          if (studio === "vault" && !vaultAudit) handleVaultAudit();
          if (studio === "quiz" && quizQuestions.length === 0) handleGenerateQuiz();
          if (studio === "summary" && !summaryText) handleGenerateSummary();
        }}
        podcastProps={{
          script: podcastScript,
          isLoading: isGeneratingPodcast,
          onGenerate: handleGeneratePodcast,
          onClose: () => setActiveStudio("none"),
        }}
        flashcardProps={{
          cards: flashcards,
          isLoading: isGeneratingFlashcards,
          onGenerate: handleGenerateFlashcards,
          onClose: () => setActiveStudio("none"),
          onAddCard: (newCard: any) => setFlashcards([...flashcards, newCard]),
        }}
        Props={{
          data: 
          isLoading: isGeneratingX,
          onGenerate: handleGenerateGraph,
          onClose: () => setActiveStudio("none"),
        }}
        debateProps={{
          transcript: debateTranscript,
          isLoading: isDebating,
          onRestart: handleStartDebate,
          onClose: () => setActiveStudio("none"),
        }}
        vaultProps={{
          audit: vaultAudit,
          isLoading: isAuditing,
          onAudit: handleVaultAudit,
          onClose: () => setActiveStudio("none"),
        }}
        quizProps={{
          questions: quizQuestions,
          isLoading: isGeneratingQuiz,
          onGenerate: handleGenerateQuiz,
          onClose: () => setActiveStudio("none"),
        }}
        summaryProps={{
          summary: summaryText,
          isLoading: isGeneratingSummary,
          onGenerate: handleGenerateSummary,
          onClose: () => setActiveStudio("none"),
        }}
        voiceProps={{
          onTranscription: (text: string) => {
            setInput(text);
          },
          onClose: () => setActiveStudio("none"),
        }}
        settingsProps={{
          settings: appSettings,
          apiKey: apiKey,
          onUpdateSettings: (newSettings: any) => setAppSettings(newSettings),
          onUpdateApiKey: updateApiKey,
          onClose: () => setActiveStudio("none"),
        }}
      />
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
