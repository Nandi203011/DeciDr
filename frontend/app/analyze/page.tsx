"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface Option {
  name: string;
  financial_security: number;
  personal_growth: number;
  relationships: number;
  autonomy: number;
  stability: number;
  achievement: number;
  wellbeing: number;
  stress_level: number;
}

const defaultOption = (): Option => ({
  name: "",
  financial_security: 5,
  personal_growth: 5,
  relationships: 5,
  autonomy: 5,
  stability: 5,
  achievement: 5,
  wellbeing: 5,
  stress_level: 5,
});

const VALUE_FIELDS = [
  { key: "financial_security", label: "Financial Security", desc: "How financially secure is this option?" },
  { key: "personal_growth", label: "Personal Growth", desc: "How much will you learn and grow?" },
  { key: "relationships", label: "Relationships", desc: "How does this affect your relationships?" },
  { key: "autonomy", label: "Autonomy", desc: "How much freedom and control do you have?" },
  { key: "stability", label: "Stability", desc: "How predictable and stable is this?" },
  { key: "achievement", label: "Achievement", desc: "How much does this help you achieve your goals?" },
  { key: "wellbeing", label: "Wellbeing", desc: "How happy will this make you?" },
  { key: "stress_level", label: "Stress Level", desc: "How much stress does this cause? (higher = more stress)" },
] as const;

const getVal = (v: number | number[]): number =>
  typeof v === "number" ? v : v[0];

export default function AnalyzePage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [question, setQuestion] = useState("");
  const [category, setCategory] = useState("");
  const [options, setOptions] = useState<Option[]>([defaultOption(), defaultOption()]);
  const [weights, setWeights] = useState({
    financial_security: 14,
    personal_growth: 15,
    relationships: 14,
    autonomy: 15,
    stability: 14,
    achievement: 14,
    wellbeing: 14,
  });
  const [emotionalState, setEmotionalState] = useState("");
  const [emotionalIntensity, setEmotionalIntensity] = useState(5);
  const [riskTolerance, setRiskTolerance] = useState("");
  const [timeInvested, setTimeInvested] = useState(0);
  const [moneyInvested, setMoneyInvested] = useState(0);
  const [satisfaction, setSatisfaction] = useState(5);
  const [isReversible, setIsReversible] = useState(true);
  const [timePressure, setTimePressure] = useState(false);

  const weightsTotal = Object.values(weights).reduce((a, b) => a + b, 0);

  const updateOption = (idx: number, field: keyof Option, value: string | number) => {
    setOptions((prev) => {
      const updated = [...prev];
      updated[idx] = { ...updated[idx], [field]: value };
      return updated;
    });
  };

  const addOption = () => {
    if (options.length < 5) setOptions((prev) => [...prev, defaultOption()]);
  };

  const removeOption = (idx: number) => {
    if (options.length > 2) setOptions((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleSubmit = async () => {
    if (weightsTotal !== 100) {
      setError(`Your value weights must sum to 100. Currently: ${weightsTotal}`);
      return;
    }
    setLoading(true);
    setError("");
    const payload = {
      question,
      category,
      options,
      values_weights: weights,
      emotional_state: emotionalState,
      emotional_intensity: emotionalIntensity,
      risk_tolerance: riskTolerance,
      time_already_invested_months: timeInvested,
      money_already_invested: moneyInvested,
      current_situation_satisfaction: satisfaction,
      is_reversible: isReversible,
      time_pressure: timePressure,
    };
    try {
      const res = await axios.post("http://localhost:8000/api/analyze", payload);
      localStorage.setItem("decidr_result", JSON.stringify(res.data.result));
      localStorage.setItem("decidr_web_data", JSON.stringify(res.data.web_data || null));
      router.push("/result");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Something went wrong. Please try again.");
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="bg-white border-b border-slate-100 px-6 py-4 flex items-center justify-between">
        <a href="/" className="text-xl font-bold text-slate-900">DeciDr</a>
        <div className="flex gap-2">
          {[1, 2, 3, 4].map((s) => (
            <div
              key={s}
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                ${step === s ? "bg-blue-600 text-white" : step > s ? "bg-blue-100 text-blue-600" : "bg-slate-100 text-slate-400"}`}
            >
              {s}
            </div>
          ))}
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-10">

        {/* STEP 1 */}
        {step === 1 && (
          <Card>
            <CardHeader>
              <CardTitle>What decision are you facing?</CardTitle>
              <p className="text-slate-500 text-sm">Be specific — the more detail, the better the analysis.</p>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>Your decision question</Label>
                <Input
                  placeholder="e.g. Should I quit my job and start freelancing?"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  maxLength={300}
                />
                <p className="text-xs text-slate-400">{question.length}/300</p>
              </div>
              <div className="space-y-2">
                <Label>Category</Label>
                <Select onValueChange={setCategory} value={category}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a category" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="career">Career</SelectItem>
                    <SelectItem value="education">Education</SelectItem>
                    <SelectItem value="financial">Financial</SelectItem>
                    <SelectItem value="purchase">Purchase</SelectItem>
                    <SelectItem value="relationship">Relationship</SelectItem>
                    <SelectItem value="lifestyle">Lifestyle</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button className="w-full" disabled={question.length < 10 || !category} onClick={() => setStep(2)}>
                Continue →
              </Button>
            </CardContent>
          </Card>
        )}

        {/* STEP 2 */}
        {step === 2 && (
          <div className="space-y-4">
            <div className="mb-6">
              <h2 className="text-xl font-bold text-slate-900">Rate your options</h2>
              <p className="text-slate-500 text-sm mt-1">
                For each option, rate how well it scores on each dimension (1 = very low, 10 = very high).
              </p>
            </div>
            {options.map((opt, idx) => (
              <Card key={idx}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">Option {idx + 1}</CardTitle>
                    {options.length > 2 && (
                      <button onClick={() => removeOption(idx)} className="text-red-400 text-sm hover:text-red-600">
                        Remove
                      </button>
                    )}
                  </div>
                  <Input
                    placeholder={`Option name (e.g. ${idx === 0 ? "Stay at job" : "Quit and freelance"})`}
                    value={opt.name}
                    onChange={(e) => updateOption(idx, "name", e.target.value)}
                    maxLength={100}
                  />
                </CardHeader>
                <CardContent className="space-y-5">
                  {VALUE_FIELDS.map(({ key, label, desc }) => (
                    <div key={key} className="space-y-2">
                      <div className="flex justify-between items-center">
                        <Label className="text-sm">{label}</Label>
                        <Badge variant="outline" className="text-xs">
                          {opt[key as keyof Option]}/10
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-400">{desc}</p>
                      <Slider
                        min={1}
                        max={10}
                        step={1}
                        value={[opt[key as keyof Option] as number]}
                        onValueChange={(v) => updateOption(idx, key as keyof Option, getVal(v))}
                        className="w-full"
                      />
                    </div>
                  ))}
                </CardContent>
              </Card>
            ))}
            {options.length < 5 && (
              <Button variant="outline" className="w-full" onClick={addOption}>
                + Add another option
              </Button>
            )}
            <div className="flex gap-3">
              <Button variant="outline" className="flex-1" onClick={() => setStep(1)}>← Back</Button>
              <Button className="flex-1" disabled={options.some((o) => o.name.length < 1)} onClick={() => setStep(3)}>
                Continue →
              </Button>
            </div>
          </div>
        )}

        {/* STEP 3 */}
        {step === 3 && (
          <Card>
            <CardHeader>
              <CardTitle>What matters most to you?</CardTitle>
              <p className="text-slate-500 text-sm">
                Set how much you personally value each dimension. Must sum to 100.
                Based on Schwartz Values Theory (1992).
              </p>
              <div className={`text-sm font-medium ${weightsTotal === 100 ? "text-green-600" : "text-red-500"}`}>
                Total: {weightsTotal}/100 {weightsTotal === 100 ? "✓" : "— adjust to reach 100"}
              </div>
            </CardHeader>
            <CardContent className="space-y-5">
              {Object.entries(weights).map(([key, val]) => (
                <div key={key} className="space-y-2">
                  <div className="flex justify-between">
                    <Label className="text-sm capitalize">{key.replace(/_/g, " ")}</Label>
                    <Badge variant="outline">{val}%</Badge>
                  </div>
                  <Slider
                    min={0}
                    max={50}
                    step={1}
                    value={[val]}
                    onValueChange={(v) => setWeights((prev) => ({ ...prev, [key]: getVal(v) }))}
                  />
                </div>
              ))}
              <div className="flex gap-3 pt-4">
                <Button variant="outline" className="flex-1" onClick={() => setStep(2)}>← Back</Button>
                <Button className="flex-1" disabled={weightsTotal !== 100} onClick={() => setStep(4)}>
                  Continue →
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* STEP 4 */}
        {step === 4 && (
          <Card>
            <CardHeader>
              <CardTitle>Tell us about your context</CardTitle>
              <p className="text-slate-500 text-sm">
                This helps DeciDr detect cognitive biases and adjust the psychological analysis.
              </p>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label>How are you feeling right now?</Label>
                <Select onValueChange={setEmotionalState} value={emotionalState}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select your emotional state" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="calm">Calm</SelectItem>
                    <SelectItem value="neutral">Neutral</SelectItem>
                    <SelectItem value="anxious">Anxious</SelectItem>
                    <SelectItem value="angry">Angry</SelectItem>
                    <SelectItem value="sad">Sad</SelectItem>
                    <SelectItem value="fearful">Fearful</SelectItem>
                    <SelectItem value="excited">Excited</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>Emotional intensity</Label>
                  <Badge variant="outline">{emotionalIntensity}/10</Badge>
                </div>
                <Slider
                  min={1} max={10} step={1}
                  value={[emotionalIntensity]}
                  onValueChange={(v) => setEmotionalIntensity(getVal(v))}
                />
              </div>

              <div className="space-y-2">
                <Label>Your risk tolerance</Label>
                <Select onValueChange={setRiskTolerance} value={riskTolerance}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select risk tolerance" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low — I prefer safe options</SelectItem>
                    <SelectItem value="medium">Medium — balanced</SelectItem>
                    <SelectItem value="high">High — I am comfortable with risk</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <Label>How satisfied are you with your current situation?</Label>
                  <Badge variant="outline">{satisfaction}/10</Badge>
                </div>
                <Slider
                  min={1} max={10} step={1}
                  value={[satisfaction]}
                  onValueChange={(v) => setSatisfaction(getVal(v))}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Months invested in current path</Label>
                  <Input
                    type="number" min={0} max={600}
                    value={timeInvested}
                    onChange={(e) => setTimeInvested(Number(e.target.value))}
                    placeholder="0"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Money invested</Label>
                  <Input
                    type="number" min={0}
                    value={moneyInvested}
                    onChange={(e) => setMoneyInvested(Number(e.target.value))}
                    placeholder="0"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Is this decision reversible?</Label>
                  <div className="flex gap-2 pt-1">
                    <Button size="sm" variant={isReversible ? "default" : "outline"} onClick={() => setIsReversible(true)}>Yes</Button>
                    <Button size="sm" variant={!isReversible ? "default" : "outline"} onClick={() => setIsReversible(false)}>No</Button>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Are you under time pressure?</Label>
                  <div className="flex gap-2 pt-1">
                    <Button size="sm" variant={timePressure ? "default" : "outline"} onClick={() => setTimePressure(true)}>Yes</Button>
                    <Button size="sm" variant={!timePressure ? "default" : "outline"} onClick={() => setTimePressure(false)}>No</Button>
                  </div>
                </div>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-100 rounded-lg p-3 text-sm text-red-600">
                  {error}
                </div>
              )}

              <div className="flex gap-3 pt-2">
                <Button variant="outline" className="flex-1" onClick={() => setStep(3)}>← Back</Button>
                <Button
                  className="flex-1"
                  disabled={!emotionalState || !riskTolerance || loading}
                  onClick={handleSubmit}
                >
                  {loading ? "Analyzing..." : "Analyze Decision →"}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </main>
  );
}
