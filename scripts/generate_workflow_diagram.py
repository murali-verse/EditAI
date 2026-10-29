"""
EditMind AI - System Workflow & Architecture Diagram Generator
Generates a high-resolution, professional infographic diagram image.
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ArrowStyle, ConnectionStyle

def create_workflow_diagram(output_path):
    fig = plt.figure(figsize=(24, 15), dpi=200)
    ax = fig.add_subplot(111)
    
    # Background
    bg_color = '#0c1017'
    fig.patch.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    ax.set_xlim(0, 240)
    ax.set_ylim(0, 150)
    ax.axis('off')

    # Color Palette
    PALETTE = {
        'ingest': {'card_bg': '#141c28', 'border': '#38bdf8', 'title': '#38bdf8', 'accent': '#0284c7'},
        'analysis': {'card_bg': '#19152b', 'border': '#a855f7', 'title': '#c084fc', 'accent': '#9333ea'},
        'assembly': {'card_bg': '#10221c', 'border': '#10b981', 'title': '#34d399', 'accent': '#059669'},
        'studio': {'card_bg': '#221c15', 'border': '#f59e0b', 'title': '#fbbf24', 'accent': '#d97706'},
        'ai_chat': {'card_bg': '#24141e', 'border': '#f43f5e', 'title': '#fb7185', 'accent': '#e11d48'},
        'export': {'card_bg': '#141e2b', 'border': '#6366f1', 'title': '#818cf8', 'accent': '#4f46e5'},
        'db': {'card_bg': '#18202c', 'border': '#64748b', 'title': '#94a3b8', 'accent': '#475569'},
        'text_light': '#f8fafc',
        'text_dim': '#94a3b8',
        'arrow_color': '#64748b',
        'arrow_active': '#38bdf8'
    }

    # Top Header Banner
    header_box = FancyBboxPatch(
        (8, 134), 224, 12,
        boxstyle="round,pad=0.6,rounding_size=1.5",
        fc='#131924', ec='#1e293b', lw=1.5
    )
    ax.add_patch(header_box)
    
    ax.text(14, 141.5, "EDITMIND AI", fontsize=20, fontweight='bold', color='#38bdf8', family='sans-serif')
    ax.text(62, 141.5, "|", fontsize=18, color='#64748b')
    ax.text(67, 141.5, "End-to-End Intelligent Video Production & Editing Architecture", fontsize=16, fontweight='bold', color='#f1f5f9', family='sans-serif')
    ax.text(14, 136.5, "Comprehensive System Workflow: Media Ingestion, Multimodal AI, Auto-Assembly, Interactive Studio, Chatbot & FFmpeg Pipeline", 
            fontsize=10.5, color='#94a3b8', family='sans-serif')

    def draw_stage_card(x, y, w, h, stage_key, title, subtitle, items, tag="STAGE"):
        pal = PALETTE[stage_key]
        
        # Outer Card
        card = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.8,rounding_size=2.0",
            fc=pal['card_bg'], ec=pal['border'], lw=2.0, zorder=2
        )
        ax.add_patch(card)
        
        # Header Badge
        badge = FancyBboxPatch(
            (x + 2, y + h - 4.5), len(tag)*1.4 + 3, 3.2,
            boxstyle="round,pad=0.2,rounding_size=0.8",
            fc=pal['border'], ec='none', zorder=3
        )
        ax.add_patch(badge)
        ax.text(x + 3.2, y + h - 2.8, tag, fontsize=8.5, fontweight='bold', color='#000000', family='sans-serif', zorder=4)

        # Title & Subtitle
        ax.text(x + len(tag)*1.4 + 7.5, y + h - 2.8, title, fontsize=12.5, fontweight='bold', color=pal['title'], family='sans-serif', zorder=3)
        ax.text(x + 2.5, y + h - 7.5, subtitle, fontsize=9, color=pal['border'], family='sans-serif', style='italic', zorder=3)
        
        # Divider line
        ax.plot([x + 2, x + w - 2], [y + h - 9.5, y + h - 9.5], color=pal['border'], lw=0.8, alpha=0.4, zorder=3)

        # Sub-items / Components
        curr_y = y + h - 13.5
        for item in items:
            box_h = item.get('h', 7.5)
            # Item Box
            item_box = FancyBboxPatch(
                (x + 2, curr_y - box_h + 3), w - 4, box_h,
                boxstyle="round,pad=0.4,rounding_size=1.0",
                fc='#0b111a', ec='#263445', lw=1.0, zorder=3
            )
            ax.add_patch(item_box)
            
            # Bullet icon / tag
            icon_text = item.get('icon', '>')
            ax.text(x + 3.5, curr_y - 0.5, icon_text, fontsize=9.5, fontweight='bold', color=pal['border'], zorder=4)
            ax.text(x + 7, curr_y - 0.5, item['name'], fontsize=10, fontweight='bold', color='#f8fafc', family='sans-serif', zorder=4)
            
            # Details description
            desc_lines = item.get('desc', [])
            dy = 2.4
            for line in desc_lines:
                ax.text(x + 7, curr_y - dy, line, fontsize=8, color='#94a3b8', family='sans-serif', zorder=4)
                dy += 2.0
            
            curr_y -= (box_h + 2.2)

    # ------------------ STAGE 1: MEDIA INGESTION ------------------
    s1_items = [
        {
            'icon': '[+]', 'name': 'Media Pool Batch Ingestion', 'h': 9.0,
            'desc': [
                '- Multi-file upload: MP4, MOV, WebM, MP3, SRT',
                '- Drag-and-drop & folder selection in UI',
                '- Asynchronous chunked storage in /uploads'
            ]
        },
        {
            'icon': '[#]', 'name': 'FFprobe Metadata Extraction', 'h': 8.5,
            'desc': [
                '- Codec, resolution (4K/1080p), FPS extraction',
                '- Duration, audio sample rate & channels',
                '- Dynamic grid/list view preview cache'
            ]
        },
        {
            'icon': '[*]', 'name': 'Automated Filmstrip Sampler', 'h': 7.5,
            'desc': [
                '- Thumbnail generation at key time offsets',
                '- Fast client-side hover scrubber previews'
            ]
        }
    ]
    draw_stage_card(8, 70, 48, 58, 'ingest', '1. Media Ingestion', 'Uploads, Probing & Asset Management', s1_items, 'INPUT')

    # ------------------ STAGE 2: MULTIMODAL AI ANALYSIS ------------------
    s2_items = [
        {
            'icon': '[#]', 'name': 'PySceneDetect Visual Analyzer', 'h': 9.0,
            'desc': [
                '- ContentDetector / Adaptive thresholding',
                '- Precise shot cut detection & timestamps',
                '- Visual motion scoring & activity classification'
            ]
        },
        {
            'icon': '[~]', 'name': 'Whisper ASR Speech-to-Text', 'h': 9.0,
            'desc': [
                '- Audio stream extraction via FFmpeg',
                '- Word-level & sentence timestamped transcripts',
                '- Automated SRT caption generation'
            ]
        },
        {
            'icon': '[_]', 'name': 'Silence & Dead-Air Detector', 'h': 8.0,
            'desc': [
                '- Decibel energy threshold analysis (<-35dB)',
                '- Identifies long pauses & redundant gaps',
                '- Generates candidate jump-cut list'
            ]
        }
    ]
    draw_stage_card(64, 70, 52, 58, 'analysis', '2. Multimodal AI Analysis', 'Vision, Audio & Semantic Scene Detection', s2_items, 'AI CORE')

    # ------------------ STAGE 3: AI AUTO-ASSEMBLY STAGE ------------------
    s3_items = [
        {
            'icon': '[*]', 'name': 'Multi-LLM Narrative Engine', 'h': 9.0,
            'desc': [
                '- Models: Gemini 1.5, GPT-4o-mini, Ollama 3.2',
                '- Prompt synthesis: Story, tone, audience',
                '- Style adaptation: Documentary, Fast-Cut, Promo'
            ]
        },
        {
            'icon': '[%]', 'name': 'Intelligent Clip Sequencing', 'h': 9.0,
            'desc': [
                '- Cross-video segment ranking & curation',
                '- Hook -> Development -> Climax -> Outro',
                '- Context-preserving pacing & audio alignment'
            ]
        },
        {
            'icon': '[+]', 'name': 'Automated Timeline Dispatch', 'h': 8.0,
            'desc': [
                '- Assembles multitrack sequence into Timeline',
                '- Emits editable segments with zero lock-in',
                '- Reversible, non-destructive refinement'
            ]
        }
    ]
    draw_stage_card(124, 70, 52, 58, 'assembly', '3. AI Auto-Assembly', 'Story Synthesis & Cross-Video Sequencing', s3_items, 'AUTONOMOUS')

    # ------------------ STAGE 6: RENDERING & EXPORT ------------------
    s6_items = [
        {
            'icon': '[#]', 'name': 'FFmpeg FilterGraph Compositor', 'h': 9.0,
            'desc': [
                '- Dynamic filter_complex builder',
                '- Precise trim, scale, setpts speed sync',
                '- Audio normalization & cross-dissolves'
            ]
        },
        {
            'icon': '[~]', 'name': 'Subtitle & Overlay Renderer', 'h': 8.0,
            'desc': [
                '- Hardcoded or soft SRT/VTT caption muxing',
                '- Aspect ratio adaptation (16:9, 9:16 vertical)',
                '- Color space & bitrate target optimization'
            ]
        },
        {
            'icon': '[^]', 'name': 'Deliverable Distribution', 'h': 8.0,
            'desc': [
                '- Master MP4 / H.264 / AAC render output',
                '- Real-time progress tracker in Export Modal',
                '- Direct browser download & stream preview'
            ]
        }
    ]
    draw_stage_card(184, 70, 48, 58, 'export', '6. Render & Export', 'FFmpeg Multitrack Compositing Engine', s6_items, 'DELIVERY')

    # ------------------ STAGE 4: INTERACTIVE RESOLVE STUDIO (BOTTOM LEFT) ------------------
    s4_items = [
        {
            'icon': '[=]', 'name': 'DaVinci Resolve 21 Layout UI', 'h': 9.0,
            'desc': [
                '- Full workspace: Media, Cut, Edit, Deliver tabs',
                '- Dual-view player with live scrubbing & TCG timecode',
                '- Inspector: Transform, Zoom, Opacity, Speed, Audio'
            ]
        },
        {
            'icon': '[#]', 'name': 'Interactive Multitrack Timeline', 'h': 9.0,
            'desc': [
                '- V1 (Video), A1 (Audio), S1 (Subtitle) lanes',
                '- Visual razor tool, ripple edit, trim in/out handles',
                '- Playhead scrubbing with frame-accurate sync'
            ]
        },
        {
            'icon': '[<>]', 'name': 'State & History Manager', 'h': 8.0,
            'desc': [
                '- Comprehensive Undo / Redo action stack',
                '- SQLite persistent project snapshotting',
                '- Non-destructive clip manipulation'
            ]
        }
    ]
    draw_stage_card(8, 6, 82, 57, 'studio', '4. Interactive Resolve Studio', 'React + Tailwind Timeline & Professional Workspace', s4_items, 'WORKSPACE')

    # ------------------ STAGE 5: EDITAI CONVERSATIONAL ASSISTANT (BOTTOM CENTER) ------------------
    s5_items = [
        {
            'icon': '[?]', 'name': 'Natural Language Command Parser', 'h': 9.0,
            'desc': [
                '- "Split clip at 00:15", "Delete second half"',
                '- "Remove silences", "Speed up clip 1 to 2x"',
                '- Ambiguity validation & confirmation prompts'
            ]
        },
        {
            'icon': '[*]', 'name': 'Multi-Provider Model Adapter', 'h': 9.0,
            'desc': [
                '- Google Gemini API (gemini-1.5-flash)',
                '- OpenAI / Groq API (gpt-4o-mini / llama-3.3-70b)',
                '- Local Ollama (llama3.2:1b) CPU/GPU inference'
            ]
        },
        {
            'icon': '[!]', 'name': 'Atomic Timeline Dispatcher', 'h': 8.0,
            'desc': [
                '- Converts LLM JSON tool intents to timeline operations',
                '- Relative reference resolver ("first clip", "last segment")',
                '- Instant real-time UI state synchronization'
            ]
        }
    ]
    draw_stage_card(98, 6, 80, 57, 'ai_chat', '5. EditAI Assistant', 'Conversational AI Co-Pilot with Multi-LLM Backend', s5_items, 'CHATBOT')

    # ------------------ CENTRAL DATABASE & REPOSITORY (BOTTOM RIGHT) ------------------
    db_items = [
        {
            'icon': '[#]', 'name': 'Persistent Storage Engine', 'h': 9.0,
            'desc': [
                '- SQLite editmind.db (Projects, Timelines, Clips)',
                '- File system cache in /backend/uploads',
                '- Generated speech SRTs & thumbnails store'
            ]
        },
        {
            'icon': '[&]', 'name': 'REST API / FastAPI Gateway', 'h': 9.0,
            'desc': [
                '- /api/media, /api/analysis, /api/assembly',
                '- /api/timeline, /api/chatbot, /api/export',
                '- Non-blocking async background workers'
            ]
        },
        {
            'icon': '[^]', 'name': 'Collision-Proof Launcher', 'h': 8.0,
            'desc': [
                '- run_app.py port sniffing & auto-recovery',
                '- Stale process cleanup (Errno 10048 protection)',
                '- Isolated git repo without virtualenv bloat'
            ]
        }
    ]
    draw_stage_card(184, 6, 48, 57, 'db', 'Backend Core', 'FastAPI, SQLite & System Hub', db_items, 'SYSTEM')

    # ------------------ CONNECTION ARROWS & DATA FLOWS ------------------
    def draw_flow_arrow(start, end, label=None, color='#38bdf8', rad=0.0, lw=2.0, style='->'):
        arrow_style = ArrowStyle(style, head_length=0.7, head_width=0.4)
        connection_style = ConnectionStyle("Arc3", rad=rad)
        
        arrow = patches.FancyArrowPatch(
            start, end,
            arrowstyle=arrow_style,
            connectionstyle=connection_style,
            color=color,
            lw=lw,
            zorder=6
        )
        ax.add_patch(arrow)
        
        if label:
            mid_x = (start[0] + end[0]) / 2
            mid_y = (start[1] + end[1]) / 2 + (rad * 10)
            bbox_props = dict(boxstyle="round,pad=0.3", fc="#0f172a", ec=color, lw=1.0, alpha=0.95)
            ax.text(mid_x, mid_y, label, fontsize=8, color='#f1f5f9', fontweight='bold',
                    ha='center', va='center', bbox=bbox_props, zorder=7)

    # Ingestion -> Analysis
    draw_flow_arrow((56, 102), (64, 102), label="Raw Video/Audio", color='#38bdf8', lw=2.2)

    # Analysis -> Assembly
    draw_flow_arrow((116, 102), (124, 102), label="Scenes & Transcripts", color='#c084fc', lw=2.2)

    # Assembly -> Studio Timeline (Curved down-left)
    draw_flow_arrow((140, 70), (75, 63), label="Assembled Timeline JSON", color='#34d399', rad=-0.22, lw=2.4)

    # Ingestion -> Studio Media Pool (Direct Downward)
    draw_flow_arrow((30, 70), (30, 63), label="Direct Asset Ingest", color='#38bdf8', lw=2.0)

    # Studio Timeline <-> EditAI Assistant (Bidirectional)
    draw_flow_arrow((90, 36), (98, 36), label="NL Action Execution", color='#fb7185', lw=2.2)
    draw_flow_arrow((98, 24), (90, 24), label="Live Timeline State", color='#fbbf24', lw=2.2)

    # Studio Timeline -> Export Engine (Long Arc Up-Right)
    draw_flow_arrow((90, 48), (184, 98), label="Final Sequence EDL & Assets", color='#818cf8', rad=0.25, lw=2.4)

    # Analysis -> Backend DB
    draw_flow_arrow((90, 70), (184, 40), label="Analysis Cache", color='#94a3b8', rad=-0.15, lw=1.5)

    # Backend Core <-> Studio
    draw_flow_arrow((184, 25), (178, 25), label="CRUD / Sync", color='#64748b', lw=1.8)

    # Export Engine -> Output Final MP4 Badge
    final_box = FancyBboxPatch(
        (205, 65), 26, 4.5,
        boxstyle="round,pad=0.2,rounding_size=0.6",
        fc='#059669', ec='#34d399', lw=1.5, zorder=8
    )
    ax.add_patch(final_box)
    ax.text(218, 67.2, "PRODUCTION MP4", fontsize=8.5, fontweight='bold', color='#ffffff', ha='center', va='center', zorder=9)

    # Footer Notes & Legend
    footer_box = FancyBboxPatch(
        (8, 0.5), 224, 4.2,
        boxstyle="round,pad=0.3,rounding_size=0.8",
        fc='#111622', ec='#1e293b', lw=1.0
    )
    ax.add_patch(footer_box)
    legend_text = (
        "LEGEND:  "
        "[Cyan] Media Ingestion   |   "
        "[Purple] Multimodal AI & Whisper   |   "
        "[Emerald] Narrative Auto-Assembly   |   "
        "[Amber] DaVinci Resolve Studio UI   |   "
        "[Rose] Conversational Co-Pilot   |   "
        "[Indigo] FFmpeg Render Engine"
    )
    ax.text(12, 2.5, legend_text, fontsize=9, fontweight='bold', color='#94a3b8', family='sans-serif')
    ax.text(228, 2.5, "v2.0 Architecture", fontsize=9, color='#64748b', ha='right', family='sans-serif')

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor='none', bbox_inches='tight', dpi=200)
    plt.close()
    print(f"Workflow diagram successfully created at: {output_path}")

if __name__ == '__main__':
    target = os.path.abspath("workflow_diagram.png")
    create_workflow_diagram(target)
