PICTURE_SCHEMA = [
    "bbox", 
    "category", 
    "page_alignment"
]

TABLE_SCHEMA = [
    "bbox", 
    "category", 
    "text", 
    "page_alignment", 
    "alignment"
]

OVERALL_SCHEMA = [
    "bbox", 
    "category", 
    "text", 
    "font_size", 
    "font_style", 
    "page_alignment", 
    "alignment"
]

CATEGORIES = [
    "Picture",
    "Title",
    "Page-header",
    "Section-header",
    "Text",
    "List-item",
    "Table",
    "Caption",
    "Footnote",
    "Page-footer"
]

FONT_SIZES = {
    "Title": '17',
    "Page-header": '12',
    "Section-header": '12',
    "Text": '11',
    "List-item": '11',
    "Table": '11',
    "Caption": '10',
    "Footnote": '9',
    "Page-footer": '9'
}


FONT_STYLES = [
    "normal",
    "bold",
    "italic",
    "underline"
]

ALIGNMENTS = [
    "left",
    "center",
    "right",
    "justify"
]


CSS_STYLES = {
    "font-size": ["11px"],
    "font-weight": ["normal", "bold"],
    "font-style": ["normal", "italic"],
    "text-decoration": ["none"],
    "text-align": ["left", "right", "center", "justify"]
}