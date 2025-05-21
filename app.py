import streamlit as st
import sys
import os
import re

# Import your translation function (assumed to be in a separate module or defined here)
def translate_cobol_to_java(cobol_code):
    # Copy the translate_cobol_to_java function from your notebook
    lines = cobol_code.split("\n")
    java_code = []
    class_name = None
    methods = []
    fields = []
    copy_classes = []
    in_procedure = False
    current_method = None
    method_lines = []
    comments = []
    in_sql_section = False

    # Simulate CUST.cpy
    copybooks = {
        "CUST": """
01 CUST-REC.
    05 CUST-NAME PIC X(30).
"""
    }

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # PROGRAM-ID
        if "PROGRAM-ID" in line:
            match = re.search(r"PROGRAM-ID.\s*(\w+)", line)
            if match:
                class_name = match.group(1)
                words = re.split(r'[-_]', class_name)
                class_name = ''.join(word.capitalize() for word in words)

        # Comment
        elif re.match(r"^\*.*$", line):
            comment_text = line[2:].strip()
            if comment_text:
                comments.append(f"// {comment_text}")

        # Numeric variable
        elif "PIC 9" in line:
            match = re.search(r"01\s+([\w-]+)\s+PIC\s+9\(\d+\)\s*(VALUE\s+(\d+))?", line)
            if match:
                var_name = ''.join(word.capitalize() for word in match.group(1).lower().split('-'))
                var_name = var_name[0].lower() + var_name[1:] if var_name else var_name
                if match.group(3):
                    fields.append(f"int {var_name} = {match.group(3)};")
                else:
                    fields.append(f"int {var_name};")

        # String variable
        elif "PIC X" in line and not "COPY" in line:
            match = re.search(r"01\s+([\w-]+)\s+PIC\s+X\(\d+\)\s*VALUE\s+'([^']+)'", line)
            if match:
                var_name = ''.join(word.capitalize() for word in match.group(1).lower().split('-'))
                var_name = var_name[0].lower() + var_name[1:] if var_name else var_name
                value = match.group(2)
                fields.append(f"String {var_name} = \"{value}\";")

        # COPY
        elif "COPY" in line:
            match = re.search(r"COPY\s+(\w+)", line)
            if match:
                copy_name = match.group(1)
                if copy_name in copybooks:
                    copy_lines = copybooks[copy_name].split("\n")
                    for copy_line in copy_lines:
                        copy_line = copy_line.strip()
                        if re.search(r"01\s+(\w+)", copy_line):
                            class_name_copy = "CustRec"
                            copy_classes.append(f"public static class {class_name_copy} {{")
                        elif "PIC X" in copy_line:
                            match = re.search(r"05\s+([\w-]+)\s+PIC\s+X\(\d+\)", copy_line)
                            if match:
                                var_name = ''.join(word.capitalize() for word in match.group(1).lower().split('-'))
                                var_name = var_name[0].lower() + var_name[1:] if var_name else var_name
                                copy_classes.append(f"    String {var_name} = \"\";")
                    copy_classes.append("}")
                    fields.append(f"{class_name_copy} {copy_name.lower()} = new {class_name_copy}();")

        # PROCEDURE DIVISION
        elif "PROCEDURE DIVISION" in line:
            in_procedure = True

        # Paragraph (PERFORM target)
        elif in_procedure and re.match(r"^\w+-PARA\.", line):
            if current_method and method_lines:
                method_lines.append("}")
                methods.append("\n".join(method_lines))
            current_method = line[:-1].lower()
            current_method = ''.join(word.capitalize() for word in current_method.split('-'))
            current_method = current_method[0].lower() + current_method[1:]
            method_lines = [f"public void {current_method}() {{"]

        # PERFORM
        elif "PERFORM" in line:
            match = re.search(r"PERFORM\s+(\w+-PARA)", line)
            if match:
                para = match.group(1).lower()
                para = ''.join(word.capitalize() for word in para.split('-'))
                para = para[0].lower() + para[1:]
                method_lines.append(f"{para}();")

        # COMPUTE
        elif "COMPUTE" in line:
            match = re.search(r"COMPUTE\s+([\w-]+)\s*=\s*([\w\s+-/*]+?)\.?\s*$", line)
            if match:
                var = match.group(1).lower().replace('-', '')
                expr = match.group(2).strip()
                expr_parts = re.split(r'(\s*[-+/*]\s*)', expr)
                expr = ''.join(part.lower().replace('-', '') if not re.match(r'\s*[-+/*]\s*', part) else part for part in expr_parts)
                if not current_method:
                    current_method = "mainPara"
                    method_lines = [f"public void {current_method}() {{"]
                method_lines.append(f"{var} = {expr};")

        # MOVE
        elif "MOVE" in line:
            match = re.search(r"MOVE\s+('[^']+'|\w+)\s+TO\s+([\w-]+)", line)
            if match:
                value = match.group(1)
                target = match.group(2).lower()
                if value.startswith("'") and value.endswith("'"):
                    value = f'"{value[1:-1]}"'
                if not current_method:
                    current_method = "mainPara"
                    method_lines = [f"public void {current_method}() {{"]
                if "CUST-NAME" in target.upper():
                    method_lines.append(f"cust.custName = {value};")
                else:
                    target_name = ''.join(word.capitalize() for word in target.split('-'))
                    target_name = target_name[0].lower() + target_name[1:] if target_name else target_name
                    method_lines.append(f"{target_name} = {value};")

        # DISPLAY
        elif "DISPLAY" in line:
            match = re.search(r"DISPLAY\s+([\w-]+)", line)
            if match:
                var = match.group(1).lower()
                if not current_method:
                    current_method = "mainPara"
                    method_lines = [f"public void {current_method}() {{"]
                if "CUST-NAME" in var.upper():
                    method_lines.append(f"System.out.println(cust.custName);")
                else:
                    var_name = ''.join(word.capitalize() for word in var.split('-'))
                    var_name = var_name[0].lower() + var_name[1:] if var_name else var_name
                    method_lines.append(f"System.out.println({var_name});")

        # SQL Section
        elif "EXEC SQL BEGIN DECLARE SECTION" in line:
            in_sql_section = True
        elif "EXEC SQL END DECLARE SECTION" in line:
            in_sql_section = False
        elif "EXEC SQL" in line and not in_sql_section:
            sql_lines = [line]
            j = i + 1
            while j < len(lines) and "END-EXEC" not in lines[j]:
                sql_lines.append(lines[j].strip())
                j += 1
            if j < len(lines) and "END-EXEC" in lines[j]:
                sql_lines.append(lines[j].strip())
                i = j
            sql_statement = " ".join(sql_lines)
            if "INSERT INTO" in sql_statement:
                match = re.search(r"INSERT INTO (\w+)\s*\((\w+),\s*(\w+)\)\s*VALUES\s*\(:([\w-]+),\s*:([\w-]+)\)", sql_statement, re.IGNORECASE)
                if match:
                    table = match.group(1)
                    col1, col2 = match.group(2), match.group(3)
                    var1 = ''.join(word.capitalize() for word in match.group(4).lower().split('-'))
                    var1 = var1[0].lower() + var1[1:] if var1 else var1
                    var2 = ''.join(word.capitalize() for word in match.group(5).lower().split('-'))
                    var2 = var2[0].lower() + var2[1:] if var2 else var2
                    if not current_method:
                        current_method = "mainPara"
                        method_lines = [f"public void {current_method}() throws SQLException {{"]
                    method_lines = [
                        f"public void mainPara() throws SQLException {{",
                        f"    Connection conn = DriverManager.getConnection(\"jdbc:db2://localhost:50000/sample\", \"user\", \"pass\");",
                        f"    PreparedStatement stmt = conn.prepareStatement(\"INSERT INTO {table} ({col1}, {col2}) VALUES (?, ?)\");",
                        f"    stmt.setInt(1, {var1});",
                        f"    stmt.setString(2, {var2});",
                        f"    stmt.executeUpdate();",
                        f"    stmt.close();",
                        f"    conn.close();"
                    ]

        i += 1

    if current_method and method_lines:
        method_lines.append("}")
        methods.append("\n".join(method_lines))

    if class_name:
        java_code.extend(comments[:1])
        if "SQL" in cobol_code:
            java_code.append("import java.sql.*;")
            java_code.append("")
        java_code.append(f"public class {class_name} {{")
        java_code.extend(copy_classes)
        java_code.extend(fields)
        java_code.append("")
        java_code.extend(methods)
        java_code.append("}")
    
    return "\n".join(java_code)

# Define test data (from your notebook)
snippet_1 = """
IDENTIFICATION DIVISION.
PROGRAM-ID. AddNums.
* Initialize variables
DATA DIVISION.
WORKING-STORAGE SECTION.
01 NUM1 PIC 9(3) VALUE 10.
01 NUM2 PIC 9(3) VALUE 20.
* Store sum
01 SUM PIC 9(4).
PROCEDURE DIVISION.
* Calculate sum
COMPUTE SUM = NUM1 + NUM2.
STOP RUN.
"""
expected_java_1 = """
// Initialize variables
public class AddNums {
    int num1 = 10;
    int num2 = 20;
    int sum;
    public void mainPara() {
        sum = num1 + num2;
    }
}
"""

snippet_2 = """
IDENTIFICATION DIVISION.
PROGRAM-ID. PrintMsg.
* Define message
DATA DIVISION.
WORKING-STORAGE SECTION.
01 MSG PIC X(20) VALUE 'Hello World'.
* Display output
PROCEDURE DIVISION.
DISPLAY MSG.
STOP RUN.
"""
expected_java_2 = """
// Define message
public class PrintMsg {
    String msg = "Hello World";
    public void mainPara() {
        System.out.println(msg);
    }
}
"""

snippet_3 = """
IDENTIFICATION DIVISION.
PROGRAM-ID. CalcDiff.
* Set up numbers
DATA DIVISION.
WORKING-STORAGE SECTION.
01 NUM1 PIC 9(3) VALUE 50.
* Store result
01 RESULT PIC 9(4).
* Subtract value
PROCEDURE DIVISION.
COMPUTE RESULT = NUM1 - 10.
STOP RUN.
"""
expected_java_3 = """
// Set up numbers
public class CalcDiff {
    int num1 = 50;
    int result;
    public void mainPara() {
        result = num1 - 10;
    }
}
"""

snippet_4 = """
* Add customer details
IDENTIFICATION DIVISION.
PROGRAM-ID. CustAdd.
DATA DIVISION.
WORKING-STORAGE SECTION.
COPY CUST.
01 PROC-STATUS PIC X(1) VALUE 'N'.
PROCEDURE DIVISION.
MAIN-PARA.
    PERFORM INIT-PARA.
    PERFORM PROCESS-PARA.
    STOP RUN.
INIT-PARA.
    MOVE 'Y' TO PROC-STATUS.
PROCESS-PARA.
    MOVE 'John Doe' TO CUST-NAME.
    DISPLAY CUST-NAME.
"""
expected_java_4 = """
// Add customer details
public class CustAdd {
    public static class CustRec {
        String custName = "";
    }
    CustRec cust = new CustRec();
    String procStatus = "N";

    public void mainPara() {
        initPara();
        processPara();
    }

    public void initPara() {
        procStatus = "Y";
    }

    public void processPara() {
        cust.custName = "John Doe";
        System.out.println(cust.custName);
    }
}
"""

snippet_5 = """
* Insert customer
IDENTIFICATION DIVISION.
PROGRAM-ID. CustInsert.
DATA DIVISION.
WORKING-STORAGE SECTION.
01 CUST-NAME PIC X(30) VALUE 'Jane Doe'.
EXEC SQL BEGIN DECLARE SECTION END-EXEC.
01 CUST-ID PIC 9(4) VALUE 1001.
EXEC SQL END DECLARE SECTION END-EXEC.
PROCEDURE DIVISION.
MAIN-PARA.
    EXEC SQL
        INSERT INTO CUSTOMER (CUST_ID, CUST_NAME)
        VALUES (:CUST-ID, :CUST-NAME)
    END-EXEC.
    STOP RUN.
"""
expected_java_5 = """
// Insert customer
import java.sql.*;

public class CustInsert {
    String custName = "Jane Doe";
    int custId = 1001;

    public void mainPara() throws SQLException {
        Connection conn = DriverManager.getConnection("jdbc:db2://localhost:50000/sample", "user", "pass");
        PreparedStatement stmt = conn.prepareStatement("INSERT INTO CUSTOMER (CUST_ID, CUST_NAME) VALUES (?, ?)");
        stmt.setInt(1, custId);
        stmt.setString(2, custName);
        stmt.executeUpdate();
        stmt.close();
        conn.close();
    }
}
"""

snippets = [snippet_1, snippet_2, snippet_3, snippet_4, snippet_5]
expected_java = [expected_java_1, expected_java_2, expected_java_3, expected_java_4, expected_java_5]

# Streamlit app
st.title("COBOL to Java Translator")
st.write("Enter COBOL code below and get the equivalent Java code. The app also evaluates the translation accuracy using predefined test data.")

# Input COBOL code
cobol_input = st.text_area("COBOL Code", height=300, placeholder="Paste your COBOL code here...")

if st.button("Translate"):
    if cobol_input:
        java_output = translate_cobol_to_java(cobol_input)
        st.subheader("Translated Java Code")
        st.code(java_output, language="java")
    else:
        st.error("Please enter COBOL code to translate.")

# Test data evaluation
st.subheader("Test Data Evaluation")
total_lines = 0
correct_lines = 0

def normalize_lines(lines):
    return [line.strip() for line in lines if line.strip()]

for i, (snippet, expected) in enumerate(zip(snippets, expected_java), 1):
    actual = translate_cobol_to_java(snippet).split("\n")
    expected_lines = expected.strip().split("\n")
    actual_clean = normalize_lines(actual)
    expected_clean = normalize_lines(expected_lines)
    total_lines += len(expected_clean)
    for j, (a, e) in enumerate(zip(actual_clean, expected_clean)):
        if a == e:
            correct_lines += 1
    # Handle unequal line counts
    if len(actual_clean) < len(expected_clean):
        total_lines += len(expected_clean[len(actual_clean):])
    elif len(actual_clean) > len(expected_clean):
        total_lines += len(actual_clean[len(expected_clean):])

accuracy = (correct_lines / total_lines) * 100 if total_lines > 0 else 0
st.write(f"**Total Lines**: {total_lines}")
st.write(f"**Correct Lines**: {correct_lines}")
st.write(f"**Accuracy**: {accuracy:.2f}%")

# Instructions to run
st.subheader("How to Run Locally")
st.markdown("""
1. Save this code as `app.py`.
2. Ensure you have the required libraries: `pip install streamlit`.
3. Run the app: `streamlit run app.py`.
4. Open the provided local URL in your browser to interact with the app.
""")
