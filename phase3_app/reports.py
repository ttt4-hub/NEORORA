"""PDF download for the selected loaded prediction series or explicit placeholders."""
from pathlib import Path
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
ROOT=Path(__file__).resolve().parent

def make_report(patient_id,rows,is_placeholder):
    if 'Neorora' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('Neorora',str(ROOT/'assets/DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('NeororaBold',str(ROOT/'assets/DejaVuSans-Bold.ttf')))
    styles=getSampleStyleSheet()
    for s in styles.byName.values():s.fontName='NeororaBold' if s.name.startswith(('Heading','Title')) else 'Neorora'
    styles['BodyText'].fontSize=9;styles['BodyText'].leading=14
    styles['Heading2'].fontSize=13;styles['Heading2'].leading=18
    out=BytesIO();doc=SimpleDocTemplate(out,leftMargin=44,rightMargin=44,topMargin=44,bottomMargin=44)
    rows=sorted(rows,key=lambda r:r['date']);last=rows[-1]
    body=[Paragraph('NEORORA | Cognitive Compass',styles['Heading1']),Paragraph('PLACEHOLDER VALUES — not model results' if is_placeholder else 'Imported prediction values — supplied by the team',styles['Heading2']),Paragraph('Screening tool, not a diagnosis.',styles['BodyText']),Spacer(1,14),Paragraph('Person ID: '+escape(patient_id),styles['BodyText']),Paragraph('Date: '+escape(last['date']),styles['BodyText']),Paragraph(f"Score: {last['risk_score']:g}% | Level: {escape(last['risk_level'])}",styles['Heading2'])]
    for key in ['reason_1','reason_2','reason_3']:body.append(Paragraph('- '+escape(str(last[key])),styles['BodyText']))
    body+=[Spacer(1,20),Paragraph('Timeline',styles['Heading2'])]
    cells=[['Date','Score','Level']]+[[r['date'],f"{r['risk_score']:g}%",r['risk_level']] for r in rows]
    t=Table(cells,colWidths=[180,150,170],repeatRows=1)
    t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'Neorora'),('FONTSIZE',(0,0),(-1,-1),9),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0F3B6E')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#E8F3FF'),colors.white]),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9)]))
    body+=[t,Spacer(1,18),Paragraph('The app displays supplied values without independently verifying the model. A percentage should not be described as a probability unless the model team has established that interpretation. No alert messages are sent automatically.',styles['BodyText'])]
    doc.build(body);return out.getvalue()
