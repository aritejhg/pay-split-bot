import re
import openai
import os
import ast

def items(text_ocr, items):# loop over each of the line items in the OCR'd receipt
    pricePattern = r'([0-9]+\.[0-9]+)'
    for row in text_ocr.split("\n"):
        # check to see if the price regular expression matches the current
        if "Total" in row:
            break
        if re.search(pricePattern, row) is not None :
            price = re.search(pricePattern, row).group(0)
            item = row.replace(price, "").strip()
            items.append([item, price])
    return items

def tax(text_ocr):
    taxPattern = r'GST\s*([0-9]+\.[0-9]+)'
    serviceTaxPattern = r'Service\s*([0-9]+\.[0-9]+)'
    tax = re.search(taxPattern, text_ocr).group(1)
    return tax

def openai_call(text_ocr):
    openai.api_key = "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"
    response = openai.Completion.create(
    model="text-davinci-003",
    prompt="parse text to give item, its price, tax and total to make up the total. Output MUST be a dict with each value as list {'items':[item1, price1]....[lastItem, lastPrice], 'taxes':[[tax1, taxAmount1],[ tax2, taxAmount2]], 'total':[total, totalPrice]}. answer with only the array. make sure item names are spelled correctly.\n\"\"\"\n"+text_ocr+"\n\"\"\"",
    temperature=0.4,
    max_tokens=256,
    top_p=0.7,
    frequency_penalty=0,
    presence_penalty=0
    )
    # print(response)

    response_text = response["choices"][0]["text"]
    strip_text = response_text.split(" = ")[1]
    # print(strip_text)
    main_response = ast.literal_eval(strip_text)

    # print(main_response)
    items = main_response["items"]
    taxes = main_response["taxes"]
    total = main_response["total"]

    return items, taxes, total

# text_ocr = """"
# eH ASH PA
# Kailash Parbat Restaurants Pte Ltd
# 3 Belilos Road, #01-03
# Singapore 219924
# TEL + 65 68369545
# GST Reg. No .2009183046

# Date:7/17/2022|3:14 PM

# Ticket No:56891
# Table:T O6

# OT:Restaurant

# 2 KP CHAAT PLATTER HD 34.00
# 4 Patiyala Lessi 4D 26.00
# * Sweet

# 1 BHATURA PLATTER HD 26.00

# 1 CHOLE BHATURAS HD 11.50
# 3 Mango Lassi HD 21.00
# 2 BHATURA PLATTER HD 40.00
# * Running

# Sub Total: 152,50
# Service Charge %10 15.25
# GST 7% 11.74
# Taxable Amount : 167.715

# Total: 179,49

# Order Online www.kailashparbat .com.sg

# ee"""

# print(openai_call(text_ocr))
