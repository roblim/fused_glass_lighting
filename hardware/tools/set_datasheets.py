#!/usr/bin/env python3
"""Fill the Datasheet field of every purchased part in the G2 schematic and board.

usage: set_datasheets.py fgl_g2.kicad_sch fgl_g2.kicad_pcb

Each part is matched by its LCSC number; the URL is the PDF itself, not a viewer page, so
tools that fetch datasheets (Flux, Pinscope, KiCad's "show datasheet") get the document.
Links checked 2026-10-28: each returned a PDF. The datasheet.lcsc.com links are LCSC's own
copies; TPS61500 points at TI's always-current copy. www.lcsc.com/datasheet/C<n>.pdf was
not used: it returns an HTML viewer page. Test points and mounting holes are left empty
(bare copper, nothing to buy). Only text in the files changes, nothing on any copper or
silkscreen layer: the Datasheet field is hidden.
"""
import re, sys

LCSC_PDF = 'https://datasheet.lcsc.com/datasheet/pdf/{}.pdf'
BY_LCSC = {
    'C1002':     LCSC_PDF.format('2ee1ae86058050beca731857aa44a9ba'),   # Sunlord GZ1608D601TF
    'C14663':    LCSC_PDF.format('23ccee80ee542e7cf156a772bb589942'),   # Yageo CC0603KRX7R9BB104
    'C15127':    LCSC_PDF.format('fee353dd1e9e0bc90b295f14f381aa4c'),   # AOS AO3401A
    'C15725':    LCSC_PDF.format('02336ea48ea44ca18c72517dd3cb7b47'),   # Samsung CL10B104KC8NNNC
    'C157923':   LCSC_PDF.format('6c6fce4367275d84ec6a99bf09f1250f'),   # JST S5B-PH-K-S
    'C157926':   LCSC_PDF.format('6c6fce4367275d84ec6a99bf09f1250f'),   # JST S4B-PH-K-S
    'C15849':    LCSC_PDF.format('02336ea48ea44ca18c72517dd3cb7b47'),   # Samsung CL10A105KB8NNNC
    'C15850':    LCSC_PDF.format('02336ea48ea44ca18c72517dd3cb7b47'),   # Samsung CL21A106KAYNNNE
    'C165948':   LCSC_PDF.format('9e56b777c022540fcce7c7f67825f55e'),   # HRO TYPE-C-31-M-12
    'C178260':   LCSC_PDF.format('e2079ce6902d97aebf17ffdc9542d2e7'),   # Jingdao SMF6.0A
    'C20917':    LCSC_PDF.format('130876b936da464599428c58fd8de8f6'),   # AOS AO3400A
    'C2480':     LCSC_PDF.format('9977bb85cd7e349115b7bcb7054cfa0d'),   # MDD SS14
    'C269137':   LCSC_PDF.format('39c533899a45d694a011d998323027fc'),   # Brightking SMD1812B150TF/8 (F1 until 2026-10-29)
    'C269145':   'https://www.mouser.com/datasheet/2/447/2017100920153415341360-1516460.pdf',   # Brightking SMD1812 series (F1: SMD1812B200TF/16), incl. derating table
    'C27985230': LCSC_PDF.format('97630011e3af48d00af22e1a04d60729'),   # Hong Cheng HC-PM254-5.0H-1x5PZ
    'C27985232': LCSC_PDF.format('459ae8ff1ec8327b929b62e0d4d9ab63'),   # Hong Cheng HC-PM254-5.0H-1x7PZ
    'C2903825':  LCSC_PDF.format('e8a285a15b5ef18869dfc48bcc8570f5'),   # LGE SS36
    'C2962951':  LCSC_PDF.format('edf099acf8994a482e4343677e6896d8'),   # JILN JL212R-35003B01 (J5-J8 alternate)
    'C7603454':  'https://atta.szlcsc.com/upload/public/pdf/source/20230907/20A31750C0F42741679442E51C870286.pdf?Expires=4070880000&OSSAccessKeyId=LTAIJDIkh7KmGS1H&Signature=bC5y63SvwdXcuwa1uZSa1Htf5PQ%3D&response-content-disposition=attachment%3Bfilename%3DC7603454_%25E5%25BC%25B9%25E7%25B0%25A7%25E5%25BC%258F%25E6%258E%25A5%25E7%25BA%25BF%25E7%25AB%25AF%25E5%25AD%2590_DG212R-THR-3.5-03P-13-1000A%2528H%2529_%25E8%25A7%2584%25E6%25A0%25BC%25E4%25B9%25A6_WJ458111.PDF',   # DEGSON DG212R-THR-3.5-03P (J5-J8 since 2026-10-29)
    'C37429':    LCSC_PDF.format('dc27f0913034a1bfb18554ababd47a88'),   # Sunlord SWPA8040S100MT
    'C49257':    LCSC_PDF.format('d52c83a07830c4e9e9a614accc55f5cd'),   # BOOMELE 2.54-1*3P
    'C576517':   LCSC_PDF.format('a5661d5fbdf2b41a50853cb83d84d655'),   # Murata GRM32EC72A106KE05L
    'C71160':    'https://www.ti.com/lit/ds/symlink/tps61500.pdf',      # TI TPS61500PWPR
    'C89632':    LCSC_PDF.format('a1390a51092e4f3c84866ab492516a00'),   # Samsung CL31B106KBHNNNE (C4 until 2026-10-29)
    'C13585':    LCSC_PDF.format('02336ea48ea44ca18c72517dd3cb7b47'),   # Samsung CL31A106KBHNNNE (C4, basic part)
}
UNI_ROYAL = LCSC_PDF.format('0a975aaa49b7c97f38a963127be4a823')     # one sheet for all UNI-ROYAL chip resistors
for c in ('C21190', 'C22775', 'C23186', 'C23254', 'C25803', 'C25804', 'C25805', 'C25808', 'C25819',
          'C30568', 'C4190', 'C53728'):
    BY_LCSC[c] = UNI_ROYAL
BY_REF = {'U1': 'https://wiki.seeedstudio.com/XIAO_ESP32C3_Getting_Started/'}   # XIAO: no LCSC number


def fill(text, block_re, ref_urls=None):
    """Set Datasheet in each block; by LCSC number (schematic) or by reference (board)."""
    done, missing, urls = [], [], {}

    def one(m):
        blk = m.group(0)
        ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
        if ref_urls is not None:
            url = ref_urls.get(ref)
        else:
            lc = re.search(r'\(property "LCSC" "([^"]*)"', blk)
            url = BY_REF.get(ref) or (BY_LCSC.get(lc.group(1)) if lc else None)
            if not url and lc and lc.group(1):
                missing.append(ref)
        if not url:
            return blk
        done.append(ref); urls[ref] = url
        return re.sub(r'\(property "Datasheet" "[^"]*"', f'(property "Datasheet" "{url}"', blk, count=1)
    return re.sub(block_re, one, text, flags=re.S), done, missing, urls


def main(sch, pcb):
    s = open(sch).read()
    # placed symbols (not the lib_symbols cache): top-level "(symbol\n\t\t(lib_id ...)" blocks
    s, done, missing, urls = fill(s, r'\n\t\(symbol\n\t\t\(lib_id "[^"]+"\).*?\n\t\)')
    open(sch, 'w').write(s)
    print(f'{sch}: {len(done)} symbols set; LCSC numbers without a URL: {missing}')
    # the board's footprints carry the same field (what "Update PCB from Schematic" would copy)
    p = open(pcb).read()
    p, done, _, _ = fill(p, r'\n\t\(footprint "[^"]+".*?\n\t\)', ref_urls=urls)
    open(pcb, 'w').write(p)
    print(f'{pcb}: {len(done)} footprints set')


if __name__ == '__main__':
    main(*sys.argv[1:3])
