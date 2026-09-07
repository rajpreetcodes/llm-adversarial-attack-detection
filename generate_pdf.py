from fpdf import FPDF
import re

def sanitize(text):
    """Replace Unicode chars with ASCII equivalents for core fonts"""
    replacements = {
        '\u2014': '--',   # em dash
        '\u2013': '-',    # en dash
        '\u2018': "'",    # left single quote
        '\u2019': "'",    # right single quote
        '\u201c': '"',    # left double quote
        '\u201d': '"',    # right double quote
        '\u2022': '-',    # bullet
        '\u2026': '...',  # ellipsis
        '\u00a0': ' ',    # non-breaking space
        '\u2192': '->',   # right arrow
        '\u2190': '<-',   # left arrow
        '\u2265': '>=',   # >=
        '\u2264': '<=',   # <=
        '\u00d7': 'x',    # multiplication sign
        '\u00b1': '+/-',  # plus-minus
        '\u20ac': 'EUR',  # euro
        '\u00a3': 'GBP',  # pound
        '\u00a5': 'JPY',  # yen
        '\u00b0': 'deg',  # degree
        '\u00b5': 'mu',   # micro
        '\u03c0': 'pi',   # pi
        '\u221e': 'inf',  # infinity
        '\u221a': 'sqrt', # square root
        '\u2260': '!=',   # not equal
        '\u2248': '~',    # approximately
        '\u2261': '===',  # identical
        '\u2208': 'in',   # element of
        '\u2209': 'not in',
        '\u2286': 'subset',
        '\u2287': 'superset',
        '\u2229': 'intersect',
        '\u222a': 'union',
        '\u21d2': '=>',   # implies
        '\u21d4': '<=>',  # iff
        '\u2200': 'forall',
        '\u2203': 'exists',
        '\u2204': 'not exists',
        '\u220f': 'prod',
        '\u2211': 'sum',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    # Remove any remaining non-latin1 chars
    return text.encode('latin-1', errors='ignore').decode('latin-1')

class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, sanitize('DGAD vs Prior Work -- Comparative Analysis'), align='C')
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')

    def section_title(self, title, level=1):
        title = sanitize(title)
        if level == 1:
            self.set_font('Helvetica', 'B', 16)
            self.set_text_color(20, 60, 120)
            self.ln(4)
            self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(20, 60, 120)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(4)
        elif level == 2:
            self.set_font('Helvetica', 'B', 13)
            self.set_text_color(40, 80, 140)
            self.ln(2)
            self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
            self.ln(2)
        elif level == 3:
            self.set_font('Helvetica', 'BI', 11)
            self.set_text_color(60, 60, 60)
            self.ln(1)
            self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
            self.ln(1)

    def body_text(self, text):
        text = sanitize(text)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def bullet(self, text, indent=10):
        text = sanitize(text)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(30, 30, 30)
        self.cell(indent, 5, '')
        self.cell(5, 5, '-')
        self.multi_cell(0, 5, text)
        self.ln(0.5)

    def table_row(self, cells, widths, header=False, fill=False):
        cells = [sanitize(str(c)) for c in cells]
        if header:
            self.set_font('Helvetica', 'B', 7)
            self.set_fill_color(20, 60, 120)
            self.set_text_color(255, 255, 255)
        else:
            self.set_font('Helvetica', '', 7)
            self.set_text_color(30, 30, 30)
            if fill:
                self.set_fill_color(240, 245, 255)
            else:
                self.set_fill_color(255, 255, 255)
        
        x_start = self.get_x()
        y_start = self.get_y()
        max_h = 0
        
        # Calculate row height
        for i, (cell, w) in enumerate(zip(cells, widths)):
            n_lines = max(1, len(self.multi_cell(w, 5, cell, split_only=True)))
            h = n_lines * 5
            if h > max_h:
                max_h = h
        
        # Check if we need a page break
        if y_start + max_h > self.h - self.b_margin:
            self.add_page()
            y_start = self.get_y()
        
        # Draw cells
        for i, (cell, w) in enumerate(zip(cells, widths)):
            self.set_xy(x_start + sum(widths[:i]), y_start)
            self.multi_cell(w, 5, cell, border=1, fill=True, new_x="RIGHT", new_y="TOP", max_line_height=5)
        self.set_y(y_start + max_h)

    def simple_table(self, headers, rows, col_widths=None):
        if col_widths is None:
            col_widths = [self.epw / len(headers)] * len(headers)
        self.table_row(headers, col_widths, header=True)
        for i, row in enumerate(rows):
            self.table_row(row, col_widths, fill=(i % 2 == 0))


def parse_markdown_to_pdf(md_text, pdf):
    lines = md_text.split('\n')
    in_table = False
    table_headers = []
    table_rows = []
    table_align = []
    
    for line in lines:
        stripped = line.strip()
        
        # Headers
        if stripped.startswith('# '):
            pdf.section_title(sanitize(stripped[2:]), level=1)
        elif stripped.startswith('## '):
            pdf.section_title(sanitize(stripped[3:]), level=2)
        elif stripped.startswith('### '):
            pdf.section_title(sanitize(stripped[4:]), level=3)
        # Table handling
        elif stripped.startswith('|') and '|' in stripped[1:]:
            parts = [sanitize(p.strip()) for p in stripped.split('|')[1:-1]]
            if not in_table:
                in_table = True
                table_headers = parts
            elif not table_align and all(re.match(r'^:?-+:?$', p) for p in parts):
                table_align = parts
            else:
                table_rows.append(parts)
        elif in_table and not stripped.startswith('|'):
            # Table ended
            if table_headers and table_rows:
                col_widths = [pdf.epw / len(table_headers)] * len(table_headers)
                pdf.simple_table(table_headers, table_rows, col_widths)
            in_table = False
            table_headers = []
            table_rows = []
            table_align = []
            # Re-process this line
            if stripped:
                if stripped.startswith('- ') or stripped.startswith('* '):
                    pdf.bullet(sanitize(stripped[2:]))
                else:
                    pdf.body_text(sanitize(stripped))
        else:
            # Regular text
            if stripped.startswith('- ') or stripped.startswith('* '):
                pdf.bullet(sanitize(stripped[2:]))
            elif stripped:
                pdf.body_text(sanitize(stripped))
    
    # Handle trailing table
    if in_table and table_headers and table_rows:
        col_widths = [pdf.epw / len(table_headers)] * len(table_headers)
        pdf.simple_table(table_headers, table_rows, col_widths)


# Read markdown
with open('DGAD_vs_Prior_Work.md', 'r', encoding='utf-8') as f:
    md_content = f.read()

# Generate PDF
pdf = PDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)
pdf.add_page()

parse_markdown_to_pdf(md_content, pdf)

pdf.output('DGAD_vs_Prior_Work.pdf')
print('PDF generated successfully!')