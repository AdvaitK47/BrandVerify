import cv2
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def variants(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    adaptive = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 10
    )
    return {
        "gray": gray,
        "inverted": cv2.bitwise_not(gray),
        "adaptive": adaptive,
    }


def run_ocr(img, psm):
    data = pytesseract.image_to_data(
        img, config=f"--psm {psm}", output_type=pytesseract.Output.DICT
    )
    words, confs = [], []
    for word, conf in zip(data["text"], data["conf"]):
        if word.strip() and float(conf) >= 40:
            words.append(word)
            confs.append(float(conf))
    score = sum(confs)  # more good words = higher score
    return words, confs, score


def extract_text_from_image(image):
    best = ([], [], 0)
    for name, img in variants(image).items():
        for psm in (11, 12, 6):
            result = run_ocr(img, psm)
            if result[2] > best[2]:
                best = result

    words, confs, _ = best
    avg_conf = sum(confs) / len(confs) if confs else 0
    return {
        "source": "ocr",
        "text": " ".join(words),
        "confidence": round(avg_conf, 1),
    }


def extract_text(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")
    return extract_text_from_image(image)


if __name__ == "__main__":
    print(extract_text("samples/poster1.jpg"))