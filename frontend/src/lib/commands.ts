import { 
  Headphones, 
  LayoutList, 
  GraduationCap, 
  Mic, 
  BookOpen,
  MessageSquare,
  ShieldCheck,
  Settings2,
  LucideIcon
} from "lucide-react";

export interface Command {
  id: string;
  label: string;
  description: string;
  icon: LucideIcon;
}

export const COMMANDS: Command[] = [
  {
    id: "podcast",
    label: "/podcast",
    description: "Generate an AI audio deep-dive discussion",
    icon: Headphones,
  },
  {
    id: "flashcards",
    label: "/flashcards",
    description: "Extract active recall study concepts with 3D flips",
    icon: LayoutList,
  },
  {
    id: "debate",
    label: "/debate",
    description: "Multi-agent research debate (Skeptic, Weaver, Veritas)",
    icon: MessageSquare,
  },
  {
    id: "vault",
    label: "/vault",
    description: "Audit document for truth, bias, and citations",
    icon: ShieldCheck,
  },
  {
    id: "quiz",
    label: "/quiz",
    description: "Generate an adaptive cognitive assessment quiz",
    icon: GraduationCap,
  },
  {
    id: "summary",
    label: "/summary",
    description: "Generate structured 5-point executive synthesis",
    icon: BookOpen,
  },
  {
    id: "voice",
    label: "/voice",
    description: "Talk to your document hands-free",
    icon: Mic,
  },
  {
    id: "settings",
    label: "/settings",
    description: "Preferences, focus mode, and API credentials",
    icon: Settings2,
  }
];
