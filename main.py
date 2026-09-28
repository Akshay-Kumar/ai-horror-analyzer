import argparse
import json
from pathlib import Path

from app.analyzer import HorrorAnalyzer
from app.media import build_segments, probe_media
from app.schemas import MovieAnalysis, Segment, SegmentAnalysis
from app.scorer import aggregate, load_weights, weighted_score


def main():
    parser = argparse.ArgumentParser(
        description="AI Horror Analyzer V1"
    )
    parser.add_argument("movie", type=Path)
    parser.add_argument(
        "--segment-seconds",
        type=int,
        default=120,
        help="Length of each analysis segment (default: 120)",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=3,
        help="Representative frames per segment (default: 3)",
    )
    args = parser.parse_args()

    if not args.movie.exists():
        raise SystemExit(f"Movie not found: {args.movie}")

    output_dir = Path("output") / args.movie.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/4] Probing: {args.movie.name}")
    media = probe_media(args.movie)

    print(
        f"      duration={media.duration_seconds:.1f}s "
        f"resolution={media.width}x{media.height} "
        f"subtitles={media.subtitle_streams}"
    )

    print("[2/4] Creating segments and extracting frames")
    raw_segments = build_segments(
        args.movie,
        media.duration_seconds,
        output_dir,
        segment_seconds=args.segment_seconds,
        frames_per_segment=args.frames,
    )
    segments = [Segment(**item) for item in raw_segments]

    print(f"      created {len(segments)} segments")

    print("[3/4] Running analyzer")
    analyzer = HorrorAnalyzer()
    analyses: list[SegmentAnalysis] = []

    for segment in segments:
        print(f"      segment {segment.index + 1}/{len(segments)}")
        analyses.append(analyzer.analyze_segment(segment))

    print("[4/4] Aggregating scores")
    weights = load_weights(Path("config/scoring.json"))
    overall_scores = aggregate(analyses)
    overall_score = weighted_score(overall_scores, weights)

    mechanisms = sorted({
        mechanism
        for analysis in analyses
        for mechanism in analysis.fear_mechanisms
    })

    result = MovieAnalysis(
        analyzer_version=analyzer.VERSION,
        media=media,
        overall_horror_score=overall_score,
        scores=overall_scores,
        fear_mechanisms=mechanisms,
        segments=analyses,
    )

    output_file = output_dir / "analysis.json"
    output_file.write_text(
        json.dumps(result.model_dump(), indent=2),
        encoding="utf-8",
    )

    print()
    print(f"Done: {output_file}")
    print(f"Current placeholder score: {overall_score}/10")
    print("Next step: replace the placeholder analyzer with the real multimodal AI.")


if __name__ == "__main__":
    main()
