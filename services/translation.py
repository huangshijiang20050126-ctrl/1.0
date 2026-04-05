from abc import ABC, abstractmethod


class TranslationService(ABC):
    @abstractmethod
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        raise NotImplementedError


class MockTranslationService(TranslationService):
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Mock 翻译：仅做可辨识转换，便于联调。"""
        return f"[{source_lang}->{target_lang}] {text[::-1]}"
