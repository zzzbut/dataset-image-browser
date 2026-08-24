import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from tk_app import LabelStore

print("=" * 80)
print("测试不同场景下的标签加载")
print("=" * 80)

# 场景1: 归一化坐标 + 正常图像尺寸
test_data_normalized = {
    "version": "4.0.0-beta.2",
    "shapes": [
        {
            "label": "car",
            "score": 0.95,
            "shape_type": "rectangle",
            "points": [[0.1, 0.2], [0.5, 0.2], [0.5, 0.6], [0.1, 0.6]],
            "group_id": None,
            "flags": {},
            "description": None,
            "mask": None
        }
    ],
    "imagePath": "test.png",
    "imageData": None,
    "imageHeight": 1080,
    "imageWidth": 1920
}

# 场景2: 像素坐标 + imageWidth/imageHeight=-1 + image_size=(1920,1080)
test_data_pixel_minus1 = {
    "version": "4.0.0-beta.2",
    "shapes": [
        {
            "label": "car",
            "score": 0.95,
            "shape_type": "rectangle",
            "points": [[192, 216], [960, 216], [960, 648], [192, 648]],
            "group_id": None,
            "flags": {},
            "description": None,
            "mask": None
        }
    ],
    "imagePath": "test2.png",
    "imageData": None,
    "imageHeight": -1,
    "imageWidth": -1
}

# 场景3: 像素坐标 + imageWidth/imageHeight=-1 + 标注尺寸与实际不符
# 用户提供的格式1数据
test_data_user_format1 = {
    "version": "4.0.0-beta.2",
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
    "imagePath": "test3.png",
    "imageData": None,
    "imageHeight": -1,
    "imageWidth": -1
}

# 场景4: 用户提供的格式2数据
test_data_user_format2 = {
    "version": "3.3.9",
    "shapes": [
        {
            "mask": None,
            "label": "outcar",
            "score": 0.9686,
            "points": [[46.165, 893.875], [1802.435, 893.875], [1802.435, 1491.525], [46.165, 1491.525]],
            "group_id": None,
            "description": None,
            "difficult": False,
            "shape_type": "rectangle",
            "flags": {},
            "attributes": {},
            "kie_linking": []
        }
    ],
    "imagePath": "test4.png",
    "imageData": None,
    "imageHeight": 2160,
    "imageWidth": 3840,
    "description": ""
}

with tempfile.TemporaryDirectory() as tmpdir:
    # 创建测试文件
    files = [
        ("test1.json", "test1.png", test_data_normalized, (1920, 1080)),
        ("test2.json", "test2.png", test_data_pixel_minus1, (1920, 1080)),
        ("test3.json", "test3.png", test_data_user_format1, (1920, 1080)),
        ("test4.json", "test4.png", test_data_user_format2, (3840, 2160)),
    ]

    store = LabelStore()
    store.configure("labelme", "detect", tmpdir)

    # 场景1: 归一化坐标
    print("\n场景1: 归一化坐标 + 正常图像尺寸")
    print("-" * 80)
    json_file, img_file, data, image_size = files[0]
    Path(tmpdir).joinpath(img_file).touch()
    with open(Path(tmpdir) / json_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
    labels = store.load_for_image(str(Path(tmpdir) / img_file), image_size)
    print(f"  JSON imageWidth/imageHeight: {data['imageWidth']}/{data['imageHeight']}")
    print(f"  传入 image_size: {image_size}")
    print(f"  原始坐标: {data['shapes'][0]['points']}")
    print(f"  归一化后坐标: {[f'({p[0]:.4f}, {p[1]:.4f})' for p in labels[0].points]}")
    print(f"  预期: 坐标应该保持不变（已是归一化）")
    if all(0 <= p[0] <= 1 and 0 <= p[1] <= 1 for p in labels[0].points):
        print(f"  结果: [PASS]")

    # 场景2: 像素坐标 + imageWidth/imageHeight=-1
    print("\n场景2: 像素坐标 + imageWidth/imageHeight=-1")
    print("-" * 80)
    json_file, img_file, data, image_size = files[1]
    Path(tmpdir).joinpath(img_file).touch()
    with open(Path(tmpdir) / json_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
    labels = store.load_for_image(str(Path(tmpdir) / img_file), image_size)
    print(f"  JSON imageWidth/imageHeight: {data['imageWidth']}/{data['imageHeight']}")
    print(f"  传入 image_size: {image_size}")
    print(f"  原始坐标: {data['shapes'][0]['points']}")
    print(f"  归一化后坐标: {[f'({p[0]:.4f}, {p[1]:.4f})' for p in labels[0].points]}")
    print(f"  预期: (192/1920, 216/1080) 到 (960/1920, 648/1080)")
    expected = [(192/1920, 216/1080), (960/1920, 648/1080), (960/1920, 648/1080), (192/1920, 648/1080)]
    actual = labels[0].points
    if all(abs(actual[i][j] - expected[i][j]) < 0.001 for i in range(4) for j in range(2)):
        print(f"  结果: [PASS]")
    else:
        print(f"  结果: [FAIL]")

    # 场景3: 用户格式1
    print("\n场景3: 用户格式1 (imageWidth=-1, y=[925.1, 1475.2])")
    print("-" * 80)
    json_file, img_file, data, image_size = files[2]
    Path(tmpdir).joinpath(img_file).touch()
    with open(Path(tmpdir) / json_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
    labels = store.load_for_image(str(Path(tmpdir) / img_file), image_size)
    print(f"  JSON imageWidth/imageHeight: {data['imageWidth']}/{data['imageHeight']}")
    print(f"  传入 image_size: {image_size}")
    print(f"  原始坐标 y: [{data['shapes'][0]['points'][0][1]}, {data['shapes'][0]['points'][2][1]}]")
    print(f"  归一化后坐标 y: [{labels[0].points[0][1]:.4f}, {labels[0].points[2][1]:.4f}]")
    print(f"  注意: y 坐标 {1475.2} 超出高度 1080，需要更大的图像尺寸")
    print(f"  如果实际图像是 1920x1080，这说明标注尺寸不匹配")
    print(f"  如果实际图像是 2160，y={1475.2/2160:.4f} 是合理的")

    # 场景4: 用户格式2
    print("\n场景4: 用户格式2 (3840x2160)")
    print("-" * 80)
    json_file, img_file, data, image_size = files[3]
    Path(tmpdir).joinpath(img_file).touch()
    with open(Path(tmpdir) / json_file, "w", encoding="utf-8") as f:
        json.dump(data, f)
    labels = store.load_for_image(str(Path(tmpdir) / img_file), image_size)
    print(f"  JSON imageWidth/imageHeight: {data['imageWidth']}/{data['imageHeight']}")
    print(f"  传入 image_size: {image_size}")
    print(f"  原始坐标 y: [{data['shapes'][0]['points'][0][1]:.2f}, {data['shapes'][0]['points'][2][1]:.2f}]")
    print(f"  归一化后坐标 y: [{labels[0].points[0][1]:.4f}, {labels[0].points[2][1]:.4f}]")
    print(f"  预期: y={893.875/2160:.4f} 到 {1491.525/2160:.4f}")
    if all(0 <= p[0] <= 1 and 0 <= p[1] <= 1 for p in labels[0].points):
        print(f"  结果: [PASS] 坐标在有效范围内")

print("\n" + "=" * 80)
print("问题分析:")
print("=" * 80)
print("场景3的问题:")
print("  - 标注坐标 y=[925.1, 1475.2]")
print("  - 传入的 image_size 是 (1920, 1080)")
print("  - 如果用 1080 作为高度归一化: y=1475.2/1080=1.366 > 1 (无效!)")
print("  - 如果用 1920 作为高度归一化: y=1475.2/1920=0.768 < 1 (有效)")
print("  - 如果用 2160 作为高度归一化: y=1475.2/2160=0.683 < 1 (有效)")
print("")
print("建议解决方案:")
print("  1. 让用户确认真实的图像尺寸")
print("  2. 或者尝试用所有可能的常见尺寸进行测试")
print("  3. 或者检查图像文件本身的尺寸")
