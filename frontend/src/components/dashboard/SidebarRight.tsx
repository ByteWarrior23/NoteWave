"use client";

import React from "react";
import { 
  Sparkles, Headphones, LayoutList, BrainCircuit, 
  MessageSquare, ShieldCheck, Mic, BookOpen 
} from "lucide-react";
import PodcastStudio from "./studios/PodcastStudio";
import FlashcardsStudio from "./studios/FlashcardsStudio";
import DebateStudio from "./studios/DebateStudio";
import VaultStudio from "./studios/VaultStudio";
import QuizStudio from "./studios/QuizStudio";
import VoiceStudio from "./studios/VoiceStudio";
import SettingsStudio from "./studios/SettingsStudio";
import SummaryStudio from "./studios/SummaryStudio";

export type StudioType =
  | "podcast"
  | "flashcards"
  | "debate"
  | "vault"
  | "quiz"
  | "summary"
  | "voice"
  | "settings"
  | "none";

interface SidebarRightProps {
  activeStudio: StudioType;
  showRightSidebar: boolean;
  isWide: boolean;
  onSelectStudio: (studio: StudioType) => void;
  podcastProps: any;
  flashcardProps: any;
  debateProps: any;
  vaultProps: any;
  quizProps: any;
  voiceProps: any;
  settingsProps: any;
  summaryProps: any;
}

export default function SidebarRight({
  activeStudio,
  showRightSidebar,
  isWide,
  onSelectStudio,
  podcastProps,
  flashcardProps,
  debateProps,
  vaultProps,
  quizProps,
  voiceProps,
  settingsProps,
  summaryProps,
}: SidebarRightProps) {
  const widthClass = !showRightSidebar
    ? "w-0 border-l-0"
    : isWide
    ? "w-[680px]"
    : "w-[380px]";

  return (
    <div
      className={`relative h-full bg-white dark:bg-black border-l border-zinc-200 dark:border-zinc-800 flex flex-col transition-all duration-300 ease-in-out shrink-0 ${widthClass}`}
    >
      <div
        className={`flex flex-col h-full overflow-hidden ${
          !showRightSidebar ? "opacity-0 invisible pointer-events-none" : "opacity-100 visible"
        }`}
      >
        {activeStudio === "none" && (
          <div className="flex-1 flex flex-col p-6 space-y-6 justify-center overflow-y-auto">
            <div className="space-y-1.5">
              <div className="h-10 w-10 rounded-xl bg-zinc-100 dark:bg-zinc-900 flex items-center justify-center mb-3">
                <Sparkles className="w-5 h-5 text-purple-400" />
              </div>
              <h3 className="text-base font-bold text-zinc-900 dark:text-white">Studio Hub</h3>
              <p className="text-xs text-zinc-400 leading-relaxed">
                Activate an intelligence studio or type <code className="text-purple-400 bg-zinc-900 px-1 py-0.5 rounded font-mono">/</code> in chat.
              </p>
            </div>

            <div className="grid gap-2.5">
              <FeatureCard
                icon={<Headphones className="w-4 h-4 text-purple-400" />}
                title="Podcast Studio"
                desc="Audio-synced 2-host deep dive conversation"
                onClick={() => onSelectStudio("podcast")}
              />
              <FeatureCard
                icon={<LayoutList className="w-4 h-4 text-emerald-400" />}
                title="3D Flashcards"
                desc="Concept decks with 3D flip card memory test"
                onClick={() => onSelectStudio("flashcards")}
              />
              <FeatureCard
                icon={<MessageSquare className="w-4 h-4 text-rose-400" />}
                title="Agentic Debate"
                desc="Dr. Skeptic, The Weaver, and Veritas in arena"
                onClick={() => onSelectStudio("debate")}
              />
              <FeatureCard
                icon={<ShieldCheck className="w-4 h-4 text-teal-400" />}
                title="Verified Vault"
                desc="Hallucination scans, bias index, and truth score"
                onClick={() => onSelectStudio("vault")}
              />
              <FeatureCard
                icon={<BrainCircuit className="w-4 h-4 text-cyan-400" />}
                title="Adaptive Quiz"
                desc="Multiple choice assessments with score reports"
                onClick={() => onSelectStudio("quiz")}
              />
              <FeatureCard
                icon={<BookOpen className="w-4 h-4 text-amber-400" />}
                title="Executive Summary"
                desc="5-point structured overview & key synthesis"
                onClick={() => onSelectStudio("summary")}
              />
              <FeatureCard
                icon={<Mic className="w-4 h-4 text-blue-400" />}
                title="Voice Immersion"
                desc="Hands-free vocal conversation with document"
                onClick={() => onSelectStudio("voice")}
              />
            </div>
          </div>
        )}

        {activeStudio === "podcast" && <PodcastStudio {...podcastProps} />}
        {activeStudio === "flashcards" && <FlashcardsStudio {...flashcardProps} />}
        {activeStudio === "debate" && <DebateStudio {...debateProps} />}
        {activeStudio === "vault" && <VaultStudio {...vaultProps} />}
        {activeStudio === "quiz" && <QuizStudio {...quizProps} />}
        {activeStudio === "voice" && <VoiceStudio {...voiceProps} />}
        {activeStudio === "settings" && <SettingsStudio {...settingsProps} />}
        {activeStudio === "summary" && <SummaryStudio {...summaryProps} />}
      </div>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  desc,
  onClick,
}: {
  icon: React.ReactNode;
  title: string;
  desc: string;
  onClick: () => void;
}) {
  return (
    <div
      onClick={onClick}
      className="flex items-start gap-3.5 p-3.5 rounded-2xl border border-zinc-200 dark:border-zinc-900 bg-zinc-50/70 dark:bg-zinc-950/60 hover:border-zinc-700 hover:bg-zinc-900/60 cursor-pointer transition-all duration-200"
    >
      <div className="mt-0.5 shrink-0">{icon}</div>
      <div className="space-y-0.5">
        <p className="text-xs font-bold text-zinc-900 dark:text-zinc-200">{title}</p>
        <p className="text-[10px] text-zinc-500 leading-tight">{desc}</p>
      </div>
    </div>
  );
}
