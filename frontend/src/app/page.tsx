"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

type HolidayMode = "auto" | "none" | "poya" | "government";
type SchoolHolidayMode = "auto" | "off" | "on";
type SchoolRushMode = "auto" | "off" | "on";
type HolidayType = "none" | "poya" | "government";

type CalendarContext = {
  date: string;
  day_of_week: number;
  day_name: string;
  is_weekend: number;
  is_public_holiday: number;
  public_holiday_name: string | null;
  is_school_holiday: number;
  is_school_rush: number;
  is_payday_week: number;
  peak_period: "am_peak" | "pm_peak" | "midday" | "off_peak" | string;
  holiday_type: HolidayType;
  holiday_mode: HolidayMode;
  school_holiday_mode: SchoolHolidayMode;
  school_rush_mode: SchoolRushMode;
  auto_holiday_type: HolidayType;
  auto_is_school_holiday: number;
  auto_is_school_rush: number;
  auto_public_holiday_name: string | null;
  override_active: boolean;
};

type DispatchData = {
  stops: string[];
  predictions: number[];
  dispatch_recommendation: {
    headway_minutes: number;
    buses_needed: number;
    peak_load: number;
    peak_stop: string;
    corridor_eta_minutes: number;
    congestion_factor?: number;
  };
  calendar_context: CalendarContext;
};

const PEAK_LABELS: Record<string, string> = {
  am_peak: "AM Peak",
  pm_peak: "PM Peak",
  midday: "Midday",
  off_peak: "Off-peak",
};

const HOLIDAY_TYPE_LABELS: Record<HolidayType, string> = {
  none: "Working day",
  poya: "Poya",
  government: "Government holiday",
};

const DAY_TYPE_OPTIONS: { value: HolidayMode; label: string }[] = [
  { value: "auto", label: "Auto" },
  { value: "none", label: "Working" },
  { value: "poya", label: "Poya" },
  { value: "government", label: "Gov't" },
];

const SCHOOL_OPTIONS: { value: SchoolHolidayMode; label: string }[] = [
  { value: "auto", label: "Auto" },
  { value: "off", label: "No" },
  { value: "on", label: "Yes" },
];

const SCHOOL_RUSH_OPTIONS: { value: SchoolRushMode; label: string }[] = [
  { value: "auto", label: "Auto" },
  { value: "off", label: "No" },
  { value: "on", label: "Yes" },
];

function stopLabel(name: string): string {
  return name.replace(/_/g, " ");
}

function isWmoRain(code: number): boolean {
  return code >= 51;
}

async function fetchColomboWeatherForDate(
  selected: string
): Promise<"Clear" | "Rain"> {
  const today = new Date();
  const todayStr = today.toISOString().split("T")[0];
  const [y, m, d] = selected.split("-").map(Number);
  const selectedDate = new Date(y, m - 1, d);
  const diffDays = Math.round(
    (selectedDate.getTime() -
      new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime()) /
      86_400_000
  );

  if (diffDays >= 0 && diffDays <= 15) {
    const res = await fetch(
      `https://api.open-meteo.com/v1/forecast?latitude=6.9271&longitude=79.8612&daily=weathercode&timezone=Asia%2FColombo&start_date=${selected}&end_date=${selected}`
    );
    const json = await res.json();
    const code = json?.daily?.weathercode?.[0];
    if (typeof code === "number") return isWmoRain(code) ? "Rain" : "Clear";
  }

  if (selected < todayStr) {
    const res = await fetch(
      `https://archive-api.open-meteo.com/v1/archive?latitude=6.9271&longitude=79.8612&daily=weathercode&timezone=Asia%2FColombo&start_date=${selected}&end_date=${selected}`
    );
    const json = await res.json();
    const code = json?.daily?.weathercode?.[0];
    if (typeof code === "number") return isWmoRain(code) ? "Rain" : "Clear";
  }

  const res = await fetch(
    "https://api.open-meteo.com/v1/forecast?latitude=6.9271&longitude=79.8612&current_weather=true"
  );
  const json = await res.json();
  const code = json?.current_weather?.weathercode ?? 0;
  return isWmoRain(code) ? "Rain" : "Clear";
}

function Segmented<T extends string>({
  value,
  options,
  onChange,
  ariaLabel,
}: {
  value: T;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
  ariaLabel: string;
}) {
  return (
    <div className="seg-group" role="group" aria-label={ariaLabel}>
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          className="seg-btn"
          data-active={value === opt.value}
          onClick={() => onChange(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

export default function Dashboard() {
  const [date, setDate] = useState(() => new Date().toISOString().split("T")[0]);
  const [hour, setHour] = useState(new Date().getHours());
  const [direction, setDirection] = useState("Inbound_to_Pettah");
  const [weather, setWeather] = useState("Clear");
  const [eventOverride, setEventOverride] = useState(false);
  const [holidayMode, setHolidayMode] = useState<HolidayMode>("auto");
  const [schoolHolidayMode, setSchoolHolidayMode] =
    useState<SchoolHolidayMode>("auto");
  const [schoolRushMode, setSchoolRushMode] = useState<SchoolRushMode>("auto");

  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<DispatchData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function loadWeather() {
      try {
        const w = await fetchColomboWeatherForDate(date);
        if (!cancelled) setWeather(w);
      } catch (err) {
        console.error("Failed to fetch weather", err);
      }
    }
    loadWeather();
    return () => {
      cancelled = true;
    };
  }, [date]);

  const fetchPredictions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        date,
        hour,
        direction,
        event_override: eventOverride ? 1 : 0,
        weather,
        holiday_mode: holidayMode,
        school_holiday_mode: schoolHolidayMode,
        school_rush_mode: schoolRushMode,
      };

      const res = await fetch("http://127.0.0.1:8000/dispatch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("API request failed — is the backend running?");

      const result = (await res.json()) as DispatchData;
      setData(result);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }, [
    date,
    hour,
    direction,
    weather,
    eventOverride,
    holidayMode,
    schoolHolidayMode,
    schoolRushMode,
  ]);

  useEffect(() => {
    fetchPredictions();
  }, [fetchPredictions]);

  const chartData =
    data?.stops.map((stop, idx) => ({
      name: stopLabel(stop),
      stop,
      passengers: Math.round(data.predictions[idx]),
    })) || [];

  const rec = data?.dispatch_recommendation;
  const cal = data?.calendar_context;
  const peakTight = Boolean(rec && (rec.buses_needed >= 2 || rec.headway_minutes < 30));
  const peakStop = rec?.peak_stop;

  const autoHint =
    holidayMode === "auto" && cal
      ? cal.auto_holiday_type === "none"
        ? "Auto suggests a working day"
        : `Auto suggests ${HOLIDAY_TYPE_LABELS[cal.auto_holiday_type]}${
            cal.auto_public_holiday_name ? ` · ${cal.auto_public_holiday_name}` : ""
          }`
      : null;

  const schoolHint =
    schoolHolidayMode === "auto" && cal
      ? cal.auto_is_school_holiday
        ? "Auto: school vacation month"
        : "Auto: term time"
      : null;

  const rushHint =
    schoolRushMode === "auto" && cal
      ? cal.auto_is_school_rush
        ? "Auto: school start/finish window"
        : "Auto: not school rush"
      : null;

  return (
    <div className="depot-atmosphere min-h-screen text-ink">
      <div className="mx-auto max-w-6xl px-5 py-8 md:px-8 md:py-10">
        {/* Masthead */}
        <header className="anim-fade-up border-b border-line pb-6">
          <p className="text-[0.7rem] font-semibold uppercase tracking-[0.22em] text-teal">
            Depot planning board
          </p>
          <div className="mt-2 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <h1 className="font-display text-4xl font-semibold tracking-tight text-ink md:text-5xl">
                SLTB Route 100
              </h1>
              <p className="mt-2 max-w-xl text-sm leading-relaxed text-muted">
                Panadura ↔ Pettah via Galle Road — stop demand forecast and
                headway recommendation for the hour ahead.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-sm">
              {cal?.peak_period && (
                <span className="border border-teal/30 bg-teal/5 px-3 py-1.5 font-semibold text-teal">
                  {PEAK_LABELS[cal.peak_period] ?? cal.peak_period}
                </span>
              )}
              {cal?.override_active && (
                <span className="border border-amber/40 bg-amber/10 px-3 py-1.5 font-semibold text-amber">
                  Override active
                </span>
              )}
              {loading && (
                <span className="text-muted">Updating…</span>
              )}
            </div>
          </div>
        </header>

        {/* Context strip */}
        {cal && (
          <div className="anim-fade-up anim-delay-1 mt-5 flex flex-wrap gap-x-5 gap-y-2 border-b border-line pb-4 text-sm text-muted">
            <span className="font-semibold text-ink">{cal.day_name}</span>
            {cal.is_weekend ? <span>Weekend</span> : null}
            {cal.is_public_holiday ? (
              <span>
                {HOLIDAY_TYPE_LABELS[cal.holiday_type]}
                {cal.public_holiday_name ? ` · ${cal.public_holiday_name}` : ""}
              </span>
            ) : (
              <span>Working day</span>
            )}
            {cal.is_school_holiday ? <span>School vacation</span> : null}
            {cal.is_school_rush ? <span>School rush</span> : null}
            {cal.is_payday_week ? <span>Payday window</span> : null}
          </div>
        )}

        {error && (
          <div className="mt-5 border border-amber/40 bg-amber/10 px-4 py-3 text-sm text-ink">
            {error}
          </div>
        )}

        <div className="mt-8 grid grid-cols-1 gap-10 lg:grid-cols-12">
          {/* Planning column */}
          <aside className="anim-fade-up anim-delay-1 lg:col-span-4 space-y-6">
            <div>
              <h2 className="font-display text-xl font-semibold text-ink">
                Plan this hour
              </h2>
              <p className="mt-1 text-sm text-muted">
                Set corridor conditions. Calendar auto-detects from date; override
                when the depot knows better.
              </p>
            </div>

            <div className="space-y-5">
              <label className="block space-y-1.5">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Direction
                </span>
                <select
                  value={direction}
                  onChange={(e) => setDirection(e.target.value)}
                  className="field-input"
                >
                  <option value="Inbound_to_Pettah">
                    Inbound — Panadura → Pettah
                  </option>
                  <option value="Outbound_to_Panadura">
                    Outbound — Pettah → Panadura
                  </option>
                </select>
              </label>

              <label className="block space-y-1.5">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Date
                </span>
                <input
                  type="date"
                  value={date}
                  onChange={(e) => setDate(e.target.value)}
                  className="field-input"
                />
              </label>

              <div className="space-y-1.5">
                <div className="flex items-baseline justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-muted">
                    Hour
                  </span>
                  <span className="font-display text-lg font-semibold text-teal">
                    {String(hour).padStart(2, "0")}:00
                  </span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={23}
                  value={hour}
                  onChange={(e) => setHour(parseInt(e.target.value, 10))}
                  className="hour-range"
                />
              </div>

              <label className="block space-y-1.5">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Weather
                </span>
                <select
                  value={weather}
                  onChange={(e) => setWeather(e.target.value)}
                  className="field-input"
                >
                  <option value="Clear">Clear</option>
                  <option value="Rain">Rain</option>
                </select>
                <p className="text-xs text-muted">
                  Prefills from Open-Meteo Colombo for the selected date.
                </p>
              </label>

              <div className="space-y-1.5">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted">
                  Day type
                </span>
                <Segmented
                  ariaLabel="Day type"
                  value={holidayMode}
                  options={DAY_TYPE_OPTIONS}
                  onChange={setHolidayMode}
                />
                {autoHint && (
                  <p className="text-xs text-muted">{autoHint}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted">
                  School vacation
                </span>
                <Segmented
                  ariaLabel="School vacation"
                  value={schoolHolidayMode}
                  options={SCHOOL_OPTIONS}
                  onChange={setSchoolHolidayMode}
                />
                {schoolHint && (
                  <p className="text-xs text-muted">{schoolHint}</p>
                )}
              </div>

              <div className="space-y-1.5">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted">
                  School rush
                </span>
                <Segmented
                  ariaLabel="School rush"
                  value={schoolRushMode}
                  options={SCHOOL_RUSH_OPTIONS}
                  onChange={setSchoolRushMode}
                />
                {rushHint && <p className="text-xs text-muted">{rushHint}</p>}
                <p className="text-xs text-muted">
                  Term weekdays 06–07 start and 13–14 finish.
                </p>
              </div>

              <label className="flex cursor-pointer items-start gap-3 border border-line bg-white px-3 py-3">
                <input
                  type="checkbox"
                  checked={eventOverride}
                  onChange={(e) => setEventOverride(e.target.checked)}
                  className="mt-0.5 accent-[var(--teal)]"
                />
                <span>
                  <span className="block text-sm font-semibold text-ink">
                    Special event
                  </span>
                  <span className="mt-0.5 block text-xs text-muted">
                    Boost demand for matches, rallies, or other corridor spikes.
                  </span>
                </span>
              </label>
            </div>
          </aside>

          {/* Results */}
          <section className="anim-fade-up anim-delay-2 lg:col-span-8 space-y-8">
            {/* KPI readout */}
            <div
              className={`grid grid-cols-2 gap-px border border-line bg-line sm:grid-cols-4 ${
                peakTight ? "outline outline-1 outline-amber/50" : ""
              }`}
            >
              <div className="bg-paper px-4 py-4">
                <p className="text-[0.65rem] font-semibold uppercase tracking-wider text-muted">
                  Headway
                  {peakTight ? (
                    <span className="ml-1 text-amber">· tight</span>
                  ) : null}
                </p>
                <p className="mt-1 font-display text-3xl font-semibold text-ink">
                  {rec ? rec.headway_minutes : "—"}
                  <span className="ml-1 text-base font-normal text-muted">min</span>
                </p>
              </div>
              <div className="bg-paper px-4 py-4">
                <p className="text-[0.65rem] font-semibold uppercase tracking-wider text-muted">
                  Buses / hr
                </p>
                <p className="mt-1 font-display text-3xl font-semibold text-ink">
                  {rec ? rec.buses_needed : "—"}
                </p>
              </div>
              <div className="bg-paper px-4 py-4">
                <p className="text-[0.65rem] font-semibold uppercase tracking-wider text-muted">
                  Peak load
                  {peakStop ? (
                    <span className="ml-1 normal-case tracking-normal text-teal">
                      · {stopLabel(peakStop)}
                    </span>
                  ) : null}
                </p>
                <p className="mt-1 font-display text-3xl font-semibold text-ink">
                  {rec ? Math.round(rec.peak_load) : "—"}
                  <span className="ml-1 text-base font-normal text-muted">pax</span>
                </p>
              </div>
              <div className="bg-paper px-4 py-4">
                <p className="text-[0.65rem] font-semibold uppercase tracking-wider text-muted">
                  Corridor ETA
                  {rec?.congestion_factor && rec.congestion_factor > 1 ? (
                    <span className="ml-1 text-amber">
                      ×{rec.congestion_factor}
                    </span>
                  ) : null}
                </p>
                <p className="mt-1 font-display text-3xl font-semibold text-ink">
                  {rec ? rec.corridor_eta_minutes : "—"}
                  <span className="ml-1 text-base font-normal text-muted">min</span>
                </p>
              </div>
            </div>

            {/* Corridor stop rail */}
            <div>
              <div className="mb-3 flex items-baseline justify-between gap-3">
                <h3 className="font-display text-lg font-semibold text-ink">
                  Corridor
                </h3>
                <p className="text-xs text-muted">
                  {direction === "Inbound_to_Pettah"
                    ? "Panadura → Pettah"
                    : "Pettah → Panadura"}
                </p>
              </div>
              <div className="relative overflow-x-auto pb-2">
                <div className="absolute left-3 right-3 top-[13px] h-px bg-line" />
                <ol className="relative flex min-w-[540px] justify-between gap-1">
                  {(data?.stops ?? []).map((stop) => {
                    const isPeak = stop === peakStop;
                    return (
                      <li
                        key={stop}
                        className="flex w-16 flex-col items-center text-center"
                      >
                        <span
                          className={`relative z-10 h-3 w-3 rounded-full border-2 ${
                            isPeak
                              ? "border-amber bg-amber"
                              : "border-teal bg-paper"
                          }`}
                        />
                        <span
                          className={`mt-2 text-[0.65rem] leading-tight ${
                            isPeak
                              ? "font-bold text-amber"
                              : "font-medium text-muted"
                          }`}
                        >
                          {stopLabel(stop)}
                        </span>
                      </li>
                    );
                  })}
                  {!data && (
                    <li className="w-full py-6 text-center text-sm text-muted">
                      Waiting for prediction…
                    </li>
                  )}
                </ol>
              </div>
            </div>

            {/* Demand chart */}
            <div>
              <div className="mb-3 flex items-baseline justify-between">
                <h3 className="font-display text-lg font-semibold text-ink">
                  Demand by stop
                </h3>
                <p className="text-xs text-muted">Predicted boardings</p>
              </div>
              <div className="h-72 w-full border border-line bg-white/70 px-2 pt-4 pb-2">
                {data ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={chartData}
                      margin={{ top: 4, right: 8, left: -12, bottom: 28 }}
                    >
                      <CartesianGrid
                        strokeDasharray="2 4"
                        stroke="#c5d2cd"
                        vertical={false}
                      />
                      <XAxis
                        dataKey="name"
                        stroke="#5a6b66"
                        fontSize={11}
                        tickMargin={8}
                        axisLine={false}
                        tickLine={false}
                        angle={-35}
                        textAnchor="end"
                        height={50}
                      />
                      <YAxis
                        stroke="#5a6b66"
                        fontSize={11}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        cursor={{ fill: "rgba(11, 79, 84, 0.06)" }}
                        contentStyle={{
                          backgroundColor: "#f4f7f5",
                          border: "1px solid #c5d2cd",
                          borderRadius: 0,
                          color: "#1a2421",
                          fontSize: 12,
                        }}
                      />
                      <Bar dataKey="passengers" radius={[2, 2, 0, 0]}>
                        {chartData.map((entry) => (
                          <Cell
                            key={entry.stop}
                            fill={
                              entry.stop === peakStop ? "#c45c26" : "#0b4f54"
                            }
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex h-full items-center justify-center text-sm text-muted">
                    Loading demand…
                  </div>
                )}
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
