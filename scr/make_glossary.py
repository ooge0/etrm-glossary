import os
import sys
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()


def get_timestamp():
    """Get the current timestamp in a formatted string."""
    return datetime.now().strftime("%H:%M / %d/%m/%Y")


def sort_and_mark_duplicates(filename, ext_filename):
    """Process the Markdown table:

    - Alphabetically group and sort `Term`.
    - Prefix duplicate terms with an asterisk (*).
    - Reorder the table while keeping rows intact.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        # Dynamically find where the glossary table starts
        table_start_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith('|') and 'Term' in line:
                table_start_idx = i
                break

        if table_start_idx is None:
            print("Error: Could not locate the glossary table in the file.")
            return

        # Skip table header and separator line
        table_data = lines[table_start_idx + 2 :]
        row_counter = 0
        cleaned_data = []
        for row in table_data:
            raw = row.strip()
            if not raw.startswith('|'):
                continue
            # Split on '|' and remove the empty leading/trailing elements
            parts = [col.strip() for col in raw.split('|')]
            if parts and parts[0] == '':
                parts.pop(0)
            if parts and parts[-1] == '':
                parts.pop()

            # Ignore existing 'Order' column if present
            if len(parts) == 4:
                parts = parts[1:]

            if len(parts) == 3:
                cleaned_data.append(parts)
            row_counter += 1
        print(f"rows: {row_counter}")
        # Create DataFrame
        df = pd.DataFrame(
            cleaned_data, columns=['Term', 'Category', 'Definition']
        )

        # Create case-insensitive terms for sorting and duplicate detection
        df['LowerCaseTerm'] = df['Term'].str.lower()

        # Identify duplicates (case-insensitive)
        is_duplicate = df.duplicated(subset=['LowerCaseTerm'], keep=False)

        # Sort alphabetically by LowerCaseTerm (stable sort keeps original order for identical terms)
        df = df.sort_values(by='LowerCaseTerm', kind='stable').reset_index(
            drop=True
        )
        is_duplicate = df.duplicated(subset=['LowerCaseTerm'], keep=False)

        # Apply asterisk prefix to duplicate terms
        df['Term'] = df.apply(
            lambda row: f"*{row['Term']}"
            if is_duplicate[row.name]
            and not row['Term'].startswith('*')
            else row['Term'],
            axis=1,
        )

        # Calculate accurate term statistics
        total_terms = len(df)
        unique_count = df['LowerCaseTerm'].nunique()
        duplicate_count = total_terms - unique_count

        # Remove helper column and add updated Order column
        df.drop(columns=['LowerCaseTerm'], inplace=True)
        df.insert(0, 'Order', range(1, total_terms + 1))

        # Convert DataFrame to Markdown table format
        markdown_table = df.to_markdown(index=False, tablefmt='pipe')

        # Build output metadata header
        metadata = (
            f"## Intro\n"
            f'<p style="font-family: Arial, sans-serif; font-size: 16px;">\n'
            f'  <span style="font-weight: bold; color: #2E8B57;">\n'
            f'  This document was created from different sources that merged into single table.</span><br />\n'
            f'  <span style="color: #4682B4;">Some terms may be duplicated, can have specific interpretations, but in general, were retrieved from the documents, manuals, and guides discovered in the project wiki.</span>\n'
            f'</p>\n\n'
            f"Last version generated at: **{get_timestamp()}**\n\n"
            f"------------\n\n"
            f"## Table contains\n"
            f"- **{total_terms}** terms.\n\n"
            f"- Unique terms: **{unique_count}**\n"
            f"- Duplicated terms: **{duplicate_count}**. Those items marked by `*` in `Term` column\n\n"
            f"------------\n\n"
            f"## Categories\n\n"
            f"_s_1_ = Energy Markets Training Programme 3.pdf\n\n"
            f"s_2 = e_h_r_m_g__habspot.net__energy-hedging-risk-management-glossary.pdf\n\n"
            f"gl_trm_1 = [Energy glossary from homefieldenergy.com](https://www.homefieldenergy.com/residential/about-energy-choice/energy-glossary)\n\n"
            f"------------\n\n"
            f"## Glossary\n\n"
        )

        final_md_data = metadata + markdown_table

        # Save result to ext_filename
        with open(ext_filename, 'w', encoding='utf-8') as file:
            file.write(final_md_data)

        print(f"File processed successfully and saved to '{ext_filename}'.")

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def reorder_original_file(filename: str) -> None:
    """Sort the glossary table by Term and renumber the Order column in place.

    Preserves everything before the table (intro, metadata) and the
    table header/separator exactly as they are.
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Locate the glossary table
        table_start_idx = None
        header_idx = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("|") and "Term" in stripped:
                table_start_idx = i
                header_idx = i
                break

        if table_start_idx is None:
            print(f"Error: no glossary table found in '{filename}'.")
            return

        # Separator is the line right after header
        separator_idx = header_idx + 1
        if not lines[separator_idx].strip().startswith("|"):
            print("Error: malformed table — no separator after header.")
            return

        # Split: prefix (intro + header + separator), rows, suffix
        prefix = lines[: separator_idx + 1]
        body = lines[separator_idx + 1 :]

        rows: list[list[str]] = []
        suffix: list[str] = []
        in_table = True

        for raw in body:
            stripped = raw.strip()
            if in_table and stripped.startswith("|"):
                parts = [c.strip() for c in stripped.split("|")]
                if parts and parts[0] == "":
                    parts.pop(0)
                if parts and parts[-1] == "":
                    parts.pop()
                # Expect: Order | TechnicalTerm | Category | Definition
                if len(parts) == 4:
                    rows.append(parts)
                else:
                    print(f"Skipping malformed row: {stripped}")
            else:
                in_table = False
                suffix.append(raw)

        if not rows:
            print("Error: no data rows found.")
            return

        # Sort by TechnicalTerm, case-insensitive, stable
        rows.sort(key=lambda r: r[1].lower())

        # Renumber Order
        for i, r in enumerate(rows, start=1):
            r[0] = str(i)

        # Rebuild the table
        rebuilt = [
            "| " + " | ".join(r) + " |\n" for r in rows
        ]

        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(prefix)
            f.writelines(rebuilt)
            f.writelines(suffix)

        print(
            f"Reordered {len(rows)} rows in '{filename}' "
            f"(sorted by TechnicalTerm, Order renumbered 1..{len(rows)})."
        )

    except FileNotFoundError:
        print(f"Error: file '{filename}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    original_file = '../etrm_wiki_glossary.md'
    new_file = 'ext_wiki_dt.md'
    sort_and_mark_duplicates(original_file, new_file)
    reorder_original_file(original_file)


if __name__ == '__main__':
    main()
