import zipfile, xml.etree.ElementTree as ET
with zipfile.ZipFile(r'C:\Users\ubee2\Downloads\DAE_P1_19Modules-feature-refactor-simulation-m17\DAE_P1_19Modules-feature-refactor-simulation-m17\DOCS\) BREL 程式需要怎麼改pcminpriv.docx') as docx:
    xml_content = docx.read('word/document.xml')
tree = ET.fromstring(xml_content)
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
text = '\n'.join(''.join(node.text for node in p.iterfind('.//w:t', ns) if node.text) for p in tree.iterfind('.//w:p', ns) if ''.join(node.text for node in p.iterfind('.//w:t', ns) if node.text))
with open(r'C:\Users\ubee2\Downloads\DAE_P1_19Modules-feature-refactor-simulation-m17\DAE_P1_19Modules-feature-refactor-simulation-m17\DOCS\temp_output.txt', 'w', encoding='utf-8') as f:
    f.write(text)
