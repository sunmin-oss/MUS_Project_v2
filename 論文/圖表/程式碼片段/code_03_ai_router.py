# 程式碼片段 3：多層 AI Provider 路由與熔斷器 (services/ai/recognizer_router.py)
# 用途：論文 3.5 節 — 多層 AI Provider 智慧路由

class RecognizerRouter:
    """多層 Vision Recognizer 統一介面"""

    def __init__(self, primary, fallback=None, settings=None, secondary=None):
        self._lock = threading.Lock()
        self._fail_count = 0
        self._breaker_open_until = 0.0

        # 依優先順序組裝 chain: primary → secondary → fallback
        chain = []
        if primary:   chain.append(("primary", primary, _provider_brand(primary)))
        if secondary:  chain.append(("secondary", secondary, _provider_brand(secondary)))
        if fallback:   chain.append(("openai_fallback", fallback, "openai"))
        self._chain = chain

    def _is_breaker_open(self):
        """檢查熔斷器是否開啟"""
        return time.time() < self._breaker_open_until

    def _open_breaker(self):
        """開啟熔斷器，冷卻期內直接走 fallback"""
        cd = int(getattr(self.settings, "AI_FALLBACK_COOLDOWN_SEC", 300))
        self._breaker_open_until = time.time() + cd

    def _record_failure(self, slot_name):
        """記錄失敗，連續失敗達門檻則觸發熔斷"""
        with self._lock:
            if slot_name in ("primary", "secondary"):
                self._fail_count += 1
                threshold = int(getattr(self.settings, "AI_FALLBACK_FAIL_THRESHOLD", 3))
                if self._fail_count >= threshold:
                    self._open_breaker()

    def _candidates(self, method):
        """回傳支援該 method 的 chain；熔斷時跳過前段"""
        supported = [s for s in self._chain if self._has_method(s[1], method)]
        if self._is_breaker_open() and len(supported) > 1:
            return supported[-1:]  # 只走最末層 fallback
        return supported

    def _call(self, method, *args, **kwargs):
        """依序嘗試 chain 中的 provider"""
        candidates = self._candidates(method)
        for idx, (name, target, brand) in enumerate(candidates):
            try:
                result = self._invoke(target, name, brand, method, *args, **kwargs)
                self._record_success(name)
                return result
            except Exception as e:
                self._record_failure(name)
                if idx == len(candidates) - 1:
                    raise
