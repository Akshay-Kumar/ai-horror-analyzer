import argparse
import json
from pathlib import Path
from app.analyzer import HorrorAnalyzer
from app.media import build_segments, probe_media
from app.schemas import MovieAnalysis, Segment
from app.scorer import aggregate, load_weights, weighted_score

def parse_segment_selection(value):
    if not value:
        return None
    try:
        return [int(x.strip()) for x in value.split(",") if x.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Segments must be comma-separated integers, e.g. 0,20,40") from exc

def main():
    parser = argparse.ArgumentParser(description="AI Horror Analyzer V2")
    parser.add_argument("movie", type=Path)
    parser.add_argument("--segment-seconds", type=int, default=120)
    parser.add_argument("--frames", type=int, default=3)
    parser.add_argument("--segments", type=parse_segment_selection, default=None, help="Selected segment indexes, e.g. 0,20,40")
    parser.add_argument("--model", default=None, help="Override OPENAI_MODEL")
    args = parser.parse_args()
    if not args.movie.exists():
        raise SystemExit(f"Movie not found: {args.movie}")
    if args.segment_seconds <= 0 or args.frames <= 0:
        raise SystemExit("--segment-seconds and --frames must be greater than 0")
    output_dir = Path("output") / args.movie.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[1/4] Probing: {args.movie.name}")
    media = probe_media(args.movie)
    print(f"      duration={media.duration_seconds:.1f}s resolution={media.width}x{media.height} subtitles={media.subtitle_streams}")
    print(f"[2/4] Extracting selected segments: {args.segments}" if args.segments else "[2/4] Creating all segments and extracting frames")
    raw = build_segments(args.movie, media.duration_seconds, output_dir, args.segment_seconds, args.frames, args.segments)
    segments = [Segment(**x) for x in raw]
    print(f"      prepared {len(segments)} segments")
    print("[3/4] Running multimodal AI analyzer")
    analyzer = HorrorAnalyzer(model=args.model)
    analyses = []
    for pos, segment in enumerate(segments, 1):
        print(f"      analyzing segment {segment.index} ({pos}/{len(segments)})...")
        analyses.append(analyzer.analyze_segment(segment))
    print("[4/4] Aggregating scores")
    weights = load_weights(Path("config/scoring.json"))
    scores = aggregate(analyses)
    overall = weighted_score(scores, weights)
    mechanisms = sorted({m for a in analyses for m in a.fear_mechanisms})
    result = MovieAnalysis(analyzer_version=analyzer.VERSION, media=media, overall_horror_score=overall, scores=scores, fear_mechanisms=mechanisms, segments=analyses)
    output_file = output_dir / "analysis.json"
    output_file.write_text(json.dumps(result.model_dump(), indent=2), encoding="utf-8")
    print(f"\nDone: {output_file}")
    print(f"Horror effectiveness score from analyzed segments: {overall}/10")
    print(f"Analyzer model: {analyzer.model}")

if __name__ == "__main__":
    main()
