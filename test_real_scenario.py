import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from tk_app import LabelStore

# 测试场景：模拟真实应用场景
# 假设图像文件的真实尺寸是 1920x1080

# 格式1 - imageWidth/imageHeight 为 -1
test_data1 = {
    "version": "4.0.0-beta.2",
    "flags": {},
    "shapes": [
        {
            "label": "outcar",
            "score": 0.9568,
            "shape_type": "rectangle",
            "points": [[0.0, 925.1], [915.5, 925.1], [915.5, 1475.2], [0.0, 1475.2]],
            "group_id": None,
            "flags": {},
            "description": None,
            "mask": None
        }
    ],
    "imagePath": "test1.png",
    "imageData": None,
    "imageHeight": -1,
    "imageWidth": -1
}

with tempfile.TemporaryDirectory() as tmpdir:
    img1 = Path(tmpdir) / "test1.png"
    img1.touch()

    label1 = Path(tmpdir) / "test1.json"
    with open(label1, "w", encoding="utf-8") as f:
        json.dump(test_data1, f)

    store = LabelStore()
    store.configure("labelme", "detect", tmpdir)

    print("=" * 80)
    print("测试场景：假设图像文件的真实尺寸是 1920x1080")
    print("=" * 80)

    # 模拟应用程序传入图像的真实尺寸
    image_size = (1920, 1080)

    labels = store.load_for_image(str(img1), image_size)

    print(f"\n传入的 image_size: {image_size}")
    print(f"JSON 中的 imageWidth/imageHeight: -1/-1")
    print(f"JSON 中坐标 y 范围: [925.1, 1475.2]")
    print(f"理论归一化 y 值: [{925.1/1920:.4f}, {1475.2/1920:.4f}]")

    print("\n实际加载结果:")
    for label in labels:
        print(f"  {label.class_name}:")
        print(f"    归一化坐标: {[f'({p[0]:.4f}, {p[1]:.4f})' for p in label.points]}")

        # 检查坐标是否有效
        for p in label.points:
            if p[0] < 0 or p[0] > 1 or p[1] < 0 or p[1] > 1:
                print(f"    ❌ 坐标 {p} 超出 [0,1] 范围！")
            else:
                print(f"    ✓ 坐标有效")

    print("\n" + "=" * 80)
    print("问题诊断:")
    print("=" * 80)
    print(f"  原始 y 坐标最大值: 1475.2")
    print(f"  如果图像高度是 1080: y/1080 = {1475.2/1080:.4f} > 1 (不合理)")
    print(f"  如果图像高度是 1920: y/1920 = {1475.2/1920:.4f} < 1 (合理)")
    print(f"  如果图像高度是 2160: y/2160 = {1475.2/2160:.4f} < 1 (合理)")

    print("\n结论:")
    print("  当 imageWidth=-1, imageHeight=-1 时:")
    print("  应用程序传入的 image_size 可能不是真实的图像尺寸")
    print("  或者标注工具使用的图像尺寸与实际图像不同")
    print("  建议：让用户提供真实的图像尺寸，或者在标注文件中正确记录尺寸")
