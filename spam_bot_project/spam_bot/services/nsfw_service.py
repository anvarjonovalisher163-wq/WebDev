from loguru import logger

# To'liq ochiq (yalang'och) holatlar — yuqori ishonch darajasida bloklanadi.
# Juda past chegara oddiy, beg'ubor rasmlarni ham xato bloklashiga olib
# keladi (soya, teri rangi, kiyim tekstsurasi kabi narsalarni "aniqlash"
# xatolari NudeNet'da tez-tez uchraydi), shuning uchun bu yerda ishonchli
# darajada saqlanadi.
_EXPLICIT_LABELS = {
    "FEMALE_GENITALIA_EXPOSED",
    "MALE_GENITALIA_EXPOSED",
    "FEMALE_BREAST_EXPOSED",
    "BUTTOCKS_EXPOSED",
    "ANUS_EXPOSED",
}
_EXPLICIT_THRESHOLD = 0.6

# Yopiq, lekin intim hudud (dumba/ko'krak/jinsiy a'zo) ta'kidlangan,
# provokatsion rasmlar — juda yuqori ishonch talab qilinadi, chunki bu
# toifalar tabiatan shovqinliroq (xato ijobiy natija ehtimoli yuqoriroq).
_SUGGESTIVE_LABELS = {
    "FEMALE_GENITALIA_COVERED",
    "BUTTOCKS_COVERED",
    "FEMALE_BREAST_COVERED",
    "ANUS_COVERED",
}
_SUGGESTIVE_THRESHOLD = 0.85


class NSFWService:
    """Profil rasmlarini mahalliy darajada (bulutsiz) tekshiradi.

    `nudenet` kutubxonasi og'ir (ONNX modeli) bo'lgani uchun ixtiyoriy
    qaramlik hisoblanadi: o'rnatilmagan bo'lsa, xizmat sokin ravishda
    o'chirilgan holatda ishlaydi va bot ishlashda davom etadi.
    """

    def __init__(self) -> None:
        self._detector = None
        self._available = self._try_load()

    def _try_load(self) -> bool:
        try:
            from nudenet import NudeDetector
        except ImportError:
            logger.info("nudenet o'rnatilmagan — NSFW profil rasm skaneri o'chirilgan")
            return False
        try:
            self._detector = NudeDetector()
            return True
        except Exception as exc:  # noqa: BLE001 - model yuklashda turli xato turlari bo'lishi mumkin
            logger.warning(f"NudeNet modelini yuklab bo'lmadi: {exc}")
            return False

    @property
    def available(self) -> bool:
        return self._available

    def is_explicit(self, image_path: str) -> bool:
        if not self._available or self._detector is None:
            return False
        try:
            results = self._detector.detect(image_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"NSFW tekshiruvida xato: {exc}")
            return False
        logger.info(f"NSFW tekshiruvi natijalari: {results}")
        for item in results or []:
            label = item.get("class") or item.get("label")
            score = item.get("score", 0)
            if label in _EXPLICIT_LABELS and score >= _EXPLICIT_THRESHOLD:
                logger.info(f"NSFW aniqlandi: {label} ({score:.2f})")
                return True
            if label in _SUGGESTIVE_LABELS and score >= _SUGGESTIVE_THRESHOLD:
                logger.info(f"NSFW aniqlandi: {label} ({score:.2f})")
                return True
        return False


nsfw_service = NSFWService()
