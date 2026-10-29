import React, { useState, useRef } from 'react';
import {
  Sparkles,
  Upload,
  Film,
  FolderOpen,
  CheckCircle2,
  AlertCircle,
  Play,
  ArrowRight,
  Layers,
  Sliders,
  Scissors,
  Trash2,
  X
} from 'lucide-react';
import { formatSMPTE, formatTimecode } from '../utils/timeUtils';
import { uploadBatchVideos, loadMultiSamplePack, analyzeAndAssembleProduction } from '../api';

export default function MultiVideoAssemblyStage({
  isOpen,
  onClose,
  onApplyAssembly,
  sourceClips = [],
  setSourceClips,
  mediaPoolVideos = []
}) {
  const [selectedStyle, setSelectedStyle] = useState('narrative');
  const [customPrompt, setCustomPrompt] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [assemblyResult, setAssemblyResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [fableKey, setFableKey] = useState(() => localStorage.getItem('editmind_fable_key') || '');
  const [showKeyModal, setShowKeyModal] = useState(false);

  const batchInputRef = useRef(null);

  if (!isOpen) return null;

  const handleSaveFableKey = () => {
    localStorage.setItem('editmind_fable_key', fableKey.trim());
    setShowKeyModal(false);
  };

  // Delete a specific clip from assembly stage
  const handleDeleteClip = (indexToDelete) => {
    setSourceClips((prev) => prev.filter((_, idx) => idx !== indexToDelete));
    setAssemblyResult(null);
  };

  // Clear all clips
  const handleClearAllClips = () => {
    setSourceClips([]);
    setAssemblyResult(null);
  };

  // Import existing media pool clips into assembly
  const handleImportFromMediaPool = () => {
    if (!mediaPoolVideos || mediaPoolVideos.length === 0) return;
    setSourceClips((prev) => {
      const existingPaths = new Set(prev.map((c) => c.filepath));
      const newItems = mediaPoolVideos.filter((v) => !existingPaths.has(v.filepath));
      return [...prev, ...newItems];
    });
  };

  // Handle multi-clip batch upload
  const handleBatchUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    try {
      setIsAnalyzing(true);
      setErrorMsg('');
      const res = await uploadBatchVideos(files);
      setSourceClips((prev) => [...prev, ...res.items]);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to upload batch clips.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Load 3-clip demo pack
  const handleLoadDemoPack = async () => {
    try {
      setIsAnalyzing(true);
      setErrorMsg('');
      const res = await loadMultiSamplePack();
      const items = res.clip_analyses.map((a, i) => ({
        filename: a.filename,
        filepath: a.filepath,
        stream_url: `/media_files/sample_media/${a.filename}`,
        metadata: {
          filename: a.filename,
          filepath: a.filepath,
          duration: a.duration,
          width: a.width,
          height: a.height,
          fps: a.fps,
          has_audio: a.has_audio
        },
        analysis: a
      }));
      setSourceClips(items);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to load sample pack.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Run AI analysis and auto-assemble with Claude Fable 5.1
  const handleRunAssembly = async () => {
    if (sourceClips.length === 0) {
      setErrorMsg('Please upload or load at least one video clip.');
      return;
    }

    try {
      setIsAnalyzing(true);
      setErrorMsg('');
      const paths = sourceClips.map((c) => c.filepath);
      const res = await analyzeAndAssembleProduction({
        media_files: paths,
        style: selectedStyle,
        user_prompt: customPrompt.trim() || null,
        include_subtitles: true,
        llm_config: fableKey.trim() ? {
          provider: 'fable',
          fable_api_key: fableKey.trim()
        } : undefined
      });
      setAssemblyResult(res);
    } catch (err) {
      setErrorMsg(err.message || 'Auto-assembly failed.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleCommit = () => {
    if (!assemblyResult) return;
    onApplyAssembly(assemblyResult);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-xs flex items-center justify-center p-4 select-none text-[12px] text-[#a0a4ae]">
      <div className="bg-[#141518] border border-[#2b2d35] rounded-lg max-w-4xl w-full h-[88vh] overflow-hidden shadow-2xl flex flex-col relative">
        {/* 1. Header */}
        <div className="h-10 px-4 border-b border-[#212328] flex items-center justify-between bg-[#16171b]">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#d4483b]" />
            <span className="font-medium text-[#d8dbe4] text-xs">
              AI Multi-Video Assembly Studio
            </span>
            <span className="text-[10px] text-[#6b707e] font-mono border-l border-[#24262c] pl-2">
              DaVinci Cut Engine
            </span>
            <button
              onClick={() => setShowKeyModal(!showKeyModal)}
              className={`flex items-center gap-1.5 px-2 py-0.5 rounded border transition text-[10px] ml-2 ${
                fableKey
                  ? 'bg-[#1b2636] border-[#395376] text-[#8ab8f2]'
                  : 'bg-[#1e2026] border-[#2c2f38] text-[#868a96] hover:text-[#d0d3dc]'
              }`}
              title="Configure Claude Fable 5.1 frontier director API key"
            >
              <Sparkles className="w-3 h-3 text-[#d48b3b]" />
              <span>{fableKey ? 'Claude Fable 5.1 Active' : 'Connect Fable 5.1 API'}</span>
            </button>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded text-[#6f7482] hover:text-[#d0d3dc] hover:bg-[#252830] transition"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Fable API Key Popover */}
        {showKeyModal && (
          <div className="absolute top-12 left-64 bg-[#181a20] border border-[#2f3340] rounded-lg shadow-2xl p-3 z-50 w-96 space-y-2 text-[11px]">
            <div className="flex items-center justify-between border-b border-[#262832] pb-1.5">
              <span className="font-semibold text-[#d8dbe4] flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[#d48b3b]" />
                <span>Claude Fable 5.1 Director Setup</span>
              </span>
              <button onClick={() => setShowKeyModal(false)} className="text-[#6c707d] hover:text-white">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <p className="text-[10px] text-[#868a96]">
              Your Claude Fable 5.1 key powers high-level narrative pacing, scene curation, and audio-video harmonization across all source footage.
            </p>
            <input
              type="password"
              value={fableKey}
              onChange={(e) => setFableKey(e.target.value)}
              placeholder="Paste Anthropic API Key (sk-ant-...) or Fable Key..."
              className="w-full bg-[#121316] text-[#d8dbe4] border border-[#272932] rounded px-2.5 py-1.5 text-[10px] focus:outline-none focus:border-[#4f6b95]"
            />
            <div className="flex items-center justify-end gap-2 pt-1 border-t border-[#262832]">
              <button
                onClick={() => setShowKeyModal(false)}
                className="px-2.5 py-1 rounded bg-[#202227] hover:bg-[#282a30] text-[#9da1ad] text-[10px]"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveFableKey}
                className="px-3 py-1 rounded bg-[#2b3a4e] hover:bg-[#344863] text-[#e0e3eb] font-medium text-[10px] border border-[#3f5778]"
              >
                Save Fable Key
              </button>
            </div>
          </div>
        )}

        {/* 2. Main Content Body */}
        <div className="flex-1 flex overflow-hidden min-h-0">
          {/* Left Column: Source Media Tray (Multiple Clips) */}
          <div className="w-80 shrink-0 border-r border-[#212328] flex flex-col bg-[#121316]">
            <div className="h-8 px-3 border-b border-[#212328] flex items-center justify-between bg-[#16171a] text-[11px]">
              <span className="font-medium text-[#c8cbcd]">Source Clips ({sourceClips.length})</span>
              <div className="flex items-center gap-1.5">
                {mediaPoolVideos && mediaPoolVideos.length > 0 && (
                  <button
                    onClick={handleImportFromMediaPool}
                    className="px-2 py-0.5 rounded bg-[#1e232d] hover:bg-[#283242] text-[#86a6d6] border border-[#2b394e] transition text-[10px]"
                    title="Add clips already in Media Pool"
                  >
                    + From Pool
                  </button>
                )}
                <button
                  onClick={() => batchInputRef.current?.click()}
                  className="px-2 py-0.5 rounded bg-[#1e2026] hover:bg-[#262830] text-[#b5b9c4] border border-[#2b2d35] transition text-[10px]"
                  title="Upload multiple video files"
                >
                  + Add Clips
                </button>
                {sourceClips.length > 0 && (
                  <button
                    onClick={handleClearAllClips}
                    className="px-1.5 py-0.5 rounded hover:bg-[#2a1d20] text-[#868a96] hover:text-[#e06c75] border border-transparent hover:border-[#42252a] transition text-[10px]"
                    title="Remove all source clips"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-2.5 space-y-2">
              {sourceClips.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center p-4 border border-dashed border-[#24262c] rounded">
                  <Film className="w-6 h-6 text-[#40434c] mb-2" />
                  <p className="text-[#6c7180] text-[11px] mb-2">No source clips loaded</p>
                  <button
                    onClick={handleLoadDemoPack}
                    className="px-2.5 py-1 rounded bg-[#1e2026] hover:bg-[#272932] text-[#d0d3dc] border border-[#2f323c] transition text-[10px]"
                  >
                    Load 3-Clip Demo Pack
                  </button>
                </div>
              ) : (
                sourceClips.map((clip, idx) => (
                  <div
                    key={idx}
                    className="bg-[#18191d] border border-[#25272e] rounded p-2 text-[11px] space-y-1 hover:border-[#383b46] transition group"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-[#d8dbe4] truncate max-w-[155px]" title={clip.filename}>
                        {idx + 1}. {clip.filename}
                      </span>
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] font-mono text-[#8a8f9e]">
                          {clip.metadata?.duration ? formatTimecode(clip.metadata.duration) : '--'}
                        </span>
                        <button
                          onClick={() => handleDeleteClip(idx)}
                          className="p-1 rounded text-[#555a66] hover:text-[#e06c75] hover:bg-[#271d20] transition opacity-0 group-hover:opacity-100"
                          title="Remove this video from assembly"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>

                    <div className="flex items-center gap-1 text-[9px]">
                      {clip.analysis?.primary_category ? (
                        <span className="px-1.5 py-0.2 rounded bg-[#202734] text-[#7ea5dc] border border-[#29364a] font-mono">
                          {clip.analysis.primary_category}
                        </span>
                      ) : (
                        <span className="px-1.5 py-0.2 rounded bg-[#1d1f25] text-[#868a96] border border-[#272932] font-mono">
                          Video Asset
                        </span>
                      )}
                      <span className="text-[#636774] font-mono">
                        {clip.metadata?.width}x{clip.metadata?.height}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>

            <input
              type="file"
              ref={batchInputRef}
              onChange={handleBatchUpload}
              multiple
              accept="video/mp4,video/quicktime,video/webm,video/x-matroska,video/avi"
              className="hidden"
            />
          </div>

          {/* Right Column: Assembly Configuration & Review */}
          <div className="flex-1 flex flex-col bg-[#141518] overflow-hidden">
            {/* Top Toolbar: Style & Prompt */}
            <div className="p-3 border-b border-[#212328] bg-[#16171b] space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-[#8e92a0] text-[11px] font-medium">Assembly Narrative Style</span>
                <button
                  onClick={handleLoadDemoPack}
                  className="text-[10px] text-[#717582] hover:text-[#d0d3dc] transition underline"
                >
                  Reload Multi-Clip Sample Pack
                </button>
              </div>

              {/* Style options */}
              <div className="grid grid-cols-4 gap-1.5 text-[11px]">
                {[
                  { id: 'narrative', label: 'Narrative Highlight Reel' },
                  { id: 'social', label: 'Fast-Paced Social Cut' },
                  { id: 'broll', label: 'Interview + B-Roll' },
                  { id: 'chronological', label: 'Chronological Cut' }
                ].map((s) => (
                  <button
                    key={s.id}
                    onClick={() => setSelectedStyle(s.id)}
                    className={`py-1.5 px-2 rounded border text-center transition ${
                      selectedStyle === s.id
                        ? 'bg-[#252b36] border-[#445b7c] text-[#e0e3eb] font-medium'
                        : 'bg-[#1a1c22] border-[#262830] text-[#7e828e] hover:text-[#b8bcc8]'
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>

              {/* Custom prompt input */}
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={customPrompt}
                  onChange={(e) => setCustomPrompt(e.target.value)}
                  placeholder="Optional custom instruction: e.g. 'Emphasize high action b-roll and opening dialogue'..."
                  className="flex-1 bg-[#1a1c22] text-[11px] text-[#d8dbe4] placeholder-[#555a66] rounded px-2.5 py-1.5 border border-[#262830] focus:outline-none focus:border-[#3e424e]"
                />
                <button
                  onClick={handleRunAssembly}
                  disabled={isAnalyzing || sourceClips.length === 0}
                  className="px-4 py-1.5 rounded bg-[#252830] hover:bg-[#323642] text-[#e0e3eb] border border-[#3b3f4c] font-medium transition text-[11px] flex items-center gap-1.5 disabled:opacity-40"
                >
                  <Sparkles className={`w-3.5 h-3.5 text-[#d48b3b] ${isAnalyzing ? 'animate-spin' : ''}`} />
                  <span>{isAnalyzing ? 'Analyzing & Assembling...' : 'Analyze & Assemble Sequence'}</span>
                </button>
              </div>

              {errorMsg && (
                <div className="bg-[#2a1d1f] border border-[#442327] p-2 rounded text-[#e28b8b] text-[11px] flex items-center gap-1.5">
                  <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}
            </div>

            {/* Assembled Storyboard & Editorial Decisions Inspection */}
            <div className="flex-1 overflow-y-auto p-3 space-y-3">
              {assemblyResult ? (
                <>
                  {/* Summary Bar */}
                  <div className="bg-[#191b20] border border-[#25272e] rounded p-2.5 flex items-center justify-between font-mono text-[11px]">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[#696e7d]">Production Style: </span>
                      <span className="text-[#d8dbe4] font-medium">{assemblyResult.style}</span>
                      {assemblyResult.style?.includes('Claude Fable') && (
                        <span className="px-1.5 py-0.5 rounded bg-[#2a2214] text-[#d48b3b] border border-[#48351a] text-[9px] font-sans font-medium flex items-center gap-1">
                          <Sparkles className="w-2.5 h-2.5" />
                          <span>Frontier AI Directed</span>
                        </span>
                      )}
                    </div>
                    <div>
                      <span className="text-[#696e7d]">Assembled Duration: </span>
                      <span className="text-[#d48b3b] font-medium">{assemblyResult.total_duration}s</span>
                    </div>
                    <div>
                      <span className="text-[#696e7d]">Segments: </span>
                      <span className="text-[#d8dbe4]">{assemblyResult.segments.length} sequential cuts</span>
                    </div>
                  </div>

                  {/* Editorial Decisions Cards */}
                  <div>
                    <p className="text-[#828692] text-[11px] font-medium mb-1.5">
                      Editorial Storyboard & Selection Rationales
                    </p>
                    <div className="space-y-2">
                      {assemblyResult.segments.map((seg, idx) => (
                        <div
                          key={idx}
                          className="bg-[#18191d] border border-[#25272e] rounded p-2.5 text-[11px] space-y-1.5"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="w-5 h-5 rounded bg-[#202228] text-[#a0a4ae] flex items-center justify-center font-mono text-[10px]">
                                {idx + 1}
                              </span>
                              <span className="font-medium text-[#d8dbe4]">{seg.role}</span>
                              <span className="text-[10px] font-mono text-[#696e7d]">
                                ({seg.duration.toFixed(1)}s)
                              </span>
                            </div>
                            <span className="text-[10px] font-mono text-[#8a8f9e]">
                              Timeline: {formatSMPTE(seg.timeline_start)} - {formatSMPTE(seg.timeline_end)}
                            </span>
                          </div>

                          <p className="text-[#9da1ad] leading-relaxed pl-7">
                            {seg.rationale}
                          </p>

                          {seg.trimmed_reason && (
                            <p className="text-[10px] text-[#717582] italic pl-7">
                              • Trimmed: {seg.trimmed_reason}
                            </p>
                          )}

                          {seg.caption_text && (
                            <div className="pl-7 text-[10px] font-mono text-[#d4a03b] flex items-center gap-1">
                              <span>Synced Caption: "{seg.caption_text}"</span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Audio & Subtitle Sync status */}
                  <div className="bg-[#18191d] border border-[#25272e] rounded p-2.5 text-[10px] text-[#7a7f8e] space-y-1">
                    <p className="flex items-center gap-1.5 text-[#5bb676]">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>{assemblyResult.audio_sync_note}</span>
                    </p>
                    <p className="pl-5 text-[#6c707d]">
                      • {assemblyResult.subtitles.length} caption segments re-mapped to timeline timestamps.
                    </p>
                  </div>
                </>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center p-6 text-[#555a66]">
                  <Layers className="w-8 h-8 text-[#3c3f4a] mb-2" />
                  <p className="text-xs">No sequence assembled yet</p>
                  <p className="text-[11px] text-[#42454f] mt-0.5 max-w-sm">
                    Select your source clips on the left, pick an assembly style, and click "Analyze & Assemble Sequence".
                  </p>
                </div>
              )}
            </div>

            {/* 3. Footer Action */}
            <div className="h-12 px-4 border-t border-[#212328] bg-[#16171a] flex items-center justify-between">
              <span className="text-[10px] text-[#696e7d]">
                {assemblyResult ? 'Sequence ready for timeline mounting & user refinement' : ''}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={onClose}
                  className="px-3 py-1.5 rounded bg-[#202228] hover:bg-[#282a32] text-[#9da1ad] transition text-[11px]"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCommit}
                  disabled={!assemblyResult}
                  className="px-4 py-1.5 rounded bg-[#2a3848] hover:bg-[#34465a] border border-[#445b78] text-[#e0e3eb] font-medium transition text-[11px] flex items-center gap-1.5 disabled:opacity-40"
                >
                  <span>Apply to Timeline & Open Editor</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
