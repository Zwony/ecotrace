import asyncio
import inspect
from ecotrace import EcoTrace

eco = EcoTrace(region_code="TR", carbon_limit=0.0001)

@eco.track
async def async_test():
    print("Asenkron fonksiyon basliyor")
    await asyncio.sleep(1)
    print("Asenkron fonksiyon tamamlandi")

@eco.track
def versiyon_1():
    sum(i*i for i in range(10**6))

@eco.track
def versiyon_2():
    total = 0
    for i in range(10**6):
        total += i*i

@eco.track_gpu
def gpu_test():
    print("GPU testi yapiliyor...")
    sum(i*i for i in range(10**6))
    print("GPU testi tamamlandi.")
    
if __name__ == "__main__":
    sonuc = eco.compare(versiyon_1, versiyon_2)
    eco.generate_pdf_report("karsilastirma_raporu.pdf", comparison=sonuc)
    
    print(inspect.iscoroutinefunction(async_test))
    asyncio.run(async_test())
    gpu_test()