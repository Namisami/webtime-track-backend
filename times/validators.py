import re
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.utils.regex_helper import _lazy_re_compile

class BrowserURLValidator(URLValidator):
    schemes = [
        'http', 'https', 'ftp', 'ftps',
        
        'chrome', 'chrome-extension',
        'edge', 'ms-browser-extension',
        'about', 'moz-extension',
        'opera', 'otpauth',
        'safari', 'webkit-extension',
        
        'data', 'file', 'javascript'
    ]

    ul = URLValidator.ul
    hostname_re = r'([a-z0-9\-._~%]+|\[[a-f0-9]*:[a-f0-9\.:]+\])'
    port_re = r'(:\d+)?'
    path_re = r'([/?#][^\s]*)?'
    regex = _lazy_re_compile(
        r'^(?:[a-z0-9\.\-]*)://'  
        r'(?:\S+(?::\S*)?@)?' 
        r'(?:' + hostname_re + port_re + ')?'  
        r'(?:' + path_re + ')?', 
        re.IGNORECASE)

    def __call__(self, value):
        try:
            super().__call__(value)
        except ValidationError as e:
            if any(value.lower().startswith(f'{scheme}://') 
                    or value.startswith(f'{scheme}:') 
                    for scheme in self.schemes):
                return
            raise e