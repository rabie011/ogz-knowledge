#!/usr/bin/env python3
"""Build two PDFs: System Overview + Caption Consultation Brief. OGZ branded."""
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, HRFlowable)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# OGZ brand
BLACK = colors.HexColor("#000000")
GOLD = colors.HexColor("#F0BE5E")
STEEL = colors.HexColor("#9FAABA")
DARK = colors.HexColor("#1a1a1a")
LIGHT = colors.HexColor("#f5f5f5")

# Arabic font
pdfmetrics.registerFont(TTFont("Arabic", "/Library/Fonts/Arial Unicode.ttf"))

def ar(text):
    """Shape Arabic for correct RTL display in reportlab."""
    return get_display(arabic_reshaper.reshape(text))

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=20, textColor=BLACK,
                    spaceAfter=6, spaceBefore=12)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#7a5c1e"),
                    spaceAfter=4, spaceBefore=14)
BODY = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10.5, leading=16, textColor=DARK)
SMALL = ParagraphStyle("Small", parent=styles["Normal"], fontSize=9, leading=13, textColor=colors.HexColor("#555"))
ARAB = ParagraphStyle("Arab", parent=styles["Normal"], fontName="Arabic", fontSize=11,
                      leading=20, alignment=TA_RIGHT, textColor=DARK)
ARAB_SM = ParagraphStyle("ArabSm", parent=styles["Normal"], fontName="Arabic", fontSize=9.5,
                         leading=16, alignment=TA_RIGHT, textColor=colors.HexColor("#444"))
BULLET = ParagraphStyle("Bullet", parent=BODY, leftIndent=14, bulletIndent=4, spaceAfter=3)


def hr():
    return HRFlowable(width="100%", thickness=1, color=GOLD, spaceBefore=6, spaceAfter=6)

def cover(title, subtitle, tagline):
    el = []
    el.append(Spacer(1, 4*cm))
    el.append(Paragraph(f'<b>OGZ</b>', ParagraphStyle("Logo", fontSize=42, textColor=GOLD, alignment=TA_CENTER)))
    el.append(Paragraph('CONTENT INTELLIGENCE', ParagraphStyle("LogoSub", fontSize=14, textColor=STEEL,
              alignment=TA_CENTER, spaceAfter=40, leading=20)))
    el.append(Spacer(1, 2*cm))
    el.append(Paragraph(title, ParagraphStyle("CTitle", fontSize=26, textColor=BLACK, alignment=TA_CENTER, leading=32)))
    el.append(Spacer(1, 0.4*cm))
    el.append(Paragraph(subtitle, ParagraphStyle("CSub", fontSize=13, textColor=colors.HexColor("#7a5c1e"), alignment=TA_CENTER)))
    el.append(Spacer(1, 1.5*cm))
    el.append(Paragraph(tagline, ParagraphStyle("CTag", fontSize=10.5, textColor=colors.HexColor("#666"),
              alignment=TA_CENTER, leading=16)))
    el.append(Spacer(1, 3*cm))
    el.append(Paragraph("OGZ Studios LLC · Riyadh · Confidential", ParagraphStyle("CFoot", fontSize=9,
              textColor=STEEL, alignment=TA_CENTER)))
    el.append(Paragraph("June 2026", ParagraphStyle("CDate", fontSize=9, textColor=STEEL, alignment=TA_CENTER)))
    el.append(PageBreak())
    return el

def kv_table(rows, col_widths=None):
    t = Table(rows, colWidths=col_widths or [6*cm, 10*cm])
    t.setStyle(TableStyle([
        ("FONTSIZE", (0,0), (-1,-1), 9.5),
        ("TEXTCOLOR", (0,0), (0,-1), BLACK),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("TEXTCOLOR", (1,0), (1,-1), DARK),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("LINEBELOW", (0,0), (-1,-1), 0.4, colors.HexColor("#ddd")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    return t

def data_table(rows, col_widths, header=True):
    t = Table(rows, colWidths=col_widths)
    style = [
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("TEXTCOLOR", (0,0), (-1,-1), DARK),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#e0e0e0")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]
    if header:
        style += [("BACKGROUND", (0,0), (-1,0), BLACK), ("TEXTCOLOR", (0,0), (-1,0), GOLD),
                  ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold")]
    t.setStyle(TableStyle(style))
    return t

def b(text): return Paragraph(f"•  {text}", BULLET)


# ════════════════════════════════════════════════════════════════════
# PDF 1 — SYSTEM OVERVIEW
# ════════════════════════════════════════════════════════════════════
def build_overview():
    el = cover("System Overview", "What we built, how it works, where we are",
               "A Saudi-native creative intelligence platform — proprietary real engagement data<br/>fused with cultural methodology — built by OGZ Studios.")

    el.append(Paragraph("1.  What it is", H1)); el.append(hr())
    el.append(Paragraph("OGZ Content Intelligence is a <b>Saudi-native creative intelligence platform</b>. "
        "It turns thousands of real, verified Saudi Instagram posts into a knowledge base that helps Saudi "
        "brands produce better Arabic content — faster, and culturally correct.", BODY))
    el.append(Spacer(1,6))
    el.append(Paragraph("The moat, in one line:", H2))
    el.append(Paragraph("<b>Real Saudi engagement data + Saudi cultural intelligence.</b> No competitor can buy this — "
        "it is built observation by observation. A foreign tool translating English to Arabic cannot replicate it.", BODY))

    el.append(Paragraph("2.  Where we are today", H1)); el.append(hr())
    el.append(kv_table([
        ["Observations", "6,888 real Saudi Instagram posts (60 brands, 23 with verified likes)"],
        ["Templates", "5,014 caption templates (3,077 with REAL engagement numbers)"],
        ["Brain", "v4.0 — 18 knowledge sections, 10 Saudi occasions, cultural guardrails"],
        ["Creative Directors", "5 CD-brain methodologies (creative techniques, not generic prompts)"],
        ["API", "21 endpoints on a FastAPI server — any system can call it"],
        ["Quality gate", "11 automated checks incl. Saudi cultural red lines + length"],
        ["Validation", "Human review by Mohamed — the only trusted quality signal"],
        ["Status", "Foundation tagged v1.0.0. Caption quality: in active improvement."],
    ]))

    el.append(Paragraph("3.  How it works — the six layers", H1)); el.append(hr())
    el.append(Paragraph("A request flows through six layers. Each adds intelligence the layer below cannot.", BODY))
    el.append(Spacer(1,4))
    el.append(data_table([
        ["Layer", "What it does"],
        ["1. Real data", "6,888 verified Saudi posts — captions, likes, visuals, occasion, sector"],
        ["2. Brain", "Aggregated intelligence: brand voice, Saudi dialect rules, occasions, guardrails"],
        ["3. Templates", "Real high-engagement captions, tiered by likes (gold/silver/bronze)"],
        ["4. CD brains", "5 creative-director methodologies route by sector + occasion"],
        ["5. Engine", "Generates the caption: brain context + real templates + CD technique"],
        ["6. Quality gate", "11 checks: Saudi dialect, product names, cultural red lines, length"],
    ], [3.6*cm, 12.4*cm]))
    el.append(Spacer(1,6))
    el.append(Paragraph("Every output is grounded in <b>real Saudi captions</b> (not invented), shaped by a "
        "<b>named creative methodology</b> (not a generic prompt), and screened by a <b>cultural gate</b> "
        "that hard-blocks anything outside Saudi norms.", BODY))

    el.append(Paragraph("4.  Why it matters", H1)); el.append(hr())
    el.append(b("<b>Proprietary & defensible.</b> The data is owned, verified, and grows with every extraction. It is the difference between a fal.ai wrapper and a real platform."))
    el.append(b("<b>Culturally correct by design.</b> Saudi dialect (not Gulf-generic), Saudi occasions, and hard cultural red lines are built in — not bolted on."))
    el.append(b("<b>Proof-first.</b> Every caption can show which real post it learned from, and that post's real likes. Answers the 'is the data fake?' question directly."))
    el.append(b("<b>Two pipelines.</b> Self-service for SMEs (Pipeline A) and managed AI-creative for enterprise brands (Pipeline B)."))

    el.append(Paragraph("5.  How it works with any system", H1)); el.append(hr())
    el.append(Paragraph("The platform is <b>file-first and API-exposed</b>, so it plugs into anything:", BODY))
    el.append(b("<b>Files are the source of truth.</b> The whole knowledge base is versioned JSON/YAML in Git — portable, auditable, syncable to any database (Postgres today)."))
    el.append(b("<b>One HTTP call.</b> <font face='Courier'>POST /api/create {brand, product, occasion}</font> returns caption + creative direction + proof. Any app, CMS, or bot can integrate in minutes."))
    el.append(b("<b>Model-agnostic.</b> The intelligence lives in the data + methodology, not the model. We proved a cheap model + good knowledge matches an expensive one."))
    el.append(b("<b>Self-documenting.</b> A 24/7 daemon keeps system state fresh; the knowledge map is readable by any new engineer or partner."))

    el.append(Paragraph("6.  The quality bar we are seeking", H1)); el.append(hr())
    el.append(Paragraph("A caption is acceptable only when a <b>Saudi creative director would approve it</b>. Concretely:", BODY))
    el.append(b("<b>Sounds Saudi</b> — real Najdi/Hejazi dialect markers, never Gulf-generic or stiff MSA."))
    el.append(b("<b>Culturally safe</b> — passes hard red lines (no clothing/veil removal, no bedroom scenes, no exploiting vulnerability)."))
    el.append(b("<b>Short & coherent</b> — one or two sentences, no rambling. Length capped per sector."))
    el.append(b("<b>On-brand & on-occasion</b> — correct product name, brand voice, occasion keywords."))
    el.append(b("<b>Genuinely creative</b> — applies a real creative technique, not generic marketing copy."))

    el.append(Paragraph("7.  Honest status", H1)); el.append(hr())
    el.append(Paragraph("The <b>foundation is strong</b> (data, brain, templates, API, cultural gate). "
        "Caption <b>creative quality is not yet at the bar</b> — validated by human review: in a blind rating of 30 "
        "captions, only 5 were approved. We learned that automated AI scoring is unreliable for Saudi cultural "
        "quality, so <b>human review is now the single source of truth</b>. The next phase is a focused push on "
        "caption quality — see the companion Consultation Brief.", BODY))

    return el


# ════════════════════════════════════════════════════════════════════
# PDF 2 — CAPTION CONSULTATION BRIEF
# ════════════════════════════════════════════════════════════════════
def build_consultation():
    el = cover("Caption Consultation Brief",
               "How do we make Saudi captions a creative director approves?",
               "A complete, self-contained brief for an external AI/creative consultant.<br/>"
               "Everything you need to advise us — assets, methods, what we tried, and the verdict.")

    el.append(Paragraph("The objective", H1)); el.append(hr())
    el.append(Paragraph("We generate Arabic Instagram captions for Saudi brands. They are technically valid but "
        "<b>a Saudi creative director (Mohamed) rates ~83% of them weak or fail</b>. We want to know: <b>how do we "
        "consistently generate captions a Saudi creative director would approve?</b> This brief gives you our full "
        "context so you can advise — on methodology, prompting, architecture, or model strategy.", BODY))

    el.append(Paragraph("What we have (the assets)", H1)); el.append(hr())
    el.append(kv_table([
        ["Real data", "6,888 verified Saudi IG posts; 3,077 captions with real likes"],
        ["Templates", "5,014 caption templates, tiered by real engagement"],
        ["Brand brain", "Voice, product names, signature hashtags for 23+ brands"],
        ["Dialect rules", "Saudi (Najdi/Hejazi) markers to use; Gulf/MSA words to avoid"],
        ["Occasions", "10 Saudi occasions w/ required words (Ramadan, founding day, etc.)"],
        ["5 CD methodologies", "Creative-director techniques (detailed below)"],
        ["Quality gate", "11 automated checks (dialect, product name, red lines, length)"],
    ]))

    el.append(Paragraph("The 5 Creative Director methodologies", H1)); el.append(hr())
    el.append(Paragraph("Each caption is routed (by sector + occasion) to one of five creative techniques:", BODY))
    el.append(Spacer(1,4))
    el.append(data_table([
        ["CD brain", "Core technique"],
        ["Firaasa Architect", "Why-before-what — name the Saudi cultural truth first"],
        ["Metaphor Architect", "Build a full metaphor system, then a 'but wait' reveal"],
        ["Authenticity Detective", "Two-scene contrast: how people perform vs how they feel"],
        ["Heritage Decoder", "A double-meaning Arabic word as the structural key"],
        ["Paradox Hunter", "A counterintuitive flip; the product as the mechanism"],
    ], [4.5*cm, 11.5*cm]))

    el.append(Paragraph("How a caption is generated now", H1)); el.append(hr())
    el.append(b("1. Route the brief (brand, product, occasion) to a CD methodology."))
    el.append(b("2. Pull 3-5 real high-engagement Saudi captions (templates) for that sector + occasion."))
    el.append(b("3. Build a prompt: brand voice + real templates + the CD technique + Saudi dialect rules + cultural red lines + length cap."))
    el.append(b("4. Generate with an LLM (gpt-4o-mini; we tested gpt-4o — no consistent gain)."))
    el.append(b("5. Screen through the quality gate (dialect, product name, red lines, length)."))

    el.append(PageBreak())
    el.append(Paragraph("The human verdict — what's actually wrong", H1)); el.append(hr())
    el.append(Paragraph("Mohamed rated 30 captions blind. Result: <b>1 excellent, 4 good, 13 weak, 12 fail.</b> "
        "His notes revealed three concrete problems:", BODY))
    el.append(Spacer(1,4))
    el.append(Paragraph("<b>1. Too long</b> — the #1 complaint (10 of 18 notes: 'too long', 'long and incoherent', 'boring'). "
        "Captions ran 300-400 characters. <i>(Fixed: hard length cap, now 116-172.)</i>", BODY))
    el.append(Paragraph("<b>2. Cultural red lines violated</b> — these are absolute:", BODY))
    el.append(Paragraph(ar("• ممنوع ذكر إزالة أي ملابس أو الخمار/الحجاب"), ARAB_SM))
    el.append(Paragraph(ar("• ممنوع مشاهد السرير أو غرفة النوم"), ARAB_SM))
    el.append(Paragraph(ar("• ممنوع استغلال ضعف الناس أو هشاشتهم كخطّاف"), ARAB_SM))
    el.append(Paragraph("<i>(Fixed: hard-blocked in the quality gate.)</i>", SMALL))
    el.append(Paragraph("<b>3. The Authenticity Detective technique was the offender</b> — its 'performance vs reality' "
        "two-scene structure generated long, intimate, inappropriate scenes (removing a veil, family on a bed). "
        "<i>(Fixed: constrained to public scenes.)</i>", BODY))

    el.append(Paragraph("Example — a FAIL (before fixes)", H2))
    el.append(Paragraph(ar("قهوة مختصة، لمّا تشعر بالجوع بعد يوم طويل من الصيام، تخيل اللحظة اللي تفك فيها الخمار وتقول: أخيرًا وقت الإفطار!"), ARAB_SM))
    el.append(Paragraph("Mohamed's note: \"we cannot use removing clothing in any caption.\" The AI judge scored this 6.8/10.", SMALL))
    el.append(Paragraph("Example — an APPROVED (excellent)", H2))
    el.append(Paragraph(ar("في مشروع سكني، يُستحضر التاريخ من عمق الأرض، حيث تُبنى البيوت لتكون ملاذًا وذكريات تُروى. في يوم التأسيس، نحتفل بجذورنا."), ARAB_SM))
    el.append(Paragraph("Heritage Decoder — coherent heritage narrative, culturally safe, on-occasion.", SMALL))

    el.append(Paragraph("A critical finding: AI cannot judge this", H1)); el.append(hr())
    el.append(Paragraph("We built an AI 'methodology judge' (gpt-4o) to score captions. We validated it against "
        "Mohamed's ratings. <b>It scored essentially random</b> (rank correlation +0.08; 47% agreement). It gave "
        "~6/10 to everything regardless of quality — including the culturally-forbidden captions. "
        "<b>Conclusion: automated AI scoring is not trustworthy for Saudi creative/cultural quality. Human review "
        "is the only ground truth.</b> Any solution you propose must be measurable against a human, not an AI judge.", BODY))

    el.append(Paragraph("What real Saudi engagement tells us", H1)); el.append(hr())
    el.append(Paragraph("We analyzed 300 of the highest-engagement real Saudi captions through the 5 techniques:", BODY))
    el.append(Spacer(1,4))
    el.append(data_table([
        ["Technique used", "Share", "Avg likes", "vs avg"],
        ["Counterintuitive flip", "19%", "6,593", "+35%"],
        ["Plain marketing (none)", "9%", "5,084", "+4%"],
        ["Double-meaning word", "10%", "4,920", "+1%"],
        ["Metaphor system", "13%", "4,912", "+1%"],
        ["Human-truth opening", "48%", "4,124", "-15%"],
    ], [6*cm, 2.5*cm, 3*cm, 2.5*cm]))
    el.append(Spacer(1,4))
    el.append(Paragraph("Insight: 91% of winning Saudi captions use a creative technique. The counterintuitive flip "
        "drives the most engagement but is underused; the emotional 'human-truth' opening is overused and underperforms.", SMALL))

    el.append(Paragraph("Questions for you (the consultant)", H1)); el.append(hr())
    el.append(b("<b>Methodology:</b> Are these 5 CD techniques the right framework for short social captions, or are some (e.g. the two-scene Authenticity Detective) better suited to video than to a 150-char caption?"))
    el.append(b("<b>Prompting:</b> Given real templates + a named technique + dialect rules, what prompt architecture most reliably produces short, coherent, culturally-safe, genuinely-creative Saudi copy?"))
    el.append(b("<b>Length vs depth:</b> How do we keep a real creative technique (e.g. a double-meaning word) while staying under ~150 characters?"))
    el.append(b("<b>Model strategy:</b> We found gpt-4o didn't beat gpt-4o-mini with our prompt. Is that a prompt ceiling, or should we fine-tune a Saudi-dialect model?"))
    el.append(b("<b>The loop:</b> Human review is our only trusted signal but doesn't scale. How do we build a learning loop that improves quality without a reliable automated judge?"))

    el.append(Paragraph("What success looks like", H1)); el.append(hr())
    el.append(Paragraph("A batch of 30 fresh captions, rated blind by a Saudi creative director, where <b>the large "
        "majority are 'good' or 'excellent'</b> — short, culturally safe, on-brand, and genuinely creative. "
        "Today that number is 5 of 30. That is the gap to close.", BODY))

    return el


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(STEEL)
    canvas.drawString(2*cm, 1.1*cm, "OGZ Studios · Confidential")
    canvas.drawRightString(19*cm, 1.1*cm, f"{doc.page}")
    canvas.setStrokeColor(GOLD); canvas.setLineWidth(0.5)
    canvas.line(2*cm, 1.4*cm, 19*cm, 1.4*cm)
    canvas.restoreState()


for name, builder in [("OGZ_System_Overview.pdf", build_overview),
                       ("OGZ_Caption_Consultation.pdf", build_consultation)]:
    doc = SimpleDocTemplate(f"/Users/abarihm/Desktop/ogz-knowledge/docs/{name}",
                            pagesize=A4, topMargin=2*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    doc.build(builder(), onLaterPages=footer)
    print(f"built {name}")
