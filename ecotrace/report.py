import os
import csv
import tempfile
from fpdf import FPDF
import matplotlib.pyplot as plt

def sanitize_for_pdf(text):
    """Strips non-ASCII characters for safe PDF rendering."""
    return "".join(c for c in str(text) if ord(c) < 128)

def create_cpu_usage_chart(samples_data, core_count=1):
    """Renders a CPU usage line chart and saves it to a temporary PNG file."""
    if not samples_data:
        return None

    try:
        timestamps = [t for t, _ in samples_data]
        cpu_values = [min(s, 100.0) for _, s in samples_data]  # Raw values with 100% cap
        relative_times = [(t - timestamps[0]) for t in timestamps]

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(relative_times, cpu_values, linewidth=2, color='#2E8B57')
        ax.fill_between(relative_times, cpu_values, alpha=0.3, color='#2E8B57')
        ax.set_xlabel('Time (seconds)', fontsize=10)
        ax.set_ylabel('Normalized CPU Usage (%)', fontsize=10)
        ax.set_title('CPU Usage Over Time (Core-Normalized)', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 110)  # Allow 10% headroom for spikes
        plt.tight_layout()

        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return temp_file.name

    except Exception as e:
        print(f"[EcoTrace] Chart generation failed: {e}")
        return None

def generate_pdf_report(
    filename="ecotrace_full_report.pdf", 
    cpu_info=None, 
    gpu_info=None, 
    region_code="TR", 
    comparison=None, 
    cpu_samples=None
):
    """Generates a comprehensive PDF audit report."""
    if cpu_info is None:
        cpu_info = {"brand": "Unknown", "cores": 1, "tdp": 65.0}
        
    try:
        history = []
        log_file = "ecotrace_log.csv"
        if os.path.exists(log_file):
            with open(log_file, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    if len(row) >= 5:
                        history.append(row)

        pdf = FPDF()
        pdf.add_page()

        pdf.set_font("helvetica", 'B', 20)
        pdf.set_text_color(46, 139, 87)
        pdf.cell(200, 15, txt="EcoTrace Analysis Report", ln=True, align='C')
        pdf.ln(5)

        pdf.set_fill_color(245, 245, 245)
        pdf.set_font("helvetica", 'B', 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, txt=" System Information", ln=True, fill=True)
        pdf.set_font("helvetica", size=10)
        cpu_display = sanitize_for_pdf(cpu_info.get('brand', 'Unknown'))
        pdf.cell(100, 8, txt=f"CPU: {cpu_display}", ln=False)
        pdf.cell(100, 8, txt=f"Cores: {cpu_info.get('cores', 1)}", ln=True)
        pdf.cell(100, 8, txt=f"TDP: {cpu_info.get('tdp', 65.0)}W", ln=False)
        pdf.cell(100, 8, txt=f"Region: {region_code}", ln=True)
        if gpu_info:
            gpu_display = sanitize_for_pdf(gpu_info.get('brand', 'Unknown'))
            pdf.cell(100, 8, txt=f"GPU: {gpu_display}", ln=False)
            pdf.cell(100, 8, txt=f"GPU TDP: {gpu_info.get('tdp', 0)}W", ln=True)
        pdf.ln(10)

        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 10, txt=" Function History", ln=True, fill=True)
        pdf.ln(2)
        pdf.set_font("helvetica", 'B', 9)
        pdf.set_fill_color(200, 220, 200)
        pdf.cell(40, 10, "Date", border=1, fill=True)
        pdf.cell(50, 10, "Function", border=1, fill=True)
        pdf.cell(25, 10, "Duration(s)", border=1, fill=True)
        pdf.cell(45, 10, "Carbon(gCO2)", border=1, fill=True)
        pdf.cell(30, 10, "Region", border=1, fill=True, ln=True)

        pdf.set_font("helvetica", size=8)
        total_sum = 0.0
        for row in history:
            safe_func_name = sanitize_for_pdf(row[1])
            pdf.cell(40, 8, str(row[0]), border=1)
            pdf.cell(50, 8, safe_func_name, border=1)
            pdf.cell(25, 8, str(row[2]), border=1)
            pdf.cell(45, 8, str(row[3]), border=1)
            pdf.cell(30, 8, str(row[4]), border=1, ln=True)
            try:
                total_sum += float(row[3])
            except ValueError:
                pass

        chart_image_path = None
        try:
            if cpu_samples:
                # Note: synchronization (locking) should be done by the caller before passing cpu_samples
                samples_list = cpu_samples

                if samples_list:
                    core_count = cpu_info.get("cores", 1)
                    normalized_samples = [
                        (t, min(s / core_count, 100.0)) 
                        for t, s in samples_list
                    ]
                    chart_image_path = create_cpu_usage_chart(normalized_samples, core_count)

                    if chart_image_path:
                        pdf.add_page()
                        pdf.set_font("helvetica", 'B', 12)
                        pdf.cell(0, 10, txt=" CPU Usage Over Time (Core-Normalized)", ln=True, fill=True)
                        pdf.ln(5)
                        pdf.image(chart_image_path, x=10, y=50, w=190)
                        pdf.ln(120)

                        normalized_values = [s for _, s in normalized_samples]
                        avg_cpu = sum(normalized_values) / len(normalized_values)
                        max_cpu = max(normalized_values)
                        min_cpu = min(normalized_values)

                        pdf.set_font("helvetica", size=9)
                        pdf.cell(0, 8, txt=f"Average CPU: {avg_cpu:.1f}% | Peak: {max_cpu:.1f}% | Min: {min_cpu:.1f}%", ln=True)

        except Exception as e:
            print(f"[EcoTrace] Chart section error: {e}")

        pdf.ln(10)
        pdf.set_font("helvetica", 'B', 14)
        pdf.set_fill_color(46, 139, 87)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 15, txt=f"TOTAL CUMULATIVE EMISSIONS: {total_sum:.8f} gCO2", border=1, fill=True, align='C', ln=True)

        if comparison is not None:
            r1 = comparison.get("func1", {})
            r2 = comparison.get("func2", {})
            pdf.ln(10)
            pdf.set_font("helvetica", 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, txt="Comparison Analysis", ln=True, fill=True)
            pdf.set_font("helvetica", 'B', 9)
            pdf.set_fill_color(200, 220, 200)
            pdf.cell(50, 10, "Function",     border=1, fill=True)
            pdf.cell(35, 10, "Duration(s)",  border=1, fill=True)
            pdf.cell(35, 10, "Avg CPU(%)",   border=1, fill=True)
            pdf.cell(50, 10, "Carbon(gCO2)", border=1, fill=True, ln=True)
            pdf.set_font("helvetica", size=9)
            pdf.cell(50, 8, r1.get("func_name", ""), border=1)
            pdf.cell(35, 8, f"{r1.get('duration', 0):.4f}", border=1)
            pdf.cell(35, 8, f"{r1.get('avg_cpu', 0):.1f}", border=1)
            pdf.cell(50, 8, f"{r1.get('carbon', 0):.8f}", border=1, ln=True)
            pdf.cell(50, 8, r2.get("func_name", ""), border=1)
            pdf.cell(35, 8, f"{r2.get('duration', 0):.4f}", border=1)
            pdf.cell(35, 8, f"{r2.get('avg_cpu', 0):.1f}", border=1)
            pdf.cell(50, 8, f"{r2.get('carbon', 0):.8f}", border=1, ln=True)

        # Performance Insights Section
        if history:
            pdf.ln(15)
            pdf.set_font("helvetica", 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, txt="Performance Insights", ln=True, fill=True)
            pdf.set_font("helvetica", 'B', 9)
            pdf.set_fill_color(240, 240, 200)
            pdf.cell(60, 10, "Function", border=1, fill=True)
            pdf.cell(40, 10, "Avg CPU", border=1, fill=True)
            pdf.cell(40, 10, "Duration", border=1, fill=True)
            pdf.cell(50, 10, "Recommendation", border=1, fill=True, ln=True)
            pdf.set_font("helvetica", size=8)
            
            for row in history[-5:]:  # Last 5 functions
                try:
                    if len(row) < 6:
                        continue
                        
                    func_name = row[1][:15] + "..." if len(row[1]) > 15 else row[1]
                    duration = float(row[2])
                    carbon = float(row[3])  
                    avg_cpu = float(row[5])
                    
                    insights = []
                    if duration > 5.0:
                        insights.append("Long execution: Check I/O bottlenecks")
                    elif duration > 2.0:
                        insights.append("Consider async implementation")
                    
                    if avg_cpu > 70:
                        insights.append("High CPU: Optimize loops")
                    elif avg_cpu < 20:
                        insights.append("Low CPU: Consider batching")
                    
                    if not insights:
                        insights.append("Performance looks optimal")
                    
                    pdf.cell(60, 8, func_name, border=1)
                    pdf.cell(40, 8, f"{avg_cpu:.1f}%", border=1)
                    pdf.cell(40, 8, f"{duration:.2f}s", border=1)
                    pdf.cell(50, 8, insights[0][:20] + "..." if len(insights[0]) > 20 else insights[0], border=1, ln=True)
                    
                except (IndexError, ValueError) as e:
                    continue

        pdf.output(filename)
        print(f"\n[EcoTrace] Report saved: {filename}")

        if chart_image_path and os.path.exists(chart_image_path):
            try:
                os.unlink(chart_image_path)
            except Exception:
                pass

    except Exception as e:
        print(f"\n[EcoTrace] PDF Error: {e}")
