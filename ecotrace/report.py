import os
import csv
import tempfile
from fpdf import FPDF
import matplotlib.pyplot as plt
import google.generativeai as genai
from .logger import logger
from .exceptions import ReportGenerationError

def sanitize_for_pdf(text):
    """Strips non-ASCII characters for safe PDF rendering.

    Args:
        text (str): Input string potentially containing non-ASCII characters.

    Returns:
        str: ASCII-safe string formatted for FPDF encoding restrictions.
    """
    return "".join(c for c in str(text) if ord(c) < 128)

def create_cpu_usage_chart(samples_data, core_count=1):
    """Renders a CPU usage line chart and saves it to a temporary PNG file.

    Generates a visual representation of CPU utilization normalized against the total
    available logical cores to prevent inflation on heavily multi-threaded systems.

    Args:
        samples_data (list): List of ``(timestamp, cpu_percent)`` float tuples.
        core_count (int): Number of logical processor cores for scaling reference.

    Returns:
        str or None: Absolute path to the generated PNG file, or None on failure.
    """
    if not samples_data:
        return None

    try:
        timestamps = [t for t, _ in samples_data]
        cpu_values = [min(s, 100.0) for _, s in samples_data]
        relative_times = [(t - timestamps[0]) for t in timestamps]

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(relative_times, cpu_values, linewidth=2, color='#2E8B57')
        ax.fill_between(relative_times, cpu_values, alpha=0.3, color='#2E8B57')
        ax.set_xlabel('Time (seconds)', fontsize=10)
        ax.set_ylabel('Normalized CPU Usage (%)', fontsize=10)
        ax.set_title('CPU Usage Over Time (Core-Normalized)', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 110)
        plt.tight_layout()

        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return temp_file.name

    except Exception as e:
        logger.error(f"CPU Chart generation failed: {e}")
        return None

def create_gpu_usage_chart(samples_data):
    """Renders a GPU utilization line chart and saves it as a temporary PNG.

    Args:
        samples_data (list): List of ``(timestamp, gpu_percent)`` float tuples.

    Returns:
        str or None: Path to PNG or None on failure.
    """
    if not samples_data:
        return None

    try:
        timestamps = [t for t, _ in samples_data]
        gpu_values = [min(s, 100.0) for _, s in samples_data]
        relative_times = [(t - timestamps[0]) for t in timestamps]

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(relative_times, gpu_values, linewidth=2, color='#4682B4')  # SteelBlue for GPU
        ax.fill_between(relative_times, gpu_values, alpha=0.3, color='#4682B4')
        ax.set_xlabel('Time (seconds)', fontsize=10)
        ax.set_ylabel('GPU Utilization (%)', fontsize=10)
        ax.set_title('GPU Utilization Over Time', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 110)
        plt.tight_layout()

        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        plt.savefig(temp_file.name, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return temp_file.name

    except Exception as e:
        logger.error(f"GPU Chart generation failed: {e}")
        return None

def get_gemini_insights(api_key, cpu_info, gpu_info, history, region_code):
    """Fetches dynamic carbon-optimization insights from Google Gemini.

    Constructs a detailed prompt containing hardware specs, regional grid intensity,
    and recent execution history to generate actionable 'Green Coding' advice.

    Args:
        api_key (str): Google Gemini API key.
        cpu_info (dict): CPU hardware specs.
        gpu_info (dict): GPU hardware specs (optional).
        history (list): Recent measurements from CSV.
        region_code (str): ISO region for grid intensity context.

    Returns:
        str: AI-generated insights or an error message if the call fails.
    """
    if not api_key:
        return None

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        # Limit history to last 5 entries for prompt efficiency
        recent_history = history[-5:]
        history_summary = ""
        for row in recent_history:
            history_summary += f"- {row[1]}: {row[2]}s, {row[3]}gCO2, {row[5]}% CPU\n"

        gpu_desc = f"GPU: {gpu_info.get('brand')} ({gpu_info.get('tdp')}W)" if gpu_info else "No GPU"

        prompt = f"""
        You are 'EcoTrace AI', a green computing expert. Analyze this Python execution data and provide 3-4 concise, 
        highly technical 'Eco-Insights' for the developer to reduce their carbon footprint.
        
        SYSTEM INFO:
        - CPU: {cpu_info.get('brand')} ({cpu_info.get('cores')} cores, {cpu_info.get('tdp')}W TDP)
        - {gpu_desc}
        - Region: {region_code}
        
        RECENT PERFORMANCE HISTORY:
        {history_summary}
        
        REQUIREMENTS:
        - Focus on energy efficiency and carbon reduction.
        - Be specific to the hardware if relevant.
        - Suggest Pythonic optimizations (e.g., vectorized operations, async, library swaps).
        - Keep insights under 60 words each.
        - Response should be in the same language as the function names if possible, but default to English if unsure.
        """

        response = model.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        return f"Gemini Insights unavailable: {str(e)}"

def generate_pdf_report(
    filename="ecotrace_full_report.pdf", 
    cpu_info=None, 
    gpu_info=None, 
    region_code="TR", 
    comparison=None, 
    cpu_samples=None,
    gpu_samples=None,
    api_key=None
):
    """Generates a comprehensive PDF audit report covering energy footprint data.

    Aggregates hardware profile insights, execution CSV history, AI-assisted performance
    diagnostics, CPU usage charts, and comparison statistics into a standalone PDF.

    Args:
        filename (str): Desired output trajectory path for the PDF document.
        cpu_info (dict): Hardware definitions dictionary detailing cores, brand, and TDP.
        gpu_info (dict): Hardware definitions dictionary detailing GPU statistics.
        region_code (str): Carbon regional intensity modifier identifier.
        comparison (dict): Context mappings when processing paired run analyses.
        cpu_samples (list): Captured process thread state samples for visualization rendering.
        gpu_samples (list): Captured GPU utilization samples for visualization rendering.
        api_key (str): Optional Google Gemini API key.

    Returns:
        None: Operations output side-effects to the disk format system, with CLI feedbacks.
    """
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
                    if len(row) >= 6:
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

        # CPU Chart Section
        if cpu_samples:
            core_count = cpu_info.get("cores", 1)
            normalized_samples = [(t, min(s / core_count, 100.0)) for t, s in cpu_samples]
            chart_path = create_cpu_usage_chart(normalized_samples, core_count)
            if chart_path:
                pdf.add_page()
                pdf.set_font("helvetica", 'B', 12)
                pdf.cell(0, 10, txt=" CPU Usage Over Time (Core-Normalized)", ln=True, fill=True)
                pdf.ln(5)
                pdf.image(chart_path, x=10, y=50, w=190)
                pdf.ln(120)

                normalized_values = [s for _, s in normalized_samples]
                avg_cpu = sum(normalized_values) / len(normalized_values) if normalized_values else 0.0
                max_cpu = max(normalized_values) if normalized_values else 0.0
                min_cpu = min(normalized_values) if normalized_values else 0.0

                pdf.set_font("helvetica", size=9)
                pdf.cell(0, 8, txt=f"Average CPU: {avg_cpu:.1f}% | Peak: {max_cpu:.1f}% | Min: {min_cpu:.1f}%", ln=True)
                if os.path.exists(chart_path): os.unlink(chart_path)

        # GPU Chart Section
        if gpu_samples:
            gpu_chart_path = create_gpu_usage_chart(gpu_samples)
            if gpu_chart_path:
                pdf.add_page()
                pdf.set_font("helvetica", 'B', 12)
                pdf.cell(0, 10, txt=" GPU Utilization Over Time", ln=True, fill=True)
                pdf.ln(5)
                pdf.image(gpu_chart_path, x=10, y=50, w=190)
                pdf.ln(120)

                gpu_values = [s for _, s in gpu_samples]
                avg_gpu = sum(gpu_values) / len(gpu_values) if gpu_values else 0.0
                peak_gpu = max(gpu_values) if gpu_values else 0.0
                
                pdf.set_font("helvetica", size=9)
                pdf.cell(0, 8, txt=f"Average GPU Usage: {avg_gpu:.1f}% | Peak Usage: {peak_gpu:.1f}%", ln=True)
                if os.path.exists(gpu_chart_path): os.unlink(gpu_chart_path)

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
            
            # Logic: Scale thresholds by core count for accurate reporting
            core_count = cpu_info.get("cores", 1)
            single_core_threshold = 100.0 / core_count
            
            for row in history[-5:]:
                try:
                    func_name = row[1][:15] + "..." if len(row[1]) > 15 else row[1]
                    duration = float(row[2])
                    avg_cpu = float(row[5])
                    
                    # --- Balanced Insight Engine ---
                    recommendation = "Optimal"
                    
                    # 1. Critical Duration (Time is the biggest carbon factor)
                    if duration > 10.0:
                        recommendation = "Check I/O bottlenecks"
                    elif duration > 3.0:
                        recommendation = "Try async implementation"
                    
                    # 2. Strategic CPU Utilization
                    elif avg_cpu > 50.0:
                        recommendation = "High Multi-Core Load"
                    elif avg_cpu > 25.0:
                        recommendation = "High CPU: Optimize loops"
                    elif (single_core_threshold * 0.7) <= avg_cpu <= (single_core_threshold * 1.3):
                        # Task is hitting 1 full core (common in Python due to GIL)
                        recommendation = "Single-Thread Intensive"
                    elif avg_cpu < 1.0:
                        recommendation = "Low CPU: Try batching"
                    
                    pdf.cell(60, 8, func_name, border=1)
                    pdf.cell(40, 8, f"{avg_cpu:.1f}%", border=1)
                    pdf.cell(40, 8, f"{duration:.2f}s", border=1)
                    pdf.cell(50, 8, recommendation, border=1, ln=True)
                except Exception as e:
                    logger.debug(f"Row {row} formatting skipped: {e}")
                    continue

        if api_key and history:
            ai_text = get_gemini_insights(api_key, cpu_info, gpu_info, history, region_code)
            if ai_text:
                pdf.add_page()
                pdf.set_font("helvetica", 'B', 16)
                pdf.set_text_color(46, 139, 87)
                pdf.cell(0, 15, txt="EcoTrace AI Insights (Beta)", ln=True, align='C')
                pdf.ln(5)
                pdf.set_fill_color(240, 255, 240)
                pdf.set_font("helvetica", 'I', 10)
                pdf.set_text_color(40, 40, 40)
                clean_ai_text = ai_text.replace("**", "").replace("*", "").replace("`", "")
                pdf.multi_cell(0, 8, txt=sanitize_for_pdf(clean_ai_text), border=1, fill=True)

        pdf.output(filename)
        logger.info(f"Report saved: {filename}")

    except Exception as e:
        logger.error(f"PDF Error during generation and saving: {str(e)}")
        raise ReportGenerationError(f"Failed to generate PDF: {str(e)}") from e
