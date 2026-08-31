from bs4 import BeautifulSoup

class HTMLParser:

    def __init__(self):
        pass

    
    def get_html_tags(self, html_content):

        soup = BeautifulSoup(html_content, 'html.parser')

        th_tags = soup.find_all('th')
        td_tags = soup.find_all('td')

        return th_tags+td_tags
    

    def get_css_properties(self, tag):

        css_properties = tag["style"].split(";")
        css_styles = {}
        for css_property in css_properties:
            if ":" in css_property:
                key, value = css_property.split(":", 1)
                css_styles[key.strip()] = value.strip()

        return css_styles