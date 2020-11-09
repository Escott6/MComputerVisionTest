import fitz 
import re 
  
class Redactor: 
    
    # static methods work independent of class object 
    @staticmethod
    def get_sensitive_data(lines): 
        
        """ Function to get all the lines """
          
        redactedLines = ["phrases to redact", "test phrase2", "Yukon", "lazy", "computer", "canada", "website"]
        redacted_lines = '|'.join(redactedLines)

        for line in lines: 
            
            # matching the regex to each line 
            if re.search(redacted_lines, line, re.IGNORECASE): 
                search = re.search(redacted_lines, line, re.IGNORECASE) 
                  
                # This is probably the problem
                yield search.group(0) 
  
    # constructor 
    def __init__(self, path): 
        self.path = path 
  
    def redaction(self): 
        
        """ main redactor code """
          
        # opening the pdf 
        doc = fitz.open(self.path) 
          
        # iterating through pages 
        for page in doc: 
            
            # _wrapContents is needed for fixing alignment issues with rect boxes 
            page._wrapContents() 
              
            # geting the rect boxes which consists the matching email regex 
            sensitive = self.get_sensitive_data(page.getText("text") 
                                                .split('\n')) 
            for data in sensitive: 
                areas = page.searchFor(data) 
                  
                # drawing outline over sensitive datas 
                [page.addRedactAnnot(area, fill = (0, 0, 0)) for area in areas] 
                  
            # applying the redaction 
            page.apply_redactions() 
              
        # saving it to a new pdf 
        doc.save('redacted7.pdf') 