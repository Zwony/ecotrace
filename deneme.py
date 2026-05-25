import time
# core.py'a hiç bulaşmadan, doğrudan kendi yazdığın ml.py dosyasından çağırıyoruz!
from ecotrace.ml import ecotrace_ml 

@ecotrace_ml(model_name="ai_model")
def model_egitim_simulasyonu():
    print("\n[SİMÜLASYON] Yapay zeka modeli eğitiliyor...")
    for i in range(1, 5):
        print(f"Epoch {i}/5 çalışıyor... Arka planda donanım dinleniyor.")
        time.sleep(1)

if __name__ == "__main__":
    model_egitim_simulasyonu()