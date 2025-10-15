"""
Tactical Processor - TAHLEEL.ai
Converts YOLOX detections into tactical insights using Claude AI
"""

import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Claude API key from environment
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Import anthropic at module level
try:
    from anthropic import Anthropic
    CLAUDE_AVAILABLE = True
    logger.info(f"✅ Anthropic SDK loaded successfully")
    if ANTHROPIC_API_KEY:
        logger.info(f"✅ ANTHROPIC_API_KEY found (length: {len(ANTHROPIC_API_KEY)})")
    else:
        logger.warning("⚠️ ANTHROPIC_API_KEY not set")
except ImportError as e:
    logger.error(f"❌ Failed to import Anthropic: {e}")
    CLAUDE_AVAILABLE = False

def analyze_formations(detections):
    """Analyze player formations from detections"""
    if not detections:
        return {"team_a": "unknown", "team_b": "unknown"}
    
    team_a_players = []
    team_b_players = []
    
    for frame in detections[:10]:
        for player in frame.get('player_detections', []):
            if player['team_id'] == 0:
                team_a_players.append(player['bbox'])
            else:
                team_b_players.append(player['bbox'])
    
    formations = {
        "team_a": detect_simple_formation(team_a_players),
        "team_b": detect_simple_formation(team_b_players)
    }
    
    return formations

def detect_simple_formation(player_positions):
    """Simple formation detection"""
    if len(player_positions) < 5:
        return "unknown"
    
    player_count = len(player_positions)
    
    if player_count <= 11:
        return "4-4-2"
    elif player_count <= 15:
        return "4-3-3"
    else:
        return "4-2-3-1"

def identify_tactical_weaknesses(detections):
    """Identify tactical weaknesses from player positioning"""
    weaknesses = []
    
    for i, frame in enumerate(detections[:20]):
        players = frame.get('player_detections', [])
        team_b_players = [p for p in players if p['team_id'] == 1]
        
        if len(team_b_players) < 4:
            weaknesses.append({
                "weakness_id": len(weaknesses),
                "frame_number": i,
                "description": "Defensive line underloaded",
                "severity": "medium",
                "recommendation": "Increase defensive coverage"
            })
    
    return weaknesses[:5]

def generate_claude_analysis(detections, formations, weaknesses, metadata):
    """Use Claude AI to generate tactical insights"""
    
    # Check if Claude is available
    if not CLAUDE_AVAILABLE:
        logger.warning("⚠️ Anthropic SDK not available, using fallback")
        return generate_basic_analysis(detections, formations, weaknesses, metadata)
    
    if not ANTHROPIC_API_KEY or len(ANTHROPIC_API_KEY) < 10:
        logger.warning(f"⚠️ Invalid ANTHROPIC_API_KEY, using fallback")
        return generate_basic_analysis(detections, formations, weaknesses, metadata)
    
    try:
        logger.info("🔄 Initializing Claude client...")
        
        # Create client with minimal parameters
        client = Anthropic(
            api_key=ANTHROPIC_API_KEY
        )
        
        logger.info("✅ Claude client initialized, calling API...")
        
        analysis_prompt = f"""You are a professional football tactical analyst. Analyze this match data:

VIDEO METADATA:
- Duration: {metadata.get('duration_seconds')}s  
- Frames analyzed: {metadata.get('total_frames')}
- Resolution: {metadata.get('video_resolution')}

FORMATIONS DETECTED:
- Team A: {formations['team_a']}
- Team B: {formations['team_b']}

TACTICAL WEAKNESSES FOUND:
{json.dumps(weaknesses, indent=2) if weaknesses else 'None identified'}

DETECTION SUMMARY:
- Total frames: {len(detections)}
- Players detected: {sum(len(d.get('player_detections', [])) for d in detections)}
- Average players per frame: {sum(len(d.get('player_detections', [])) for d in detections) / len(detections):.1f}

Provide a concise tactical analysis (max 1000 characters) including:
1. Formation effectiveness assessment
2. Key tactical weaknesses to exploit  
3. Defensive vulnerabilities
4. 3 specific recommended strategies
5. Priority areas to review

Be direct and actionable for a professional football coach."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[
                {"role": "user", "content": analysis_prompt}
            ]
        )
        
        claude_insights = message.content[0].text
        logger.info("✅✅✅ REAL CLAUDE AI ANALYSIS GENERATED! ✅✅✅")
        
        return claude_insights
        
    except Exception as e:
        logger.error(f"❌ Claude API call failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        return generate_basic_analysis(detections, formations, weaknesses, metadata)

def generate_basic_analysis(detections, formations, weaknesses, metadata):
    """Fallback basic analysis without Claude"""
    return f"""TACTICAL ANALYSIS REPORT (Basic Mode)

FORMATIONS:
- Team A: {formations['team_a']}
- Team B: {formations['team_b']}

KEY FINDINGS:
- {len(weaknesses)} tactical weaknesses identified
- Analysis based on {len(detections)} frames
- Average players per frame: {sum(len(d.get('player_detections', [])) for d in detections) / len(detections):.1f}

RECOMMENDATIONS:
1. Review defensive positioning in identified weak frames
2. Analyze formation transitions
3. Focus on exploiting identified vulnerabilities

Note: Enhanced AI analysis with Claude API available when properly configured."""

def process_tactical_analysis(video_id, detections, metadata):
    """Main tactical analysis pipeline"""
    logger.info(f"🎯 Starting tactical analysis for video {video_id}")
    
    formations = analyze_formations(detections)
    logger.info(f"✅ Formations detected: {formations}")
    
    weaknesses = identify_tactical_weaknesses(detections)
    logger.info(f"✅ Weaknesses found: {len(weaknesses)}")
    
    claude_insights = generate_claude_analysis(detections, formations, weaknesses, metadata)
    
    tactical_report = {
        "video_id": video_id,
        "status": "success",
        "formations": formations,
        "weaknesses": weaknesses,
        "claude_insights": claude_insights,
        "metadata": metadata,
        "statistics": {
            "frames_analyzed": len(detections),
            "total_players": sum(len(d.get('player_detections', [])) for d in detections),
            "weaknesses_found": len(weaknesses)
        }
    }
    
    logger.info("🎉 Tactical analysis pipeline complete!")
    
    return tactical_report
