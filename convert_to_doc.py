import sys
import subprocess
import os

def install_and_convert():
    try:
        import pypandoc
    except ImportError:
        print("Installing pypandoc...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pypandoc", "markdown"])
        import pypandoc

    try:
        # Download pandoc if not installed
        pypandoc.download_pandoc()
    except Exception as e:
        print(f"Pandoc setup note: {e}")

    input_md = r"c:\Users\ubee2\.gemini\antigravity\brain\54a231eb-f46a-4c8f-8afc-0e6b46eba387\cable_integration_guide.md"
    output_docx = r"c:\Users\ubee2\Downloads\DAE_P1_19Modules-feature-refactor-simulation-m17\DAE_P1_19Modules-feature-refactor-simulation-m17\Cable_Integration_Guide.docx"

    print(f"Converting {input_md} to {output_docx}...")
    try:
        pypandoc.convert_file(input_md, 'docx', outputfile=output_docx)
        print("Successfully generated Cable_Integration_Guide.docx")
    except Exception as e:
        print(f"Conversion failed: {e}")
        
        # Fallback to simple HTML->DOC if pandoc fails
        print("Attempting fallback HTML conversion...")
        try:
            import markdown
            with open(input_md, 'r', encoding='utf-8') as f:
                md_text = f.read()
            html = markdown.markdown(md_text, extensions=['tables'])
            
            fallback_doc = r"c:\Users\ubee2\Downloads\DAE_P1_19Modules-feature-refactor-simulation-m17\DAE_P1_19Modules-feature-refactor-simulation-m17\Cable_Integration_Guide.doc"
            with open(fallback_doc, 'w', encoding='utf-8') as f:
                f.write('<html><head><meta charset="utf-8"></head><body>')
                f.write(html)
                f.write('</body></html>')
            print("Successfully generated Cable_Integration_Guide.doc via fallback method.")
        except Exception as fallback_e:
            print(f"Fallback also failed: {fallback_e}")

if __name__ == "__main__":
    install_and_convert()
