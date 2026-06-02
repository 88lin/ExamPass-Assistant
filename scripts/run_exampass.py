"""
Single entry-point for /exampass skill.
Usage: python scripts/run_exampass.py <target_directory>

Handles the full pipeline:
  1. Scan & group files
  2. Extract content (text + images)
  3. Save extraction to JSON for Claude analysis
  4. Print instructions for the next step

No inline Python in shell commands needed. All output written to files.
"""

import sys, os, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scanner import scan_and_group, get_group_name
from extractor import extract_file, merge_group_content
from image_extractor import extract_from_pptx
from ocr_backend import ocr_images, is_multimodal_hint


def main(target_dir):
    target = os.path.abspath(target_dir)
    if not os.path.isdir(target):
        print("ERROR: Directory not found:", target)
        sys.exit(1)

    groups = scan_and_group(target)
    if not groups:
        print("No supported files (PPTX/DOCX/PDF) found in", target)
        sys.exit(0)

    print("Found", len(groups), "group(s)\n")

    for folder, files in groups.items():
        group_name = get_group_name(folder, target)
        print("=" * 50)
        print("Processing:", group_name)
        print("Files:", len(files))
        print("=" * 50)

        results = []
        all_images = []

        img_dir = os.path.join(folder, '_images')
        os.makedirs(img_dir, exist_ok=True)

        for fpath in files:
            fname = os.path.basename(fpath)
            ext = os.path.splitext(fpath)[1].lower()
            print("  Extracting:", fname, "(" + ext + ")")

            result = extract_file(fpath, image_output_dir=img_dir)
            results.append(result)
            all_images.extend(result.get('images', []))

            # Save individual extraction text for debugging
            txt_path = os.path.join(folder, fname + '_extracted.txt')
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(result['text_summary'])
            print("    Text:", len(result['text_summary']), "chars ->", txt_path)

        merged = merge_group_content(results)

        # Non-multimodal models can't see images -> OCR them into text so
        # chart/formula/diagram content isn't lost.
        ocr_text = ''
        if all_images and not is_multimodal_hint():
            print("  Model is text-only; running OCR on", len(all_images), "image(s)...")
            ocr_text = ocr_images(all_images)
            if ocr_text:
                merged += "\n\n## 图片 OCR 文本\n" + ocr_text
                print("    OCR text:", len(ocr_text), "chars merged into bundle")

        # Save extraction bundle for Claude analysis
        bundle = {
            'group_name': group_name,
            'folder': folder,
            'merged_text': merged,
            'file_count': len(files),
            'image_count': len(all_images),
            'images': all_images,
            'ocr_used': bool(ocr_text),
            'individual_results': [
                {'filename': os.path.basename(f), 'text_length': len(r['text_summary'])}
                for f, r in zip(files, results)
            ],
        }
        bundle_path = os.path.join(folder, '_extraction_bundle.json')
        with open(bundle_path, 'w', encoding='utf-8') as f:
            json.dump(bundle, f, ensure_ascii=False)
        print("  Bundle saved:", bundle_path)
        print("  Total merged:", len(merged), "chars")
        print()

    print("Done. Extraction complete for", len(groups), "group(s).")
    print()
    print("Next step: Claude reads the _extraction_bundle.json files and runs:")
    print("  from template_engine import save_knowledge_html, save_test")
    print("  save_knowledge_html(body_html, 'path/to/output.html', title)")
    print("  save_test(questions_list, 'path/to/test.html', title, subtitle)")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python run_exampass.py <target_directory>")
        sys.exit(1)
    main(sys.argv[1])
