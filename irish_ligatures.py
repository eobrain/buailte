import fontforge
import sys

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
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

    lookup_name = "IrishLenition"
    subtable_name = "IrishLenition_subtable"
    
    # 1. FIX: Check 'gsub_lookups' instead of generic 'lookups'
    # We check if our custom lookup already exists to allow re-running script
    if lookup_name not in font.gsub_lookups:
        print("Creating 'liga' lookup table...")
        # Type: gsub_ligature, Feature: liga (standard ligatures)
        # The tuple structure here is specific: (("feature_tag", (("script", ("lang",...)),)),)
        font.addLookup(lookup_name, "gsub_ligature", (), (("liga", (("latn", ("dflt")),)),))
        font.addLookupSubtable(lookup_name, subtable_name)
    else:
        print(f"Lookup '{lookup_name}' found. Using existing subtable.")
        # Get existing subtables for this lookup
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
            glyph = font.createChar(uni, name)
            glyph.clear()
            
            try:
                # auto-build based on unicode composition
                glyph.build() 
            except:
                print(f"Warning: Could not auto-build {name}.")
                
            # Fallback if build failed to add content
            if len(glyph.layers['Fore']) == 0:
                if base_char in font and 'dotaccent' in font:
                    glyph.addReference(base_char)
                    glyph.addReference('dotaccent')
        
        else:
            # If checking Gentium, it has these glyphs, so we just grab them
            glyph = font[name]

        # B. Add the Ligature Rule
        ligature_source = f"{base_char} {suffix}"
        
        # Clear old ligatures to avoid duplicates if running multiple times
        # (Optional, but cleaner)
        
        try:
            # Add the ligature mapping
            glyph.addPosSub(subtable, ligature_source)
            print(f"  Linked: {ligature_source} -> {name}")
        except Exception as e:
            # Sometimes errors occur if the mapping exists, we can ignore
            print(f"  Note on {name}: {e}")

        # Handle Title Case (Bh -> Ḃ) for Uppercase letters
        if is_upper:
            mixed_case_source = f"{base_char} h"
            try:
                glyph.addPosSub(subtable, mixed_case_source)
                print(f"  Linked: {mixed_case_source} -> {name}")
            except:
                pass

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: fontforge -script irish_ligatures_v2.py input.ttf output.ttf")
    else:
        main(sys.argv[1], sys.argv[2])