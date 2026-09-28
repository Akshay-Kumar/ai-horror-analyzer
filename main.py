import argparse
import json
from pathlib import Path
from app.media import probe_media, build_segments
from app.analyzer import HorrorAnalyzer
from app.scorer import average_scores, load_weights, weighted_score
from app.schemas import AnalyzedSegment, MovieAnalysis


def parse_indices(value: str | None):
    if not value:
        return None
    return {int(x.strip()) for x in value.split(",") if x.strip()}


def main():
    parser = argparse.ArgumentParser(description="Local AI Horror Analyzer using Ollama + Qwen3-VL")
    parser.add_argument("media")
    parser.add_argument("--segments", help="Comma-separated segment indexes, e.g. 0,20,40")
    parser.add_argument("--model", default="qwen3-vl:8b")
    parser.add_argument("--segment-seconds", type=int, default=120)
    parser.add_argument("--frames-per-segment", type=int, default=3)
    parser.add_argument("--num-ctx", type=int, default=8192)
    parser.add_argument("--ollama-host", default="http://127.0.0.1:11434")
    args = parser.parse_args()

    media = probe_media(args.media)
    movie_dir = Path("output") / Path(args.media).stem
    frame_dir = movie_dir / "frames"
    selected = parse_indices(args.segments)
    segments = build_segments(
        media, str(frame_dir),
        segment_seconds=args.segment_seconds,
        frames_per_segment=args.frames_per_segment,
        selected_indices=selected,
    )

    analyzer = HorrorAnalyzer(model=args.model, host=args.ollama_host, num_ctx=args.num_ctx)
    analyzed = []
    for pos, segment in enumerate(segments, 1):
        print(f"Analyzing segment {segment.index} ({pos}/{len(segments)})...")
        result = analyzer.analyze_segment(segment)
        analyzed.append(AnalyzedSegment(segment=segment, analysis=result))
        print(f"  escalation={result.escalation} confidence={result.confidence:.2f}")

    scores = average_scores([x.analysis.scores for x in analyzed])
    weights = load_weights()
    overall = weighted_score(scores, weights)
    sampled_coverage = (len(segments) * args.segment_seconds / media.duration_seconds * 100) if media.duration_seconds else 0
    sampled_coverage = min(100.0, round(sampled_coverage, 2))

    output = MovieAnalysis(
        analyzer_version="ollama-v3",
        model=args.model,
        media=media,
        sampled_segment_count=len(segments),
        sampled_coverage_percent=sampled_coverage,
        segments=analyzed,
        overall_horror_score=overall,
        dimension_scores=scores,
    )
    movie_dir.mkdir(parents=True, exist_ok=True)
    out_path = movie_dir / "analysis.json"
    out_path.write_text(output.model_dump_json(indent=2), encoding="utf-8")
    print(f"\nSampled coverage: {sampled_coverage}%")
    print(f"Sampled horror score: {overall}/10")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
