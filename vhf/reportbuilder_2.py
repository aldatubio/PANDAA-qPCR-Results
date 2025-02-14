from datetime import datetime
import re, csv, os
import pandas as pd

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import utils, colors
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.platypus import Flowable, Table, TableStyle
from reportlab.pdfbase.pdfmetrics import stringWidth

version = '1.0.0'


#################################################################################
### Make header and footer to be repeated on each page
#################################################################################

class PageNumCanvas(canvas.Canvas):
    '''Instances can be passed to the canvasmaker argument of doc.build(), allowing page numbers to be added in the bottom right corner.'''
    def __init__(self, *args, **kwargs):
        '''Constructor'''
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []

    def showPage(self): #override
        '''On a page break, add new page info to list'''
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self): #override
        '''Get total pages, then draw 'Page x of y' text on each page'''
        page_count = len(self.pages)
        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            canvas.Canvas.showPage(self)

        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        '''Format 'Page x of y' text in bottom right corner of each page'''
        page = 'Page %s of %s' % (self._pageNumber, page_count)
        self.setFont('Helvetica-Oblique', 9)
        self.drawRightString(7.75*inch-5, 0.5*inch+3, page)


def strip_ascii(text):
    '''Remove non-ASCII characters from string.
    
       Function also rounds floats, as needed.
    '''
    if isinstance(text, str):
        return "".join(char for char in text
                    if 31 < ord(char) < 127
                  )
    
    elif isinstance(text, float):
        return(round(text, 2))
    
    else:
        return text


def footer(canvas, doc):
    '''Draw left-aligned footer with version and date info'''
    width, height = doc.pagesize
    styles = getSampleStyleSheet()
    font_size = 9
    
    # left aligned part
    ptext = '''<font size={fsize}><em>
            Generated by ReFocus Assistant version {ver} 
            at {date}
            </em></font>'''.format(fsize=font_size,
                                   ver=version,
                                   date=datetime.now().strftime('%d-%b-%Y %H:%M:%S'))
    p = Paragraph(ptext, styles['Normal'])
    p.wrapOn(canvas, width, height)
    p.drawOn(canvas, doc.leftMargin+5, 0.5*inch)

    # right aligned part - 'Page x of y' - is covered by PageNumCanvas


def header(canvas, doc):
    '''Draw header with right-aligned experiment name'''
    width, height = doc.pagesize
    styles = getSampleStyleSheet()
    font_size = 9
    regex = re.compile('<.*?>') #lazy - match as few chars as possible between <>
    
    # left aligned part of header
    ptext = '<font size={}><em>Report</em></font>'.format(font_size)
    p = Paragraph(ptext, styles['Normal'])
    p.wrapOn(canvas, width, height)
    p.drawOn(canvas, doc.leftMargin+5, height - doc.topMargin)

    # right aligned part of header
    ptext = '''<font size={0}><em>{1}</em></font>'''.format(font_size, doc.name)
    p = Paragraph(ptext, styles['Normal'])
    p_width = stringWidth(re.sub(regex, '', ptext), styles['Normal'].fontName, font_size)
    p.wrapOn(canvas, width, height)
    p.drawOn(canvas, width - doc.rightMargin - p_width - 5, height - doc.topMargin)


def header_and_footer(canvas, doc):
    '''Draw header and footer on same page'''
    header(canvas, doc)
    footer(canvas, doc)


#######################################################################################
### Create flowable page formatting
#######################################################################################

class Header(Flowable):
    '''First-page header with logo and minimal text'''
    def __init__(self, width=2*inch, height=0.2*inch):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.styles = getSampleStyleSheet()

    def coord(self, x, y, unit=1):
        '''Based on (x,y) in inches or mm, get coordinate in points'''
        x, y = x*unit, self.height - y*unit
        return x, y
    
    def draw(self):
        '''Draw logo and minimal text'''
        img_filepath = r"C:\Users\lucy\OneDrive - Aldatu Biosciences\Desktop\PANDAA qPCR Results\vhf\aldatulogo_icon.gif"
        desired_width = 30

        img = utils.ImageReader(img_filepath) #ImageReader uses Pillow to get information about image, so that we can grab the image size
        img_width, img_height = img.getSize()
        aspect = img_height / float(img_width) #calculate aspect ratio based on obtained height and width information
        img = Image(img_filepath,
                width=desired_width,
                height=(desired_width * aspect)) #scale height based on aspect ratio
        img.wrapOn(self.canv, self.width, self.height)
        img.drawOn(self.canv, *self.coord(0,0,inch))

        ptext = '<font size=18><b>Report</b></font>'
        p = Paragraph(ptext, self.styles['Normal'])
        p.wrapOn(self.canv, self.width, self.height)
        p.drawOn(self.canv, *self.coord(0.55,-0.2, inch))


class Report:
    '''Report class'''
    def __init__(self, pdf_file, head, results, pagesize=letter, path_as_filename=None):
        ''''''
        self.doc = SimpleDocTemplate(pdf_file, pagesize=pagesize,
                                     rightMargin=0.75*inch, leftMargin=0.75*inch,
                                     topMargin=0.75*inch, bottomMargin=0.75*inch)
        self.elements = []
        self.styles = getSampleStyleSheet()
        self.width, self.height = pagesize
        self.head = head
        self.results = results
        self.path_as_filename = path_as_filename
        self.doc.name = ''


    def coord(self, x, y, unit=1):
        '''Based on (x,y) in inches or mm, get coordinate in points'''
        x, y = x*unit, self.height - y*unit
        return x, y
    

    def create_text(self, text, size=10, bold=False):
        '''Convert string to Paragraph object'''
        if bold:
            return Paragraph('''<font size={size}><b>
            {text}</b></font>
            '''.format(size=size, text=text),
               self.styles['Normal'])

        return Paragraph('''<font size={size}>
        {text}</font>
        '''.format(size=size, text=text),
           self.styles['Normal'])
    

    def get_exp_name(self, input_data, use_path=False, kw=None):
        """Find file name in run info metadata or keyword in the data."""
        
        def process_reader(reader, keyword):
            """Process the reader (file or list) to find the desired keyword or experiment name."""
            for row in reader:
                if keyword:  # Find keyword in the first column
                    if keyword in row[0]:
                        return row[1]
                else:  # Default: find "Experiment Name" or similar
                    if 'Name' in row[0] and 'File' not in row[0]:
                        return row[1]
            return 'None'  # Default return value if nothing is found

        if use_path:  # Use filepath to get the file's name
            if ' - Summary' in self.path_as_filename:
                self.path_as_filename = self.path_as_filename.replace(' - Summary', '')
            return os.path.splitext(os.path.basename(self.path_as_filename))[0]
        

        # Handle input_data (file or list)
        if isinstance(input_data, list):  # If input is a list
            return process_reader(input_data, kw)
        else:  # If input is a CSV file
            with open(input_data, newline='') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                return process_reader(reader, kw)
    
    
    def csv_to_table(self, input_data, bold='left'):
        """Convert CSV or list data to a list of Paragraph objects, for use in a ReportLab Table object."""

        def process_data(reader, bold):
            """Process the rows of the reader or list data."""
            data = []
            if bold == 'left': #make left-most column bold
                for row in reader:
                    row_data = []
                    first = True
                    for item in row:
                        if item != '':
                            plain = strip_ascii(item)
                            if first:
                                row_data.append(self.create_text(plain, bold=True))
                                first = False
                            else:
                                row_data.append(self.create_text(plain))
                    if len(row_data) > 1: #if there's data in this row, add it to list
                        data.append(row_data)


            elif bold == 'top': #make top row bold
                first = True
                for row in reader:
                    row_data = []
                    for item in row:
                        if item != '':
                            plain = strip_ascii(item)
                            if first:
                                row_data.append(self.create_text(plain, bold=True))
                            else:
                                row_data.append(self.create_text(plain))
                    if len(row_data) > 1: #if there's data in this row, add it to list
                        data.append(row_data)
                    if first:
                        first = False
            
            else:
                raise ValueError("Invalid value for 'bold'. Use 'left' or 'top'.")
            
            return data

        # Handle input_data (file or list)
        if isinstance(input_data, list):
            return process_data(input_data, bold)
        
        elif isinstance(input_data, pd.DataFrame):
            header = list(input_data) #gets column headers
            data = input_data.values.tolist() #gets dataframe as a list of lists, but lacks column headers
            data.insert(0, header)
            return process_data(data, bold)
        
        else:
            with open(input_data, newline='') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                return process_data(reader, bold)


    def count_columns(self, input_data):
        '''Count the number of columns present in data table.
        
           Returns the number of columns in the widest row, if input is a list or a CSV file.
           If input is a dataframe, returns the number of columns in the first row.
        '''

        # Handle input_data (file or list)
        if isinstance(input_data, list):
            return len(max(input_data, key=len))
        
        elif isinstance(input_data, pd.DataFrame):
            return len(list(input_data)) #get length of list containing column headers
        
        else:
            with open(input_data, newline='') as csvfile:
                reader = csv.reader(csvfile, delimiter=',')
                return len(max(reader, key=len))


    def create_header(self):
        '''Create Header object'''
        header = Header()
        self.elements.append(header)
    

    def create_run_info(self):
        '''Draw run info table for traceability/quality purposes'''
        ptext = '<font size=14><b>Run Information</b></font>'
        p = Paragraph(ptext, self.styles['Normal'])
        self.elements.append(p)
        self.elements.append(Spacer(1,0.2*inch))

        data = self.csv_to_table(self.head, bold='left')
        self.doc.name = self.get_exp_name(self.head, use_path=self.path_as_filename)

        colWidths = [1.125*inch, 5.7*inch] #original: 0.875*inch, 5.95*inch
        table_style = TableStyle([('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                                  ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                                  ('VALIGN',(0,0),(-1,-1),'MIDDLE')])

        table = Table(data, colWidths=colWidths)
        table.setStyle(table_style)
        table.hAlign = 'LEFT'
        self.elements.append(table)
        self.elements.append(Spacer(1, 0.3*inch))


    def create_results(self):
        '''Draw run results table'''
        ptext = '<font size=14><b>Samples</b></font>'
        p = Paragraph(ptext, self.styles['Normal'])
        self.elements.append(p)
        self.elements.append(Spacer(1, 0.2*inch))

        data = self.csv_to_table(self.results, bold='top')

        numCols = self.count_columns(self.results) #get number of columns in dataset
        dataWidth = 6.375*inch // (numCols-1)      #page width is allocated equally across data (non-index) columns
        colWidths = [dataWidth]*(numCols-1)        #turn column widths into list
        colWidths.insert(0, 0.5*inch)              #add index column width to beginning of list

        table_style = TableStyle([('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                                  ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                                  ('VALIGN',(0,0),(-1,-1),'MIDDLE')])

        table = Table(data,
                      colWidths=colWidths,
                      repeatRows=1)
        table.setStyle(table_style)
        table.hAlign = 'LEFT'
        self.elements.append(table)


    def create(self):
        '''Create Report PDF with header, run info table, results table'''
        self.create_header()
        self.create_run_info()
        self.create_results()
        self.save()


    def save(self):
        '''Build Report doc'''
        self.doc.build(self.elements,
                       onFirstPage=footer,
                       onLaterPages=header_and_footer,
                       canvasmaker=PageNumCanvas)



#############################################################
### Run program
#############################################################


if __name__ == '__main__':
    pdf_file = 'results_example.pdf'
    #header_file = r'C:\Users\lucy\OneDrive - Aldatu Biosciences\Desktop\PANDAA qPCR Results\reportlab\sample_header.csv'
    header_file = [['Experiment Barcode',''],	
['Experiment Comment',''],	
['Experiment File Name',	r'C:\Users\lucy\Aldatu Biosciences\Aldatu Lab - Documents\Cooperative Lab Projects\PANDAA Software\2024-01-17 - LASV Training Kit QC.eds'],
['Experiment Name',	'2024-01-17 - LASV Training Kit QC'],
['Experiment Run End Time',	'2024-01-17 11:18:31 AM EST'],
['Experiment Type',	'Standard Curve'],
['Instrument Name',	'Aldatu-QS3'],
['',''],
[],
['Instrument Serial Number',	'272310002'],
['Instrument Type',	'QuantStudio™ 3 System'],
['Passive Reference',	'ROX'],
['Post-read Stage/Step'],	
['Pre-read Stage/Step'	],
['Quantification Cycle Method',	'Ct'],
['Signal Smoothing On',	'TRUE'],
['Stage/ Cycle where Ct Analysis is performed',	'Stage3, Step2'],
['User Name',	'IJM']]
    data_file = r'C:\Users\lucy\OneDrive - Aldatu Biosciences\Desktop\PANDAA qPCR Results\reportlab\sample_results.csv'
    results = Report(pdf_file, header_file, data_file)
    results.create()
    print('PDF generated successfully')
