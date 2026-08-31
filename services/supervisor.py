from config import *
from services.html_parser import HTMLParser

class Supervisor:

    def __init__(self):
        self.picture_schema = PICTURE_SCHEMA
        self.table_schema = TABLE_SCHEMA
        self.overall_schema = OVERALL_SCHEMA
        self.categories = CATEGORIES
        self.font_sizes = FONT_SIZES
        self.font_styles = FONT_STYLES
        self.alignments = ALIGNMENTS
        self.css_styles = CSS_STYLES

        self.html_parser = HTMLParser()

    
    def validate_schema(self, entry: dict):

        if "category" not in entry.keys():
            return False
        
        schema = None
        if entry["category"] == "Picture":
            schema = self.picture_schema
        elif entry["category"] == "Table":
            schema = self.table_schema
        else:
            schema = self.overall_schema

        available_schema = set(entry.keys())
        required_schema = set(schema)
        extra_schema = available_schema.symmetric_difference(required_schema)

        if len(extra_schema) == 0:
            return True
        else:
            return False
        

    def validate_bbox(self, bbox: list):

        pos_coord = [int(coord)>0 for coord in bbox]
        if False in pos_coord:
            return False
        
        if bbox[0]>bbox[2] or bbox[1]>bbox[3]:
            return False
        
        return True
    

    def validate_category(self, category: str):

        return category in self.categories
    

    def validate_font_size(self, entry: dict):

        if entry["category"] in ["Picture", "Table"]:
            return True

        return self.font_sizes[entry["category"]] == entry["font_size"]
    

    def validate_font_style(self, font_style: list):

        for style in font_style:
            if style not in self.font_styles:
                return False
            
        return True
    

    def validate_alignment(self, alignment: str):

        return alignment in self.alignments
    

    def validate_css_properties(self, css_style: dict):

        expected_properties = list(self.css_styles.keys())
        available_properties = list(css_style.keys())

        if not sorted(expected_properties) == sorted(available_properties):
            expected_properties = set(expected_properties)
            available_properties = set(available_properties)
            missing_properties = expected_properties.difference(available_properties)
            extra_properties = available_properties.difference(expected_properties)
            return list(missing_properties), list(extra_properties)
        
        return [],[]
    

    def validate_css_style(self, css_style):

        for key, val in self.css_styles.items():
            if css_style[key] not in val:
                return False

        return True
    

    def validate_table_style(self, table_content):

        tags = self.html_parser.get_html_tags(table_content)

        errors = []
        for tag in tags:
            css_style = self.html_parser.get_css_properties(tag)

            missing_properties, extra_properties = self.validate_css_properties(css_style=css_style)
            if len(missing_properties)>0: errors.append(f"Missing CSS properties: {missing_properties}")
            if len(extra_properties)>0: errors.append(f"Extra CSS properties: {extra_properties}")

        return errors