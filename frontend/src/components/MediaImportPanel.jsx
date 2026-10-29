import React, { useRef, useState } from 'react';
import {
  Folder,
  Film,
  Music,
  FileText,
  Plus,
  Trash2,
  Search,
  LayoutGrid,
  List,
  CheckCircle2,
  ArrowUpDown
} from 'lucide-react';
import { formatTimecode, formatBytes } from '../utils/timeUtils';

export default function MediaImportPanel({
  videoMetadata,
  audioTrack,
  subtitles,
  onUploadVideo,
  onUploadAudio,
  onUploadSubtitle,
  onRemoveMedia,
  onSelectMedia
}) {
  const [viewMode, setViewMode] = useState('grid'); // 'grid' | 'list'
  const [searchQuery, setSearchQuery] = useState('');
  const [isImportMenuOpen, setIsImportMenuOpen] = useState(false);

  const videoInputRef = useRef(null);
  const audioInputRef = useRef(null);
  const subtitleInputRef = useRef(null);

  const hasAnyMedia = !!videoMetadata || !!audioTrack || (subtitles && subtitles.length > 0);

  return (
    <div className="h-full flex flex-col bg-[#141518] text-[#a0a4ae] select-none text-[12px]">
      {/* 1. Media Pool Sub-header */}
      <div className="h-8 px-2.5 border-b border-[#212328] flex items-center justify-between bg-[#18191d] text-[11px]">
        {/* Breadcrumb: Master */}
        <div className="flex items-center gap-1.5 text-[#c8cbcd]">
          <Folder className="w-3.5 h-3.5 text-[#737887]" />
          <span className="font-medium">Master</span>
        </div>

        {/* Action icons: Grid/List toggle, Search, Import (+) */}
        <div className="flex items-center gap-1 text-[#7a7f8e]">
          <div className="relative">
            <button
              onClick={() => setIsImportMenuOpen(!isImportMenuOpen)}
              className="p-1 rounded hover:bg-[#252830] hover:text-[#d0d3dc] transition"
              title="Import Media File"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>

            {isImportMenuOpen && (
              <div className="absolute top-7 left-0 w-36 bg-[#1a1c22] border border-[#2e313b] rounded shadow-xl py-1 z-30 text-[11px]">
                <button
                  onClick={() => {
                    setIsImportMenuOpen(false);
                    videoInputRef.current?.click();
                  }}
                  className="w-full text-left px-3 py-1.5 hover:bg-[#252934] text-[#d0d3dc] flex items-center gap-2"
                >
                  <Film className="w-3 h-3 text-[#7f8595]" />
                  <span>Import Video...</span>
                </button>
                <button
                  onClick={() => {
                    setIsImportMenuOpen(false);
                    audioInputRef.current?.click();
                  }}
                  className="w-full text-left px-3 py-1.5 hover:bg-[#252934] text-[#d0d3dc] flex items-center gap-2"
                >
                  <Music className="w-3 h-3 text-[#7f8595]" />
                  <span>Import Audio...</span>
                </button>
                <button
                  onClick={() => {
                    setIsImportMenuOpen(false);
                    subtitleInputRef.current?.click();
                  }}
                  className="w-full text-left px-3 py-1.5 hover:bg-[#252934] text-[#d0d3dc] flex items-center gap-2"
                >
                  <FileText className="w-3 h-3 text-[#7f8595]" />
                  <span>Import Subtitles...</span>
                </button>
              </div>
            )}
          </div>

          <button
            onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
            className="p-1 rounded hover:bg-[#252830] hover:text-[#d0d3dc] transition"
            title="Toggle Grid / List View"
          >
            {viewMode === 'grid' ? <List className="w-3.5 h-3.5" /> : <LayoutGrid className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* 2. Media Pool Canvas */}
      <div className="flex-1 overflow-y-auto p-3">
        {!hasAnyMedia ? (
          /* Empty state exactly matching screenshot */
          <div
            onClick={() => videoInputRef.current?.click()}
            className="h-full flex flex-col items-center justify-center text-center cursor-pointer group"
          >
            <p className="text-[#555a66] text-sm font-normal mb-1 group-hover:text-[#888e9d] transition">
              No clips in media pool
            </p>
            <p className="text-[#3b3e47] text-[11px] group-hover:text-[#555a66] transition">
              Add clips from Media Storage to get started
            </p>
          </div>
        ) : (
          <div className={viewMode === 'grid' ? 'grid grid-cols-2 gap-2' : 'space-y-1.5'}>
            {/* Primary Video Item */}
            {videoMetadata && (
              <div
                className={`bg-[#1c1d22] border border-[#2b2d35] rounded p-2 hover:border-[#3e424e] transition relative group ${
                  viewMode === 'list' ? 'flex items-center justify-between gap-2' : ''
                }`}
              >
                {viewMode === 'grid' && (
                  <div className="w-full aspect-video bg-[#0d0e10] rounded mb-1.5 flex items-center justify-center relative overflow-hidden border border-[#22242a]">
                    <Film className="w-6 h-6 text-[#424653]" />
                    <span className="absolute bottom-1 right-1 bg-black/80 text-[9px] font-mono text-[#a5abb8] px-1 rounded">
                      {formatTimecode(videoMetadata.duration)}
                    </span>
                  </div>
                )}

                <div className="min-w-0 flex-1">
                  <p className="text-[#d8dbe4] font-medium truncate text-[11px]" title={videoMetadata.filename}>
                    {videoMetadata.filename}
                  </p>
                  <p className="text-[10px] text-[#696e7d] font-mono mt-0.5">
                    {videoMetadata.width}x{videoMetadata.height} • {videoMetadata.fps} fps
                  </p>
                </div>

                <div className="flex items-center gap-1 mt-1">
                  <button
                    onClick={() => onRemoveMedia('video')}
                    className="p-1 rounded hover:bg-[#2b2123] hover:text-[#d45555] text-[#555a66] transition opacity-0 group-hover:opacity-100"
                    title="Remove from Media Pool"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            )}

            {/* External Audio Item */}
            {audioTrack && (
              <div
                className={`bg-[#1c1d22] border border-[#2b2d35] rounded p-2 hover:border-[#3e424e] transition relative group ${
                  viewMode === 'list' ? 'flex items-center justify-between gap-2' : ''
                }`}
              >
                {viewMode === 'grid' && (
                  <div className="w-full aspect-video bg-[#0d0e10] rounded mb-1.5 flex items-center justify-center relative border border-[#22242a]">
                    <Music className="w-6 h-6 text-[#424653]" />
                    <span className="absolute bottom-1 right-1 bg-black/80 text-[9px] font-mono text-[#a5abb8] px-1 rounded">
                      {formatTimecode(audioTrack.duration)}
                    </span>
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <p className="text-[#d8dbe4] font-medium truncate text-[11px]">{audioTrack.filename}</p>
                  <p className="text-[10px] text-[#696e7d] font-mono mt-0.5">Audio Track</p>
                </div>
                <button
                  onClick={() => onRemoveMedia('audio')}
                  className="p-1 rounded hover:bg-[#2b2123] hover:text-[#d45555] text-[#555a66] transition opacity-0 group-hover:opacity-100"
                  title="Remove Audio"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            )}

            {/* Subtitles Item */}
            {subtitles && subtitles.length > 0 && (
              <div
                className={`bg-[#1c1d22] border border-[#2b2d35] rounded p-2 hover:border-[#3e424e] transition relative group ${
                  viewMode === 'list' ? 'flex items-center justify-between gap-2' : ''
                }`}
              >
                {viewMode === 'grid' && (
                  <div className="w-full aspect-video bg-[#0d0e10] rounded mb-1.5 flex items-center justify-center relative border border-[#22242a]">
                    <FileText className="w-6 h-6 text-[#424653]" />
                    <span className="absolute bottom-1 right-1 bg-black/80 text-[9px] font-mono text-[#a5abb8] px-1 rounded">
                      {subtitles.length} lines
                    </span>
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <p className="text-[#d8dbe4] font-medium truncate text-[11px]">Subtitles Track</p>
                  <p className="text-[10px] text-[#696e7d] font-mono mt-0.5">{subtitles.length} segments</p>
                </div>
                <button
                  onClick={() => onRemoveMedia('subtitles')}
                  className="p-1 rounded hover:bg-[#2b2123] hover:text-[#d45555] text-[#555a66] transition opacity-0 group-hover:opacity-100"
                  title="Remove Subtitles"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            )}
          </div>
        )}

        {/* Hidden File Inputs */}
        <input
          type="file"
          ref={videoInputRef}
          onChange={(e) => e.target.files?.[0] && onUploadVideo(e.target.files[0])}
          accept="video/mp4,video/quicktime,video/webm,video/x-matroska,video/avi"
          className="hidden"
        />
        <input
          type="file"
          ref={audioInputRef}
          onChange={(e) => e.target.files?.[0] && onUploadAudio(e.target.files[0])}
          accept="audio/mp3,audio/wav,audio/aac,audio/m4a"
          className="hidden"
        />
        <input
          type="file"
          ref={subtitleInputRef}
          onChange={(e) => e.target.files?.[0] && onUploadSubtitle(e.target.files[0])}
          accept=".srt,.vtt,text/plain"
          className="hidden"
        />
      </div>
    </div>
  );
}
