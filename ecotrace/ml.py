import time
import threading
import functools
from ecotrace.gpu import get_gpu_info, get_gpu_power_w

class EcoTraceML:
    """
    Yapay zeka ve makine öğrenimi modelleri için bağımsız enerji ve karbon takip motoru.
    Kullanımı:
    @trace_ml(model_name="My AI Model")
    def train_model(...):
        ...
    Bu sınıf, GPU enerji tüketimini gerçek zamanlı olarak izler ve model eğitimi tamamlandığında toplam enerji tüketimi ve tahmini karbon salınımını raporlar. GPU bilgisi alınamazsa, varsayılan TDP değerleri kullanılarak simülasyon yapılır.
    """
    
    def __init__(self, model_name: str = "AI Model", gpu_index: int = 0, sample_interval: float = 1.0):
        self.model_name = model_name
        self.sample_interval = sample_interval

        self.total_gpu_energy_joules = 0.0
        self.is_running = False
        self._thread = None

        # 1. Ana motoru çakışma yaşamadan, sessiz modda arkada ayağa kaldırıyoruz
        from ecotrace.core import EcoTrace
        self.core_tracker = EcoTrace(quiet=True, check_updates=False)
        
        if self.core_tracker.gpu_info:
            self.gpu_info = self.core_tracker.gpu_info
        else:
            gpu_tdp_defaults = {"intel": 15.0, "amd": 75.0, "unknown": 100.0}
            self.gpu_info = get_gpu_info(gpu_index, gpu_tdp_defaults)

    def _monitor_gpu(self):
        """
        GPU enerji tüketimini izlemek için arka planda çalışan fonksiyon.
            - Her sample_interval saniyede bir GPU gücünü ölçer.
            - Ölçülen güç değeri geçerli değilse, GPU'nun TDP'sinin yarısı kadar bir değer kullanır.
            - Toplam enerji tüketimini joule cinsinden hesaplar (güç * zaman).
            - İzleme durdurulduğunda, toplam enerji tüketimini kWh'ye çevirir ve tahmini karbon salınımını raporlar.
        """
        last_time = time.time()

        while self.is_running:
            time.sleep(self.sample_interval)

            current_time = time.time()
            elapsed = current_time - last_time
            last_time = current_time  # Zamanı hassas şekilde ilerletiyoruz

            current_watt = get_gpu_power_w(self.gpu_info)

            # Emniyet Kemeri (Fallback): Eğer o saniye anlık watt okunamazsa, kart varsa TDP'nin yarısını al
            if current_watt is None:
                if self.gpu_info:
                    current_watt = self.gpu_info.get("tdp", 100.0) * 0.5
                else:
                    current_watt = 45.0  # Tamamen donadımsız ortamda sabit simülasyon değeri

            if current_watt:
                self.total_gpu_energy_joules += current_watt * elapsed

    def __enter__(self):
        if self.gpu_info:
            print(f"Starting energy tracking for {self.model_name} on GPU: {self.gpu_info['brand']} with TDP: {self.gpu_info['tdp']}W")
        else:
            print(f"Starting energy tracking for {self.model_name} with no GPU detected. Using default TDP assumptions.")

        self.is_running = True
        self._thread = threading.Thread(target=self._monitor_gpu, daemon=True)
        self._thread.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.is_running = False
        if self._thread:
            self._thread.join()

        gpu_kwh = self.total_gpu_energy_joules / 3600000.0
        carbon_intensity = getattr(self.core_tracker, "carbon_intensity", 0.475)
        co2_emitted_g = gpu_kwh * carbon_intensity * 1000.0

        print(f"\n--- [{self.model_name}] Yapay Zeka Eğitim Karbon Raporu ---")
        print(f"Harcanan Toplam Enerji : {gpu_kwh:.6f} kWh ({self.total_gpu_energy_joules:.2f} Joule)")
        print(f"Tahmini Karbon Salınımı: {co2_emitted_g:.4f} g CO2")
        print("-----------------------------------------------------------\n")
        return False

def trace_ml(model_name: str = "AI Model"):
    """
    Yapay zeka ve makine öğrenimi modelleri için dekoratör fonksiyonu.
    Kullanımı: @trace_ml(model_name="My AI Model")
    Bu dekoratör, sarılan fonksiyonun çalışması sırasında EcoTraceML izleyicisini otomatik olarak başlatır ve durdurur. Model adı isteğe bağlıdır ve raporlarda kullanılmak üzere sağlanabilir.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with EcoTraceML(model_name=model_name) as tracker:
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator