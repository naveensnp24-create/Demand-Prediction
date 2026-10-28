from pathlib import Path
import json, math, fitz
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
ROOT=Path.cwd();OUT=ROOT/'output/pdf';OUT.mkdir(parents=True,exist_ok=True);TMP=ROOT/'tmp/pdfs'
for name,file in [('Times','times.ttf'),('TimesB','timesbd.ttf'),('TimesI','timesi.ttf'),('Arial','arial.ttf'),('ArialB','arialbd.ttf'),('Narrow','ARIALN.TTF'),('NarrowB','ARIALNB.TTF')]:pdfmetrics.registerFont(TTFont(name,str(Path('C:/Windows/Fonts')/file)))
pdfmetrics.registerFontFamily('Times',normal='Times',bold='TimesB',italic='TimesI',boldItalic='TimesB')
config=OUT/'report_details.json'
if not config.exists():config.write_text(json.dumps({'student_name':'','register_number':'','guide_name':'','guide_designation':'Associate Professor, CSE','batch':'2024 - 2028','month_year':'OCTOBER 2026'},indent=2))
D=json.loads(config.read_text());NAME=D['student_name'] or '________________________________';REG=D['register_number'] or '__________________';GUIDE=D['guide_name'] or '________________________________'
W,H=596,842;L=99;CW=429
C=canvas.Canvas(str(OUT/'DemandPredict_Project_Report.pdf'),pagesize=(W,H));C.setTitle('DemandPredict - Data Science Project Report');C.setAuthor('DemandPredict Project')
BODY=ParagraphStyle('body',fontName='Times',fontSize=12,leading=16,alignment=TA_JUSTIFY)
y=0;page_num=0;audit=[]
def line(t,x,yy,font='Times',size=12,align='left'):
 C.setFont(font,size);getattr(C,{'left':'drawString','right':'drawRightString','center':'drawCentredString'}[align])(x,yy,t)
def para(t,size=12,leading=16,align=TA_JUSTIFY,gap=11):
 global y
 p=Paragraph(t,ParagraphStyle('p',parent=BODY,fontSize=size,leading=leading,alignment=align));_,h=p.wrap(CW,800)
 if y-h<73:raise RuntimeError(f'Overflow page {page_num}: {t[:65]} at {y-h}')
 p.drawOn(C,L,y-h);y-=h+gap
def heading(t):para(t,12,16,TA_LEFT,8)
def start(t=None,number=None):
 global y,page_num
 page_num+=1;y=764
 if number is not None:line(str(number),313,39,size=11,align='center')
 if t:para("<b>"+t+"</b>",14,18,TA_CENTER,18)
def end():audit.append({'page':page_num,'bottom_y':round(y,1)});C.showPage()
def table(rows,widths=None,fs=10):
 global y
 st=ParagraphStyle('cell',fontName='Times',fontSize=fs,leading=fs+3)
 t=Table([[Paragraph(str(c),st) for c in row] for row in rows],colWidths=widths or [CW/len(rows[0])]*len(rows[0]))
 t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeeee')),('LINEABOVE',(0,0),(-1,0),.6,colors.black),('LINEBELOW',(0,0),(-1,0),.5,colors.black),('LINEBELOW',(0,-1),(-1,-1),.6,colors.black)]));_,h=t.wrap(CW,800)
 if y-h<73:raise RuntimeError(f'Table overflow {page_num}: {y-h}')
 t.drawOn(C,L,y-h);y-=h+13
def picture(path,caption,maxh=440):
 global y
 im=ImageReader(str(path));iw,ih=im.getSize();s=min(CW/iw,maxh/ih);ww,hh=iw*s,ih*s
 C.drawImage(im,L+(CW-ww)/2,y-hh,width=ww,height=hh,mask='auto');y-=hh+10;para(caption,10,13,TA_CENTER,13)
def box(t,x,top,w,h=50):
 C.setStrokeColor(colors.HexColor('#333333'));C.setFillColor(colors.HexColor('#f3f6f8'));C.roundRect(x,top-h,w,h,5,stroke=1,fill=1);C.setFillColor(colors.black)
 p=Paragraph(t,ParagraphStyle('box',fontName='Times',fontSize=11,leading=14,alignment=TA_CENTER));_,hh=p.wrap(w-16,h);p.drawOn(C,x+8,top-h+(h-hh)/2)
def arrow(x1,y1,x2,y2):
 C.setStrokeColor(colors.black);C.setLineWidth(.8);C.line(x1,y1,x2,y2);a=math.atan2(y2-y1,x2-x1);p=C.beginPath();p.moveTo(x2,y2);p.lineTo(x2-6*math.cos(a-.4),y2-6*math.sin(a-.4));p.lineTo(x2-6*math.cos(a+.4),y2-6*math.sin(a+.4));p.close();C.drawPath(p,fill=1)
def code(t):
 global y
 ls=t.strip('\n').splitlines();fs=min(8.2,(CW-18)/(.6*max(map(len,ls))));lh=fs+3;h=len(ls)*lh+20
 if y-h<73:raise RuntimeError(f'Code overflow {page_num}')
 C.setFillColor(colors.HexColor('#f5f5f5'));C.rect(L,y-h,CW,h,stroke=0,fill=1);C.setFillColor(colors.black);C.setFont('Courier',fs)
 for n,t in enumerate(ls):C.drawString(L+9,y-14-n*lh,t)
 y-=h+13
# Institutional artwork only, extracted from the reference PDF.
tpl=fitz.open(r'D:\II CSE B\III CSE B\DS\Report\Madhu-DS-Project.pdf')
tpl[1].get_pixmap(matrix=fitz.Matrix(3,3),clip=fitz.Rect(135,49,490,128)).save(str(TMP/'college-header.png'))
tpl[0].get_pixmap(matrix=fitz.Matrix(3,3),clip=fitz.Rect(57,688,553,764)).save(str(TMP/'college-footer.png'))
start();line('DEMANDPREDICT',548,733,'ArialB',18,'right')
for t,yy in [('DATA SCIENCE',678),('PROJECT',657),(D['month_year'],616),('PROJECT',466),('WORK',445),('BATCH',363),(D['batch'],342)]:line(t,119,yy,'NarrowB',18,'center')
C.setLineWidth(2);C.line(57,502,173,502);C.line(57,429,173,429)
for t,yy in [('PROJECT REPORT SUBMITTED IN PARTIAL FULFILLMENT OF THE',686),('REQUIREMENTS FOR THE AWARD OF THE DEGREE OF',665),('BACHELOR OF ENGINEERING IN COMPUTER SCIENCE AND',644),('ENGINEERING OF THE ANNA UNIVERSITY',623)]:line(t,548,yy,'Narrow',12,'right')
line('Submitted by',548,421,'Arial',12,'right');line(NAME,548,399,'ArialB',12,'right');line(REG,548,378,'ArialB',12,'right');line('Under the Guidance of',548,265,'Arial',12,'right');line(GUIDE,548,243,'ArialB',12,'right');line(D['guide_designation'],548,221,'ArialB',12,'right');C.drawImage(str(TMP/'college-footer.png'),57,78,width=496,height=76);end()
start();C.drawImage(str(TMP/'college-header.png'),135,714,width=355,height=79);y=679
para('<b>DEMANDPREDICT</b>',16,20,TA_CENTER,13);para('RETAIL DEMAND FORECASTING AND CUSTOMER ANALYTICS',11,15,TA_CENTER,26);para('<b>DATA SCIENCE PROJECT REPORT</b>',14,18,TA_CENTER,25);para('<i><b>Submitted by</b></i>',14,18,TA_CENTER,15);para(f'<b>{NAME}</b>',14,18,TA_CENTER,10);para(f'<b>{REG}</b>',14,18,TA_CENTER,27);para('<b>BACHELOR OF ENGINEERING</b>',14,18,TA_CENTER,15);para('<b><i>in</i></b>',14,18,TA_CENTER,10);para('<b>COMPUTER SCIENCE AND ENGINEERING</b>',14,18,TA_CENTER,45)
for t in ['SRI ESHWAR COLLEGE OF ENGINEERING','(AN AUTONOMOUS INSTITUTION)','COIMBATORE - 641 202',D['month_year']]:para('<b>'+t+'</b>',14,18,TA_CENTER,15)
end()
start('BONAFIDE CERTIFICATE');para('This is to certify that the project report entitled <b>"DemandPredict"</b> was carried out by',gap=16);para(f'<b>{NAME}<br/>{REG}</b>',align=TA_CENTER,gap=20);para('who carried out the Data Science Project work under my supervision.');y-=60
for xx in [L,L+238]:C.line(xx,y,xx+185,y);line('SIGNATURE',xx,y-24,'TimesB',11)
line('Head of the Department',L,y-55,'TimesB',12);line('Project Guide',L+238,y-55,'TimesB',12);line(GUIDE,L+238,y-78,'TimesB',10)
for xx in [L,L+238]:
 for t,dy in [('Department of Computer',105),('Science and Engineering,',124),('Sri Eshwar College of',150),('Engineering,',169),('Coimbatore - 641 202.',188)]:line(t,xx,y-dy,size=12)
y-=253;para('Submitted for the End Semester Project examination <b>U23AD491 Data Science</b> Project viva-voce held on ....................................',align=TA_CENTER,gap=65);line('................................',L+8,y);line('................................',L+264,y);line('(Internal Examiner)',L,y-35,'TimesB');line('(External Examiner)',L+254,y-35,'TimesB');end()
start('DECLARATION');y-=12;para(f'<b>{NAME}<br/>{REG}</b>',align=TA_CENTER,gap=28)
para('I declare that the project entitled <b>"DemandPredict"</b>, submitted in partial fulfilment of the requirements for the Bachelor of Engineering degree in Computer Science and Engineering, is a record of the project work carried out under the supervision and guidance of the project guide, Department of Computer Science and Engineering, Sri Eshwar College of Engineering, Coimbatore.')
para('The report describes the implemented application, its methods and the results obtained from the project demonstration dataset. Sources used in the study are acknowledged in the references. The work has not been submitted by me for the award of another degree or diploma.');y-=68;line('Place: Coimbatore',L,y);line('Date: ................................',L,y-35);line('Signature of the Student',L+235,y-80,'TimesB');end()
start('ACKNOWLEDGEMENT');y-=12
for t in ['I express my sincere gratitude to the management of Sri Eshwar College of Engineering for providing the academic environment and facilities required to carry out this Data Science project.','I thank the Principal and the Head of the Department of Computer Science and Engineering for their encouragement and support during the development of the project.','I extend my gratitude to my project guide for guidance, constructive feedback and assistance in shaping the project methodology and presentation.','I also thank the faculty members of the Department of Computer Science and Engineering for sharing their knowledge and supporting the learning process. Their teaching helped establish the foundations in programming, databases, statistics and machine learning used in this project.','I acknowledge the developers and maintainers of the open-source libraries used in DemandPredict. Their work makes it possible to combine an interactive application with reproducible data analysis and machine learning.','Finally, I thank my family and friends for their encouragement and support throughout the completion of this project.']:para(t)
y-=45;para(f'<b>{NAME}</b>',align=TA_CENTER);end()
start()
table([['<b>Chapter</b>','<b>Table of Contents</b>','<b>Page No.</b>'],['','<b>ABSTRACT</b>','i'],['','<b>LIST OF FIGURES</b>','ii'],['1','<b>INTRODUCTION</b>','1'],['2','<b>SYSTEM ANALYSIS AND DESIGN</b><br/>2.1 Literature Survey<br/>2.2 Existing Product<br/>2.3 Problem Statement','2'],['3','<b>PROPOSED SYSTEM</b><br/>3.1 Overview<br/>3.2 Block Diagram','3'],['4','<b>PROJECT DESCRIPTION</b><br/>4.1 Dataset Collection and Description<br/>4.2 Methodology<br/>4.3 Implementation','4<br/>4<br/>5-7<br/>8-9'],['5','<b>RESULTS AND INFERENCES</b><br/>5.1 Model Evaluation<br/>5.2 Application Outputs<br/>5.3 Testing and Verification','10<br/>10<br/>11-16<br/>17'],['6','<b>CONCLUSION AND FUTURE SCOPE</b><br/>6.1 Conclusion<br/>6.2 Future Scope','18'],['','<b>REFERENCES</b>','19']],[55,310,64],12);end()
start('ABSTRACT',number='i')
para('DemandPredict is a retail analytics application that combines demand forecasting, customer purchase propensity, behavioural segmentation and inventory planning in a single dashboard. Retail records often remain distributed across transaction exports, customer lists and product catalogues, making it difficult to connect demand patterns with customer behaviour and available stock. This project provides a structured workflow for importing such records and producing interpretable analytical outputs.')
para('The system uses React and TypeScript for the interface, FastAPI for the application programming interface, and SQLite with SQLAlchemy for persistent storage. Five related CSV datasets represent customers, products, promotions, behavioural events and orders. Schema validation, reference checks and transactional imports maintain consistency before analysis begins.')
para('Demand is forecast using a moving-average baseline, Prophet, XGBoost, LightGBM and a validation-weighted ensemble. Chronological holdouts separate model evaluation from fitting. Regularized logistic regression estimates customer-product purchase probability from historical behaviour, while linear SHAP contributions describe the fitted model\'s feature effects. RFM features and K-means support customer segmentation. Inventory recommendations combine recent demand, stock and a planning buffer.')
para('The implemented system was evaluated using a synthetic demonstration dataset with 120 customers, 24 products, 1,481 order rows and 12,039 events. The purchase model achieved a ROC AUC of 0.7265 and a Brier score of 0.05744 on a later 30-day window. Forecast results varied across categories, demonstrating the need to compare alternatives against a simple baseline. Application verification covered API behaviour, import integrity and browser workflows. The project demonstrates an integrated, reproducible local decision-support workflow; its synthetic-data results do not establish production effectiveness.')
para('<b>Keywords:</b> demand forecasting, purchase propensity, retail analytics, RFM, K-means, explainable machine learning.',size=11,leading=15);end()
start('LIST OF FIGURES',number='ii')
table([['<b>Figure</b>','<b>Description</b>','<b>Page</b>'],['3.1','System block diagram','3'],['4.1','Methodology and chronological validation flow','5'],['5.1','Retail overview dashboard','11'],['5.2','Demand forecasting and model validation','12'],['5.3','Customer recommendations and explanation','13'],['5.4','Dataset import and status interface','14'],['5.5','Customer segmentation interface','15'],['5.6','Inventory planning interface','16']],[55,320,54],12)
y-=20;heading('<b>LIST OF TABLES</b>');table([['<b>Table</b>','<b>Description</b>','<b>Page</b>'],['4.1','Demonstration dataset and key attributes','4'],['4.2','Application technologies and responsibilities','8'],['5.1','Category forecast MAE on the holdout','10'],['5.2','Purchase propensity validation','10'],['5.3','Verification summary','17']],[55,320,54],11);end()
start('1. INTRODUCTION',number=1)
para('Retail businesses record purchases, product views, shopping-cart additions and stock levels through their digital systems. These records can support decisions about replenishment and customer engagement when they are organized into a consistent analytical workflow. Sales summaries alone describe what happened; useful planning also requires estimates of future demand and an understanding of the customers behind those transactions.')
para('DemandPredict addresses this need through a local web application for retail demand forecasting and customer analytics. It brings validated data import, historical summaries, forecasting, customer recommendations, segmentation and inventory suggestions into one interface. Users can move from an overview of the business to a specific product or customer without preparing separate analysis scripts for each task.')
para('The project has four main analytical objectives. The first is to compare daily demand forecasts from a baseline and several machine learning models. The second is to estimate the probability that a customer will purchase a product within a chosen horizon. The third is to identify behavioural customer groups using recency, frequency and monetary value. The fourth is to translate recent demand and current stock into understandable inventory planning indicators.')
para('A reliable workflow must also handle invalid inputs and communicate uncertainty. The application therefore checks file schemas, data types and related record identifiers before updating the database. Forecasts display the final observed date, and evaluation uses later time periods that were excluded from fitting. Purchase explanations are presented as model associations rather than causal reasons for customer behaviour.')
para('The demonstration uses generated retail records so that the complete workflow can be reproduced without relying on private customer information. The generated history contains variation in product preferences, purchasing activity and calendar patterns. Evaluation on this dataset verifies the implemented analytical process, while evaluation on real retail data remains necessary before operational adoption.')
para('The scope is a trusted, single-user project environment. DemandPredict provides estimates and recommendations for human review; it does not place purchase orders or execute marketing campaigns. Subsequent chapters describe the system analysis, proposed architecture, dataset, methodology, implementation and measured results.');end()
start('2. SYSTEM ANALYSIS AND DESIGN',number=2)
heading('<b>2.1 Literature Survey</b>')
para('Taylor and Letham describe forecasting at scale using an interpretable model with trend and seasonal components [1]. This motivates the inclusion of Prophet as one candidate for retail daily demand. In this project, weekly seasonality is enabled; annual seasonality requires at least a year of observations.',11.5,15)
para('Chen and Guestrin introduce XGBoost, a scalable tree boosting system [2]. Ke et al. present LightGBM and techniques for efficient gradient boosting [3]. DemandPredict uses their regression implementations with lag, rolling and calendar features. The LightGBM configuration uses its standard regressor; the project does not claim a custom implementation of the paper\'s algorithms.',11.5,15)
para('Lundberg and Lee develop SHAP, a framework for additive feature attributions [4]. DemandPredict uses the closed-form linear, independent-feature interpretation for logistic regression, explaining 30-day log odds relative to mean training features. It does not use a general-purpose SHAP package or claim causal explanations.',11.5,15)
heading('<b>2.2 Existing Product</b>')
para('The existing workflow considered here consists of spreadsheets, sales reports and separate modelling notebooks. These can summarize transactions or train individual models, but require manual coordination to maintain consistent dates, customer identifiers and product definitions. A forecast prepared separately from stock and customer records also requires additional interpretation before it can support a planning decision.',11.5,15)
para('DemandPredict consolidates those steps into a purpose-built application. This comparison describes the workflow addressed by the project; it is not a benchmark of commercial retail products.',11.5,15)
heading('<b>2.3 Problem Statement</b>')
para('Develop a reproducible retail analytics system that accepts related CSV datasets, validates their integrity and provides demand forecasts, customer purchase estimates, behavioural segments and inventory recommendations. The system must report validation results, explain key outputs and handle insufficient history without presenting unsupported certainty.',11.5,15)
para('The design prioritizes data consistency, chronological evaluation, a usable dashboard and traceable outputs. Production-scale processing, authenticated multi-user access and automatic replenishment are outside the implemented scope.',11.5,15);end()
start('3. PROPOSED SYSTEM',number=3)
heading('<b>3.1 Overview</b>')
para('DemandPredict uses a three-layer architecture. The presentation layer provides six dashboard screens. The FastAPI application validates requests and coordinates analytical services. SQLite stores the related retail records, while Python modules generate forecasts and customer estimates from the same imported data.')
para('A user imports the five supported CSV tables or loads the fictional demonstration dataset into an empty database. The application checks all supplied files before committing changes. Analytics then operate on a common dataset snapshot. Forecasts, customer recommendations and inventory plans can be exported as CSV for further review.')
heading('<b>3.2 Block Diagram</b>');top=y
box('User<br/>CSV files and dashboard requests',L+95,top,239,46);arrow(L+214,top-46,L+214,top-62)
box('React + TypeScript interface<br/>Overview | Forecast | Customer | Segments | Insights | Settings',L,top-63,CW,56);arrow(L+214,top-119,L+214,top-135)
box('FastAPI routes and analytics services<br/>Validation, query handling and consistent dataset snapshot',L,top-136,CW,53);C.line(L+214,top-189,L+214,top-198);C.line(L+102,top-198,L+327,top-198);arrow(L+102,top-198,L+102,top-205);arrow(L+327,top-198,L+327,top-205)
box('SQLite + SQLAlchemy<br/>Customers, products, promotions,<br/>events and orders',L,top-206,204,68);box('Python analytical modules<br/>Forecasting, logistic regression,<br/>RFM / K-means and inventory rules',L+225,top-206,204,68);arrow(L+204,top-239,L+225,top-239);arrow(L+327,top-274,L+327,top-290);arrow(L+102,top-274,L+102,top-290)
box('Outputs: forecasts, explanations, segments and planning indicators<br/>Charts, tables, API responses and CSV exports',L,top-291,CW,54);y=top-362
para('<b>Figure 3.1 System block diagram</b>',10,13,TA_CENTER)
para('The analytical modules read validated records and return derived results. Imported changes invalidate the cached customer model through a data fingerprint, so subsequent outputs reflect the updated dataset.',11,15);end()
start('4. PROJECT DESCRIPTION',number=4)
heading('<b>4.1 Dataset Collection and Description</b>')
para('The system accepts user-provided CSV files and includes a seeded synthetic generator for reproducible demonstrations. The evaluated database contains 180 days of order history, from 22 April to 18 October 2026. Its customers and retail activities are fictional. Values in the interface are interpreted as Indian rupees (INR).')
para('<b>Table 4.1 Demonstration dataset and key attributes</b>',10,13,TA_CENTER,8)
table([['<b>Table</b>','<b>Rows</b>','<b>Representative attributes</b>'],['Customers','120','Customer ID, name, email, signup date, location'],['Products','24','Product ID, category, price, launch date, stock and reorder point'],['Promotions','1','Promotion ID, type, active dates and discount details'],['Orders','1,481','Customer ID, product ID, date, quantity, price, status and session'],['Events','12,039','Customer ID, product ID, timestamp, event type and session']],[78,49,302],10.5)
para('Customers and products each have one-to-many relationships with orders and events. Optional promotion references connect eligible transaction or behaviour records to promotions. Primary identifiers are preserved as strings. Foreign-key checks reject references to records that do not exist after an import.')
para('The 24 products span eight categories: Beauty and Personal Care, Books and Media, Clothing, Electronics, Grocery and Gourmet, Home and Kitchen, Sports and Fitness, and Toys and Games. Product preferences and time-dependent purchasing patterns are generated with seed 42. These patterns are demonstration assumptions, not observations from a commercial retailer.')
para('Sales calculations include confirmed, shipped and delivered orders. Pending, cancelled and returned orders are excluded. An order row is a stored transaction record; it is not necessarily a unique purchase session. Frequency for customer segmentation is calculated from distinct eligible sessions.')
para('Missing calendar days within the observed series are filled with zero demand. Product history begins no earlier than its launch date. The application limits daily forecasting history to the latest 730 days and anchors forecasts after the dataset\'s latest order or event date.');end()
start('4.2 Methodology',number=5)
para('The methodology separates data ingestion, feature construction, temporal evaluation and presentation. The same data definitions are used for dashboard summaries and model inputs so that outputs can be interpreted against the recorded history.')
steps=[('1. Collect and validate','Read CSV tables; check schemas, values and related IDs.'),('2. Persist and prepare','Commit imports atomically; derive eligible sales and daily series.'),('3. Construct past-only features','Build demand lags, customer behaviour and RFM measures.'),('4. Validate chronologically','Fit on earlier data; evaluate on later, completed periods.'),('5. Refit and generate outputs','Forecast demand; estimate purchase probability; assign segments.'),('6. Present decision support','Show charts, explanations, error metrics and inventory suggestions.')];top=y
for i,(a,b) in enumerate(steps):
 yy=top-i*66;box('<b>'+a+'</b><br/>'+b,L,yy,CW,49)
 if i<5:arrow(L+CW/2,yy-49,L+CW/2,yy-64)
y=top-6*66+3;para('<b>Figure 4.1 Methodology and chronological validation flow</b>',10,13,TA_CENTER)
heading('<b>Evaluation discipline</b>')
para('Demand forecast metrics use the final 14 observed days when sufficient history is available. Ensemble weights use an earlier, separate window, preventing their selection from using the final evaluation targets. The final forecast is refitted on all observations after validation.',11.5,15)
para('Purchase propensity uses an earlier 30-day outcome window for fitting and a later 30-day window for validation. Features at each cutoff use only prior records. Final refitting combines the two completed windows. This avoids using future customer activity in the features.',11.5,15);end()
start('4.2 Methodology (continued)',number=6)
heading('<b>Demand forecasting</b>')
para('The moving-average baseline predicts the mean of the last 28 daily observations. Prophet models trend and weekly seasonality [1]. XGBoost and LightGBM fit boosted regression trees [2, 3]. Their inputs include demand at lags 1, 7 and 14; means over 7, 14 and 28 days; seven-day standard deviation; and day-of-week, month and day-of-year.')
para('The tree models use 60 estimators, maximum depth 3, learning rate 0.06 and random seed 42. LightGBM uses seven leaves and a minimum of five observations per child. Future tree predictions are recursive: each predicted value is appended to the history before the next day is estimated. Outputs are constrained to non-negative demand.')
para('The ensemble combines the four model forecasts. For sufficiently long histories, inverse-MAE weights are estimated from the 14 days preceding the final validation window. Shorter eligible histories use equal weights. Fewer than 49 observations or constant demand trigger a moving-average fallback. Fewer than 14 observations do not produce validation metrics.')
heading('<b>Error measures and forecast ranges</b>')
para('Let y(t) be observed demand, f(t) the prediction and n the number of validation days. The implemented error measures are:',gap=8)
for t in ['MAE = sum |y(t) - f(t)| / n','RMSE = sqrt(sum (y(t) - f(t))<super>2</super> / n)','MAPE = 100 x mean(|y(t) - f(t)| / y(t)), for y(t) &gt; 0','WMAPE = 100 x sum |y(t) - f(t)| / sum y(t)']:para(t,11,15,TA_LEFT,7)
para('MAPE excludes zero-demand days. WMAPE is omitted when the total observed holdout demand is zero. These rules prevent division by zero, but MAPE can still underrepresent the difficulty of intermittent demand.')
para('Forecast bands use validation residual error with an approximate 1.96 x RMSE multiplier and increasing horizon width. Lower bounds are truncated at zero. These bands are heuristic ranges; their nominal probability coverage has not been calibrated. They should support interpretation rather than be treated as guaranteed stock requirements.');end()
start('4.2 Methodology (continued)',number=7)
heading('<b>Customer purchase propensity and explanations</b>')
para('A regularized logistic regression model uses eight customer-product features: prior product purchases, recent views, recent cart additions, customer order count, product order count, category affinity, days since the product was purchased, and relative price. The pipeline applies feature transformations and standardization before fitting. Uniform pair sampling preserves the observed label prevalence within each temporal window.',11.5,15)
para('The target is whether a customer purchases the product in the next 30 days. For a horizon h, the application converts the 30-day probability p30 using p(h) = 1 - (1 - p30)<super>h/30</super>. This assumes a constant purchase hazard. Expected quantity multiplies the probability by historical conditional purchase quantity, and expected revenue also multiplies by product price.',11.5,15)
para('For the linear model, a feature contribution is its standardized deviation from the training mean multiplied by its coefficient. The largest absolute contributions explain 30-day log odds under an independent-feature assumption [4]. Correlated features can complicate interpretation. Insufficient history or a single target class produces an explicitly labelled smoothed-history estimate.',11.5,15)
heading('<b>Behavioural customer segmentation</b>')
para('RFM features represent recency in days, purchase frequency in distinct sessions, and eligible monetary spend. Purchasers are clustered using standardized log(1 + RFM) values and K-means, with up to four distinct clusters, random seed 42 and ten initializations. Labels describe the resulting cluster profiles rather than using the synthetic generator\'s latent segment labels.',11.5,15)
para('Customers without eligible purchases form a separate group. Purchasers inactive for at least 60 days are labelled at risk. Discount-heavy occasional buyers can receive a promotion-responsive label. These rules aid interpretation but do not represent a validated churn model.',11.5,15)
heading('<b>Inventory planning</b>')
para('Expected demand is the last 28 days\' mean daily units multiplied by the planning horizon. Stockout risk compares that estimate and a 20% buffer with available stock. Suggested replenishment is max(0, ceil(1.2 x demand + reorder point - stock)) when expected demand is positive. More than 90 days of stock cover indicates overstock. Lead times, inbound orders and demand hidden by past stockouts are not included.',11.5,15);end()
start('4.3 Implementation',number=8)
para('<b>Table 4.2 Application technologies and responsibilities</b>',10,13,TA_CENTER,8)
table([['<b>Component</b>','<b>Technology and purpose</b>'],['Presentation','React 18, TypeScript, Vite, Tailwind CSS and Recharts; interactive views, charts, routing and themes.'],['API','FastAPI, Pydantic and Uvicorn; request validation, API responses and generated API documentation.'],['Persistence','SQLAlchemy and SQLite; related customer, product, promotion, event and order records.'],['Data and models','pandas, NumPy, scikit-learn, Prophet, XGBoost and LightGBM; preparation, estimation and evaluation.'],['Verification','pytest, HTTPX, Playwright, TypeScript, ESLint and Ruff; application and code checks.']],[90,339],10.5)
heading('<b>Import and API implementation</b>')
para('The upload service rejects missing or unknown columns, invalid dates, non-finite monetary values, invalid quantities and unresolved references. Customer emails must be valid and unique. Individual uploads default to a 100 MB limit. Repeated identifiers are upserted, and all files in one import either succeed together or are rolled back. List-like values use safe literal parsing rather than expression evaluation.',11.5,15)
para('API routes expose product and category forecasts, customer predictions, segments, stock insights, dataset status and CSV templates. Forecast requests restrict the horizon to 1-90 days and model selection to supported identifiers. SQLAlchemy sessions provide access to the same database for all services.',11.5,15)
heading('<b>Interface and local operation</b>')
para('The six screens provide responsive navigation, loading and error feedback, empty states and light/dark themes. CSV downloads escape spreadsheet formula prefixes. The local launcher starts the interface on port 5173 and the API on port 8000, both on localhost. Documentation is available through /docs.',11.5,15)
para('Model training and analytics run inside the API process. A fingerprint-based cache avoids reusing a customer model after data changes. The application is intended for a trusted single-user environment and does not implement login or multi-tenant authorization.',11.5,15);end()
start('4.3 Implementation (continued)',number=9)
heading('<b>Representative source code</b>')
para('The following excerpts are taken from the implemented project. The first constructs the lag, rolling and calendar predictors used by the tree forecasting models.',11.5,15)
src=(ROOT/'ml/forecasting.py').read_text();code(src[src.index('def features('):src.index('\n\ndef predict(')])
para('<i>Source: ml/forecasting.py</i>',10,13,TA_LEFT,14)
para('The product forecast route validates the planning horizon and the requested model before delegating to the shared analytical dataset service.',11.5,15)
src=(ROOT/'backend/app/api/forecast.py').read_text();code(src[src.index('@router.get("/forecast/product'):src.index('\n\n@router.get("/forecast/category')])
para('<i>Source: backend/app/api/forecast.py</i>',10,13,TA_LEFT,14)
heading('<b>Reproducible execution</b>')
para('Install the Python requirements into the project virtual environment, install the frontend dependencies, and run <font name="Courier" size="10">npm run dev</font> from the project root. The Settings screen provides schema examples and the demo-data action. The training pipeline writes the evaluation JSON and customer-model artifact into the models directory. The README records the complete setup and verification commands.',11.5,15);end()
start('5. RESULTS AND INFERENCES',number=10)
heading('<b>5.1 Model Evaluation</b>')
para('The saved evaluation uses the dataset through 18 October 2026. Table 5.1 reports daily-unit MAE over the latest 14 days, rounded to three decimals. Lower values indicate smaller absolute errors.',11,14,gap=8)
E=json.loads((ROOT/'models/evaluation.json').read_text());keys=['ma','prophet','xgboost','lightgbm','ensemble']
rows=[['<b>Category</b>','<b>MA</b>','<b>Prophet</b>','<b>XGB</b>','<b>LGBM</b>','<b>Ensemble</b>']]
for cat,val in E['categories'].items():rows.append([cat]+[f"{val['model_metrics'][k]['mae']:.3f}" for k in keys])
means={k:sum(v['model_metrics'][k]['mae'] for v in E['categories'].values())/8 for k in keys};rows.append(['<b>Category mean</b>']+[f'<b>{means[k]:.3f}</b>' for k in keys])
para('<b>Table 5.1 Category forecast MAE on the holdout</b>',10,13,TA_CENTER,6);table(rows,[129,51,59,51,55,84],9.3)
para('MA denotes moving average; XGB and LGBM denote XGBoost and LightGBM. The mean is an unweighted average across categories, not a pooled sales-weighted metric. The ensemble has the lowest category MAE for Toys and Games, while other categories favour individual models. Sparse daily demand also produces WMAPE above 100% for some models and categories. These results do not justify claiming universal superiority.',10.8,14,gap=9)
V=E['purchase_propensity']['validation'];para('<b>Table 5.2 Purchase propensity validation</b>',10,13,TA_CENTER,6)
table([['<b>Measure</b>','<b>Observed value</b>'],['Later-window examples / positive rate',f"{V['examples']:,} / {V['positive_rate']*100:.2f}%"],['ROC AUC',f"{V['roc_auc']:.4f}"],['Brier score / constant baseline',f"{V['brier_score']:.5f} / {V['constant_baseline_brier']:.5f}"],['Examples used in final refit',f"{E['purchase_propensity']['training_examples']:,}"]],[260,169],10)
para('The lower Brier score than the constant baseline indicates improved squared-probability error on this window. ROC AUC measures ranking, not percentage accuracy. Neither result establishes calibration or commercial benefit on real customers. Values are sourced from models/evaluation.json.',10.8,14);end()
screens=[
 ('Retail overview','frontend/test-results/overview-desktop.png','5.1 Retail overview dashboard',
  'The Overview screen connects the imported data to summary indicators, daily demand and category performance. The captured dataset contains 120 customers, 24 products, 1,481 order rows and 12,039 behaviour events. The 30-day demand estimate is based on the recent daily average, while recorded revenue summarizes eligible historical sales.',
  'The displayed as-of date identifies the end of the dataset. Historical revenue and estimated future demand refer to different periods and should not be compared as if they were the same measure.'),
 ('Demand forecast','frontend/test-results/forecast-desktop.png','5.2 Demand forecasting and model validation',
  'The Forecast screen supports product and category selection, a 1-90 day horizon and the five model options. This screenshot shows a seven-day moving-average category forecast. Historical demand, predicted values and approximate residual ranges are presented together, with held-out error measures below the chart.',
  'The user can compare model validation metrics and download the forecast as CSV. Predictions begin after the last observed dataset date; the interface does not present an old dataset as current demand.'),
 ('Customer analysis','tmp/pdfs/screen-customer.png','5.3 Customer recommendations and explanation',
  'This viewport excerpt shows a selected customer\'s recommended products, purchase probabilities, expected quantities and expected revenue. Expanding a prediction displays the strongest positive and negative linear model contributions. Customer search supports name, email and customer ID.',
  'The explanation describes the 30-day logistic-regression score in log-odds units. It identifies associations used by the fitted model, such as prior product activity and category affinity. It does not prove that changing a feature would cause a purchase. The full customer page also includes recent activity.'),
 ('Data import','tmp/pdfs/screen-settings.png','5.4 Dataset import and status interface',
  'The Settings screen displays database counts and provides upload controls for customers, products, promotions, events and orders. Schema examples and downloadable CSV templates guide preparation. The screenshot shows the existing demonstration data and the beginning of the upload form.',
  'Validation failures return row-specific feedback. An invalid file does not partially update the other supplied files. The demo action is restricted to an empty database, and repeated IDs update existing records instead of adding duplicates. The workflow keeps data preparation visible to the user.'),
 ('Customer segments','tmp/pdfs/screen-segments.png','5.5 Customer segmentation interface',
  'The Segments screen displays the distribution of behaviour-based groups and their summary RFM measures. In the captured demonstration, 120 customers are assigned to five labelled groups, including 25 at-risk customers. Cards provide recommendations and access to paginated customer lists.',
  'Labels summarize observed activity and rule-based overrides. They are not validated predictions of future churn or guaranteed responses to a promotion. The interface is intended to help users identify groups for further investigation.'),
 ('Inventory insights','tmp/pdfs/screen-insights.png','5.6 Inventory planning interface',
  'The Insights screen combines stock, recent daily demand and the selected planning horizon. The captured 30-day view identifies 13 stockout risks, eight overstock risks and 412 suggested reorder units. The product table exposes stock, expected demand, risk and demand trend for review.',
  'These outputs are deterministic planning estimates from the snapshot. Potential demand revenue multiplies projected units by price; it is not guaranteed future revenue. Reorder suggestions exclude supplier lead times, inbound orders and historical stockout censoring, and never execute a purchase order.')]
for i,(name,path,caption,a,b) in enumerate(screens):
 start('5.2 Application Outputs' if i==0 else '5.2 Application Outputs (continued)',number=11+i);heading('<b>'+name+'</b>');picture(ROOT/path,'<b>Figure '+caption+'</b>',maxh=440 if i!=1 else 455);para(a,11,14,gap=10);para(b,11,14);end()
start('5.3 Testing and Verification',number=17)
para('Verification combined backend tests with an end-to-end browser workflow. The backend suite checked API behaviour, data import integrity and model edge cases. Browser checks exercised user-facing actions on the demonstration database rather than relying only on isolated component tests.')
para('<b>Table 5.3 Verification summary</b>',10,13,TA_CENTER,8)
table([['<b>Area</b>','<b>Checks and observed outcome</b>'],['Backend suite','32 pytest tests passed across API, import and model tests.'],['Import integrity','Invalid schemas and references rejected; transactional behaviour, duplicate IDs and unsafe values covered.'],['Browser workflow','One comprehensive Playwright workflow passed across six screens, downloads, import rejection and responsive navigation.'],['Presentation','Desktop screenshots and a mobile dark-theme screenshot captured from the running application.'],['Static checks','TypeScript/production build, ESLint, formatting and Ruff checks passed during project completion.'],['Dependency checks','npm and Python dependency audits reported no findings at the time of verification.'],['Container configuration','Dockerfiles and compose configuration are included; container execution was not verified because Docker was unavailable.']],[105,324],10.5)
heading('<b>Inference from verification</b>')
para('The checks support that the implemented workflow runs on the local demonstration environment and handles the tested invalid inputs. They do not establish unlimited dataset capacity, security against all attacks, or production reliability. No throughput, latency or large-scale load benchmark was performed.')
para('Evaluation data, model settings and screenshots are retained with the project. The saved JSON provides machine-readable forecast and purchase-model metrics. Re-running the generator with a different end date or importing different records will change the outputs, so comparisons must record the dataset snapshot as well as the random seed.');end()
start('6. CONCLUSION AND FUTURE SCOPE',number=18)
heading('<b>6.1 Conclusion</b>')
para('DemandPredict provides a complete local workflow for importing retail records and analysing demand, customer purchase propensity, behavioural segments and inventory needs. React and FastAPI connect the analytical modules to an interactive interface, while SQLite and validated transactional imports maintain consistent source data.')
para('The project implements several forecasting approaches with chronological validation rather than presenting a single unsupported accuracy claim. Results on the demonstration dataset show that the best forecast method depends on the category. The logistic-regression customer model improves Brier score over a constant-probability baseline on its validation window and provides interpretable linear feature contributions.')
para('The application also demonstrates practical engineering requirements: input validation, dataset-aware model caching, error and empty states, responsive navigation, CSV export and automated verification. These features make the analytical workflow repeatable and accessible for project demonstration and further development.')
para('The evidence remains limited to synthetic data and a local environment. Approximate forecast bands, constant-hazard probability conversion and inventory rules rely on simplifying assumptions. The system supports informed human review; it does not establish business gains or replace operational judgement.')
heading('<b>6.2 Future Scope</b>')
para('Future evaluation should use authorized real retail history, multiple chronological backtests and category-specific baselines for intermittent demand. Calibration checks and measured forecast-interval coverage would improve interpretation. Promotion, price and external calendar effects could be added where reliable historical features are available.')
para('Inventory planning can be extended with supplier lead times, service-level objectives, inbound purchase orders and stockout-censored demand. Customer models can be monitored for drift and assessed using outcomes from appropriately designed business experiments.')
para('For broader deployment, the application requires authentication, authorization, HTTPS, managed secrets, backups and privacy controls. Background model jobs, scalable storage and caching would support larger datasets. Container execution and deployment tests should be completed before claiming operational readiness.');end()
start('REFERENCES',number=19)
refs=[
 '[1] S. J. Taylor and B. Letham, <i>Forecasting at Scale</i>, PeerJ Preprints, 2017. DOI: 10.7287/peerj.preprints.3190v2. <link href="https://peerj.com/preprints/3190/">https://peerj.com/preprints/3190/</link>',
 '[2] T. Chen and C. Guestrin, <i>XGBoost: A Scalable Tree Boosting System</i>, Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 2016. DOI: 10.1145/2939672.2939785. <link href="https://arxiv.org/abs/1603.02754">https://arxiv.org/abs/1603.02754</link>',
 '[3] G. Ke, Q. Meng, T. Finley, T. Wang, W. Chen, W. Ma, Q. Ye and T.-Y. Liu, <i>LightGBM: A Highly Efficient Gradient Boosting Decision Tree</i>, Advances in Neural Information Processing Systems 30, 2017. <link href="https://proceedings.neurips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html">NeurIPS 2017 proceedings (online)</link>.',
 '[4] S. M. Lundberg and S.-I. Lee, <i>A Unified Approach to Interpreting Model Predictions</i>, Advances in Neural Information Processing Systems 30, 2017. <link href="https://arxiv.org/abs/1705.07874">https://arxiv.org/abs/1705.07874</link>',
 '[5] DemandPredict project repository, <i>Implementation and operating instructions</i>, local source snapshot, October 2026. Key files: README.md; ml/forecasting.py; ml/recommendations.py; backend/app/services/analytics.py; backend/app/services/upload_service.py.',
 '[6] DemandPredict project repository, <i>Saved model evaluation</i>, models/evaluation.json, data as of 18 October 2026. Contains category forecast metrics, validation settings and purchase-propensity results.',
 '[7] DemandPredict project repository, <i>Verification sources and application captures</i>, tests/test_api.py; tests/test_imports.py; tests/test_models.py; frontend/e2e/workflows.spec.ts; frontend/test-results. Screenshots used in this report were captured from the running demonstration application.'
]
for r in refs:para(r,11,15,gap=17)
para('Online research references accessed 19 October 2026. Project results refer to the saved demonstration-data snapshot and the local implementation described in this report.',10,14);end()
C.save()
final=fitz.open(OUT/'DemandPredict_Project_Report.pdf')
final.set_toc([[1,'Front matter',1],[2,'Certificate',3],[2,'Declaration',4],[2,'Acknowledgement',5],[2,'Contents',6],[1,'Abstract',7],[1,'List of figures and tables',8],[1,'1. Introduction',9],[1,'2. System Analysis and Design',10],[1,'3. Proposed System',11],[1,'4. Project Description',12],[2,'Dataset',12],[2,'Methodology',13],[2,'Implementation',16],[1,'5. Results and Inferences',18],[2,'Application Outputs',19],[2,'Testing and Verification',25],[1,'6. Conclusion and Future Scope',26],[1,'References',27]])
final.saveIncr();final.close()
(TMP/'layout-audit.json').write_text(json.dumps(audit,indent=2));print('Created',OUT/'DemandPredict_Project_Report.pdf','pages',page_num)
