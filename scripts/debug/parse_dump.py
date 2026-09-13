import xml.etree.ElementTree as ET

tree = ET.parse('/tmp/window_dump2.xml')
print(f'{"Text":<20} | {"Content-Desc":<20} | {"Resource-ID":<40} | {"Bounds":<20}')
print("-" * 110)
for node in tree.iter():
    if node.get('clickable') == 'true':
        text = str(node.get("text"))[:20] if node.get("text") else ""
        desc = str(node.get("content-desc"))[:20] if node.get("content-desc") else ""
        rid = str(node.get("resource-id"))
        bounds = str(node.get("bounds"))
        print(f'{text:<20} | {desc:<20} | {rid:<40} | {bounds:<20}')
