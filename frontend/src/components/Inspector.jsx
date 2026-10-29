import React from 'react';
import { Sliders, Film, Volume2, Sparkles, Clock, CheckCircle2 } from 'lucide-react';
import { formatSMPTE, formatTimecode } from '../utils/timeUtils';

export default function Inspector({
  selectedClip,
  timeline,
  analysis,
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
          <span className="flex items-center gap-1.5">
            <Film className="w-3.5 h-3.5 text-[#7c8190]" />
            <span>{selectedClip ? selectedClip.name : 'No Clip Selected'}</span>
          </span>
          <span className="text-[10px] text-[#636774] font-mono">
            {selectedClip ? selectedClip.id : ''}
          </span>
        </div>

        {selectedClip ? (
          <div className="space-y-2 font-mono text-[10px]">
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

      {/* 2. Detected Scenes List (if video has been analyzed) */}
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
