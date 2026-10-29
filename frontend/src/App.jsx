import React, { useState, useEffect, useCallback, useRef } from 'react';
import Navbar from './components/Navbar';
import MediaImportPanel from './components/MediaImportPanel';
import VideoPlayer from './components/VideoPlayer';
import InteractiveTimeline from './components/InteractiveTimeline';
import Inspector from './components/Inspector';
import AIChatbotPanel from './components/AIChatbotPanel';
import ExportModal from './components/ExportModal';
import ProjectListModal from './components/ProjectListModal';
import BottomPageBar from './components/BottomPageBar';

import {
  uploadVideo,
  uploadAudio,
  uploadSubtitle,
  loadSampleProject,
  analyzeVideo,
  sendChatbotCommand,
  splitTimeline,
  deleteTimelineSelection,
  cutTimelineSelection,
  undoTimelineAction,
  redoTimelineAction,
  createProject,
  saveProject,
  getProject,
  autosaveProject
} from './api';

export default function App() {
  // Project management state
  const [projectId, setProjectId] = useState('proj_default');
  const [projectName, setProjectName] = useState('New Project 1');
  const [isEdited, setIsEdited] = useState(false);
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);

  // Media state
  const [videoMetadata, setVideoMetadata] = useState(null);
  const [videoSrc, setVideoSrc] = useState('');
  const [audioTrack, setAudioTrack] = useState(null);
  const [subtitles, setSubtitles] = useState([]);

  // Timeline state
  const [timeline, setTimeline] = useState({
    clips: [],
    total_duration: 0.0,
    selected_clip_id: null,
    selection_range: null,
    audio_track: null,
    subtitles: [],
    playhead_time: 0.0,
  });

  // Playback & Viewer state
  const [currentTime, setCurrentTime] = useState(0.0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackRange, setPlaybackRange] = useState(null);

  // Analysis & Inspector state
  const [analysis, setAnalysis] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [activeRightTab, setActiveRightTab] = useState('ai'); // 'inspector' | 'ai'

  // AI Assistant Chat state
  const [chatMessages, setChatMessages] = useState([
    {
      id: 'init_1',
      sender: 'assistant',
      text: 'EditMind AI ready. You can describe any edit in natural language, for example:\n• "Select the clip from 00:10 to 00:25."\n• "Split at 00:18."\n• "Delete the selected segment."\n• "Delete the second half of the selected clip."\n• "Export the edited video."',
      timestamp: 'Ready',
    },
  ]);
  const [isChatProcessing, setIsChatProcessing] = useState(false);

  // Export modal
  const [isExportOpen, setIsExportOpen] = useState(false);

  // Add message helper
  const addChatMessage = useCallback((sender, text, extra = {}) => {
    const newMsg = {
      id: `msg_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      sender,
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      ...extra,
    };
    setChatMessages((prev) => [...prev, newMsg]);
  }, []);

  // 1. Initialize SQLite Default Project on mount
  useEffect(() => {
    async function initProject() {
      try {
        const proj = await createProject('New Project 1');
        setProjectId(proj.id);
        setProjectName(proj.name);
      } catch (err) {
        console.error('Project init error:', err);
      }
    }
    initProject();
  }, []);

  // 2. Autosave periodically if edited
  useEffect(() => {
    if (!isEdited || !projectId) return;

    const timer = setTimeout(async () => {
      try {
        await autosaveProject(projectId, {
          name: projectName,
          settings: { fps: 25.0, resolution: '1080p' },
          clips: timeline.clips,
          subtitles: timeline.subtitles
        });
        setIsEdited(false);
      } catch (e) {
        console.error('Autosave error:', e);
      }
    }, 4000);

    return () => clearTimeout(timer);
  }, [timeline, isEdited, projectId, projectName]);

  // 3. Manual Save Project
  const handleSaveProject = async () => {
    try {
      await saveProject(projectId, {
        name: projectName,
        settings: { fps: 25.0, resolution: '1080p' },
        clips: timeline.clips,
        subtitles: timeline.subtitles
      });
      setIsEdited(false);
      addChatMessage('assistant', `Project "${projectName}" saved to database.`);
    } catch (err) {
      addChatMessage('assistant', `Failed to save: ${err.message}`, { isError: true });
    }
  };

  // 4. Switch Project
  const handleSwitchProject = async (targetId) => {
    try {
      const proj = await getProject(targetId);
      setProjectId(proj.id);
      setProjectName(proj.name);
      setTimeline(proj.timeline);
      setSubtitles(proj.timeline.subtitles || []);
      setIsEdited(false);
      addChatMessage('assistant', `Loaded project "${proj.name}".`);
    } catch (err) {
      console.error(err);
    }
  };

  // 5. Upload Video
  const handleUploadVideo = async (file) => {
    try {
      const res = await uploadVideo(file);
      setVideoMetadata(res.metadata);
      setTimeline(res.timeline);
      setVideoSrc(res.stream_url);
      setCurrentTime(0.0);
      setAnalysis(null);
      setIsEdited(true);
      addChatMessage(
        'assistant',
        `Imported video "${file.name}" (${res.metadata.duration.toFixed(1)}s, ${res.metadata.width}x${res.metadata.height}, ${res.metadata.fps} fps).`
      );
    } catch (err) {
      addChatMessage('assistant', `Import error: ${err.message}`, { isError: true });
    }
  };

  // 6. Upload Audio
  const handleUploadAudio = async (file) => {
    try {
      const res = await uploadAudio(file);
      setAudioTrack(res.audio_track);
      setTimeline((prev) => ({ ...prev, audio_track: res.audio_track }));
      setIsEdited(true);
      addChatMessage('assistant', `Imported audio track "${file.name}".`);
    } catch (err) {
      addChatMessage('assistant', `Audio error: ${err.message}`, { isError: true });
    }
  };

  // 7. Upload Subtitles
  const handleUploadSubtitle = async (file) => {
    try {
      const res = await uploadSubtitle(file);
      setSubtitles(res.subtitles);
      setTimeline((prev) => ({ ...prev, subtitles: res.subtitles }));
      setIsEdited(true);
      addChatMessage('assistant', `Imported ${res.count} subtitle cues from "${file.name}".`);
    } catch (err) {
      addChatMessage('assistant', `Subtitle error: ${err.message}`, { isError: true });
    }
  };

  // 8. Load Sample Project
  const handleLoadSample = async () => {
    try {
      const res = await loadSampleProject();
      setVideoMetadata(res.metadata);
      setTimeline(res.timeline);
      setVideoSrc(res.stream_url);
      setSubtitles(res.timeline.subtitles);
      setCurrentTime(0.0);
      setAnalysis(null);
      setIsEdited(true);
      addChatMessage(
        'assistant',
        'Loaded demo sample: 30.0s multi-scene video + synchronized SRT subtitles.'
      );
    } catch (err) {
      addChatMessage('assistant', `Failed to load sample: ${err.message}`, { isError: true });
    }
  };

  // 9. Remove media
  const handleRemoveMedia = (type) => {
    if (type === 'video') {
      setVideoMetadata(null);
      setVideoSrc('');
      setTimeline({ clips: [], total_duration: 0.0, selected_clip_id: null, selection_range: null, subtitles: [], playhead_time: 0 });
      setAnalysis(null);
      setIsEdited(true);
    } else if (type === 'audio') {
      setAudioTrack(null);
      setTimeline((prev) => ({ ...prev, audio_track: null }));
      setIsEdited(true);
    } else if (type === 'subtitles') {
      setSubtitles([]);
      setTimeline((prev) => ({ ...prev, subtitles: [] }));
      setIsEdited(true);
    }
  };

  // 10. Analyze Video
  const handleAnalyze = async () => {
    if (!videoMetadata) return;
    setIsAnalyzing(true);
    setActiveRightTab('inspector');
    try {
      const res = await analyzeVideo(videoMetadata.filepath, videoMetadata.duration);
      setAnalysis(res);
      addChatMessage(
        'assistant',
        `Analysis complete: detected ${res.scenes.length} scene changes, ${res.silences.length} silences, and ${res.low_activity_segments.length} static sections.`
      );
    } catch (err) {
      addChatMessage('assistant', `Analysis error: ${err.message}`, { isError: true });
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 11. Send Chatbot Command
  const handleSendCommand = async (prompt) => {
    addChatMessage('user', prompt);
    setIsChatProcessing(true);

    try {
      const res = await sendChatbotCommand({
        prompt,
        current_timeline: timeline,
        media_metadata: videoMetadata,
        scenes: analysis?.scenes || [],
      });

      if (res.intent === 'play') {
        setIsPlaying(true);
      } else if (res.intent === 'pause') {
        setIsPlaying(false);
      } else if (res.intent === 'play_selected') {
        if (res.target_range) {
          setPlaybackRange(res.target_range);
          setCurrentTime(res.target_range[0]);
          setIsPlaying(true);
        } else {
          setIsPlaying(true);
        }
      } else if (res.intent === 'show_scenes') {
        setActiveRightTab('inspector');
      } else if (res.intent === 'export') {
        setIsExportOpen(true);
      }

      if (res.updated_timeline) {
        setTimeline(res.updated_timeline);
        setSubtitles(res.updated_timeline.subtitles || []);
        if (res.target_time !== null && res.target_time !== undefined) {
          setCurrentTime(res.target_time);
        }
        setIsEdited(true);
      }

      addChatMessage('assistant', res.message, {
        actionProposal: res.action_proposal,
        actionDescription: res.action_description || (res.updated_timeline ? 'Timeline Updated' : null),
      });
    } catch (err) {
      addChatMessage('assistant', `Error executing command: ${err.message}`, { isError: true });
    } finally {
      setIsChatProcessing(false);
    }
  };

  // 12. Direct Timeline Operations
  const handleSplitAtPlayhead = async (splitTime = currentTime) => {
    try {
      const res = await splitTimeline(timeline, splitTime);
      setTimeline(res.timeline);
      setIsEdited(true);
      addChatMessage('assistant', res.message, { actionDescription: 'Clip Split' });
    } catch (err) {
      addChatMessage('assistant', `Split error: ${err.message}`, { isError: true });
    }
  };

  const handleDelete = async () => {
    try {
      const res = await deleteTimelineSelection(timeline);
      setTimeline(res.timeline);
      setSubtitles(res.timeline.subtitles || []);
      setIsEdited(true);
      addChatMessage('assistant', res.message, { actionDescription: 'Segment Deleted' });
    } catch (err) {
      addChatMessage('assistant', `Delete error: ${err.message}`, { isError: true });
    }
  };

  const handleCut = async () => {
    try {
      const res = await cutTimelineSelection(timeline);
      setTimeline(res.timeline);
      setSubtitles(res.timeline.subtitles || []);
      setIsEdited(true);
      addChatMessage('assistant', res.message, { actionDescription: 'Segment Cut' });
    } catch (err) {
      addChatMessage('assistant', `Cut error: ${err.message}`, { isError: true });
    }
  };

  const handleUndo = async () => {
    try {
      const res = await undoTimelineAction(timeline);
      setTimeline(res.timeline);
      setSubtitles(res.timeline.subtitles || []);
      setIsEdited(true);
      addChatMessage('assistant', res.message, { actionDescription: 'Undo' });
    } catch (err) {
      addChatMessage('assistant', `Undo error: ${err.message}`, { isError: true });
    }
  };

  const handleRedo = async () => {
    try {
      const res = await redoTimelineAction(timeline);
      setTimeline(res.timeline);
      setSubtitles(res.timeline.subtitles || []);
      setIsEdited(true);
      addChatMessage('assistant', res.message, { actionDescription: 'Redo' });
    } catch (err) {
      addChatMessage('assistant', `Redo error: ${err.message}`, { isError: true });
    }
  };

  const handleSelectClip = (clipId) => {
    const clip = timeline.clips.find((c) => c.id === clipId);
    if (!clip) return;
    setTimeline((prev) => ({
      ...prev,
      selected_clip_id: clipId,
      selection_range: [clip.timeline_start, clip.timeline_end],
    }));
    setCurrentTime(clip.timeline_start);
  };

  const handleSeekToScene = (start, end) => {
    setCurrentTime(start);
    setPlaybackRange([start, end]);
    setTimeline((prev) => ({ ...prev, selection_range: [start, end] }));
    setIsPlaying(true);
  };

  // Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;

      if (e.code === 'Space') {
        e.preventDefault();
        setIsPlaying((prev) => !prev);
      } else if (e.key === 's' || e.key === 'S') {
        e.preventDefault();
        handleSplitAtPlayhead();
      } else if (e.key === 'Delete' || e.key === 'Backspace') {
        e.preventDefault();
        handleDelete();
      } else if ((e.ctrlKey || e.metaKey) && (e.key === 'z' || e.key === 'Z')) {
        e.preventDefault();
        if (e.shiftKey) handleRedo();
        else handleUndo();
      } else if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'S')) {
        e.preventDefault();
        handleSaveProject();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [timeline, currentTime]);

  const selectedClip = timeline.clips.find((c) => c.id === timeline.selected_clip_id) || null;

  return (
    <div className="h-screen w-screen flex flex-col bg-[#111215] text-[#b3b7c0] overflow-hidden font-sans">
      {/* 1. DaVinci Resolve Top Navigation & Toolbar */}
      <Navbar
        projectName={projectName}
        onSaveProject={handleSaveProject}
        onNewProject={() => setIsProjectModalOpen(true)}
        onOpenProjectList={() => setIsProjectModalOpen(true)}
        onAnalyze={handleAnalyze}
        isAnalyzing={isAnalyzing}
        onOpenExport={() => setIsExportOpen(true)}
        onLoadSample={handleLoadSample}
        hasMedia={!!videoMetadata}
        activeRightTab={activeRightTab}
        setActiveRightTab={setActiveRightTab}
        isEdited={isEdited}
      />

      {/* 2. Middle Main Workspace (Media Pool | Video Viewer | Inspector/AI) */}
      <div className="flex-1 flex overflow-hidden min-h-0 border-b border-[#212328]">
        {/* Left: Media Pool */}
        <div className="w-80 shrink-0 h-full border-r border-[#212328]">
          <MediaImportPanel
            videoMetadata={videoMetadata}
            audioTrack={audioTrack}
            subtitles={subtitles}
            onUploadVideo={handleUploadVideo}
            onUploadAudio={handleUploadAudio}
            onUploadSubtitle={handleUploadSubtitle}
            onRemoveMedia={handleRemoveMedia}
          />
        </div>

        {/* Center: Video Viewer */}
        <div className="flex-1 h-full flex flex-col min-w-0">
          <VideoPlayer
            videoSrc={videoSrc}
            timeline={timeline}
            currentTime={currentTime}
            onTimeUpdate={setCurrentTime}
            isPlaying={isPlaying}
            setIsPlaying={setIsPlaying}
            subtitles={subtitles}
            playbackRange={playbackRange}
            onPlaybackComplete={() => setPlaybackRange(null)}
            fps={videoMetadata?.fps || 25}
          />
        </div>

        {/* Right: Inspector & AI Assistant Panel */}
        <div className="w-80 shrink-0 h-full border-l border-[#212328] flex flex-col bg-[#141518]">
          <div className="flex-1 overflow-hidden">
            {activeRightTab === 'inspector' ? (
              <Inspector
                selectedClip={selectedClip}
                timeline={timeline}
                analysis={analysis}
                onSeekToScene={handleSeekToScene}
                onUpdateClipSpeed={(id, spd) => {
                  setTimeline((prev) => ({
                    ...prev,
                    clips: prev.clips.map((c) => (c.id === id ? { ...c, speed: spd } : c)),
                  }));
                  setIsEdited(true);
                }}
                onUpdateClipVolume={(id, vol) => {
                  setTimeline((prev) => ({
                    ...prev,
                    clips: prev.clips.map((c) => (c.id === id ? { ...c, volume: vol } : c)),
                  }));
                  setIsEdited(true);
                }}
                videoMetadata={videoMetadata}
              />
            ) : (
              <AIChatbotPanel
                chatMessages={chatMessages}
                onSendCommand={handleSendCommand}
                isProcessing={isChatProcessing}
                onSelectSuggestion={(cmd) => handleSendCommand(cmd)}
                onApplyProposal={() => {}}
                onCancelProposal={() => {}}
              />
            )}
          </div>
        </div>
      </div>

      {/* 3. Bottom: DaVinci Multi-Track Timeline */}
      <div className="h-56 shrink-0">
        <InteractiveTimeline
          timeline={timeline}
          currentTime={currentTime}
          onSeek={setCurrentTime}
          onSelectClip={handleSelectClip}
          onSelectRange={(start, end) =>
            setTimeline((prev) => ({ ...prev, selection_range: [start, end] }))
          }
          onSplitAtPlayhead={handleSplitAtPlayhead}
          onDeleteSelection={handleDelete}
          onUndo={handleUndo}
          fps={videoMetadata?.fps || 25}
        />
      </div>

      {/* 4. Bottom DaVinci Page Switcher */}
      <BottomPageBar activePage="edit" />

      {/* 5. Modals */}
      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        timeline={timeline}
        audioTrack={audioTrack}
        videoMetadata={videoMetadata}
      />

      <ProjectListModal
        isOpen={isProjectModalOpen}
        onClose={() => setIsProjectModalOpen(false)}
        currentProjectId={projectId}
        onSwitchProject={handleSwitchProject}
      />
    </div>
  );
}
