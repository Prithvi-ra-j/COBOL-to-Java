import streamlit as st
import re
from transformers import pipeline

# Initialize LLM
explainer = pipeline("text-generation", model="distilgpt2")

def translate_comments(cobol_code):
    comments = re.findall(r"^\*.*$", cobol_code, re.MULTILINE)
    java_comments = []
    for comment in comments:
        prompt = f"Convert this COBOL comment to a Java-style comment using //: {comment}"
        try:
            result = explainer(prompt, max_length=50, num_return_sequences=1)[0]["generated_text"]
            java_comment = result.split("Java Comment:")[1].strip() if "Java Comment:" in result else f"// {comment[2:].strip()}"
        except:
            java_comment = f"// {comment[2:].strip()}"  # Fallback if LLM fails
        java_comments.append(java_comment)
    return java_comments

# Streamlit UI
st.title("COBOL-to-Java Comment Translator")
st.write("Input COBOL code to convert comments to Java style.")

cobol_input = st.text_area("COBOL Code")
if st.button("Translate"):
    if cobol_input:
        with st.spinner("Translating..."):
            java_comments = translate_comments(cobol_input)
            st.subheader("Java Comments")
            for comment in java_comments:
                st.write(comment)
    else:
        st.error("Enter COBOL code.")