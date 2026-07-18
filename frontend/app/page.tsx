"use client";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

export default function Home() {
  const features = [
    {
      icon: "🧠",
      title: "Prospect Theory Engine",
      description: "Implements Kahneman & Tversky's (1992) CPT formulas — calculates the psychological value of each option, not just the financial value.",
    },
    {
      icon: "⚖️",
      title: "Values Alignment",
      description: "Based on Schwartz's Theory of Basic Human Values (1992), validated across 60+ countries. Weights decisions against what YOU personally care about.",
    },
    {
      icon: "🔍",
      title: "Cognitive Bias Detection",
      description: "Automatically detects sunk cost fallacy, status quo bias, loss aversion, and 4 more biases — with research citations for each.",
    },
    {
      icon: "📋",
      title: "Pre-Mortem Analysis",
      description: "Klein (2007) pre-mortem technique — imagine the decision failed and work backwards. Increases failure identification accuracy by 30%.",
    },
  ];

  const biases = [
    "Sunk Cost Fallacy", "Status Quo Bias", "Loss Aversion",
    "Present Bias", "Emotional Decision Making", "Time Pressure Bias", "Reversibility Neglect",
  ];

  return (
    <main className="min-h-screen bg-white">
      {/* Nav */}
      <nav className="border-b border-slate-100 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl font-bold text-slate-900">DeciDr</span>
          <Badge variant="secondary" className="text-xs">Beta</Badge>
        </div>
        <div className="flex gap-2">
          <a href="/chat">
            <Button size="sm" variant="outline">Quick Mode</Button>
          </a>
          <a href="/analyze">
            <Button size="sm">Guided Form</Button>
          </a>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-6 pt-24 pb-16 text-center">
        <Badge variant="outline" className="mb-6 text-slate-500">
          Grounded in Nobel Prize-winning psychology
        </Badge>
        <h1 className="text-5xl font-bold text-slate-900 leading-tight mb-6">
          Decisions backed by{" "}
          <span className="text-blue-600">real psychology</span>
        </h1>
        <p className="text-xl text-slate-500 max-w-2xl mx-auto mb-10 leading-relaxed">
          DeciDr analyzes your decisions using Cumulative Prospect Theory,
          Schwartz Values Framework, and automated cognitive bias detection —
          not just pros and cons.
        </p>

        {/* Two mode cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto mb-8">
          <a href="/chat" className="block">
            <div className="border-2 border-blue-200 bg-blue-50 rounded-xl p-6 text-left hover:border-blue-400 transition-colors cursor-pointer h-full">
              <div className="text-2xl mb-2">⚡</div>
              <h3 className="font-bold text-slate-900 mb-1">Quick Mode</h3>
              <p className="text-sm text-slate-500">
                Just describe your situation in plain text. DeciDr understands and analyzes automatically.
              </p>
              <p className="text-xs text-blue-500 mt-3 font-medium">~1 minute →</p>
            </div>
          </a>
          <a href="/analyze" className="block">
            <div className="border-2 border-slate-200 bg-slate-50 rounded-xl p-6 text-left hover:border-slate-400 transition-colors cursor-pointer h-full">
              <div className="text-2xl mb-2">🎯</div>
              <h3 className="font-bold text-slate-900 mb-1">Guided Form</h3>
              <p className="text-sm text-slate-500">
                Step-by-step form for precise control over how each option is rated and weighted.
              </p>
              <p className="text-xs text-slate-400 mt-3 font-medium">~3 minutes →</p>
            </div>
          </a>
        </div>
      </section>

      {/* Bias chips */}
      <section className="bg-slate-50 py-10">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <p className="text-sm text-slate-400 mb-4 uppercase tracking-wide">Cognitive biases we detect</p>
          <div className="flex flex-wrap gap-2 justify-center">
            {biases.map((bias) => (
              <Badge key={bias} variant="secondary" className="text-sm py-1 px-3">{bias}</Badge>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-4xl mx-auto px-6 py-20">
        <h2 className="text-3xl font-bold text-slate-900 text-center mb-12">
          Three psychology layers, one recommendation
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {features.map((f) => (
            <Card key={f.title} className="border-slate-100">
              <CardContent className="p-6">
                <div className="text-3xl mb-3">{f.icon}</div>
                <h3 className="font-semibold text-slate-900 mb-2">{f.title}</h3>
                <p className="text-slate-500 text-sm leading-relaxed">{f.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Research */}
      <section className="bg-slate-50 py-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-bold text-slate-900 mb-8">Built on peer-reviewed research</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left">
            {[
              { year: "1979", title: "Prospect Theory", authors: "Kahneman & Tversky", journal: "Econometrica" },
              { year: "1992", title: "Schwartz Values Theory", authors: "Schwartz, S.H.", journal: "Advances in Exp. Social Psychology" },
              { year: "2015", title: "Emotion & Decision Making", authors: "Lerner et al.", journal: "Annual Review of Psychology" },
              { year: "1985", title: "Sunk Cost Fallacy", authors: "Arkes & Blumer", journal: "OBHDP" },
              { year: "2007", title: "Pre-Mortem Technique", authors: "Klein, G.", journal: "Harvard Business Review" },
              { year: "2024", title: "Automatic Bias ID", authors: "Ramos, Campos & Baião", journal: "arXiv:2405.14067" },
            ].map((paper) => (
              <div key={paper.title} className="bg-white rounded-lg p-4 border border-slate-100">
                <span className="text-xs text-blue-500 font-medium">{paper.year}</span>
                <p className="font-medium text-slate-900 text-sm mt-1">{paper.title}</p>
                <p className="text-xs text-slate-400 mt-1">{paper.authors}</p>
                <p className="text-xs text-slate-300">{paper.journal}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-4xl mx-auto px-6 py-20 text-center">
        <h2 className="text-3xl font-bold text-slate-900 mb-4">Ready to make a better decision?</h2>
        <p className="text-slate-500 mb-8">DeciDr does the psychology. You make the call.</p>
        <div className="flex gap-4 justify-center">
          <a href="/chat">
            <Button size="lg" className="px-8">⚡ Quick Mode</Button>
          </a>
          <a href="/analyze">
            <Button size="lg" variant="outline" className="px-8">🎯 Guided Form</Button>
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-100 py-8 text-center">
        <p className="text-sm text-slate-400">
          DeciDr — Psychology-backed decision engine.{" "}
          <span className="text-slate-300">Built with CPT, Schwartz Values and Bias Detection.</span>
        </p>
        <p className="text-xs text-slate-300 mt-1">UI components by shadcn/ui (MIT License)</p>
      </footer>
    </main>
  );
}
