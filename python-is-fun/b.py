from PIL import Image, ImageDraw

# 이미지 불러오기
image = Image.open("favicon.ico").convert("RGBA")

# 원형 마스크 만들기
size = image.size
mask = Image.new("L", size, 0)
draw = ImageDraw.Draw(mask)
draw.ellipse((0, 0, size[0], size[1]), fill=255)

# 마스크 적용
circular_image = Image.new("RGBA", size)
circular_image.paste(image, (0, 0), mask=mask)

# 원형 이미지 저장 (ICO 포맷)
circular_image.save("favicon_circular.ico", format="ICO")
