import xml.etree.ElementTree as ET

# String XML
xml_string = """
<students>
    <student id="1">
        <name>Alice</name>
        <age>20</age>
        <major>Computer Science</major>
    </student>
    <student id="2">
        <name>Bob</name>
        <age>21</age>
        <major>Mathematics</major>
    </student>
</students>
"""

# Parsing string XML
root = ET.fromstring(xml_string)

# Menampilkan elemen-elemen dari root element
for child in root:
    print('Tag:', child.tag, 'Atribut:', child.attrib)

    # Menampilkan isi dari elemen
    for grandchild in child:
        print('Tag:', grandchild.tag, 'Isi:', grandchild.text)
