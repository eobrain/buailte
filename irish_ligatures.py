import fontforge
import sys

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
# Define the mapping of Base char -> Target Unicode for lenition
# Format: 'base_char': (Target Unicode, 'Target Glyph Name')
LOWERCASE_MAP = {
    'b': (0x1e03, 'bdot'),
    'c': (0x020b, 'cdot'),
    'd': (0x1e0b, 'ddot'),
    'f': (0x1e1f, 'fdot'),
    'g': (0x0121, 'gdot'),
    'm': (0x1e41, 'mdot'),
    'p': (0x1e57, 'pdot'),
    's': (0x1e61, 'sdot'),
    't': (0x1e6b, 'tdot'),
}

UPPERCASE_MAP = {
    'B': (0x1e02, 'Bdot'),
    'C': (0x020a, 'Cdot'),
    'D': (0x1e0a, 'Ddot'),
    'F': (0x1e1e, 'Fdot'),
    'G': (0x0120, 'Gdot'),
    'M': (0x1e40, 'Mdot'),
    'P': (0x1e56, 'Pdot'),
    'S': (0x1e60, 'Sdot'),
    'T': (0x1e6a, 'Tdot'),
}

def main(input_font_path, output_font_path):
    print(f"Opening font: {input_font_path}")
    font = fontforge.open(input_font_path)

    # 1. Create the Ligature Lookup Table if it doesn't exist
    lookup_name = "IrishLenition"
    subtable_name = "IrishLenition_subtable"
    
    # Check if 'liga' feature exists, if not create it
    if lookup_name not in font.lookups:
        print("Creating 'liga' lookup table...")
        # Type: gsub_ligature, Feature: liga (standard ligatures)
        font.addLookup(lookup_name, "gsub_ligature", (), (("liga", (("latn", ("dflt")),)),))
        font.addLookupSubtable(lookup_name, subtable_name)
    else:
        # If it exists, we try to grab the first subtable or create one
        subtables = font.getLookupSubtables(lookup_name)
        if subtables:
            subtable_name = subtables[0]
        else:
            font.addLookupSubtable(lookup_name, subtable_name)

    # 2. Process Glyphs
    process_set(font, LOWERCASE_MAP, subtable_name, is_upper=False)
    process_set(font, UPPERCASE_MAP, subtable_name, is_upper=True)

    # 3. Generate Output
    print(f"Generating updated font: {output_font_path}")
    font.generate(output_font_path)
    font.close()

def process_set(font, mapping, subtable, is_upper):
    suffix = 'H' if is_upper else 'h'
    
    for base_char, (uni, name) in mapping.items():
        # A. Create Glyph if missing
        if name not in font:
            print(f"Creating missing glyph: {name} ({base_char} + dot)")
            # Create the char slot
            glyph = font.createChar(uni, name)
            
            # clear any junk
            glyph.clear()
            
            # Add References (Base + Dot)
            # We use 'dotaccent' (U+02D9) usually. 
            # FontForge's "build()" command tries to auto-assemble based on Unicode data
            try:
                # This automatically finds the base and the accent and places them
                glyph.build() 
            except:
                print(f"Warning: Could not auto-build {name}. Check manually.")
                
            # If build() failed to add references (common in cheap fonts), manual fallback:
            if len(glyph.layers['Fore']) == 0:
                if base_char in font and 'dotaccent' in font:
                    glyph.addReference(base_char)
                    glyph.addReference('dotaccent')
                    # Center the dot roughly (simplified)
                    # For a real project, use anchors
        
        else:
            print(f"Glyph {name} already exists. Adding ligature rule only.")
            glyph = font[name]

        # B. Add the Ligature Rule
        # Syntax: replace "Base + h" with "This Glyph"
        # We handle Title Case (Bh) and Lowercase (bh)
        # Note: Uppercase map handles 'BH' -> 'Ḃ'
        
        ligature_source = f"{base_char} {suffix}"
        
        # Check if we also need to handle Title Case (Bh -> Ḃ) inside the Uppercase loop?
        # Actually, standard Irish uses Bh -> Ḃ. 
        # So for the Uppercase map (B), we should bind 'B h' AND 'B H'.
        
        # Bind the primary ligature
        try:
            glyph.addPosSub(subtable, ligature_source)
            print(f"  Added Ligature: {ligature_source} -> {name}")
        except Exception as e:
            print(f"  Error adding ligature for {name}: {e}")

        # If we are processing Uppercase (B), we also want to catch "Bh" (Title case)
        if is_upper:
            mixed_case_source = f"{base_char} h"
            try:
                glyph.addPosSub(subtable, mixed_case_source)
                print(f"  Added Ligature: {mixed_case_source} -> {name}")
            except:
                pass

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: fontforge -script irish_ligatures.py input.ttf output.ttf")
    else:
        main(sys.argv[1], sys.argv[2])