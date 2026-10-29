import React from 'react';
import { Sliders, Film, Volume2, Sparkles, Clock, CheckCircle2 } from 'lucide-react';
import { formatSMPTE, formatTimecode } from '../utils/timeUtils';

export default function Inspector({
  selectedClip,
  timeline,
  analysis,
  assemblyResult,
  onSeekToScene,
  onUpdateClipSpeed,
  onUpdateClipVolume,
  videoMetadata
}) {
  const clips = timeline?.clips || [];
  const scenes = analysis?.scenes || [];

  return (
    <div className="h-full flex flex-col bg-[#141518] text-[#a0a4ae] select-none text-[11px] overflow-y-auto p-3 space-y-4">
      {/* 1. Selected Clip Section */}
      <div className="bg-[#18191d] border border-[#23252b] rounded p-2.5 space-y-2.5">
        <div className="flex items-center justify-between text-[#d0d3dc] font-medium border-b border-[#212328] pb-1.5">
          <span className="flex items-center gap-1.5 truncate max-w-[190px]">
            <Film className="w-3.5 h-3.5 text-[#7c8190] shrink-0" />
            <span className="truncate">{selectedClip ? selectedClip.name : 'No Clip Selected'}</span>
          </span>
          <span className="text-[10px] text-[#636774] font-mono shrink-0">
            {selectedClip ? selectedClip.id : ''}
          </span>
        </div>

        {selectedClip ? (
          <div className="space-y-2 font-mono text-[10px]">
            {/* Source filename and role */}
            {selectedClip.source_filename && (
              <div className="flex justify-between text-[#858a98]">
                <span>Source Media:</span>
                <span className="text-[#a8adb8] truncate max-w-[150px]" title={selectedClip.source_filename}>
                  {selectedClip.source_filename}
                </span>
              </div>
            )}

            {selectedClip.role && (
              <div className="flex justify-between text-[#858a98]">
                <span>AI Role:</span>
                <span className="text-[#7ea5dc] font-medium px-1 py-0.2 rounded bg-[#1e2634] border border-[#27354a]">
                  {selectedClip.role}
                </span>
              </div>
            )}

            <div className="flex justify-between text-[#858a98]">
              <span>Timeline:</span>
              <span className="text-[#c4c7d2]">
                {formatSMPTE(selectedClip.timeline_start)} - {formatSMPTE(selectedClip.timeline_end)}
              </span>
            </div>
            <div className="flex justify-between text-[#858a98]">
              <span>Source In/Out:</span>
              <span className="text-[#a8adb8]">
                {formatTimecode(selectedClip.source_start)} - {formatTimecode(selectedClip.source_end)}
              </span>
            </div>
            <div className="flex justify-between text-[#858a98]">
              <span>Duration:</span>
              <span className="text-[#c4c7d2] font-semibold">{selectedClip.duration.toFixed(2)}s</span>
            </div>

            {/* AI Editorial Rationale if present */}
            {selectedClip.editorial_rationale && (
              <div className="pt-2 border-t border-[#212328] font-sans">
                <span className="text-[#858a98] text-[10px] font-medium block mb-1">
                  Editorial Rationale:
                </span>
                <p className="text-[#b5b9c4] text-[10px] leading-relaxed bg-[#1b1d22] p-2 rounded border border-[#272932]">
                  {selectedClip.editorial_rationale}
                </p>
                {selectedClip.trimmed_reason && (
                  <p className="text-[9px] text-[#787d8c] italic mt-1 pl-1">
                    • {selectedClip.trimmed_reason}
                  </p>
                )}
              </div>
            )}

            {/* Playback Speed Slider */}
            <div className="pt-1.5 border-t border-[#212328]">
              <div className="flex justify-between text-[#858a98] mb-1">
                <span>Speed:</span>
                <span>{selectedClip.speed || 1.0}x</span>
              </div>
              <input
                type="range"
                min="0.25"
                max="3.0"
                step="0.25"
                value={selectedClip.speed || 1.0}
                onChange={(e) => onUpdateClipSpeed(selectedClip.id, parseFloat(e.target.value))}
                className="w-full h-1 bg-[#252830] rounded appearance-none accent-[#a0a4ae] cursor-pointer"
              />
            </div>
          </div>
        ) : (
          <p className="text-[#555a66] italic text-[10px]">
            Click any clip on the timeline or enter a selection command to inspect parameters.
          </p>
        )}
      </div>

      {/* 2. Assembled Sequence Storyboard (if sequence was assembled) */}
      {assemblyResult && assemblyResult.segments && (
        <div className="bg-[#18191d] border border-[#23252b] rounded p-2.5 space-y-2">
          <div className="flex items-center justify-between text-[#d0d3dc] font-medium border-b border-[#212328] pb-1.5">
            <span className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[#d48b3b]" />
              <span>Production Storyboard</span>
            </span>
            <span className="text-[10px] text-[#8a8f9e] font-mono">
              {assemblyResult.segments.length} cuts
            </span>
          </div>

          <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
            {assemblyResult.segments.map((seg, idx) => (
              <div
                key={idx}
                onClick={() => onSeekToScene(seg.timeline_start, seg.timeline_end)}
                className="bg-[#1e2025] hover:bg-[#252830] border border-[#282a32] rounded p-1.5 cursor-pointer transition space-y-0.5"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[#d0d3dc] font-medium text-[10px]">
                    {idx + 1}. {seg.role}
                  </span>
                  <span className="text-[9px] font-mono text-[#8a8f9e]">
                    {seg.duration.toFixed(1)}s
                  </span>
                </div>
                <p className="text-[9px] text-[#717684] truncate">
                  {seg.source_filename}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Detected Scenes List (if video has been analyzed) */}
      <div className="bg-[#18191d] border border-[#23252b] rounded p-2.5 space-y-2">
        <div className="flex items-center justify-between text-[#d0d3dc] font-medium border-b border-[#212328] pb-1.5">
          <span className="flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-[#7c8190]" />
            <span>Detected Scenes</span>
          </span>
          <span className="text-[10px] text-[#636774] font-mono">{scenes.length}</span>
        </div>

        {scenes.length > 0 ? (
          <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
            {scenes.map((s) => (
              <div
                key={s.scene_id}
                onClick={() => onSeekToScene(s.start_time, s.end_time)}
                className="bg-[#1e2025] hover:bg-[#252830] border border-[#282a32] rounded p-1.5 flex items-center justify-between cursor-pointer transition"
              >
                <div>
                  <p className="text-[#d0d3dc] font-medium text-[11px]">Scene {s.scene_id}</p>
                  <p className="text-[9px] text-[#6f7482] font-mono">
                    {formatSMPTE(s.start_time)} - {formatSMPTE(s.end_time)}
                  </p>
                </div>
                <span className="text-[9px] font-mono text-[#8a8f9e] bg-[#16171b] px-1 py-0.5 rounded border border-[#23252b]">
                  {s.duration.toFixed(1)}s
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-[#555a66] italic text-[10px]">
            No scenes detected. Click "Analyze" in the top bar to inspect video shot transitions.
          </p>
        )}
      </div>
    </div>
  );
}
