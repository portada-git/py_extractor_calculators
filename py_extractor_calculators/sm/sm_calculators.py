# from flask import Flask, jsonify, request

from datetime import datetime, timedelta
import re
from difflib import get_close_matches
from difflib import SequenceMatcher

# app = Flask(__name__)


# @app.route("/api/get_arrival_date_from_publication_date", methods=['POST'])
def get_arrival_date_from_publication_date(params):
    # jsonp = request.get_json()
    # params = jsonp["parameters_by_position"]
    pub_date = params[0]
    arrival_date = params[1]
    arrival_day = extract_number_from_ocr_string(arrival_date)

    try:
        pub_date = compose_date(int(pub_date))
        if pub_date.day >= arrival_day:
            arrival_date = pub_date.replace(day=arrival_day)
        if pub_date.day < arrival_day:
            if pub_date.month == 1:
                arrival_date = pub_date.replace(month=12, year = pub_date.year-1)
            else:
                arrival_date = pub_date.replace(month=pub_date.month-1)

        ret = {'status': 0, 'value': arrival_date.strftime('%Y-%m-%d')}
    except Exception as e:
        ret = {'status': -1, 'message': str(e)}

    return ret
    # return jsonify(ret)


# @app.route("/api/get_departure_date", methods=['POST'])
def get_departure_date(params):
    # jsonp = request.get_json()
    # params = jsonp["parameters_by_position"]
    pub_date = params[0]
    departure_date = params[1]

    pub_date = compose_date(int(pub_date))

    french_months = {
        "janvier": 1, "février": 2, "mars": 3, "avril": 4,
        "mai": 5, "juin": 6, "juillet": 7, "août": 8,
        "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
    }

    # Normalize text to ASCII-friendly lowercase
    def normalize(text):
        accents = {
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'à': 'a', 'â': 'a',
            'î': 'i', 'ï': 'i',
            'ô': 'o',
            'û': 'u', 'ù': 'u',
            'ç': 'c',
            'œ': 'oe',
        }
        for k, v in accents.items():
            text = text.replace(k, v)
        return re.sub(r'[^a-zA-Z]', '', text.lower())

    # Mapping common OCR/abbreviated month forms to full French month names
    month_abbr_corrections = {
        "janv": "janvier",
        "fev": "février", "fevr": "février",
        "mar": "mars",
        "avr": "avril",
        "mai": "mai",
        "jui": "juin",  # fallback
        "juin": "juin",
        "juil": "juillet",
        "aou": "août", "aout": "août",
        "sep": "septembre", "sept": "septembre",
        "oct": "octobre",
        "nov": "novembre",
        "dec": "décembre", "decem": "décembre"
    }

    fuzzy_cour_variants = ["cour", "courr", "courant", "cpurant", "c0ur", "coiir", "coun", "coue"]

    # Add normalized French month names
    normalized_months = {normalize(k): (k, v) for k, v in french_months.items()}

    # Enhanced regex to match "1er juil", "15 avr.", etc.
    match = re.search(r'\b(?:le\s+)?(\d{1,2})(?:er|eme|e)?[.,]?\s+([a-zA-Zéèêàùûôçîïëœ.]+)', departure_date)
    if not match:
        return {'status': -1, 'message': f"Unable to parse date from string: {departure_date}"}
        # return jsonify({'status': -1, 'message': f"Unable to parse date from string: {departure_date}"})

    day = int(match.group(1))
    raw_monthish = normalize(match.group(2))

    # Step 1: Direct match for abbreviations
    if raw_monthish in month_abbr_corrections:
        corrected_month = month_abbr_corrections[raw_monthish]
        month_num = french_months[corrected_month]
    # Step 2: "courant" or OCR variants
    elif get_close_matches(raw_monthish, fuzzy_cour_variants, n=1, cutoff=0.7):
        month_num = pub_date.month
    # Step 3: Fuzzy match against full normalized months
    else:
        close = get_close_matches(raw_monthish, normalized_months.keys(), n=1, cutoff=0.6)
        if not close:
            return {'status': -1, 'message': f"Could not recognize the month from: {raw_monthish}"}
            # return jsonify({'status': -1, 'message': f"Could not recognize the month from: {raw_monthish}"})
        _, month_num = normalized_months[close[0]]

    try:
        departure_date = datetime(year=pub_date.year, month=month_num, day=day)
        ret = {'status': 0, 'value': departure_date.strftime('%Y-%m-%d')}
    except Exception as e:
        ret = {'status': -1, 'message': str(e)}

    return ret
    # return jsonify(ret)


# @app.route("/api/get_duration_value", methods=['POST'])
def get_duration_value(params):
    # jsonp = request.get_json()
    # params = jsonp["parameters_by_position"]
    departure_date = params[0]
    arrival_date = params[1]

    try:
        departure_date = datetime.strptime(departure_date, "%Y-%m-%d")
        arrival_date = datetime.strptime(arrival_date, "%Y-%m-%d")
        duration = (arrival_date - departure_date).days
        ret = {'status': 0, 'value': duration}
    except Exception as e:
        ret = {'status': -1, 'message': str(e)}

    return ret
    # return jsonify(ret)


# @app.route("/api/get_quarantine", methods=['POST'])
def get_quarantine(params):
    # jsonp = request.get_json()
    # params = jsonp["parameters_by_position"]
    arrivees_text = params[0]

    print(params)

    # Normalize input
    text = arrivees_text.lower().strip()

    # Expected references
    quarantine_text = "arrivees en quarantaine"
    libre_pratique_text = "arrivees en libre pratique"

    def is_similar(a, b, threshold=0.8):
        return SequenceMatcher(None, a, b).ratio() >= threshold

    try:
        if is_similar(text, quarantine_text):
            value = True
        elif is_similar(text, libre_pratique_text):
            value = False
        else:
            value = "?"
        ret = {'status': 0, 'value': value}
    except Exception as e:
        ret = {'status': -1, 'message': str(e)}

    return ret
    # return jsonify(ret)


# @app.route("/api/get_port_of_call_list", methods=['POST'])
def get_port_of_call_list(params):
    # jsonp = request.get_json()
    # params = jsonp["parameters_by_position"]
    pub_date_str = params[0]
    first_departure_date_str = params[1]
    extracted_text = params[2]

    pub_date = compose_date(int(pub_date_str))

    try:
        first_date = datetime.strptime(first_departure_date_str.strip(), "%Y-%m-%d")
    except Exception as e:
        return {'status': -1, 'message': f"Invalid first_departure_date_str: {e}"}
        # return jsonify({'status': -1, 'message': f"Invalid first_departure_date_str: {e}"})

    french_months = {
        "janvier": 1, "février": 2, "mars": 3, "avril": 4,
        "mai": 5, "juin": 6, "juillet": 7, "août": 8,
        "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
    }

    month_abbr_corrections = {
        "janv": "janvier", "fev": "février", "fevr": "février", "mar": "mars",
        "avr": "avril", "mai": "mai", "jui": "juin", "juin": "juin", "juil": "juillet",
        "aou": "août", "aout": "août", "sep": "septembre", "sept": "septembre",
        "oct": "octobre", "nov": "novembre", "dec": "décembre", "decem": "décembre"
    }

    fuzzy_cour_variants = ["cour", "courr", "courant", "cpurant", "c0ur", "coiir", "coun", "coue"]
    dito_variants = ['dito', 'ditto', 'dite', 'd1to', 'dlto', 'dlt0', 'dilo', 'dlte']

    def normalize(text):
        accents = {
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'à': 'a', 'â': 'a',
            'î': 'i', 'ï': 'i',
            'ô': 'o',
            'û': 'u', 'ù': 'u',
            'ç': 'c',
            'œ': 'oe',
        }
        for k, v in accents.items():
            text = text.replace(k, v)
        return re.sub(r'[^a-zA-Z]', '', text.lower())

    normalized_months = {normalize(k): (k, v) for k, v in french_months.items()}

    results = []
    current_month = first_date.month

    parts = re.split(r'[:;]', extracted_text)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        match = re.match(r'([A-Za-zÉéèêîôçàù\s\-]+)\.?[\s,]+(\d{1,2})(?:er|eme|e)?[\s]+([a-zA-Zéèêàùûôçîïëœ.]+)(?:\s*;\s*([A-Za-zÉéèêîôçàù\s\-]+)\.?[\s,]+(\d{1,2})(?:er|eme|e)?[\s]+([a-zA-Zéèêàùûôçîïëœ.]+))?', part)

        if match:
            place = match.group(1).strip()
            day = int(match.group(2))
            raw_month = match.group(3)

            month = None

            if raw_month:
                norm_month = normalize(raw_month)

                # Fuzzy check for 'dito'
                if get_close_matches(norm_month, dito_variants, n=1, cutoff=0.7):
                    month = current_month
                elif norm_month in month_abbr_corrections:
                    corrected = month_abbr_corrections[norm_month]
                    month = french_months[corrected]
                elif norm_month in normalized_months:
                    _, month = normalized_months[norm_month]
                elif get_close_matches(norm_month, fuzzy_cour_variants, n=1, cutoff=0.7):
                    month = pub_date.month
                else:
                    close = get_close_matches(norm_month, normalized_months.keys(), n=1, cutoff=0.6)
                    if not close:
                        return {'status': -1, 'message': f"Unrecognized month in part: {raw_month}"}
                        # return jsonify({'status': -1, 'message': f"Unrecognized month in part: {raw_month}"})
                    _, month = normalized_months[close[0]]
            else:
                # No month string at all — if it's the first entry, fall back to first_departure_date
                if not results:
                    month = first_date.month
                else:
                    month = current_month


            try:
                dep_date = datetime(pub_date.year, month, day)
                current_month = month
                results.append({
                    "port_of_call_place": place,
                    "port_of_call_departure_date": dep_date.strftime('%Y-%m-%d')
                })
            except Exception as e:
                return {'status': -1, 'message': str(e)}
                # return jsonify({'status': -1, 'message': str(e)})

    return {'status': 0, 'value': results}
    # return jsonify({'status': 0, 'value': results})


def compose_date(date_in_ms: int) -> datetime:
    
    # Convert milliseconds to seconds
    seconds = date_in_ms / 1000
    
    # Base date (1970-01-01, 22:00)
    epoch = datetime(1970, 1, 1, 22, 0)
    
    # Calculate the date by adding/subtracting seconds
    delta = timedelta(seconds=seconds)
    date = epoch + delta

    return date


def extract_number_from_ocr_string(ocr_str: str) -> int:
    """
    Extracts the first integer from a string, e.g. "Du 6." -> 6
    """
    match = re.search(r'\d+', ocr_str)
    if match:
        return int(match.group())
    else:
        raise ValueError(f"No day number found in: '{ocr_str}'")



# if __name__ == "__main__":
#     app.run(debug=True)
