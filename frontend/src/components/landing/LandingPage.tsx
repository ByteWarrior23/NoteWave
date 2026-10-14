"use client";

import React, { useState, useEffect } from "react";
import { useTheme } from "next-themes";
import { 
  Sun, Moon, UploadCloud, Loader2, Sparkles, 
  Headphones, LayoutList, Zap, ShieldCheck, ArrowRight, Key
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

interface LandingPageProps {
  onEnter: () => void;
  onUploadFile: (file: File) => Promise<void>;
  isUploading: boolean;
  apiKey: string;
  onUpdateApiKey: (key: string) => void;
}

export default function LandingPage({
  onEnter,
  onUploadFile,
  isUploading,
  apiKey,
  onUpdateApiKey,
}: LandingPageProps) {
  const { setTheme, theme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [tempApiKey, setTempApiKey] = useState(apiKey);
  const [isKeyDialogOpen, setIsKeyDialogOpen] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files?.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type === "application/pdf" || file.name.endsWith(".pdf")) {
        onUploadFile(file);
      } else {
        alert("Please select a valid PDF file.");
      }
    }
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      onUploadFile(file);
    }
  };

  const handleSaveApiKey = () => {
    onUpdateApiKey(tempApiKey);
    setIsKeyDialogOpen(false);
  };

  return (
    <div className="min-h-screen flex flex-col bg-white dark:bg-black text-zinc-900 dark:text-zinc-100 font-sans selection:bg-zinc-800 selection:text-white">
      {/* HEADER */}
      <header className="h-16 flex items-center justify-between px-6 md:px-12 border-b border-zinc-200 dark:border-zinc-900 bg-white/70 dark:bg-black/70 backdrop-blur-xl z-20">
        <div className="flex items-center gap-2.5">
          <div className="h-7 w-7 rounded-xl bg-black dark:bg-white flex items-center justify-center text-white dark:text-black font-bold text-xs shadow-lg">
            <Zap className="w-4 h-4 fill-current" />
          </div>
          <span className="font-bold text-base tracking-tight">NoteWave</span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-zinc-400 font-mono">
            RAG Copilot
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Dialog open={isKeyDialogOpen} onOpenChange={setIsKeyDialogOpen}>
            <DialogTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-zinc-500 hover:text-zinc-200 gap-1.5 h-8 rounded-full border border-zinc-800/80"
              >
                <Key className="w-3.5 h-3.5" />
                <span className="font-mono">API Key</span>
              </Button>
            </DialogTrigger>
            <DialogContent className="dark:bg-zinc-950 dark:border-zinc-800">
              <DialogHeader>
                <DialogTitle>Configure Google Gemini Key</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 mt-2">
                <p className="text-xs text-zinc-400">
                  Enter your Google Gemini API key to power RAG search, embeddings, and intelligence studios.
                </p>
                <Input
                  type="password"
                  value={tempApiKey}
                  onChange={(e) => setTempApiKey(e.target.value)}
                  placeholder="AIzaSy... or AQ..."
                  className="bg-zinc-900 border-zinc-800 font-mono text-xs"
                />
                <Button onClick={handleSaveApiKey} className="w-full bg-white text-black font-semibold text-xs">
                  Save Credentials
                </Button>
              </div>
            </DialogContent>
          </Dialog>

          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="h-8 w-8 icon-btn"
          >
            {mounted ? (theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />) : null}
          </Button>

          <Button
            onClick={onEnter}
            variant="outline"
            className="rounded-full text-xs font-semibold h-8 px-4 border-zinc-300 dark:border-zinc-800 hover:bg-zinc-900"
          >
            Open Dashboard <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
          </Button>
        </div>
      </header>

      {/* HERO SECTION */}
      <main className="flex-1 flex flex-col items-center justify-center p-6 relative overflow-hidden">
        {/* Subtle glowing backdrop orb */}
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
          <div className="w-[640px] h-[640px] bg-purple-600/10 dark:bg-purple-900/10 rounded-full blur-[140px]" />
          <div className="w-[420px] h-[420px] bg-indigo-600/10 dark:bg-blue-900/10 rounded-full blur-[100px] translate-x-32 -translate-y-20" />
        </div>

        <div className="relative z-10 text-center max-w-3xl mx-auto space-y-10 w-full flex flex-col items-center">
          <div className="space-y-4">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-[11px] font-medium text-zinc-600 dark:text-zinc-400 mb-2">
              <Sparkles className="w-3.5 h-3.5 text-purple-400" />
              <span>Next-Generation Document Intelligence</span>
            </div>
            <h1 className="text-4xl md:text-7xl font-bold tracking-tight text-zinc-900 dark:text-white">
              Chat with your documents.
            </h1>
            <p className="text-base md:text-lg text-zinc-500 dark:text-zinc-400 max-w-xl mx-auto leading-relaxed">
              Transform any PDF into conversational deep dives, 3D concept flashcards, audio podcasts, and multi-agent debates.
            </p>
          </div>

          {/* DROPZONE */}
          <div className="w-full max-w-lg">
            <div
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              onDrop={onDrop}
              className={`group relative border-2 border-dashed rounded-3xl p-10 transition-all duration-300 cursor-pointer ${
                isDragging
                  ? "border-purple-500 bg-purple-500/10 scale-[1.02]"
                  : "border-zinc-300 dark:border-zinc-800 hover:border-zinc-500 dark:hover:border-zinc-700 bg-zinc-50/50 dark:bg-zinc-950/60 shadow-2xl"
              }`}
            >
              <div className="flex flex-col items-center gap-4">
                <div
                  className={`p-4 rounded-2xl transition-colors ${
                    isDragging
                      ? "bg-purple-500/20 text-purple-300"
                      : "bg-zinc-100 dark:bg-zinc-900 text-zinc-400 group-hover:text-zinc-900 dark:group-hover:text-white"
                  }`}
                >
                  {isUploading ? (
                    <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
                  ) : (
                    <UploadCloud className="w-8 h-8" />
                  )}
                </div>
                <div className="space-y-1.5 text-center">
                  <p className="font-semibold text-sm text-zinc-800 dark:text-zinc-200">
                    {isUploading ? "Chunking & Synthesizing Document..." : "Drop PDF document here"}
                  </p>
                  <p className="text-xs text-zinc-400">or click to browse from your device</p>
                </div>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={onFileChange}
                  disabled={isUploading}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
              </div>
            </div>
          </div>

          {/* FEATURES CHIPS */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 w-full max-w-2xl pt-4">
            <div className="p-3 rounded-2xl bg-zinc-100/50 dark:bg-zinc-950/40 border border-zinc-200 dark:border-zinc-900 flex items-center gap-2.5 text-left">
              <Headphones className="w-4 h-4 text-purple-400 shrink-0" />
              <div>
                <p className="text-xs font-bold">Podcast Studio</p>
                <p className="text-[10px] text-zinc-500">2-host audio scripts</p>
              </div>
            </div>
            <div className="p-3 rounded-2xl bg-zinc-100/50 dark:bg-zinc-950/40 border border-zinc-200 dark:border-zinc-900 flex items-center gap-2.5 text-left">
              <LayoutList className="w-4 h-4 text-emerald-400 shrink-0" />
              <div>
                <p className="text-xs font-bold">3D Flashcards</p>
                <p className="text-[10px] text-zinc-500">Active recall decks</p>
              </div>
            </div>
            <div className="p-3 rounded-2xl bg-zinc-100/50 dark:bg-zinc-950/40 border border-zinc-200 dark:border-zinc-900 flex items-center gap-2.5 text-left">
              <ShieldCheck className="w-4 h-4 text-teal-400 shrink-0" />
              <div>
                <p className="text-xs font-bold">Verified Vault</p>
                <p className="text-[10px] text-zinc-500">Integrity & bias audit</p>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* FOOTER */}
      <footer className="py-6 border-t border-zinc-200 dark:border-zinc-900 bg-white/80 dark:bg-black/80 backdrop-blur-sm z-20">
        <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-zinc-500">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-zinc-900 dark:text-zinc-200">NoteWave</span>
            <span>• Powered by Google Gemini 2.5 Flash & ChromaDB</span>
          </div>
          <div className="flex items-center gap-4">
            <button onClick={onEnter} className="hover:text-zinc-900 dark:hover:text-white transition-colors">
              Launch Workspace
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}
