import json
import os

# --- MAPPING DATA ---
MAPPING_74 = {
    "राम रक्षा स्तोत्र": "Ram Raksha Stotra",
    "पंचमुखी हनुमान कवच": "Panchmukhi Hanuman Kavach",
    "दुर्गा सप्तश्लोकी": "Durga Saptashloki",
    "नृसिंह स्तोत्रम": "Nrisimha Stotram",
    "कालभैरव अष्टकम": "Kalabhairav Ashtakam",
    "सुदर्शन अष्टकम": "Sudarshan Ashtakam",
    "नृसिंह कवच": "Nrisimha Kavach",
    "देवी कवच": "Devi Kavach",
    "महाकाली स्तोत्र": "Mahakali Stotra",
    "कार्तिकेय कवच": "Kartikeya Kavach",
    "श्री राम का आगमन": "Shri Ram Ka Aagman",
    "नरकासुर वध": "Narakasur Vadh",
    "पूतना वध की कथा": "Putana Vadh Ki Katha",
    "कालिया नाग मर्दन": "Kaliya Nag Mardan",
    "अपराजिता मंत्र": "Aparajita Mantra",
    "भय नाशक मंत्र": "Bhay Nashak Mantra",
    "सिद्धि मंत्र": "Siddhi Mantra",
    "राम गायत्री मंत्र": "Ram Gayatri Mantra",
    "आरती कीजै रामलला की": "Aarti Kije Ramlala Ki",
    "मंगल भवन अमंगल हारी": "Mangal Bhavan Amangal Hari",
    "राम चालीसा": "Ram Chalisa",
    "सीता जी की आरती": "Sita Ji Ki Aarti",
    "सीता चालीसा": "Sita Chalisa",
    "हनुमान गायत्री मंत्र:": "Hanuman Gayatri Mantra",
    "हनुमान चालीसा": "Hanuman Chalisa",
    "हनुमानाष्टक": "Hanumanashtak",
    "सुन्दरकाण्ड": "Sunderkand",
    "बजरंग बाण": "Bajrang Baan",
    "हनुमान चालीसा": "Hanuman Chalisa",
    "हनुमान चालीसा": "Hanuman Chalisa",
    "संकटमोचन हनुमानाष्टक": "Sankatmochan Hanumanashtak",
    "संकटमोचन हनुमानाष्टक": "Sankatmochan Hanumanashtak",
    "बजरंग बाण": "Bajrang Baan",
    "बजरंग बाण": "Bajrang Baan",
    "सुन्दरकाण्ड: भाग 1 (हनुमान जी का प्रस्थान और लंका प्रवेश)": "Sunderkand: Part 1 (Hanuman Ji Ka Prasthan Aur Lanka Pravesh)",
    "सुन्दरकाण्ड: भाग 2 (सीता-हनुमान संवाद और लंका दहन)": "Sunderkand: Part 2 (Sita-Hanuman Samvad Aur Lanka Dahan)",
    "हनुमान जी की आरती": "Hanuman Ji Ki Aarti",
    "राम स्तुति (श्री रामचंद्र कृपालु भजमन)": "Ram Stuti (Shri Ramachandra Kripalu Bhajman)",
    "भरत मिलाप": "Bharat Milap",
    "अहिल्या उद्धार": "Ahilya Uddhar",
    "शबरी के बेर": "Shabari Ke Ber",
    "श्री राम का वनवास": "Shri Ram Ka Vanvas",
    "सीता स्वयंवर": "Sita Swayamvar",
    "गणेश गायत्री मंत्र": "Ganesh Gayatri Mantra",
    "गणेश स्तुति": "Ganesh Stuti",
    "गणेश चालीसा": "Ganesh Chalisa",
    "गणेश जी की आरती (जय गणेश जय गणेश देवा)": "Ganesh Ji Ki Aarti (Jai Ganesh Jai Ganesh Deva)",
    "गणेश जी की आरती (शेंदुर लाल चढ़ायो)": "Ganesh Ji Ki Aarti (Shendur Lal Chadhayo)",
    "विष्णु गायत्री मंत्र": "Vishnu Gayatri Mantra",
    "श्री विष्णु चालीसा": "Shri Vishnu Chalisa",
    "विष्णु जी की आरती (ओम जय जगदीश हरे)": "Vishnu Ji Ki Aarti (Om Jai Jagdish Hare)",
    "गजेन्द्र मोक्ष": "Gajendra Moksha",
    "ध्रुव तारा की कथा": "Dhruv Tara Ki Katha",
    "प्रह्लाद की कथा": "Prahlad Ki Katha",
    "लक्ष्मी गायत्री मंत्र": "Lakshmi Gayatri Mantra",
    "महालक्ष्मी अष्टकम": "Mahalakshmi Ashtakam",
    "श्री लक्ष्मी चालीसा": "Shri Lakshmi Chalisa",
    "लक्ष्मी जी की आरती (ओम जय लक्ष्मी माता)": "Lakshmi Ji Ki Aarti (Om Jai Lakshmi Mata)",
    "शनि गायत्री मंत्र": "Shani Gayatri Mantra",
    "शनि चालीसा": "Shani Chalisa",
    "शनि देव की आरती": "Shani Dev Ki Aarti",
    "दुर्गा गायत्री मंत्र": "Durga Gayatri Mantra",
    "श्री दुर्गा चालीसा": "Shri Durga Chalisa",
    "दुर्गा जी की आरती (जय अम्बे गौरी)": "Durga Ji Ki Aarti (Jai Ambe Gauri)",
    "महिषासुर वध की कथा": "Mahishasur Vadh Ki Katha",
    "माँ दुर्गा का जन्म": "Maa Durga Ka Janm",
    "कृष्ण गायत्री मंत्र": "Krishna Gayatri Mantra",
    "बांके बिहारी की आरती": "Banke Bihari Ki Aarti",
    "श्री कृष्ण चालीसा": "Shri Krishna Chalisa",
    "श्री कृष्णाष्टकम": "Shri Krishnashtakam",
    "अच्युतम केशवम": "Achyutam Keshavam",
    "मधुराष्टकम": "Madhurashtakam",
    "गोवर्धन पूजा की कथा": "Govardhan Puja Ki Katha",
    "राधा-कृष्ण प्रेम कथा": "Radha-Krishna Prem Katha",
    "मेरे सरकार आए हैं": "Mere Sarkar Aaye Hain",
    "सजा दो घर को गुलशन सा": "Saja Do Ghar Ko Gulshan Sa",
    "ओ माँ मेरी झोपड़ी के भाग": "O Maa Meri Jhopdi Ke Bhag",
    "हम कथा सुनाते राम सकल": "Hum Katha Sunate Ram Sakal",
    "हनुमान जयंती कथा": "Hanuman Jayanti Katha",
    "हनुमान बाहुक": "Hanuman Bahuk",
    "एकमुखी हनुमत् कवच": "Ekamukhi Hanumat Kavach",
    "बम लहरी": "Bam Lahari",
    "श्री हनुमत् स्तवन": "Shri Hanumat Stavan",
    "हनुमान साठिका": "Hanuman Sathika",
    "हनुमान चालीसा (फास्ट वर्शन)": "Hanuman Chalisa (Fast Version)",
    "हनुमान जंजीरा": "Hanuman Janjira",
    "हनुमान वन्दना": "Hanuman Vandana",
    "हनुमान वडवानल स्तोत्र": "Hanuman Vadvanal Stotra",
    "अश्वत्थामा की कथा": "Ashwatthama Ki Katha",
    "महिषासुर मर्दन": "Mahishasur Mardan",
    "लिंगाष्टकम": "Lingashtakam",
    "द्वादश ज्योतिर्लिंग स्तोत्र": "Dwadash Jyotirlinga Stotra",
    "शिव पंचाक्षर स्तोत्र": "Shiva Panchakshar Stotra",
    "बिल्वाष्टकम": "Bilvashtakam",
    "शिव महिम्न स्तोत्र": "Shiva Mahimna Stotra",
    "निर्वाण षटकम": "Nirvana Shatakam",
    "पशुपत्यष्टकम": "Pashupatyashtakam",
    "कालाष्टकम": "Kalashtakam",
    "अर्धनारीश्वर स्तोत्र": "Ardhanarishwar Stotra",
    "दारिद्रय दहन शिव स्तोत्र": "Daridraya Dahan Shiva Stotra",
    "शिव मानस पूजा": "Shiva Manas Puja",
    "शिव ताण्डव स्तोत्र": "Shiva Tandava Stotra",
    "महामृत्युंजय मंत्र (फास्ट वर्शन)": "Mahamrityunjay Mantra (Fast Version)",
    "श्री सुब्रमण्य अष्टकम": "Shri Subramanya Ashtakam",
    "सुख के सब साथी": "Sukh Ke Sab Sathi",
    "राम जी का नाम लेकर": "Ram Ji Ka Naam Lekar",
    "कभी राम बनके कभी श्याम": "Kabhi Ram Banke Kabhi Shyam",
    "श्री राम चालीसा": "Shri Ram Chalisa",
    "अयोध्या राम मंदिर कथा": "Ayodhya Ram Mandir Katha",
    "श्री राम स्तुति": "Shri Ram Stuti",
    "श्री राम गायत्री मंत्र": "Shri Ram Gayatri Mantra",
    "सीता माता की कथा": "Sita Mata Ki Katha",
    "लव कुश की कथा": "Luv Kush Ki Katha",
    "राम वनवास कथा": "Ram Vanvas Katha",
    "रावण वध की कथा": "Ravan Vadh Ki Katha",
    "विभीषण शरणागति कथा": "Vibhishan Sharanagati Katha",
    "राम राज्य की कथा": "Ram Rajya Ki Katha",
    "अंगद-रावण संवाद": "Angad-Ravan Samvad",
    "हनुमान-लक्ष्मण मिलन": "Hanuman-Lakshman Milan",
    "वेदसार शिव स्तोत्र": "Vedsar Shiva Stotra",
    "मेरा भोला है भंडारी": "Mera Bhola Hai Bhandari",
    "शिव कैलाशों के वासी": "Shiva Kailashon Ke Vasi",
    "मन मेरा मंदिर शिव मेरी पूजा": "Man Mera Mandir Shiva Meri Puja",
    "सत्यम शिवम सुंदरम": "Satyam Shivam Sundaram",
    "नगर में जोगी आया": "Nagar Mein Jogi Aaya",
    "भोले ओ भोले": "Bhole O Bhole",
    "ऐसी सुबह ना आए": "Aisi Subah Na Aaye",
    "शिव जी सत्य है": "Shiva Ji Satya Hai",
    "शिव पार्वती विवाह की संपूर्ण कथा": "Shiva Parvati Vivah Ki Sampoorn Katha",
    "सिद्धि विनायक मंत्र": "Siddhi Vinayak Mantra",
    "ऋद्धि-सिद्धि मंत्र": "Riddhi-Siddhi Mantra",
    "ऋणमोचन गणेश स्तोत्र": "Rinamochana Ganesha Stotra",
    "गणपति गकार स्तोत्र": "Ganapati Gakar Stotra",
    "लम्बोदर स्तोत्र": "Lambodar Stotra",
    "गणेश द्वादशनाम स्तोत्र": "Ganesha Dwadashnaam Stotra",
    "देवा श्री गणेशा": "Deva Shri Ganesha",
    "ओ माय फ्रेंड गणेशा": "O My Friend Ganesha",
    "देवा हो देवा गणपति देवा": "Deva Ho Deva Ganapati Deva",
    "हनुमत-राम मंत्र": "Hanumat-Ram Mantra",
    "भए प्रगट कृपाला दीनदयाला": "Bhaye Pragat Kripala Deendayala",
    "सुख के सब साथी दुःख में ना कोई": "Sukh Ke Sab Sathi Dukh Mein Na Koi",
    "सुरक्षा मंत्र": "Suraksha Mantra",
    "राम-दूत मंत्र": "Ram-Doot Mantra",
    "सुंदरकांड": "Sunderkand",
    "मारुति स्तोत्र": "Maruti Stotra",
    "बालाजी अच्छा लागे से": "Balaji Achha Lage Se",
    "हनुमान जब चले": "Hanuman Jab Chale"
}
# ---------------------

def main():
    input_file = "CleanTracksDTO.json"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    translation_count = 0
    punctuation_count = 0

    for track in data:
        updated = False
        thumbnail = track.get('thumbnail', {})
        title = thumbnail.get('title', {})
        description = thumbnail.get('description', {})

        hi_title = title.get('hi', '')
        en_title = title.get('en', '')
        en_desc = description.get('en', '')

        # 1. Translation Fix
        if hi_title in MAPPING_74:
            corrected_en = MAPPING_74[hi_title]
            if en_title != corrected_en:
                title['en'] = corrected_en
                description['en'] = corrected_en
                translation_count += 1
                updated = True

        # 2. Punctuation Fix
        # Re-check en_title because it might have been updated above
        curr_en_title = title.get('en', '')
        curr_en_desc = description.get('en', '')
        
        if curr_en_title.endswith(',') or curr_en_title.endswith('.'):
            # Strip trailing punctuation and spaces
            new_en = curr_en_title.rstrip(',. ')
            new_desc = curr_en_desc.rstrip(',. ')
            
            title['en'] = new_en
            description['en'] = new_desc
            punctuation_count += 1
            updated = True

    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Summary of changes:")
    print(f" - Translation corrections: {translation_count}")
    print(f" - Trailing punctuation removed: {punctuation_count}")
    print(f"Updated {input_file} successfully.")

if __name__ == "__main__":
    main()
