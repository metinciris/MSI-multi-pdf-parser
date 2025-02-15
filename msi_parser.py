import tkinter as tk
from tkinter import filedialog, ttk
import pdfplumber
import re

def extract_msi_summary(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    
    # Örnek adı
    sample_name = "Unknown"
    for line in text.split("\n"):
        if "Sample name" in line:
            sample_name = line.split("Sample name")[-1].strip().split("(")[0]
            sample_name = sample_name.split("_")[0]
            break
    
    # MSI durumu tespiti
    msi_status = "Not Found"
    msi_emoji = "⚪"
    
    msi_match = re.findall(r"MSI status[:\s]*(\S+)", text, re.IGNORECASE)
    clinical_match = re.findall(r"Clinical term[:\s]*(\S+)", text, re.IGNORECASE)
    
    if msi_match:
        msi_value = msi_match[0].upper()
        clinical_value = clinical_match[0].upper() if clinical_match else ""
        
        if "MSI-H" in msi_value or "HIGH" in clinical_value:
            msi_status = "MSI-H (MSI-High)"
            msi_emoji = "🔴"
        elif "MSI-L" in msi_value or "LOW" in clinical_value:
            msi_status = "MSI-L (MSI-Low)"
            msi_emoji = "🟡"
        elif "MSS" in msi_value or "STABLE" in clinical_value:
            msi_status = "MSS (MS-Stable)"
            msi_emoji = "🟢"

    # Locus listesi
    loci_names = [
        "BAT40(T)37", "MONO-27(T)27", "BAT26(A)27", "NR24(T)23",
        "BAT25(T)25", "NR22(T)21", "HSP110-T17(T)17", "NR21(A)21",
        "BAT34C4(A)18"
    ]
    
    # Önce yeni format için dene
    loci_results = []
    stability_found = False
    
    # Yeni format kontrolü
    if "Locus Stability threshold Stability" in text:
        stability_section = False
        for line in text.split("\n"):
            if "Locus Stability threshold Stability" in line:
                stability_section = True
                continue
            if stability_section and line.strip():
                parts = line.split()
                if len(parts) >= 3:
                    locus = parts[0]
                    stability = parts[-1]
                    if stability in ["Stable", "Unstable"]:
                        emoji = "✅" if stability == "Stable" else "⚠️"
                        loci_results.append(f"{emoji} {locus} - {stability}")
                        stability_found = True
    
    # Eğer yeni format bulunamadıysa eski formatı dene
    if not stability_found:
        stability_values = []
        stability_section = False
        
        for line in text.split("\n"):
            if "Stability threshold Stability" in line:
                stability_section = True
                continue
            if stability_section:
                parts = line.split()
                if len(parts) == 2 and parts[1] in ["Stable", "Unstable"]:
                    stability_values.append(parts[1])
                if len(stability_values) == 9:
                    break
        
        if len(stability_values) == 9:
            loci_results = [
                f"{'✅' if stability == 'Stable' else '⚠️'} {locus} - {stability}"
                for locus, stability in zip(loci_names, stability_values)
            ]
        else:
            loci_results = [f"❓ {locus} - Belirsiz" for locus in loci_names]
    
    # Çıktıyı oluştur
    output_text = f"📌 {sample_name}\nMSI status: {msi_status} {msi_emoji}\n" + "\n".join(loci_results)
    return output_text

def select_pdfs():
    file_paths = filedialog.askopenfilenames(filetypes=[("PDF Files", "*.pdf")])
    results = []
    progress_bar["maximum"] = len(file_paths)
    progress_bar["value"] = 0
    
    for i, file in enumerate(file_paths):
        result = extract_msi_summary(file)
        results.append(result)
        progress_bar["value"] = i + 1
        root.update_idletasks()
    
    text_output.delete("1.0", tk.END)
    text_output.insert(tk.END, "\n\n".join(results))

def copy_to_clipboard():
    root.clipboard_clear()
    root.clipboard_append(text_output.get("1.0", tk.END))
    root.update()
    copy_label.config(text="✅ Kopyalandı!")

# GUI oluştur
root = tk.Tk()
root.title("MSI PDF Parser (Birleştirilmiş Versiyon)")
root.geometry("1000x700")

btn_select = tk.Button(root, text="📂 PDF Seç", command=select_pdfs, font=("Arial", 14))
btn_select.pack(pady=10)

progress_bar = ttk.Progressbar(root, length=700, mode="determinate")
progress_bar.pack(pady=5)

frame = tk.Frame(root)
frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

text_output = tk.Text(frame, font=("Arial", 14), wrap=tk.WORD, height=20, width=70)
scrollbar = tk.Scrollbar(frame, command=text_output.yview)
text_output.config(yscrollcommand=scrollbar.set)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
text_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

btn_copy = tk.Button(root, text="📋 Kopyala", command=copy_to_clipboard, font=("Arial", 14))
btn_copy.pack(pady=5)

copy_label = tk.Label(root, text="", font=("Arial", 12), fg="green")
copy_label.pack()

root.mainloop()
