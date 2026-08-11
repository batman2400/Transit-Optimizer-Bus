"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import {
  MapPin,
  Clock,
  Calendar,
  CloudRain,
  AlertTriangle,
  Bus,
  Users,
  Activity,
  Timer,
} from "lucide-react";

/** Convert JS Date (Sun=0) → pandas/Python dayofweek (Mon=0). */
function pythonDayOfWeek(d: Date): number {
  return (d.getDay() + 6) % 7;
}

export default function Dashboard() {
  const [date, setDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [hour, setHour] = useState(new Date().getHours());
  const [direction, setDirection] = useState("Inbound_to_Pettah");
  const [weather, setWeather] = useState("Clear");
  const [eventOverride, setEventOverride] = useState(false);

  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchWeather() {
      try {
        const res = await fetch(
          "https://api.open-meteo.com/v1/forecast?latitude=6.9271&longitude=79.8612&current_weather=true"
        );
        const json = await res.json();
        const code = json.current_weather.weathercode;
        setWeather(code >= 51 ? "Rain" : "Clear");
      } catch (err) {
        console.error("Failed to fetch weather", err);
      }
    }
    fetchWeather();
  }, []);

  const fetchPredictions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Parse as local calendar date (avoid UTC shift from Date('YYYY-MM-DD'))
      const [y, m, day] = date.split("-").map(Number);
      const selectedDate = new Date(y, m - 1, day);
      const dow = pythonDayOfWeek(selectedDate);

      const payload = {
        date,
        hour,
        direction,
        day_of_week: dow,
        is_weekend: dow >= 5 ? 1 : 0,
        // Backend recomputes LK holidays from date; send placeholder
        is_public_holiday: 0,
        is_school_holiday: [4, 8, 12].includes(selectedDate.getMonth() + 1) ? 1 : 0,
        is_payday_week:
          selectedDate.getDate() >= 25 || selectedDate.getDate() <= 5 ? 1 : 0,
        event_override: eventOverride ? 1 : 0,
        weather,
      };

      const res = await fetch("http://127.0.0.1:8000/dispatch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("API request failed — is the backend running?");

      const result = await res.json();
      setData(result);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }, [date, hour, direction, weather, eventOverride]);

  useEffect(() => {
    fetchPredictions();
  }, [fetchPredictions]);

  const chartData =
    data?.stops.map((stop: string, idx: number) => ({
      name: stop,
      passengers: Math.round(data.predictions[idx]),
    })) || [];

  const rec = data?.dispatch_recommendation;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-6 md:p-10 font-sans selection:bg-indigo-500/30">
      <div className="max-w-7xl mx-auto space-y-8">
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent flex items-center gap-2">
              <Bus className="text-indigo-400" />
              SLTB Route 100
            </h1>
            <p className="text-slate-400 mt-1">
              Smart Transit Optimization Dashboard
            </p>
          </div>

          <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-xl px-4 py-2 flex items-center gap-3">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500" />
            </span>
            <span className="text-sm font-medium text-slate-300">
              System Active
            </span>
          </div>
        </header>

        {error && (
          <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-3 space-y-6">
            <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6">
              <h2 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
                <Activity className="w-5 h-5 text-indigo-400" />
                Parameters
              </h2>

              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-400 flex items-center gap-2">
                    <MapPin className="w-4 h-4" /> Direction
                  </label>
                  <select
                    value={direction}
                    onChange={(e) => setDirection(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all"
                  >
                    <option value="Inbound_to_Pettah">
                      Inbound (Panadura → Pettah)
                    </option>
                    <option value="Outbound_to_Panadura">
                      Outbound (Pettah → Panadura)
                    </option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-400 flex items-center gap-2">
                    <Calendar className="w-4 h-4" /> Date
                  </label>
                  <input
                    type="date"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-400 flex items-center gap-2">
                    <Clock className="w-4 h-4" /> Hour ({hour}:00)
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="23"
                    value={hour}
                    onChange={(e) => setHour(parseInt(e.target.value))}
                    className="w-full accent-indigo-500"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-400 flex items-center gap-2">
                    <CloudRain className="w-4 h-4" /> Weather
                  </label>
                  <select
                    value={weather}
                    onChange={(e) => setWeather(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all"
                  >
                    <option value="Clear">Clear</option>
                    <option value="Rain">Rain</option>
                  </select>
                </div>

                <div className="pt-2">
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <div className="relative">
                      <input
                        type="checkbox"
                        checked={eventOverride}
                        onChange={(e) => setEventOverride(e.target.checked)}
                        className="sr-only"
                      />
                      <div
                        className={`block w-10 h-6 rounded-full transition-colors ${
                          eventOverride ? "bg-indigo-500" : "bg-slate-800"
                        }`}
                      />
                      <div
                        className={`absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${
                          eventOverride ? "translate-x-4" : ""
                        }`}
                      />
                    </div>
                    <span className="text-sm font-medium text-slate-300 flex items-center gap-2 group-hover:text-indigo-300 transition-colors">
                      <AlertTriangle
                        className={`w-4 h-4 ${
                          eventOverride ? "text-amber-400" : "text-slate-500"
                        }`}
                      />
                      Event Override
                    </span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-9 space-y-8">
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6">
              <div className="bg-gradient-to-br from-indigo-900/40 to-slate-900/50 backdrop-blur-xl border border-indigo-500/20 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
                <h3 className="text-slate-400 font-medium text-sm">
                  Recommended Headway
                </h3>
                <div className="mt-4 flex items-baseline gap-2">
                  <span className="text-4xl font-bold text-white tracking-tight">
                    {rec ? rec.headway_minutes : "--"}
                  </span>
                  <span className="text-indigo-300 font-medium">mins</span>
                </div>
              </div>

              <div className="bg-gradient-to-br from-cyan-900/40 to-slate-900/50 backdrop-blur-xl border border-cyan-500/20 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
                <h3 className="text-slate-400 font-medium text-sm">
                  Buses Required (Per Hr)
                </h3>
                <div className="mt-4 flex items-baseline gap-2">
                  <span className="text-4xl font-bold text-white tracking-tight">
                    {rec ? rec.buses_needed : "--"}
                  </span>
                  <span className="text-cyan-300 font-medium flex items-center gap-1">
                    <Bus className="w-4 h-4" /> buses
                  </span>
                </div>
              </div>

              <div className="bg-gradient-to-br from-purple-900/40 to-slate-900/50 backdrop-blur-xl border border-purple-500/20 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
                <h3 className="text-slate-400 font-medium text-sm">
                  Peak Load
                  {rec?.peak_stop ? ` · ${rec.peak_stop}` : ""}
                </h3>
                <div className="mt-4 flex items-baseline gap-2">
                  <span className="text-4xl font-bold text-white tracking-tight">
                    {rec ? Math.round(rec.peak_load) : "--"}
                  </span>
                  <span className="text-purple-300 font-medium flex items-center gap-1">
                    <Users className="w-4 h-4" /> pax
                  </span>
                </div>
              </div>

              <div className="bg-gradient-to-br from-emerald-900/40 to-slate-900/50 backdrop-blur-xl border border-emerald-500/20 rounded-2xl p-6 shadow-2xl relative overflow-hidden">
                <h3 className="text-slate-400 font-medium text-sm">
                  Corridor ETA
                </h3>
                <div className="mt-4 flex items-baseline gap-2">
                  <span className="text-4xl font-bold text-white tracking-tight">
                    {rec ? rec.corridor_eta_minutes : "--"}
                  </span>
                  <span className="text-emerald-300 font-medium flex items-center gap-1">
                    <Timer className="w-4 h-4" /> mins
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 shadow-2xl">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-slate-100">
                  Demand Prediction by Stop
                </h3>
                {loading && (
                  <div className="text-sm text-indigo-400 animate-pulse flex items-center gap-2">
                    <Activity className="w-4 h-4 animate-spin" /> Updating...
                  </div>
                )}
              </div>

              <div className="h-80 w-full">
                {data ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={chartData}
                      margin={{ top: 10, right: 10, left: -20, bottom: 20 }}
                    >
                      <CartesianGrid
                        strokeDasharray="3 3"
                        stroke="#334155"
                        vertical={false}
                      />
                      <XAxis
                        dataKey="name"
                        stroke="#94a3b8"
                        fontSize={12}
                        tickMargin={10}
                        axisLine={false}
                        tickLine={false}
                        angle={-45}
                        textAnchor="end"
                      />
                      <YAxis
                        stroke="#94a3b8"
                        fontSize={12}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        cursor={{ fill: "#1e293b" }}
                        contentStyle={{
                          backgroundColor: "#0f172a",
                          border: "1px solid #334155",
                          borderRadius: "8px",
                          color: "#f8fafc",
                        }}
                        itemStyle={{ color: "#818cf8" }}
                      />
                      <Bar
                        dataKey="passengers"
                        fill="url(#colorPassengers)"
                        radius={[4, 4, 0, 0]}
                        animationDuration={1500}
                      />
                      <defs>
                        <linearGradient
                          id="colorPassengers"
                          x1="0"
                          y1="0"
                          x2="0"
                          y2="1"
                        >
                          <stop
                            offset="5%"
                            stopColor="#818cf8"
                            stopOpacity={0.9}
                          />
                          <stop
                            offset="95%"
                            stopColor="#818cf8"
                            stopOpacity={0.3}
                          />
                        </linearGradient>
                      </defs>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-slate-500">
                    Loading chart data...
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
