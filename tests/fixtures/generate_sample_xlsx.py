"""
Generator script for tests/fixtures/sample_document.xlsx
Creates a multi-sheet Excel workbook with sample Zambian school data.
"""
import os
import openpyxl


def main():
    wb = openpyxl.Workbook()

    # ---- Sheet 1: Academic Records ----
    ws1 = wb.active
    ws1.title = "Academic Records"
    ws1.append(["Student ID", "Name", "Subject", "Grade", "Term"])
    ws1.append(["ZM-2026-0401", "Mutale Chilufya", "Mathematics", "B+", "Term 1"])
    ws1.append(["ZM-2026-0402", "Thandiwe Banda", "English Language", "A", "Term 1"])
    ws1.append(["ZM-2026-0403", "Bwalya Mwansa", "Integrated Science", "B", "Term 1"])

    # ---- Sheet 2: Budget Summary ----
    ws2 = wb.create_sheet("Budget Summary")
    ws2.append(["Item", "Amount (ZMW)", "Category"])
    ws2.append(["Textbooks", 45000, "Teaching Materials"])
    ws2.append(["Laboratory Equipment", 120000, "Capital Expenditure"])
    ws2.append(["Staff Training Workshop", 18500, "Professional Development"])

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_document.xlsx")
    wb.save(out_path)
    print(f"Created: {out_path}")


if __name__ == "__main__":
    main()
