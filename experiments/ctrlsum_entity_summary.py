from transformers import AutoModelForSeq2SeqLM, PreTrainedTokenizerFast
import torch

# 1. Choose a pretrained CTRLsum checkpoint
MODEL_NAME = "hyunwoongko/ctrlsum-cnndm"  
# alternatives: "hyunwoongko/ctrlsum-arxiv", "hyunwoongko/ctrlsum-bigpatent"

# 2. Load model & tokenizer
tokenizer = PreTrainedTokenizerFast.from_pretrained(MODEL_NAME)  
# uses the same SentencePiece files under-the-hood :contentReference[oaicite:2]{index=2}

model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

def ctrlsum_summary(text: str,
                    control: str = None,
                    num_beams: int = 5,
                    length_penalty: float = 1.0,
                    max_length: int = 150,
                    min_length: int = 30):
    """
    If `control` is provided, uses 'control => text' format; 
    otherwise does uncontrolled summarization.
    """
    # 3. Build the input string
    if control:
        # ensure proper spacing around the => token
        inp = f"{control.strip()} => {text.strip()}"
    else:
        inp = text.strip()

    # 4. Tokenize
    inputs = tokenizer(inp, 
                       return_tensors="pt", 
                       truncation=True, 
                       max_length=1024)
    input_ids = inputs["input_ids"].to(device)
    attention_mask = inputs["attention_mask"].to(device)

    # 5. Generate
    output_ids = model.generate(
        input_ids=input_ids,
        attention_mask=attention_mask,
        num_beams=num_beams,
        length_penalty=length_penalty,
        max_length=max_length,
        min_length=min_length,
        early_stopping=True     # stop when best beams finish :contentReference[oaicite:3]{index=3}
    )

    # 6. Decode
    summary = tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0]
    return summary

# --- sample usage ---
if __name__ == "__main__":
    # Sample long document text but ideally try to make it less about main entity for real world simulation
    # (e.g., a news article, research paper, etc.)
    
#     old_text = """Marie Curie was a pioneering physicist and chemist who conducted groundbreaking research on radioactivity. Born
# in Warsaw, Poland in 1867, she moved to Paris to study at the Sorbonne. Curie's research focused on the properties of radioactive
# elements, leading to the discovery of two new elements: polonium and radium. Her work was instrumental in advancing the field of
# nuclear physics and medicine. Curie was the first woman to win a Nobel Prize in Physics in 1903 for her research on radioactivity.
# She also received a Nobel Prize in Chemistry in 1906 for her discovery of radium. Curie's contributions to science and medicine
# have had a profound impact on the world, and her legacy continues to inspire scientists worldwide."""
    text = """
Modern medicine has been shaped by centuries of research, experimentation, and groundbreaking discoveries, many of which trace 
their origins to the late 19th and early 20th centuries. During this transformative period, several scientists laid the groundwork 
for technologies and treatments that continue to save lives today.

One of the key advancements came in the form of X-ray technology, pioneered by Wilhelm Röntgen, who accidentally discovered X-rays 
in 1895. His work earned him the first Nobel Prize in Physics and revolutionized medical diagnostics, enabling physicians to look 
inside the human body without surgery for the first time.

Around the same time, Marie Curie made enormous strides in the study of radioactivity. Her discoveries of polonium and radium, 
alongside her development of mobile radiography units during World War I, had a lasting impact on cancer treatment and battlefield 
medicine. Despite the risks, she continued to work with radioactive materials, ultimately laying the foundation for modern radiation 
therapy.

Another contemporary, Alexander Fleming, changed the course of medicine in 1928 when he discovered penicillin. This chance 
discovery, followed by years of refinement and production, ushered in the antibiotic era and drastically reduced mortality from 
bacterial infections. Fleming's work demonstrated the potential of naturally occurring substances in medical treatment, a principle 
that continues to guide pharmaceutical research today.

In more recent decades, Rosalind Franklin's X-ray crystallography images were instrumental in identifying the double-helix structure 
of DNA—a breakthrough often credited to Watson and Crick. Franklin’s contributions, though underappreciated during her lifetime, 
are now recognized as central to the field of molecular biology.

These pioneers—Röntgen, Curie, Fleming, Franklin—each played a pivotal role in different branches of science and medicine. Their 
work continues to resonate in modern research labs and hospitals alike. Today, as scientists explore new frontiers like gene editing, 
AI in diagnostics, and personalized medicine, the legacy of these figures serves as a powerful reminder of how curiosity, persistence, 
and a willingness to challenge established norms can lead to discoveries that benefit all of humanity.
"""

    long_doc = text

    # 1) Generic summary
    generic = ctrlsum_summary(long_doc, control=None)
    print(">> Generic CTRLsum:\n", generic)

    # 2) Entity-focused summary (“PERSON” = “Marie Curie”)
    focused = ctrlsum_summary(long_doc, control="Marie Curie")
    print("\n>> Entity-Focused CTRLsum:\n", focused)
