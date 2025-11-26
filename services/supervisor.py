import os
import json
import logging

logging.basicConfig(
    filename="supervision_logs.log",
    filemode="w",
    format="%(asctime)s - %(name)s - %(message)s",
    level=logging.INFO
)


class Supervisor:

    def __init__(self,data_dir):

        self.data_dir = data_dir
        self.font_sizes = {
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


    def validate_objects(self, entry):

        if "category" not in entry.keys():
            return False

        if entry["category"] == "Picture":
            for key in entry.keys():
                if key not in ["bbox", "category", "page_alignment"]:
                    return False
        elif entry["category"] == "Table":
            for key in entry.keys():
                if key not in ["bbox", "category", "text", "page_alignment", "alignment"]:
                    return False   
        else:
            for key in entry.keys():
                if key not in ["bbox", "category", "text", "font_size", "font_style", "page_alignment", "alignment"]:
                    return False
                
        return True
    

    def validate_null_values(self, entry):

        for key in entry.keys():
            if entry[key] in ["", None]:
                return False

        return True
    

    def validate_font_size(self, entry):

        if entry["category"] in ["Picture", "Table"]:
            return True

        return self.font_sizes[entry["category"]] == entry["font_size"]
    

    def validate_values(self, entry):

        if entry["category"]!="Picture" and entry["category"] not in self.font_sizes.keys():
            return False

        if entry["category"] == "Picture":
            if entry["page_alignment"] not in ["left", "center", "right", "justify"]:
                return False
        elif entry["category"] == "Table":
            if entry["page_alignment"] not in ["left", "center", "right", "justify"]:
                return False
            if entry["alignment"] not in ["left", "center", "right", "justify"]:
                return False
        else:
            if entry["page_alignment"] not in ["left", "center", "right", "justify"]:
                return False
            if entry["alignment"] not in ["left", "center", "right", "justify"]:
                return False
            for tmp in entry["font_style"]:
                if tmp not in ["normal", "bold", "italic", "underline"]:
                    return False

        return True
    

    def check_files_availability(self):

        for folder in os.listdir(self.data_dir):
            fnames = os.listdir(os.path.join(self.data_dir, folder))

            has_img = [fname.endswith(".jpg") or fname.endswith(".png") for fname in fnames]
            has_json = [fname.endswith(".json") for fname in fnames]


            if len(fnames)==2 and (True in has_img and True in has_json):
                continue
            else:
                logging.info(f"Required file missing in: {folder}")



    def check_annotation_schema(self, print_details=False):

        for root, _, fnames in os.walk(self.data_dir):
            for fname in fnames:
                if not fname.endswith(".json"):
                    continue

                try:
                    with open(os.path.join(root, fname), "r", encoding="utf-8", errors="replace") as f:
                        annotations = json.load(f)
                except Exception as e:
                    logging.info(f"Error while reading annotation file: {fname}")
                    logging.info(f"Error: {e}")
                    continue 
                
                try:
                    schema_errors = []
                    for entry in annotations:
                        if not self.validate_objects(entry):
                            schema_errors.append(entry)

                    if len(schema_errors)>0:
                        logging.info(f"{len(schema_errors)} entries with schema errors found in: {fname}")
                        if print_details:
                            logging.info("Entries are-")
                            for entry in schema_errors:
                                logging.info(entry)
                except Exception as e:
                    logging.info(f"Unknown error at: {fname}")
                    logging.info(f"Error: {e}")


    def check_annotation_values(self, print_details=False):

        for root, _, fnames in os.walk(self.data_dir):
            for fname in fnames:
                if not fname.endswith(".json"):
                    continue

                try:
                    with open(os.path.join(root, fname), "r", encoding="utf-8", errors="replace") as f:
                        annotations = json.load(f)
                except Exception as e:
                    logging.info(f"Error while reading annotation file: {fname}")
                    logging.info(f"Error: {e}")
                    continue 
                
                try:
                    null_errors = []
                    wrong_errors = []
                    for entry in annotations:
                        if not self.validate_null_values(entry):
                            null_errors.append(entry)
                        if not self.validate_values(entry):
                            wrong_errors.append(entry)

                    if len(null_errors)>0:
                        logging.info(f"{len(null_errors)} entries with missing values found in: {fname}")
                        if print_details:
                            logging.info("Entries are-")
                            for entry in null_errors:
                                logging.info(entry)

                    if len(wrong_errors)>0:
                        logging.info(f"{len(wrong_errors)} entries with wrong values found in: {fname}")
                        if print_details:
                            logging.info("Entries are-")
                            for entry in wrong_errors:
                                logging.info(entry)
                except Exception as e:
                    logging.info(f"Unknown error at: {fname}")
                    logging.info(f"Error: {e}")



    def check_font_size(self, print_details=False):

        for root, _, fnames in os.walk(self.data_dir):
            for fname in fnames:
                if not fname.endswith(".json"):
                    continue

                try:
                    with open(os.path.join(root, fname), "r", encoding="utf-8", errors="replace") as f:
                        annotations = json.load(f)
                except Exception as e:
                    logging.info(f"Error while reading annotation file: {fname}")
                    logging.info(f"Error: {e}")
                    continue 
                
                try:
                    font_size_errors = []
                    for entry in annotations:
                        if not self.validate_font_size(entry):
                            font_size_errors.append(entry)

                    if len(font_size_errors)>0:
                        logging.info(f"{len(font_size_errors)} entries with wrong values found in: {fname}")
                        if print_details:
                            logging.info("Entries are-")
                            for entry in font_size_errors:
                                logging.info(entry)
                except Exception as e:
                    logging.info(f"Unknown error at: {fname}")
                    logging.info(f"Error: {e}")



    def main(self):
        
        logging.info(f"Starting supervision on {self.data_dir}\n\n\n")

        total_data = os.listdir(self.data_dir)
        logging.info(f"Total data: {len(total_data)}")
        
        logging.info(f"Checking file availability.")
        logging.info("----------------------------------------------------------------------------------")
        self.check_files_availability()
        logging.info("\n\n")

        logging.info(f"Checking annotation schema.")
        logging.info("----------------------------------------------------------------------------------")
        self.check_annotation_schema(print_details=True)
        logging.info("\n\n")

        logging.info(f"Checking annotation values.")
        logging.info("----------------------------------------------------------------------------------")
        self.check_annotation_values(print_details=True)
        logging.info("\n\n")

        logging.info(f"Checking font size.")
        logging.info("----------------------------------------------------------------------------------")
        self.check_font_size(print_details=True)
        logging.info("\n\n")



if __name__ == "__main__":

    data_path = "/media/mehedi-shesher/WhyAlwaysMe/Files/Work/Code/github/ocr/data_annotator/data/For Supervision/split1(mehedi)/bucket/"


    Supervisor(data_dir=data_path).main()