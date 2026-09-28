import argparse
import json
from pathlib import Path

from app.media import probe_media, build_segments
from app.analyzer import OllamaV5
from app.scorer import weighted_score, aggregate_segments


def main():
    parser = argparse.ArgumentParser(description="AI Horror Analyzer V5 - local Ollama pipeline")
    parser.add_argument("movie", help="Path to movie/video file")
    parser.add_argument("--segments", type=int, default=None,
                        help="Analyze only N evenly spaced segments (useful for testing)")
    parser.add_argument("--segment-seconds", type=int, default=120)
    parser.add_argument("--vision-model", default="qwen3-vl:8b")
    parser.add_argument("--text-model", default="qwen3:4b")
    parser.add_argument("--output", default="output/analysis.json")
    args = parser.parse_args()

    movie = probe_media(args.movie)

    total_segments = int((movie["duration_seconds"] + args.segment_seconds - 1) // args.segment_seconds)

    if args.segments:
        n = min(args.segments, total_segments)
        if n == 1:
            indices = [0]
        else:
            indices = sorted(set(round(i * (total_segments - 1) / (n - 1)) for i in range(n)))
    else:
        indices = None

    work_dir = Path("output/frames")
    segments, total = build_segments(
        movie["duration_seconds"],
        args.segment_seconds,
        str(work_dir),
        args.movie,
        indices,
    )

    analyzer = OllamaV5(
        vision_model=args.vision_model,
        text_model=args.text_model,
    )

    weights = json.loads(Path("config/scoring.json").read_text())["weights"]
    rows = []

    print(f"Movie: {args.movie}")
    print(f"Duration: {movie['duration_seconds']:.1f}s")
    print(f"Segments selected: {len(segments)} / {total}")
    print(f"Vision model: {args.vision_model}")
    print(f"Text model: {args.text_model}")

    for i, seg in enumerate(segments, 1):
        print(f"\n[{i}/{len(segments)}] Segment {seg['start']:.0f}-{seg['end']:.0f}s")

        evidence = analyzer.vision_stage(
            seg["frame_paths"], seg["start"], seg["end"]
        )
        print(f"  Vision evidence: {len(evidence)} chars")

        analysis = analyzer.score_stage(
            evidence, seg["start"], seg["end"]
        )
        score, used = weighted_score(analysis, weights)

        print(f"  Score: {score}")

        rows.append({
            "index": seg["index"],
            "start": seg["start"],
            "end": seg["end"],
            "score": score,
            "dimension_scores": {
                d: {
                    "score": getattr(analysis, d).score,
                    "confidence": getattr(analysis, d).confidence,
                    "evidence": getattr(analysis, d).evidence,
                }
                for d in weights
            },
            "summary": analysis.summary,
            "visual_observations": analysis.visual_observations,
            "horror_mechanisms": analysis.horror_mechanisms,
            "weighted_dimensions": used,
        })

    result = {
        "analyzer_version": "ollama-v5-two-stage",
        "model_vision": args.vision_model,
        "model_text": args.text_model,
        "movie": movie,
        "coverage": {
            "total_segments": total,
            "analyzed_segments": len(segments),
            "segment_seconds": args.segment_seconds,
            "frames_per_segment": 3,
        },
        "segments": rows,
        "aggregate": aggregate_segments(rows),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    print("\n=== FINAL ===")
    print(json.dumps(result["aggregate"], indent=2))
    print(f"\nSaved: {output}")


if __name__ == "__main__":
    main()
